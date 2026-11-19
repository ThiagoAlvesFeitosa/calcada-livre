from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
import json
import tempfile
import threading
import uuid

import cv2

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, ConfigDict
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles

from app.config import (
    INTERVALO_ANDAMENTO_S,
    RAIZ,
    Configuracao,
    conferir_configuracao,
    criar_armazenamento,
    obter_configuracao,
)
from app.nota.parametros import (
    BYTES_POR_MEGABYTE,
    CENSO_CALCADA_DESOBSTRUIDA,
    COR_AMARELO,
    COR_CINZA,
    COR_VERDE,
    COR_VERMELHO,
    EXTENSOES_VIDEO,
    GPS_ESPERA_S,
    GPS_ESPERA_SEM_PRECISAO_S,
    GPS_IDADE_MAXIMA_S,
    MENSAGEM_DIGITE_ENDERECO,
    MENSAGEM_ENDERECO_NAO_ENCONTRADO,
    MOTIVOS_GPS,
    NOME_LOCAL_SEM_NOME,
)
from app.nota.regras import calcular_nota
from app.portas.armazenamento import Armazenamento
from app.portas.detector import Detector
from app.portas.geocodificador import Geocodificador
from app.processamentos import marcar_erro, marcar_pronto, obter, registrar, trava_visao
from app.registro import configurar_registro, registrar_falha, registrar_gps
from app.trechos.cadastro import (
    acrescentar_feature,
    candidato_mesmo_trecho,
    comprimento_efetivo,
    geometria_do_relato,
    nova_feature,
    trava_cadastro,
)
from app.trechos.consulta import (
    detalhe_do_trecho,
    formatar_data_brasilia,
    geojson_com_notas,
    nota_do_trecho,
    resumo_censo,
)
from app.trechos.geometria import (
    comprimento_do_trecho,
    feature_por_id,
    ids_dos_trechos,
    trecho_mais_proximo,
)
from app.visao.pipeline import processar_video

PASTA_WEB = RAIZ / "app" / "web"


class PedidoRegistroGps(BaseModel):
    model_config = ConfigDict(extra="ignore")
    codigo: int


@asynccontextmanager
async def lifespan(_app: FastAPI):
    conferir_configuracao()
    configurar_registro(obter_configuracao().pasta_saida)
    yield


app = FastAPI(title="FIAP Calçada Livre", lifespan=lifespan)
app.mount("/estatico", StaticFiles(directory=PASTA_WEB), name="estatico")

_detector_real: Detector | None = None


def obter_armazenamento(
    configuracao: Configuracao = Depends(obter_configuracao),
) -> Armazenamento:
    return criar_armazenamento(configuracao)


_geocodificador_real: Geocodificador | None = None


def obter_geocodificador() -> Geocodificador:
    global _geocodificador_real
    if _geocodificador_real is None:
        from app.adaptadores.geocodificador_nominatim import GeocodificadorNominatim

        _geocodificador_real = GeocodificadorNominatim()
    return _geocodificador_real


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


def _float_opcional(valor: str | None) -> float | None:
    if valor is None:
        return None
    texto = str(valor).strip()
    if texto == "":
        return None
    return float(texto)


def _colecao(armazenamento: Armazenamento) -> dict:
    return armazenamento.ler_colecao_trechos()


