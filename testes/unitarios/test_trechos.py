import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.adaptadores.armazenamento_falso import ArmazenamentoFalso
from app.config import Configuracao, obter_configuracao
from app.main import app, obter_armazenamento

TRECHO_A = "marilia_2026-11-17_trecho-01"
TRECHO_B = "face-sem-video"


def _preparar(tmp_path: Path) -> None:
    saida = tmp_path / "saida"
    saida.mkdir()
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
    pasta = saida / TRECHO_A
    pasta.mkdir()
    (pasta / "resultado.json").write_text(
        json.dumps({"obstaculos": []}),
        encoding="utf-8",
    )
    configuracao = Configuracao(
        armazenamento="local",
        pasta_saida=str(saida),
        pasta_modelos=tmp_path / "modelos",
        tamanho_maximo_video_mb=200,
        caminho_trechos=geojson,
    )
    app.dependency_overrides[obter_configuracao] = lambda: configuracao
    app.dependency_overrides[obter_armazenamento] = lambda: ArmazenamentoFalso(True)


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
