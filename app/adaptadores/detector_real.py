from pathlib import Path

import numpy as np

from app.config import preparar_pastas_modelos

preparar_pastas_modelos()

from app.portas.detector import ResultadoQuadro
from app.visao.deteccao import DetectorObstaculos
from app.visao.segmentacao import SegmentadorCalcada


class DetectorReal:
    def __init__(self, pasta_modelos: Path | None = None) -> None:
        pasta = pasta_modelos or preparar_pastas_modelos()
        self.segmentador = SegmentadorCalcada()
        self.detector = DetectorObstaculos(pasta)

    def analisar(self, quadro: np.ndarray, instante_s: float) -> ResultadoQuadro:
        del instante_s
        return ResultadoQuadro(
            mascara_calcada=self.segmentador.mascara_calcada(quadro),
            caixas=self.detector.detectar(quadro),
        )
