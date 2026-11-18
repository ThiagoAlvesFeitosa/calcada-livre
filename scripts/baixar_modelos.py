"""Carrega SegFormer, YOLO-World e CLIP uma vez (passo RUN do Docker)."""

from pathlib import Path

from app.adaptadores.detector_real import DetectorReal
from app.config import preparar_pastas_modelos


def main() -> None:
    pasta = preparar_pastas_modelos()
    print(f"baixando modelos para {pasta}", flush=True)
    DetectorReal()
    arquivos = sorted(caminho.name for caminho in Path(pasta).rglob("*") if caminho.is_file())
    print(f"modelos prontos ({len(arquivos)} arquivos)", flush=True)


if __name__ == "__main__":
    main()
