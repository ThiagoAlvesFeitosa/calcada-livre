from dataclasses import dataclass
from typing import Protocol

import numpy as np


@dataclass
class Caixa:
    classe: str
    confianca: float
    x1: int
    y1: int
    x2: int
    y2: int
    id_rastreio: int | None = None


@dataclass
class ResultadoQuadro:
    mascara_calcada: np.ndarray
    caixas: list[Caixa]


class Detector(Protocol):
    def analisar(self, quadro: np.ndarray, instante_s: float) -> ResultadoQuadro:
        """Devolve a máscara da calçada e as caixas encontradas no quadro."""
        ...
