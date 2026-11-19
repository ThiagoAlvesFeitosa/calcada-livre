import numpy as np
from pathlib import Path

from app.adaptadores.detector_falso import DetectorFalso
from app.nota.parametros import DESCONTO_BARREIRA, DESCONTO_PARCIAL
from app.nota.regras import calcular_nota, frase_dos_obstaculos
from app.portas.detector import Caixa, ResultadoQuadro
from app.visao.pipeline import processar_quadros
from app.visao.parametros import CLASSE_CAMINHO_OBSTRUIDO, SOBREPOSICAO_MAXIMA


def _quadro(altura: int = 80, largura: int = 80) -> np.ndarray:
    return np.full((altura, largura, 3), 128, dtype=np.uint8)


def _mascara_chao() -> np.ndarray:
    return np.ones((80, 80), dtype=bool)


def test_calcada_danificada_so_conta_se_caixa_inteira_esta_no_caminho(tmp_path: Path) -> None:
    # preparar
    mascara = _mascara_chao()
    alta = Caixa(
        classe="damaged sidewalk",
        confianca=0.9,
        x1=10,
        y1=4,
        x2=30,
        y2=70,
        id_rastreio=1,
    )
    detector = DetectorFalso([ResultadoQuadro(mascara_calcada=mascara, caixas=[alta])])

    # executar
    resultado = processar_quadros(
        [(_quadro(), 0.0)],
        detector,
        pasta_saida=tmp_path,
        identificador="danificada-alta",
    )

    # verificar
    assert resultado["obstaculos"] == []


def test_calcada_danificada_no_chao_conta(tmp_path: Path) -> None:
    # preparar
    mascara = _mascara_chao()
    baixa = Caixa(
        classe="damaged sidewalk",
        confianca=0.9,
        x1=10,
        y1=55,
        x2=30,
        y2=75,
        id_rastreio=1,
    )
    detector = DetectorFalso([ResultadoQuadro(mascara_calcada=mascara, caixas=[baixa])])

    # executar
    resultado = processar_quadros(
        [(_quadro(), 0.0)],
        detector,
        pasta_saida=tmp_path,
        identificador="danificada-chao",
    )

    # verificar
    assert [item["classe"] for item in resultado["obstaculos"]] == ["damaged sidewalk"]


def test_caixa_nova_sobreposta_a_arvore_fica_so_a_arvore(tmp_path: Path) -> None:
    # preparar
    mascara = _mascara_chao()
    arvore = Caixa(classe="tree", confianca=0.9, x1=10, y1=50, x2=40, y2=75, id_rastreio=1)
    objeto = Caixa(
        classe="objects on sidewalk",
        confianca=0.8,
        x1=12,
        y1=52,
        x2=38,
        y2=74,
        id_rastreio=2,
    )
    detector = DetectorFalso(
        [ResultadoQuadro(mascara_calcada=mascara, caixas=[arvore, objeto])]
    )

    # executar
    resultado = processar_quadros(
        [(_quadro(), 0.0)],
        detector,
        pasta_saida=tmp_path,
        identificador="sobreposta",
    )

    # verificar
    assert SOBREPOSICAO_MAXIMA > 0
    assert [item["classe"] for item in resultado["obstaculos"]] == ["tree"]


def test_chao_pouco_livre_vira_caminho_obstruido(tmp_path: Path) -> None:
    # preparar
    vazio = np.zeros((80, 80), dtype=bool)
    detector = DetectorFalso(
        [ResultadoQuadro(mascara_calcada=vazio, caixas=[]) for _ in range(5)]
    )
    instantes = [0.0, 0.5, 1.0, 1.5, 2.0]

    # executar
    resultado = processar_quadros(
        [(_quadro(), t) for t in instantes],
        detector,
        pasta_saida=tmp_path,
        identificador="chao-vazio",
    )

    # verificar
    classes = [item["classe"] for item in resultado["obstaculos"]]
    assert CLASSE_CAMINHO_OBSTRUIDO in classes


def test_queda_curta_do_chao_nao_vira_obstrucao(tmp_path: Path) -> None:
    # preparar
    cheio = np.ones((80, 80), dtype=bool)
    vazio = np.zeros((80, 80), dtype=bool)
    detector = DetectorFalso(
        [
            ResultadoQuadro(mascara_calcada=cheio, caixas=[]),
            ResultadoQuadro(mascara_calcada=vazio, caixas=[]),
            ResultadoQuadro(mascara_calcada=cheio, caixas=[]),
        ]
    )

    # executar
    resultado = processar_quadros(
        [(_quadro(), 0.0), (_quadro(), 0.5), (_quadro(), 1.0)],
        detector,
        pasta_saida=tmp_path,
        identificador="queda-curta",
    )

    # verificar
    assert resultado["obstaculos"] == []


def test_calcada_danificada_desconta_como_barreira() -> None:
    # preparar
    ocupacao = 0.2
    poste = [{"classe": "pole", "ocupacao_faixa": ocupacao}]
    danificada = [{"classe": "damaged sidewalk", "ocupacao_faixa": ocupacao}]

    # executar
    nota_poste = calcular_nota(poste, comprimento_m=100)
    nota_danificada = calcular_nota(danificada, comprimento_m=100)

    # verificar
    assert nota_danificada["nota"] == 100 - DESCONTO_BARREIRA
    assert nota_danificada["nota"] < nota_poste["nota"]
    assert nota_poste["nota"] == 100 - DESCONTO_PARCIAL


def test_frase_da_nota_lista_os_problemas() -> None:
    # preparar
    vazio: list[dict] = []
    varios = [
        {"classe": "blocked path"},
        {"classe": "construction debris"},
        {"classe": "damaged sidewalk"},
    ]

    # executar
    sem = frase_dos_obstaculos(vazio)
    com = frase_dos_obstaculos(varios)

    # verificar
    assert sem == "Nenhum obstáculo encontrado"
    assert com == "3 problemas: caminho obstruído, entulho, calçada danificada"
