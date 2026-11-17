import numpy as np
import torch
from transformers import AutoImageProcessor, AutoModelForSemanticSegmentation

from app.visao.parametros import ID_CLASSE_CALCADA, MODELO_SEGFORMER, NOMES_MASCARA_CALCADA


class SegmentadorCalcada:
    def __init__(self) -> None:
        self.processor = AutoImageProcessor.from_pretrained(MODELO_SEGFORMER)
        self.modelo = AutoModelForSemanticSegmentation.from_pretrained(MODELO_SEGFORMER)
        self.modelo.to("cpu")
        self.modelo.eval()
        self.ids_calcada = self._ids_calcada()

    def _ids_calcada(self) -> set[int]:
        rotulos = getattr(self.modelo.config, "id2label", {}) or {}
        ids: set[int] = set()
        for chave, nome in rotulos.items():
            if str(nome).lower() in NOMES_MASCARA_CALCADA:
                ids.add(int(chave))
        if not ids:
            ids.add(ID_CLASSE_CALCADA)
        return ids

    def mascara_calcada(self, quadro_bgr: np.ndarray) -> np.ndarray:
        rgb = np.ascontiguousarray(quadro_bgr[:, :, ::-1])
        entradas = self.processor(images=rgb, return_tensors="pt")
        with torch.no_grad():
            saidas = self.modelo(**entradas)
        altura, largura = quadro_bgr.shape[:2]
        logits = torch.nn.functional.interpolate(
            saidas.logits,
            size=(altura, largura),
            mode="bilinear",
            align_corners=False,
        )
        predicao = logits.argmax(dim=1)[0].cpu().numpy()
        return np.isin(predicao, list(self.ids_calcada))
