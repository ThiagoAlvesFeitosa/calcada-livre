import time
from pathlib import Path

import cv2
import numpy as np
from fastapi.testclient import TestClient

from app.adaptadores.armazenamento_falso import ArmazenamentoFalso
from app.adaptadores.detector_falso import DetectorFalso
from app.config import Configuracao, obter_configuracao
from app.main import app, obter_armazenamento, obter_detector
from app.portas.detector import ResultadoQuadro
from app.processamentos import resetar

TRECHO = "marilia_2026-11-17_trecho-01"


def _configuracao(tmp_path: Path, tamanho_mb: int = 95) -> Configuracao:
    return Configuracao(
        armazenamento="local",
        pasta_saida=str(tmp_path / "saida"),
        pasta_modelos=tmp_path / "modelos",
        tamanho_maximo_video_mb=tamanho_mb,
        caminho_trechos=tmp_path / "trechos.geojson",
    )


def _gravar_geojson(caminho: Path) -> None:
    caminho.write_text(
        """
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "id": "marilia_2026-11-17_trecho-01",
      "properties": {"nome": "Trecho 01"},
      "geometry": {
        "type": "LineString",
        "coordinates": [[-49.9456, -22.2139], [-49.9455, -22.2139]]
      }
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )


def _video_minimo(caminho: Path) -> None:
    escritor = cv2.VideoWriter(str(caminho), cv2.VideoWriter_fourcc(*"mp4v"), 2, (80, 80))
    quadro = np.full((80, 80, 3), 128, dtype=np.uint8)
    escritor.write(quadro)
    escritor.write(quadro)
    escritor.release()


def _preparar(tmp_path: Path, tamanho_mb: int = 95) -> tuple[Configuracao, ArmazenamentoFalso]:
    configuracao = _configuracao(tmp_path, tamanho_mb=tamanho_mb)
    Path(configuracao.pasta_saida).mkdir(parents=True, exist_ok=True)
    _gravar_geojson(configuracao.caminho_trechos)
    mascara = np.ones((80, 80), dtype=bool)
    detector = DetectorFalso([ResultadoQuadro(mascara_calcada=mascara, caixas=[])])
    armazenamento = ArmazenamentoFalso(disponivel=True)
    armazenamento.guardar_colecao_trechos({"type": "FeatureCollection", "features": []})
    app.dependency_overrides[obter_configuracao] = lambda: configuracao
    app.dependency_overrides[obter_armazenamento] = lambda: armazenamento
    app.dependency_overrides[obter_detector] = lambda: detector
    return configuracao, armazenamento


def _esperar_pronto(cliente: TestClient, codigo: str) -> dict:
    for _ in range(80):
        resposta = cliente.get(f"/processamentos/{codigo}")
        assert resposta.status_code == 200
        corpo = resposta.json()
        if corpo["status"] == "pronto":
            return corpo
        if corpo["status"] == "erro":
            raise AssertionError(corpo.get("mensagem"))
        time.sleep(0.05)
    raise AssertionError("processamento não terminou")


def _limpar() -> None:
    app.dependency_overrides.clear()
    resetar()


def test_post_videos_recusa_arquivo_que_nao_e_video(tmp_path: Path) -> None:
    # preparar
    _preparar(tmp_path)
    cliente = TestClient(app)

    # executar
    resposta = cliente.post(
        "/videos",
        data={"lat_inicio": "-22.2", "lon_inicio": "-49.9"},
        files={"video": ("texto.txt", b"nao e video", "text/plain")},
    )

    # verificar
    assert resposta.status_code == 400
    _limpar()


def test_post_videos_recusa_arquivo_acima_do_limite(tmp_path: Path) -> None:
    # preparar
    _preparar(tmp_path, tamanho_mb=0)
    cliente = TestClient(app)
    video = tmp_path / "curto.mp4"
    _video_minimo(video)

    # executar
    resposta = cliente.post(
        "/videos",
        data={"lat_inicio": "-22.2", "lon_inicio": "-49.9"},
        files={"video": ("curto.mp4", video.read_bytes(), "video/mp4")},
    )

    # verificar
    assert resposta.status_code == 400
    _limpar()


def test_post_videos_recusa_trecho_que_nao_existe(tmp_path: Path) -> None:
    # preparar
    _preparar(tmp_path)
    cliente = TestClient(app)
    video = tmp_path / "curto.mp4"
    _video_minimo(video)

    # executar
    resposta = cliente.post(
        "/videos",
        data={
            "lat_inicio": "-22.2",
            "lon_inicio": "-49.9",
            "atualizar": "sim",
            "mesmo_trecho_id": "trecho-inventado",
        },
        files={"video": ("curto.mp4", video.read_bytes(), "video/mp4")},
    )

    # verificar
    assert resposta.status_code == 400
    _limpar()


def test_post_videos_devolve_codigo_na_hora(tmp_path: Path) -> None:
    # preparar
    _preparar(tmp_path)
    cliente = TestClient(app)
    video = tmp_path / "curto.mp4"
    _video_minimo(video)

    # executar
    resposta = cliente.post(
        "/videos",
        data={"lat_inicio": "-22.2", "lon_inicio": "-49.9", "nome": "Rua teste"},
        files={"video": ("curto.mp4", video.read_bytes(), "video/mp4")},
    )

    # verificar
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["status"] == "processando"
    assert corpo["codigo"]
    assert "nota" not in corpo
    _esperar_pronto(cliente, corpo["codigo"])
    _limpar()


def test_video_bruto_e_apagado_depois_do_processamento(tmp_path: Path) -> None:
    # preparar
    _config, armazenamento = _preparar(tmp_path)
    cliente = TestClient(app)
    video = tmp_path / "curto.mp4"
    _video_minimo(video)

    # executar
    resposta = cliente.post(
        "/videos",
        data={"lat_inicio": "-22.2", "lon_inicio": "-49.9", "nome": "Rua teste"},
        files={"video": ("curto.mp4", video.read_bytes(), "video/mp4")},
    )
    corpo = _esperar_pronto(cliente, resposta.json()["codigo"])

    # verificar
    assert corpo["nota"] == 100
    pasta = tmp_path / "saida" / corpo["trecho_id"]
    brutos = [caminho for caminho in tmp_path.rglob("*.mp4") if caminho != video]
    assert brutos == []
    assert (pasta / "resultado.json").exists()
    assert (pasta / "nota.json").exists()
    assert armazenamento.ler_json(corpo["trecho_id"], "nota.json") is not None
    assert not any(chave.endswith(".mp4") for chave in armazenamento.arquivos)
    _limpar()


def test_quadro_com_dois_pontos_devolve_404(tmp_path: Path) -> None:
    # preparar
    _preparar(tmp_path)
    cliente = TestClient(app)

    # executar
    resposta = cliente.get(f"/quadros/{TRECHO}/../../../etc/passwd")

    # verificar
    assert resposta.status_code == 404
    _limpar()
