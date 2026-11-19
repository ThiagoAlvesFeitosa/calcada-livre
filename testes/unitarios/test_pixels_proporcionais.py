from app.visao.parametros import (
    LADO_REFERENCIA_PIXELS,
    PIXELS_DILATACAO_REFERENCIA,
    pixels_dilatacao,
)


def test_dilatacao_no_video_deitado_continua_24() -> None:
    # preparar / executar / verificar
    assert LADO_REFERENCIA_PIXELS == 576
    assert pixels_dilatacao(576, 1024) == PIXELS_DILATACAO_REFERENCIA
    assert PIXELS_DILATACAO_REFERENCIA == 24


def test_dilatacao_cresce_com_a_altura_do_quadro() -> None:
    # preparar / executar / verificar
    assert pixels_dilatacao(288, 512) == 12
    assert pixels_dilatacao(1152, 648) == 48
    assert pixels_dilatacao(576, 324) == pixels_dilatacao(576, 1024)
