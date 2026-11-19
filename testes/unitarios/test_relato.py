import time
from pathlib import Path

import cv2
import numpy as np
from fastapi.testclient import TestClient

from app.adaptadores.armazenamento_falso import ArmazenamentoFalso
from app.adaptadores.detector_falso import DetectorFalso
from app.adaptadores.geocodificador_falso import GeocodificadorFalso
from app.config import Configuracao, obter_configuracao
from app.main import app, obter_armazenamento, obter_detector, obter_geocodificador
from app.nota.parametros import NOME_LOCAL_SEM_NOME
from app.portas.detector import ResultadoQuadro
from app.processamentos import resetar
from app.trechos.cadastro import colecao_vazia, nova_feature

LON = -49.9464
LAT = -22.2175


def _video_minimo(caminho: Path) -> None:
    escritor = cv2.VideoWriter(str(caminho), cv2.VideoWriter_fourcc(*"mp4v"), 2, (80, 80))
    quadro = np.full((80, 80, 3), 128, dtype=np.uint8)
    escritor.write(quadro)
    escritor.write(quadro)
    escritor.release()


def _preparar(
    tmp_path: Path,
    nome_rua: str | None = "Rua de teste",
    colecao: dict | None = None,
) -> ArmazenamentoFalso:
    configuracao = Configuracao(
        armazenamento="local",
        pasta_saida=str(tmp_path / "saida"),
        pasta_modelos=tmp_path / "modelos",
        tamanho_maximo_video_mb=95,
        caminho_trechos=tmp_path / "trechos.geojson",
    )
    Path(configuracao.pasta_saida).mkdir(parents=True, exist_ok=True)
    mascara = np.ones((80, 80), dtype=bool)
    detector = DetectorFalso([ResultadoQuadro(mascara_calcada=mascara, caixas=[])])
    armazenamento = ArmazenamentoFalso(disponivel=True)
    armazenamento.guardar_colecao_trechos(colecao or colecao_vazia())
    app.dependency_overrides[obter_configuracao] = lambda: configuracao
    app.dependency_overrides[obter_armazenamento] = lambda: armazenamento
    app.dependency_overrides[obter_detector] = lambda: detector
    app.dependency_overrides[obter_geocodificador] = lambda: GeocodificadorFalso(nome=nome_rua)
    return armazenamento


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


def _enviar(
    cliente: TestClient,
    video: Path,
    lat_fim: str | None = None,
    lon_fim: str | None = None,
    atualizar: str = "",
    mesmo_id: str = "",
    nome: str = "Rua de teste",
    lat: float = LAT,
    lon: float = LON,
) -> dict:
    dados = {
        "lat_inicio": str(lat),
        "lon_inicio": str(lon),
        "nome": nome,
        "atualizar": atualizar,
        "mesmo_trecho_id": mesmo_id,
    }
    if lat_fim is not None:
        dados["lat_fim"] = lat_fim
    if lon_fim is not None:
        dados["lon_fim"] = lon_fim
    return cliente.post(
        "/videos",
        data=dados,
        files={"video": ("curto.mp4", video.read_bytes(), "video/mp4")},
    )


def test_relato_longe_de_tudo_cria_trecho_novo(tmp_path: Path) -> None:
    # preparar
    armazenamento = _preparar(tmp_path)
    cliente = TestClient(app)
    video = tmp_path / "curto.mp4"
    _video_minimo(video)

    # executar
    resposta = _enviar(cliente, video, lat_fim="-22.2176", lon_fim="-49.9465")
    corpo = _esperar_pronto(cliente, resposta.json()["codigo"])

    # verificar
    assert resposta.status_code == 200
    colecao = armazenamento.ler_colecao_trechos()
    assert len(colecao["features"]) == 1
    assert colecao["features"][0]["id"] == corpo["trecho_id"]
    assert colecao["features"][0]["geometry"]["type"] == "LineString"
    _limpar()


def test_pontas_perto_e_confirmado_atualiza_o_mesmo_trecho(tmp_path: Path) -> None:
    # preparar
    existente = nova_feature(
        "Rua de teste",
        {"type": "LineString", "coordinates": [[LON, LAT], [LON + 0.0002, LAT]]},
        trecho_id="trecho-existente",
    )
    armazenamento = _preparar(tmp_path, colecao={"type": "FeatureCollection", "features": [existente]})
    cliente = TestClient(app)
    video = tmp_path / "curto.mp4"
    _video_minimo(video)

    # executar
    resposta = _enviar(
        cliente,
        video,
        lat_fim=str(LAT),
        lon_fim=str(LON + 0.0002),
        atualizar="sim",
        mesmo_id="trecho-existente",
    )
    corpo = _esperar_pronto(cliente, resposta.json()["codigo"])

    # verificar
    assert corpo["trecho_id"] == "trecho-existente"
    assert len(armazenamento.ler_colecao_trechos()["features"]) == 1
    _limpar()


def test_mesmo_lugar_com_nao_cria_trecho_novo(tmp_path: Path) -> None:
    # preparar
    existente = nova_feature(
        "Rua de teste",
        {"type": "LineString", "coordinates": [[LON, LAT], [LON + 0.0002, LAT]]},
        trecho_id="trecho-existente",
    )
    armazenamento = _preparar(tmp_path, colecao={"type": "FeatureCollection", "features": [existente]})
    cliente = TestClient(app)
    video = tmp_path / "curto.mp4"
    _video_minimo(video)

    # executar
    resposta = _enviar(
        cliente,
        video,
        lat_fim=str(LAT),
        lon_fim=str(LON + 0.0002),
        atualizar="nao",
        mesmo_id="trecho-existente",
    )
    corpo = _esperar_pronto(cliente, resposta.json()["codigo"])

    # verificar
    assert corpo["trecho_id"] != "trecho-existente"
    assert len(armazenamento.ler_colecao_trechos()["features"]) == 2
    _limpar()


def test_sem_gps_no_fim_vira_ponto(tmp_path: Path) -> None:
    # preparar
    armazenamento = _preparar(tmp_path)
    cliente = TestClient(app)
    video = tmp_path / "curto.mp4"
    _video_minimo(video)

    # executar
    resposta = _enviar(cliente, video)
    corpo = _esperar_pronto(cliente, resposta.json()["codigo"])

    # verificar
    feature = next(
        item for item in armazenamento.ler_colecao_trechos()["features"] if item["id"] == corpo["trecho_id"]
    )
    assert feature["geometry"]["type"] == "Point"
    _limpar()


def test_geocodificador_que_falha_devolve_local_sem_nome(tmp_path: Path) -> None:
    # preparar
    _preparar(tmp_path, nome_rua=None)
    cliente = TestClient(app)

    # executar
    resposta = cliente.get("/endereco", params={"lat": LAT, "lon": LON})

    # verificar
    assert resposta.status_code == 200
    assert resposta.json()["nome"] == NOME_LOCAL_SEM_NOME
    _limpar()
