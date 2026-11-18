from pathlib import Path

import cv2
import numpy as np

from app.adaptadores.detector_falso import DetectorFalso
from app.portas.detector import Caixa, ResultadoQuadro
from app.visao.pipeline import processar_quadros


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


def test_objeto_fora_do_caminho_nao_conta_como_obstaculo(tmp_path: Path) -> None:
    # preparar
    quadro = _quadro_cinza()
    mascara = _mascara_metade_de_baixo()
    no_alto_da_calcada = Caixa(
        classe="tree",
        confianca=0.9,
        x1=10,
        y1=40,
        x2=20,
        y2=42,
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


def test_quadro_salvo_tem_pessoas_e_placas_borradas(tmp_path: Path) -> None:
    # preparar
    quadro = _quadro_cinza()
    quadro[6:16, 6:16] = 255
    quadro[24:32, 40:58] = 0
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
    assert not np.all(gravado[6:16, 6:16] == 255)
    assert not np.all(gravado[24:32, 40:58] == 0)
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
