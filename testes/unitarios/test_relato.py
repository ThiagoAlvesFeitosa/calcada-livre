import json
import math
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
from app.nota.parametros import COMPRIMENTO_PONTO_M, RAIO_TERRA_M
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


def _processar_com_duracao(duracao_s: float):
    def _falso(caminho, detector, pasta_saida, identificador=None):
        pasta = Path(pasta_saida) / identificador
        (pasta / "quadros").mkdir(parents=True, exist_ok=True)
        resultado = {"obstaculos": [], "duracao_s": duracao_s}
        (pasta / "resultado.json").write_text(
            json.dumps(resultado, ensure_ascii=False),
            encoding="utf-8",
        )
        return resultado

    return _falso


def _preparar(
    tmp_path: Path,
    nome_rua: str | None = "Rua de teste",
    colecao: dict | None = None,
    ponto_busca: dict | None = None,
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
    geocodificador = GeocodificadorFalso(nome=nome_rua, ponto=ponto_busca)
    app.dependency_overrides[obter_geocodificador] = lambda: geocodificador
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


def test_geocodificador_que_falha_nao_mostra_local_sem_nome(tmp_path: Path) -> None:
    # preparar
    _preparar(tmp_path, nome_rua=None)
    cliente = TestClient(app)

    # executar
    resposta = cliente.get("/endereco", params={"lat": LAT, "lon": LON})

    # verificar
    assert resposta.status_code == 200
    assert not resposta.json().get("nome")
    _limpar()


def test_trecho_ponto_com_video_de_30s_fica_com_30m(tmp_path: Path, monkeypatch) -> None:
    # preparar
    armazenamento = _preparar(tmp_path)
    monkeypatch.setattr("app.main.processar_video", _processar_com_duracao(30))
    cliente = TestClient(app)
    video = tmp_path / "curto.mp4"
    _video_minimo(video)

    # executar
    resposta = _enviar(cliente, video)
    corpo = _esperar_pronto(cliente, resposta.json()["codigo"])
    nota = armazenamento.ler_json(corpo["trecho_id"], "nota.json")

    # verificar
    assert nota["comprimento_m"] == 30
    assert nota["comprimento_origem"] == "estimado pela duração"
    _limpar()


def test_trecho_ponto_com_video_de_4s_fica_com_10m(tmp_path: Path, monkeypatch) -> None:
    # preparar
    armazenamento = _preparar(tmp_path)
    monkeypatch.setattr("app.main.processar_video", _processar_com_duracao(4))
    cliente = TestClient(app)
    video = tmp_path / "curto.mp4"
    _video_minimo(video)

    # executar
    resposta = _enviar(cliente, video)
    corpo = _esperar_pronto(cliente, resposta.json()["codigo"])
    nota = armazenamento.ler_json(corpo["trecho_id"], "nota.json")

    # verificar
    assert nota["comprimento_m"] == COMPRIMENTO_PONTO_M
    assert nota["comprimento_origem"] == "estimado pela duração"
    _limpar()


def test_linha_com_gps_de_50m_continua_com_50m(tmp_path: Path, monkeypatch) -> None:
    # preparar
    armazenamento = _preparar(tmp_path)
    monkeypatch.setattr("app.main.processar_video", _processar_com_duracao(4))
    metros_por_grau = RAIO_TERRA_M * math.cos(math.radians(LAT)) * math.pi / 180
    lon_fim = LON + 50 / metros_por_grau
    cliente = TestClient(app)
    video = tmp_path / "curto.mp4"
    _video_minimo(video)

    # executar
    resposta = _enviar(cliente, video, lat_fim=str(LAT), lon_fim=str(lon_fim))
    corpo = _esperar_pronto(cliente, resposta.json()["codigo"])
    nota = armazenamento.ler_json(corpo["trecho_id"], "nota.json")

    # verificar
    assert abs(nota["comprimento_m"] - 50) < 0.5
    assert nota["comprimento_origem"] == "gps"
    _limpar()


def test_endereco_digitado_vira_ponto(tmp_path: Path, monkeypatch) -> None:
    # preparar
    ponto = {"lat": LAT, "lon": LON, "nome": "Rua digitada"}
    armazenamento = _preparar(tmp_path, ponto_busca=ponto)
    monkeypatch.setattr("app.main.processar_video", _processar_com_duracao(12))
    cliente = TestClient(app)
    video = tmp_path / "curto.mp4"
    _video_minimo(video)

    # executar
    busca = cliente.get("/endereco", params={"q": "Rua digitada, Marília"})
    resposta = _enviar(
        cliente,
        video,
        lat=busca.json()["lat"],
        lon=busca.json()["lon"],
        nome=busca.json()["nome"],
    )
    corpo = _esperar_pronto(cliente, resposta.json()["codigo"])
    feature = next(
        item for item in armazenamento.ler_colecao_trechos()["features"] if item["id"] == corpo["trecho_id"]
    )

    # verificar
    assert busca.json()["encontrado"] is True
    assert feature["geometry"]["type"] == "Point"
    assert feature["geometry"]["coordinates"] == [LON, LAT]
    _limpar()


def test_endereco_nao_encontrado_mostra_a_mensagem(tmp_path: Path) -> None:
    # preparar
    _preparar(tmp_path, ponto_busca=None)
    cliente = TestClient(app)

    # executar
    resposta = cliente.get("/endereco", params={"q": "rua que nao existe xyz"})

    # verificar
    assert resposta.status_code == 200
    assert resposta.json()["encontrado"] is False
    assert resposta.json()["mensagem"] == "Endereço não encontrado, confira e tente de novo"
    _limpar()


def test_erro_no_processamento_grava_linha_no_log_com_a_etapa(tmp_path: Path) -> None:
    # preparar
    _preparar(tmp_path)

    class DetectorQuebra:
        def analisar(self, quadro, instante_s):
            raise RuntimeError("falha de teste")

    app.dependency_overrides[obter_detector] = lambda: DetectorQuebra()
    cliente = TestClient(app)
    video = tmp_path / "curto.mp4"
    _video_minimo(video)

    # executar
    resposta = _enviar(cliente, video)
    codigo = resposta.json()["codigo"]
    for _ in range(80):
        andamento = cliente.get(f"/processamentos/{codigo}").json()
        if andamento["status"] == "erro":
            break
        time.sleep(0.05)
    log = (tmp_path / "saida" / "logs" / "app.log").read_text(encoding="utf-8")

    # verificar
    assert andamento["status"] == "erro"
    assert codigo in log
    assert "visão" in log or "visao" in log
    assert "RuntimeError" in log
    _limpar()


def test_registro_gps_grava_so_o_codigo_sem_coordenada(tmp_path: Path) -> None:
    # preparar
    _preparar(tmp_path)
    cliente = TestClient(app)

    # executar
    resposta = cliente.post(
        "/registro-gps",
        json={"codigo": 1, "lat": LAT, "lon": LON},
    )
    log = (tmp_path / "saida" / "logs" / "app.log").read_text(encoding="utf-8")

    # verificar
    assert resposta.status_code == 200
    assert "gps codigo=1" in log
    assert str(LAT) not in log
    assert str(LON) not in log
    _limpar()
