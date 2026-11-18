from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import tempfile

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.adaptadores.armazenamento_local import ArmazenamentoLocal
from app.config import RAIZ, Configuracao, obter_configuracao
from app.nota.parametros import (
    BYTES_POR_MEGABYTE,
    CENSO_CALCADA_DESOBSTRUIDA,
    COR_AMARELO,
    COR_CINZA,
    COR_VERDE,
    COR_VERMELHO,
    EXTENSOES_VIDEO,
)
from app.nota.regras import calcular_nota
from app.portas.armazenamento import Armazenamento
from app.portas.detector import Detector
from app.trechos.consulta import (
    carregar_trechos,
    detalhe_do_trecho,
    formatar_data_brasilia,
    geojson_com_notas,
    resumo_censo,
)
from app.trechos.geometria import comprimento_do_trecho, ids_dos_trechos, trecho_mais_proximo
from app.visao.pipeline import processar_video

PASTA_WEB = RAIZ / "app" / "web"

app = FastAPI(title="FIAP Calçada Livre")
app.mount("/estatico", StaticFiles(directory=PASTA_WEB), name="estatico")

_detector_real: Detector | None = None


def obter_armazenamento(
    configuracao: Configuracao = Depends(obter_configuracao),
) -> Armazenamento:
    if configuracao.armazenamento == "local":
        return ArmazenamentoLocal(pasta=configuracao.pasta_saida)
    raise RuntimeError("Armazenamento ainda não implementado.")


def obter_detector() -> Detector:
    global _detector_real
    if _detector_real is None:
        from app.adaptadores.detector_real import DetectorReal

        _detector_real = DetectorReal()
    return _detector_real


def _eh_video(arquivo: UploadFile) -> bool:
    tipo = (arquivo.content_type or "").lower()
    if tipo.startswith("video/"):
        return True
    nome = Path(arquivo.filename or "").suffix.lower()
    return nome in EXTENSOES_VIDEO


@app.get("/saude")
def saude(armazenamento: Armazenamento = Depends(obter_armazenamento)) -> dict[str, str]:
    try:
        disponivel = armazenamento.verificar()
    except Exception:
        disponivel = False
    return {
        "status": "ok",
        "armazenamento": "ok" if disponivel else "falha",
    }


@app.get("/", response_class=HTMLResponse)
def pagina_coleta() -> FileResponse:
    return FileResponse(PASTA_WEB / "coleta.html")


@app.get("/painel", response_class=HTMLResponse)
def pagina_painel() -> FileResponse:
    return FileResponse(PASTA_WEB / "painel.html")


@app.get("/trechos")
def listar_trechos(configuracao: Configuracao = Depends(obter_configuracao)) -> dict:
    colecao = carregar_trechos(configuracao.caminho_trechos)
    return geojson_com_notas(Path(configuracao.pasta_saida), colecao)


@app.get("/localizacao")
def localizacao(
    lat: float,
    lon: float,
    configuracao: Configuracao = Depends(obter_configuracao),
) -> dict:
    colecao = carregar_trechos(configuracao.caminho_trechos)
    achado = trecho_mais_proximo(colecao, lon, lat)
    return {"trecho": achado}


@app.get("/trechos/{trecho_id}")
def detalhe(trecho_id: str, configuracao: Configuracao = Depends(obter_configuracao)) -> dict:
    colecao = carregar_trechos(configuracao.caminho_trechos)
    detalhe = detalhe_do_trecho(Path(configuracao.pasta_saida), colecao, trecho_id)
    if detalhe is None:
        raise HTTPException(status_code=404, detail="Trecho não encontrado.")
    return detalhe


@app.get("/censo")
def censo(configuracao: Configuracao = Depends(obter_configuracao)) -> dict:
    colecao = carregar_trechos(configuracao.caminho_trechos)
    resumo = resumo_censo(Path(configuracao.pasta_saida), colecao)
    return {
        "sem_obstaculo": resumo["sem_obstaculo"],
        "filmados": resumo["filmados"],
        "censo": CENSO_CALCADA_DESOBSTRUIDA,
        "cores": {
            "verde": COR_VERDE,
            "amarelo": COR_AMARELO,
            "vermelho": COR_VERMELHO,
            "cinza": COR_CINZA,
        },
    }


@app.get("/quadros/{trecho_id}/{nome:path}")
def quadro(
    trecho_id: str,
    nome: str,
    configuracao: Configuracao = Depends(obter_configuracao),
) -> FileResponse:
    if ".." in trecho_id or ".." in nome or Path(nome).name != nome:
        raise HTTPException(status_code=404)
    if not nome.lower().endswith(".png"):
        raise HTTPException(status_code=404)
    colecao = carregar_trechos(configuracao.caminho_trechos)
    if trecho_id not in ids_dos_trechos(colecao):
        raise HTTPException(status_code=404)
    caminho = (Path(configuracao.pasta_saida) / trecho_id / "quadros" / nome).resolve()
    raiz_quadros = (Path(configuracao.pasta_saida) / trecho_id / "quadros").resolve()
    if raiz_quadros not in caminho.parents and caminho.parent != raiz_quadros:
        raise HTTPException(status_code=404)
    if not caminho.is_file():
        raise HTTPException(status_code=404)
    return FileResponse(caminho)


@app.post("/videos")
async def enviar_video(
    trecho_id: str = Form(...),
    video: UploadFile = File(...),
    configuracao: Configuracao = Depends(obter_configuracao),
    detector: Detector = Depends(obter_detector),
) -> dict:
    colecao = carregar_trechos(configuracao.caminho_trechos)
    if trecho_id not in ids_dos_trechos(colecao):
        raise HTTPException(status_code=400, detail="Trecho não existe.")
    if not _eh_video(video):
        raise HTTPException(status_code=400, detail="Arquivo não é vídeo.")
    conteudo = await video.read()
    limite = configuracao.tamanho_maximo_video_mb * BYTES_POR_MEGABYTE
    if len(conteudo) > limite or configuracao.tamanho_maximo_video_mb <= 0:
        raise HTTPException(status_code=400, detail="Vídeo acima do tamanho máximo.")

    sufixo = Path(video.filename or "envio.mp4").suffix or ".mp4"
    bruto = tempfile.NamedTemporaryFile(delete=False, suffix=sufixo)
    caminho_bruto = Path(bruto.name)
    try:
        bruto.write(conteudo)
        bruto.close()
        resultado = processar_video(
            caminho_bruto,
            detector,
            configuracao.pasta_saida,
            identificador=trecho_id,
        )
        comprimento = comprimento_do_trecho(colecao, trecho_id)
        if comprimento <= 0:
            raise HTTPException(status_code=400, detail="Trecho sem comprimento no mapa.")
        nota = calcular_nota(list(resultado.get("obstaculos", [])), comprimento)
        nota["data"] = datetime.now(timezone.utc).isoformat()
        nota["comprimento_m"] = comprimento
        pasta = Path(configuracao.pasta_saida) / trecho_id
        pasta.mkdir(parents=True, exist_ok=True)
        (pasta / "nota.json").write_text(
            json.dumps(nota, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        resposta = {"trecho_id": trecho_id, **nota}
        resposta["data"] = formatar_data_brasilia(nota["data"])
        return resposta
    finally:
        caminho_bruto.unlink(missing_ok=True)


