from app.trechos.geometria import ponto_na_linha


def test_ponto_na_metade_da_linha() -> None:
    # preparar
    linha = [[-49.9465, -22.2175], [-49.9463, -22.2175]]

    # executar
    lon, lat = ponto_na_linha(linha, 0.5)

    # verificar
    assert round(lon, 5) == -49.9464
    assert round(lat, 5) == -22.2175
