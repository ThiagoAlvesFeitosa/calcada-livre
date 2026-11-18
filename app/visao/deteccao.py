from pathlib import Path

import numpy as np
from ultralytics import YOLO, settings

from app.portas.detector import Caixa
from app.visao.parametros import (
    ARQUIVO_YOLO_WORLD,
    CONFIANCA_MINIMA_BRUTA,
    nomes_para_yolo,
)


class DetectorObstaculos:
    def __init__(self, pasta_modelos: Path, arquivo_yolo: str | None = None) -> None:
        settings.update(
            {
                "weights_dir": str(pasta_modelos),
                "runs_dir": str(pasta_modelos / "runs"),
            }
        )
        arquivo = arquivo_yolo or ARQUIVO_YOLO_WORLD
        caminho = pasta_modelos / arquivo
        for origem in (Path(arquivo), pasta_modelos.parent / arquivo):
            if origem.exists() and origem.resolve() != caminho.resolve():
                caminho.parent.mkdir(parents=True, exist_ok=True)
                origem.replace(caminho)
        self.modelo = YOLO(str(caminho) if caminho.exists() else arquivo)
        baixado = Path(arquivo)
        if baixado.exists() and baixado.resolve() != caminho.resolve():
            caminho.parent.mkdir(parents=True, exist_ok=True)
            baixado.replace(caminho)
        self.modelo.to("cpu")
        self.modelo.set_classes(nomes_para_yolo())

    def detectar(self, quadro_bgr: np.ndarray) -> list[Caixa]:
        resultados = self.modelo.predict(
            quadro_bgr,
            verbose=False,
            device="cpu",
            conf=CONFIANCA_MINIMA_BRUTA,
        )
        if not resultados:
            return []
        caixas_modelo = resultados[0].boxes
        if caixas_modelo is None or len(caixas_modelo) == 0:
            return []
        nomes = resultados[0].names
        saida: list[Caixa] = []
        ids = caixas_modelo.id
        for indice in range(len(caixas_modelo)):
            xyxy = caixas_modelo.xyxy[indice].cpu().tolist()
            classe_id = int(caixas_modelo.cls[indice])
            identificador = None
            if ids is not None:
                identificador = int(ids[indice])
            if isinstance(nomes, dict):
                nome_classe = str(nomes.get(classe_id, classe_id))
            else:
                nome_classe = str(nomes[classe_id])
            saida.append(
                Caixa(
                    classe=nome_classe,
                    confianca=float(caixas_modelo.conf[indice]),
                    x1=int(xyxy[0]),
                    y1=int(xyxy[1]),
                    x2=int(xyxy[2]),
                    y2=int(xyxy[3]),
                    id_rastreio=identificador,
                )
            )
        return saida
