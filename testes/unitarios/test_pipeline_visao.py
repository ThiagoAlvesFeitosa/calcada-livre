import json
from pathlib import Path

import cv2
import numpy as np

from app.adaptadores.detector_falso import DetectorFalso
from app.portas.detector import Caixa, ResultadoQuadro
from app.visao.pipeline import filtrar_obstaculos, processar_quadros


def _quadro_cinza(altura: int = 80, largura: int = 80) -> np.ndarray:
    return np.full((altura, largura, 3), 128, dtype=np.uint8)


def _mascara_metade_de_baixo(altura: int = 80, largura: int = 80) -> np.ndarray:
    mascara = np.zeros((altura, largura), dtype=bool)
    mascara[altura // 2 :, :] = True
    return mascara


def test_objeto_fora_da_calcada_nao_conta_como_obstaculo(tmp_path: Path) -> None:
    # preparar
    quadro = _quadro_cinza()
    mascara = _mascara_metade_de_baixo()
    na_calcada = Caixa(
        classe="tree",
        confianca=0.9,
        x1=10,
        y1=50,
        x2=20,
        y2=70,
        id_rastreio=1,
    )
    no_ceu = Caixa(
        classe="pole",
        confianca=0.9,
        x1=40,
        y1=0,
        x2=50,
        y2=8,
        id_rastreio=2,
    )
    detector = DetectorFalso(
        [
            ResultadoQuadro(mascara_calcada=mascara, caixas=[na_calcada, no_ceu]),
        ]
    )

    # executar
    resultado = processar_quadros(
        [(quadro, 0.0)],
        detector,
        pasta_saida=tmp_path,
        identificador="teste-calcada",
    )

    # verificar
    assert len(resultado["obstaculos"]) == 1
    obstaculo = resultado["obstaculos"][0]
    assert obstaculo["classe"] == "tree"
    assert "ocupacao_faixa" in obstaculo
    assert obstaculo["ocupacao_faixa"] > 0
    assert "duracao_s" in resultado


def test_deteccoes_brutas_guardam_o_que_fica_fora_do_filtro(tmp_path: Path) -> None:
    # preparar
    quadro = _quadro_cinza()
    mascara = _mascara_metade_de_baixo()
    fraca_no_ceu = Caixa(
        classe="tree",
        confianca=0.06,
        x1=40,
        y1=0,
        x2=50,
        y2=8,
        id_rastreio=3,
    )
    detector = DetectorFalso(
        [ResultadoQuadro(mascara_calcada=mascara, caixas=[fraca_no_ceu])]
    )

    # executar
    processar_quadros(
        [(quadro, 1.0)],
        detector,
        pasta_saida=tmp_path,
        identificador="teste-brutas",
    )

    # verificar
    brutas = json.loads((tmp_path / "teste-brutas" / "deteccoes_brutas.json").read_text(encoding="utf-8"))
    assert len(brutas["deteccoes"]) == 1
    assert brutas["deteccoes"][0]["classe"] == "tree"
    assert brutas["deteccoes"][0]["confianca"] == 0.06
    assert brutas["deteccoes"][0]["na_calcada"] is False
    resultado = json.loads((tmp_path / "teste-brutas" / "resultado.json").read_text(encoding="utf-8"))
    assert resultado["obstaculos"] == []


def test_entulho_pode_ter_corte_de_confianca_menor() -> None:
    # preparar
    deteccoes = [
        {
            "classe": "construction debris",
            "confianca": 0.12,
            "instante_s": 8.0,
            "x1": 10,
            "y1": 50,
            "x2": 30,
            "y2": 70,
            "id_rastreio": None,
            "altura_quadro": 80,
            "largura_quadro": 80,
            "na_calcada": True,
            "largura_calcada_na_linha": 80,
        }
    ]

    # executar
    com_corte_alto = filtrar_obstaculos(
        deteccoes,
        confianca_padrao=0.25,
        fracao_caminho=0.45,
        confianca_por_classe={"construction debris": 0.25},
    )
    com_corte_entulho = filtrar_obstaculos(
        deteccoes,
        confianca_padrao=0.25,
        fracao_caminho=0.45,
        confianca_por_classe={"construction debris": 0.10},
    )

    # verificar
    assert com_corte_alto["obstaculos"] == []
    assert len(com_corte_entulho["obstaculos"]) == 1


def test_objeto_fora_do_caminho_nao_conta_como_obstaculo(tmp_path: Path) -> None:
    # preparar
    quadro = _quadro_cinza()
    mascara = np.ones((80, 80), dtype=bool)
    no_alto_da_calcada = Caixa(
        classe="tree",
        confianca=0.9,
        x1=10,
        y1=5,
        x2=20,
        y2=18,
        id_rastreio=1,
    )
    no_caminho = Caixa(
        classe="pole",
        confianca=0.9,
        x1=30,
        y1=55,
        x2=40,
        y2=75,
        id_rastreio=2,
    )
    detector = DetectorFalso(
        [ResultadoQuadro(mascara_calcada=mascara, caixas=[no_alto_da_calcada, no_caminho])]
    )

    # executar
    resultado = processar_quadros(
        [(quadro, 0.0)],
        detector,
        pasta_saida=tmp_path,
        identificador="teste-caminho",
    )

    # verificar
    assert [item["classe"] for item in resultado["obstaculos"]] == ["pole"]


def test_carro_com_placa_no_lugar_errado_ainda_borra_a_faixa_de_baixo(tmp_path: Path) -> None:
    # preparar
    quadro = _quadro_cinza()
    faixa_baixo = quadro[48:70, 10:70]
    faixa_baixo[:, :] = 0
    faixa_baixo[::2, ::2] = 255
    faixa_baixo[1::2, 1::2] = 255
    original_baixo = faixa_baixo.copy()
    mascara = _mascara_metade_de_baixo()
    carro = Caixa(
        classe="car",
        confianca=0.9,
        x1=10,
        y1=20,
        x2=70,
        y2=70,
        id_rastreio=1,
    )
    placa_errada = Caixa(
        classe="license plate",
        confianca=0.5,
        x1=12,
        y1=22,
        x2=28,
        y2=32,
        id_rastreio=2,
    )
    detector = DetectorFalso(
        [ResultadoQuadro(mascara_calcada=mascara, caixas=[carro, placa_errada])]
    )

    # executar
    processar_quadros(
        [(quadro, 0.0)],
        detector,
        pasta_saida=tmp_path,
        identificador="teste-placa-errada",
    )

    # verificar
    salvos = list((tmp_path / "teste-placa-errada" / "quadros").glob("*.png"))
    assert len(salvos) == 1
    gravado = cv2.imread(str(salvos[0]))
    assert gravado is not None
    assert not np.array_equal(gravado[48:70, 10:70], original_baixo)


def test_quadro_salvo_tem_pessoas_e_placas_borradas(tmp_path: Path) -> None:
    # preparar
    quadro = _quadro_cinza()
    quadro[6:16, 6:16] = 0
    quadro[6:16:2, 6:16:2] = 255
    quadro[24:32, 40:58] = 0
    quadro[24:32:2, 40:58:2] = 255
    original_pessoa = quadro[6:16, 6:16].copy()
    original_placa = quadro[24:32, 40:58].copy()
    mascara = _mascara_metade_de_baixo()
    pessoa = Caixa(
        classe="person",
        confianca=0.4,
        x1=6,
        y1=6,
        x2=16,
        y2=16,
        id_rastreio=1,
    )
    placa = Caixa(
        classe="license plate",
        confianca=0.4,
        x1=40,
        y1=24,
        x2=58,
        y2=32,
        id_rastreio=2,
    )
    detector = DetectorFalso(
        [ResultadoQuadro(mascara_calcada=mascara, caixas=[pessoa, placa])]
    )

    # executar
    processar_quadros(
        [(quadro, 0.0)],
        detector,
        pasta_saida=tmp_path,
        identificador="teste-privacidade",
    )

    # verificar
    salvos = list((tmp_path / "teste-privacidade" / "quadros").glob("*.png"))
    assert len(salvos) == 1
    gravado = cv2.imread(str(salvos[0]))
    assert gravado is not None
    assert not np.array_equal(gravado[6:16, 6:16], original_pessoa)
    assert not np.array_equal(gravado[24:32, 40:58], original_placa)
    assert np.all(gravado[0:4, 0:4] == 128)


def test_mesmo_obstaculo_em_varios_quadros_aparece_uma_vez(tmp_path: Path) -> None:
    # preparar
    quadro = _quadro_cinza()
    mascara = _mascara_metade_de_baixo()
    primeiro = Caixa(
        classe="tree",
        confianca=0.6,
        x1=10,
        y1=50,
        x2=20,
        y2=70,
        id_rastreio=10,
    )
    segundo = Caixa(
        classe="tree",
        confianca=0.9,
        x1=12,
        y1=50,
        x2=24,
        y2=70,
        id_rastreio=99,
    )
    detector = DetectorFalso(
        [
            ResultadoQuadro(mascara_calcada=mascara, caixas=[primeiro]),
            ResultadoQuadro(mascara_calcada=mascara, caixas=[segundo]),
        ]
    )

    # executar
    resultado = processar_quadros(
        [(quadro, 0.0), (quadro, 0.5)],
        detector,
        pasta_saida=tmp_path,
        identificador="teste-juntar",
    )

    # verificar
    assert len(resultado["obstaculos"]) == 1
    obstaculo = resultado["obstaculos"][0]
    assert obstaculo["classe"] == "tree"
    assert obstaculo["instante_s"] == 0.0
    assert obstaculo["confianca"] == 0.9
    assert obstaculo["ocupacao_faixa"] > 0
