from app.nota.regras import calcular_nota, cor_da_nota


def test_trecho_sem_obstaculo_tem_nota_100() -> None:
    # preparar
    obstaculos: list[dict] = []

    # executar
    resultado = calcular_nota(obstaculos, comprimento_m=100)

    # verificar
    assert resultado["nota"] == 100
    assert resultado["cor"] == "verde"
    assert resultado["obstaculos_por_100m"] == 0
    assert resultado["faixa_livre_media"] == 1.0


def test_obstaculo_que_bloqueia_mais_da_metade_desconta_mais_que_parcial() -> None:
    # preparar
    bloqueio = [{"classe": "tree", "ocupacao_faixa": 0.6}]
    parcial = [{"classe": "tree", "ocupacao_faixa": 0.3}]

    # executar
    nota_bloqueio = calcular_nota(bloqueio, comprimento_m=100)
    nota_parcial = calcular_nota(parcial, comprimento_m=100)

    # verificar
    assert nota_bloqueio["nota"] < nota_parcial["nota"]
    assert nota_parcial["nota"] < 100


def test_buraco_e_degrau_descontam_como_barreira() -> None:
    # preparar
    ocupacao_baixa = 0.2
    poste = [{"classe": "pole", "ocupacao_faixa": ocupacao_baixa}]
    buraco = [{"classe": "pothole", "ocupacao_faixa": ocupacao_baixa}]
    degrau = [{"classe": "stairs", "ocupacao_faixa": ocupacao_baixa}]

    # executar
    nota_poste = calcular_nota(poste, comprimento_m=100)
    nota_buraco = calcular_nota(buraco, comprimento_m=100)
    nota_degrau = calcular_nota(degrau, comprimento_m=100)

    # verificar
    assert nota_buraco["nota"] == nota_degrau["nota"]
    assert nota_buraco["nota"] < nota_poste["nota"]


def test_nota_nunca_fica_negativa() -> None:
    # preparar
    obstaculos = [{"classe": "tree", "ocupacao_faixa": 0.9} for _ in range(20)]

    # executar
    resultado = calcular_nota(obstaculos, comprimento_m=10)

    # verificar
    assert resultado["nota"] >= 0


def test_nota_considera_comprimento_do_trecho() -> None:
    # preparar
    obstaculos = [{"classe": "tree", "ocupacao_faixa": 0.3}]

    # executar
    curto = calcular_nota(obstaculos, comprimento_m=50)
    longo = calcular_nota(obstaculos, comprimento_m=100)

    # verificar
    assert curto["nota"] < longo["nota"]
    assert curto["obstaculos_por_100m"] == 2
    assert longo["obstaculos_por_100m"] == 1


def test_cor_segue_limites_80_e_50() -> None:
    # preparar
    # executar
    verde = cor_da_nota(80)
    amarelo_alto = cor_da_nota(79)
    amarelo_baixo = cor_da_nota(50)
    vermelho = cor_da_nota(49)

    # verificar
    assert verde == "verde"
    assert amarelo_alto == "amarelo"
    assert amarelo_baixo == "amarelo"
    assert vermelho == "vermelho"