def _trabalhar(
    codigo: str,
    caminho_bruto: Path,
    trecho_id: str,
    pasta_saida: str,
    comprimento_gps: float,
    eh_ponto: bool,
    detector: Detector,
    armazenamento: Armazenamento,
) -> None:
    etapa = "leitura do vídeo"
    try:
        with trava_visao:
            etapa = "leitura do vídeo"
            captura = cv2.VideoCapture(str(caminho_bruto))
            aberto = captura.isOpened()
            captura.release()
            if not aberto:
                raise RuntimeError("vídeo ilegível")
            etapa = "visão"
            resultado = processar_video(
                caminho_bruto,
                detector,
                pasta_saida,
                identificador=trecho_id,
            )
            etapa = "nota"
            duracao = float(resultado.get("duracao_s") or 0)
            comprimento, origem = comprimento_efetivo(comprimento_gps, duracao, eh_ponto)
            nota = calcular_nota(list(resultado.get("obstaculos", [])), comprimento)
            nota["data"] = datetime.now(timezone.utc).isoformat()
            nota["comprimento_m"] = comprimento
            nota["comprimento_origem"] = origem
            etapa = "gravação no armazenamento"
            pasta = Path(pasta_saida) / trecho_id
            pasta.mkdir(parents=True, exist_ok=True)
            (pasta / "nota.json").write_text(
                json.dumps(nota, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            armazenamento.guardar_trecho(trecho_id, pasta)
        resposta = {"trecho_id": trecho_id, **nota}
        resposta["data"] = formatar_data_brasilia(nota["data"])
        marcar_pronto(codigo, resposta)
    except Exception as erro:
        registrar_falha(pasta_saida, codigo, etapa, erro)
        marcar_erro(codigo, "Não foi possível processar. Tente de novo.")
    finally:
        caminho_bruto.unlink(missing_ok=True)


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
def listar_trechos(
    configuracao: Configuracao = Depends(obter_configuracao),
    armazenamento: Armazenamento = Depends(obter_armazenamento),
) -> dict:
    return geojson_com_notas(armazenamento, _colecao(armazenamento))


@app.get("/localizacao")
def localizacao(
    lat: float,
    lon: float,
    armazenamento: Armazenamento = Depends(obter_armazenamento),
) -> dict:
    achado = trecho_mais_proximo(_colecao(armazenamento), lon, lat)
    return {"trecho": achado}


def _parametros_gps() -> dict:
    return {
        "gps_espera_s": GPS_ESPERA_S,
        "gps_espera_sem_precisao_s": GPS_ESPERA_SEM_PRECISAO_S,
        "gps_idade_maxima_s": GPS_IDADE_MAXIMA_S,
        "mensagem_digite_endereco": MENSAGEM_DIGITE_ENDERECO,
        "mensagem_endereco_nao_encontrado": MENSAGEM_ENDERECO_NAO_ENCONTRADO,
        "motivos_gps": {str(codigo): texto for codigo, texto in MOTIVOS_GPS.items()},
    }


@app.post("/registro-gps")
def registro_gps(
    pedido: PedidoRegistroGps,
    configuracao: Configuracao = Depends(obter_configuracao),
) -> dict:
    registrar_gps(configuracao.pasta_saida, pedido.codigo)
    return {"ok": True}


@app.get("/endereco")
def endereco(
    lat: float | None = None,
    lon: float | None = None,
    q: str | None = None,
    geocodificador: Geocodificador = Depends(obter_geocodificador),
) -> dict:
    base = _parametros_gps()
    if q is not None and str(q).strip():
        ponto = geocodificador.ponto_do_endereco(str(q).strip())
        if not ponto:
            return {
                **base,
                "encontrado": False,
                "mensagem": MENSAGEM_ENDERECO_NAO_ENCONTRADO,
            }
        return {
            **base,
            "encontrado": True,
            "nome": ponto["nome"],
            "lat": ponto["lat"],
            "lon": ponto["lon"],
        }
    if lat is not None and lon is not None:
        nome = geocodificador.nome_da_rua(lat, lon)
        return {**base, "nome": nome}
    return base


@app.get("/trechos/candidatos")
def candidatos(
    lat_inicio: float,
    lon_inicio: float,
    rua: str = "",
    lat_fim: float | None = None,
    lon_fim: float | None = None,
    armazenamento: Armazenamento = Depends(obter_armazenamento),
) -> dict:
    colecao = _colecao(armazenamento)
    achado = candidato_mesmo_trecho(colecao, lon_inicio, lat_inicio, lon_fim, lat_fim, rua)
    if achado is None:
        return {"candidato": None}
    nota = nota_do_trecho(armazenamento, colecao, achado["id"])
    if nota and nota.get("data"):
        achado["data"] = formatar_data_brasilia(nota["data"])
    return {"candidato": achado}


@app.get("/trechos/{trecho_id}")
def detalhe(
    trecho_id: str,
    configuracao: Configuracao = Depends(obter_configuracao),
    armazenamento: Armazenamento = Depends(obter_armazenamento),
) -> dict:
    detalhe = detalhe_do_trecho(armazenamento, _colecao(armazenamento), trecho_id)
    if detalhe is None:
        raise HTTPException(status_code=404, detail="Trecho não encontrado.")
    return detalhe


@app.get("/censo")
def censo(
    configuracao: Configuracao = Depends(obter_configuracao),
    armazenamento: Armazenamento = Depends(obter_armazenamento),
) -> dict:
    resumo = resumo_censo(armazenamento, _colecao(armazenamento))
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
    armazenamento: Armazenamento = Depends(obter_armazenamento),
) -> Response:
    if ".." in trecho_id or ".." in nome or Path(nome).name != nome:
        raise HTTPException(status_code=404)
    if not nome.lower().endswith(".png"):
        raise HTTPException(status_code=404)
    if trecho_id not in ids_dos_trechos(_colecao(armazenamento)):
        raise HTTPException(status_code=404)
    dados = armazenamento.ler_quadro(trecho_id, nome)
    if not dados:
        raise HTTPException(status_code=404)
    return Response(content=dados, media_type="image/png")


@app.get("/processamentos/{codigo}")
def andamento(codigo: str) -> dict:
    registro = obter(codigo)
    if registro is None:
        raise HTTPException(status_code=404, detail="Processamento não encontrado.")
    return registro


@app.post("/videos")
async def enviar_video(
    video: UploadFile = File(...),
    lat_inicio: str = Form(...),
    lon_inicio: str = Form(...),
    lat_fim: str | None = Form(None),
    lon_fim: str | None = Form(None),
    nome: str = Form(""),
    atualizar: str = Form(""),
    mesmo_trecho_id: str = Form(""),
    configuracao: Configuracao = Depends(obter_configuracao),
    detector: Detector = Depends(obter_detector),
    armazenamento: Armazenamento = Depends(obter_armazenamento),
) -> dict:
    if not _eh_video(video):
        raise HTTPException(status_code=400, detail="Arquivo não é vídeo.")
    conteudo = await video.read()
    limite = configuracao.tamanho_maximo_video_mb * BYTES_POR_MEGABYTE
    if len(conteudo) > limite or configuracao.tamanho_maximo_video_mb <= 0:
        raise HTTPException(status_code=400, detail="Vídeo acima do tamanho máximo.")
    try:
        lat_i = float(lat_inicio)
        lon_i = float(lon_inicio)
    except ValueError:
        raise HTTPException(status_code=400, detail="Localização inicial inválida.")
    lat_f = _float_opcional(lat_fim)
    lon_f = _float_opcional(lon_fim)
    nome_rua = (nome or "").strip() or NOME_LOCAL_SEM_NOME

    with trava_cadastro():
        colecao = _colecao(armazenamento)
        if atualizar.strip().lower() == "sim" and mesmo_trecho_id.strip():
            trecho_id = mesmo_trecho_id.strip()
            if trecho_id not in ids_dos_trechos(colecao):
                raise HTTPException(status_code=400, detail="Trecho não existe.")
        else:
            feature = nova_feature(nome_rua, geometria_do_relato(lon_i, lat_i, lon_f, lat_f))
            trecho_id = str(feature["id"])
            colecao = acrescentar_feature(colecao, feature)
            armazenamento.guardar_colecao_trechos(colecao)
        comprimento_gps = comprimento_do_trecho(colecao, trecho_id)
        feature = feature_por_id(colecao, trecho_id) or {}
        eh_ponto = (feature.get("geometry") or {}).get("type") == "Point"

    sufixo = Path(video.filename or "envio.mp4").suffix or ".mp4"
    bruto = tempfile.NamedTemporaryFile(delete=False, suffix=sufixo)
    caminho_bruto = Path(bruto.name)
    bruto.write(conteudo)
    bruto.close()

    codigo = uuid.uuid4().hex
    registrar(codigo)
    trabalhador = threading.Thread(
        target=_trabalhar,
        args=(
            codigo,
            caminho_bruto,
            trecho_id,
            configuracao.pasta_saida,
            comprimento_gps,
            eh_ponto,
            detector,
            armazenamento,
        ),
        daemon=True,
    )
    trabalhador.start()
    return {
        "codigo": codigo,
        "status": "processando",
        "intervalo_s": INTERVALO_ANDAMENTO_S,
        "trecho_id": trecho_id,
    }

