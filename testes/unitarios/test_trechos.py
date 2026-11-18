import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.adaptadores.armazenamento_falso import ArmazenamentoFalso
from app.config import Configuracao, obter_configuracao
from app.main import app, obter_armazenamento

TRECHO_A = "marilia_2026-11-17_trecho-01"
TRECHO_B = "face-sem-video"


def _preparar(tmp_path: Path) -> ArmazenamentoFalso:
    geojson = tmp_path / "trechos.geojson"
    geojson.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "id": TRECHO_A,
                        "properties": {"nome": "Filmado"},
                        "geometry": {
                            "type": "LineString",
                            "coordinates": [[-49.9465, -22.2175], [-49.9464, -22.2175]],
                        },
                    },
                    {
                        "type": "Feature",
                        "id": TRECHO_B,
                        "properties": {"nome": "Sem vídeo"},
                        "geometry": {
                            "type": "LineString",
                            "coordinates": [[-49.9465, -22.2174], [-49.9464, -22.2174]],
                        },
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    pasta = tmp_path / "origem" / TRECHO_A
    pasta.mkdir(parents=True)
    (pasta / "resultado.json").write_text(
        json.dumps({"obstaculos": []}),
        encoding="utf-8",
    )
    (pasta / "nota.json").write_text(
        json.dumps({"nota": 100, "cor": "verde", "obstaculos_por_100m": 0}),
        encoding="utf-8",
    )
    quadros = pasta / "quadros"
    quadros.mkdir()
    (quadros / "0000_0.0s.png").write_bytes(b"png-mosaico")
    armazenamento = ArmazenamentoFalso(True)
    armazenamento.guardar_trecho(TRECHO_A, pasta)
    configuracao = Configuracao(
        armazenamento="supabase",
        pasta_saida=str(tmp_path / "disco-vazio"),
        pasta_modelos=tmp_path / "modelos",
        tamanho_maximo_video_mb=95,
        caminho_trechos=geojson,
    )
    app.dependency_overrides[obter_configuracao] = lambda: configuracao
    app.dependency_overrides[obter_armazenamento] = lambda: armazenamento
    return armazenamento


def test_get_trechos_devolve_geojson_com_a_nota_mais_recente(tmp_path: Path) -> None:
    # preparar
    _preparar(tmp_path)
    cliente = TestClient(app)

    # executar
    resposta = cliente.get("/trechos")

    # verificar
    assert resposta.status_code == 200
    corpo = resposta.json()
    por_id = {item["id"]: item["properties"] for item in corpo["features"]}
    assert por_id[TRECHO_A]["nota"] == 100
    assert por_id[TRECHO_A]["cor"] == "verde"
    assert por_id[TRECHO_B]["nota"] is None
    assert por_id[TRECHO_B]["cor"] is None
    app.dependency_overrides.clear()


def test_get_quadro_le_do_armazenamento_e_nao_do_disco(tmp_path: Path) -> None:
    # preparar
    _preparar(tmp_path)
    cliente = TestClient(app)

    # executar
    resposta = cliente.get(f"/quadros/{TRECHO_A}/0000_0.0s.png")

    # verificar
    assert resposta.status_code == 200
    assert resposta.content == b"png-mosaico"
    app.dependency_overrides.clear()
