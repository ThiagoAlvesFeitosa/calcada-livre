from app.nota.parametros import DISTANCIA_MAXIMA_TRECHO_M
from app.trechos.geometria import carregar_colecao, trecho_mais_proximo
from app.config import RAIZ


def test_ponto_perto_do_trecho_02_escolhe_o_02() -> None:
    # preparar
    colecao = carregar_colecao(RAIZ / "dados" / "trechos.geojson")
    # meio da linha do trecho 02 no GeoJSON
    lon, lat = -49.94625, -22.21750

    # executar
    achado = trecho_mais_proximo(colecao, lon, lat, maximo_m=DISTANCIA_MAXIMA_TRECHO_M)

    # verificar
    assert achado is not None
    assert achado["id"] == "marilia_2026-11-17_trecho-02"


def test_ponto_longe_de_todos_nao_escolhe_nenhum() -> None:
    # preparar
    colecao = carregar_colecao(RAIZ / "dados" / "trechos.geojson")
    lon, lat = -46.633, -23.550

    # executar
    achado = trecho_mais_proximo(colecao, lon, lat, maximo_m=DISTANCIA_MAXIMA_TRECHO_M)

    # verificar
    assert achado is None
