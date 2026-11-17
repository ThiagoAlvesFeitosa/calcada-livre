import numpy as np
import cv2

from app.portas.detector import Caixa
from app.visao.parametros import (
    CLASSES_PRIVACIDADE,
    CLASSES_VEICULO,
    CONFIANCA_MINIMA_PRIVACIDADE,
    FRACAO_INFERIOR_VEICULO,
    TAMANHO_DESFOQUE,
    classe_nossa,
)


def _recortar(caixa: Caixa, altura: int, largura: int) -> tuple[int, int, int, int]:
    x1 = min(max(int(caixa.x1), 0), largura)
    y1 = min(max(int(caixa.y1), 0), altura)
    x2 = min(max(int(caixa.x2), 0), largura)
    y2 = min(max(int(caixa.y2), 0), altura)
    return x1, y1, x2, y2


def _borrar(quadro: np.ndarray, x1: int, y1: int, x2: int, y2: int) -> None:
    if x2 <= x1 or y2 <= y1:
        return
    nucleo = TAMANHO_DESFOQUE if TAMANHO_DESFOQUE % 2 == 1 else TAMANHO_DESFOQUE + 1
    margem = nucleo // 2
    altura, largura = quadro.shape[:2]
    xa = max(x1 - margem, 0)
    ya = max(y1 - margem, 0)
    xb = min(x2 + margem, largura)
    yb = min(y2 + margem, altura)
    recorte = quadro[ya:yb, xa:xb]
    borrado = cv2.GaussianBlur(recorte, (nucleo, nucleo), 0)
    quadro[y1:y2, x1:x2] = borrado[y1 - ya : y2 - ya, x1 - xa : x2 - xa]


def _placa_dentro(veiculo: Caixa, placas: list[Caixa]) -> bool:
    for placa in placas:
        centro_x = (placa.x1 + placa.x2) // 2
        centro_y = (placa.y1 + placa.y2) // 2
        if veiculo.x1 <= centro_x <= veiculo.x2 and veiculo.y1 <= centro_y <= veiculo.y2:
            return True
    return False


def borrar_pessoas_e_placas(quadro: np.ndarray, caixas: list[Caixa]) -> np.ndarray:
    saida = quadro.copy()
    altura, largura = saida.shape[:2]
    visiveis = [
        caixa
        for caixa in caixas
        if caixa.confianca >= CONFIANCA_MINIMA_PRIVACIDADE
    ]
    placas = [caixa for caixa in visiveis if classe_nossa(caixa.classe) == "license plate"]
    for caixa in visiveis:
        classe = classe_nossa(caixa.classe)
        x1, y1, x2, y2 = _recortar(caixa, altura, largura)
        if classe in CLASSES_PRIVACIDADE:
            _borrar(saida, x1, y1, x2, y2)
        elif classe in CLASSES_VEICULO and not _placa_dentro(caixa, placas):
            faixa = int((y2 - y1) * FRACAO_INFERIOR_VEICULO)
            _borrar(saida, x1, y2 - faixa, x2, y2)
    return saida
