from app.visao.recorte import (
    gabarito_do_recorte,
    recorte_central_9_16,
)


def test_recorte_central_9_16_em_video_deitado() -> None:
    # preparar / executar
    x1, y1, x2, y2 = recorte_central_9_16(1024, 576)

    # verificar
    assert y1 == 0
    assert y2 == 576
    assert x2 - x1 == 324
    assert x1 == (1024 - 324) // 2


def test_gabarito_marca_item_fora_do_recorte() -> None:
    # preparar
    recorte = recorte_central_9_16(1024, 576)
    original = [
        {"id": 1, "classes": ["pole"], "inicio_s": 7, "fim_s": 12},
        {"id": 2, "classes": ["tree"], "inicio_s": 2, "fim_s": 5},
    ]
    deteccoes = [
        {
            "classe": "pole",
            "instante_s": 8.0,
            "x1": 10,
            "y1": 100,
            "x2": 40,
            "y2": 400,
            "confianca": 0.4,
            "na_calcada": True,
        },
        {
            "classe": "tree",
            "instante_s": 3.0,
            "x1": 480,
            "y1": 100,
            "x2": 520,
            "y2": 400,
            "confianca": 0.4,
            "na_calcada": True,
        },
    ]

    # executar
    saida = gabarito_do_recorte(original, deteccoes, recorte)

    # verificar
    por_id = {item["id"]: item for item in saida}
    assert por_id[1]["fora_do_quadro"] is True
    assert por_id[2].get("fora_do_quadro") is not True
