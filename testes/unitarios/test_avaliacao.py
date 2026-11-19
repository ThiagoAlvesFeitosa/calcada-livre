from app.visao.avaliacao import avaliar


def test_acerto_por_posicao_aceita_classe_errada() -> None:
    # preparar
    gabarito = [
        {"id": 1, "classes": ["sand pile"], "inicio_s": 12, "fim_s": 20},
    ]
    resultado = {"obstaculos": [{"classe": "construction debris", "instante_s": 14.0}]}

    # executar
    metricas = avaliar(resultado, gabarito)

    # verificar
    assert metricas["acertos_posicao"] == 1
    assert metricas["acertos_classe"] == 0
    assert metricas["falsos_positivos"] == 0
    assert metricas["revocacao_posicao"] == 1.0
    assert metricas["revocacao_classe"] == 0.0


def test_cada_marcacao_casa_com_um_item_so() -> None:
    # preparar
    gabarito = [
        {"id": 1, "classes": ["tree"], "inicio_s": 2, "fim_s": 5},
        {"id": 2, "classes": ["cardboard box"], "inicio_s": 2, "fim_s": 6},
    ]
    resultado = {"obstaculos": [{"classe": "tree", "instante_s": 3.0}]}

    # executar
    metricas = avaliar(resultado, gabarito)

    # verificar
    assert metricas["acertos_posicao"] == 1
    assert metricas["acertos_classe"] == 1
    assert metricas["falsos_positivos"] == 0
    assert metricas["revocacao_posicao"] == 0.5


def test_item_fora_do_quadro_nao_entra_na_conta() -> None:
    # preparar
    gabarito = [
        {"id": 1, "classes": ["pole"], "inicio_s": 7, "fim_s": 12, "fora_do_quadro": True},
        {"id": 2, "classes": ["tree"], "inicio_s": 2, "fim_s": 5},
    ]
    resultado = {"obstaculos": [{"classe": "tree", "instante_s": 3.0}]}

    # executar
    metricas = avaliar(resultado, gabarito)

    # verificar
    assert metricas["itens_gabarito"] == 1
    assert metricas["acertos_posicao"] == 1
    assert metricas["falsos_positivos"] == 0
    assert metricas["revocacao_posicao"] == 1.0


def test_marcacao_fora_do_intervalo_e_falso_positivo() -> None:
    # preparar
    gabarito = [
        {"id": 1, "classes": ["pole"], "inicio_s": 7, "fim_s": 12},
    ]
    resultado = {"obstaculos": [{"classe": "pole", "instante_s": 0.0}]}

    # executar
    metricas = avaliar(resultado, gabarito)

    # verificar
    assert metricas["acertos_posicao"] == 0
    assert metricas["acertos_classe"] == 0
    assert metricas["falsos_positivos"] == 1
    assert metricas["precisao_posicao"] == 0.0
