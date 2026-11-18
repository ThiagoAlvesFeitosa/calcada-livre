import numpy as np
import cv2

from app.portas.detector import Caixa
from app.visao.parametros import (
    CLASSES_PRIVACIDADE,
    CLASSES_VEICULO,
    CONFIANCA_MINIMA_PRIVACIDADE,
    DIVISOES_MOSAICO,
    FRACAO_EXTENSAO_INFERIOR_VEICULO,
    FRACAO_INFERIOR_VEICULO,
    PIXELS_MINIMOS_MOSAICO,
    classe_nossa,
)


def _recortar(caixa: Caixa, altura: int, largura: int) -> tuple[int, int, int, int]:
    x1 = min(max(int(caixa.x1), 0), largura)
    y1 = min(max(int(caixa.y1), 0), altura)
    x2 = min(max(int(caixa.x2), 0), largura)
    y2 = min(max(int(caixa.y2), 0), altura)
    return x1, y1, x2, y2


def _pixelizar(quadro: np.ndarray, x1: int, y1: int, x2: int, y2: int) -> None:
    if x2 <= x1 or y2 <= y1:
        return
    recorte = quadro[y1:y2, x1:x2]
    altura, largura = recorte.shape[:2]
    bloco = max(PIXELS_MINIMOS_MOSAICO, min(largura, altura) // DIVISOES_MOSAICO)
    pequeno_largura = max(1, largura // bloco)
    pequeno_altura = max(1, altura // bloco)
    pequeno = cv2.resize(recorte, (pequeno_largura, pequeno_altura), interpolation=cv2.INTER_AREA)
    mosaico = cv2.resize(pequeno, (largura, altura), interpolation=cv2.INTER_NEAREST)
    quadro[y1:y2, x1:x2] = mosaico


def borrar_pessoas_e_placas(quadro: np.ndarray, caixas: list[Caixa]) -> np.ndarray:
    saida = quadro.copy()
    altura, largura = saida.shape[:2]
    visiveis = [
        caixa
        for caixa in caixas
        if caixa.confianca >= CONFIANCA_MINIMA_PRIVACIDADE
    ]
    for caixa in visiveis:
        classe = classe_nossa(caixa.classe)
        x1, y1, x2, y2 = _recortar(caixa, altura, largura)
        if classe in CLASSES_PRIVACIDADE:
            _pixelizar(saida, x1, y1, x2, y2)
        elif classe in CLASSES_VEICULO:
            altura_caixa = max(y2 - y1, 0)
            faixa = int(altura_caixa * FRACAO_INFERIOR_VEICULO)
            extra = int(altura_caixa * FRACAO_EXTENSAO_INFERIOR_VEICULO)
            _pixelizar(saida, x1, y2 - faixa, x2, min(altura, y2 + extra))
    return saida
