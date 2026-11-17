import numpy as np

from app.portas.detector import ResultadoQuadro


class DetectorFalso:
    def __init__(self, resultados: list[ResultadoQuadro]) -> None:
        self._resultados = list(resultados)
        self._indice = 0

    def analisar(self, quadro: np.ndarray, instante_s: float) -> ResultadoQuadro:
        del quadro, instante_s
        if not self._resultados:
            raise RuntimeError("Detector falso sem resultados.")
        posicao = min(self._indice, len(self._resultados) - 1)
        self._indice += 1
        return self._resultados[posicao]
