from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from app.visao.pipeline import _abrir_video, _corrigir_rotacao
from app.visao.recorte import gabarito_do_recorte, recorte_central_9_16

PASTA_VIDEOS = Path(r"d:\Projetos\Projeto GS2\videos")
PASTA_RETRATO = RAIZ / "saida" / "retrato"
GABARITO = RAIZ / "dados" / "gabarito.json"
TRECHOS = (
    "marilia_2026-11-17_trecho-01",
    "marilia_2026-11-17_trecho-02",
)


def _gravar_recorte(origem: Path, destino: Path, recorte: tuple[int, int, int, int]) -> None:
    captura = _abrir_video(origem)
    if not captura.isOpened():
        raise FileNotFoundError(origem)
    fps = captura.get(cv2.CAP_PROP_FPS) or 30.0
    x1, y1, x2, y2 = recorte
    destino.parent.mkdir(parents=True, exist_ok=True)
    escritor = cv2.VideoWriter(
        str(destino),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (x2 - x1, y2 - y1),
    )
    while True:
        ok, quadro = captura.read()
        if not ok:
            break
        quadro = _corrigir_rotacao(captura, quadro)
        escritor.write(quadro[y1:y2, x1:x2])
    captura.release()
    escritor.release()


def main() -> int:
    gabarito = json.loads(GABARITO.read_text(encoding="utf-8"))
    trechos = gabarito.setdefault("trechos", {})
    PASTA_RETRATO.mkdir(parents=True, exist_ok=True)
    for chave in TRECHOS:
        origem = PASTA_VIDEOS / f"{chave}.mp4"
        if not origem.exists():
            print(f"Vídeo não encontrado: {origem}")
            return 1
        captura = _abrir_video(origem)
        ok, quadro = captura.read()
        captura.release()
        if not ok:
            print(f"Não li o primeiro quadro de {origem}")
            return 1
        altura, largura = quadro.shape[:2]
        recorte = recorte_central_9_16(largura, altura)
        destino = PASTA_RETRATO / f"{chave}-retrato.mp4"
        _gravar_recorte(origem, destino, recorte)
        brutas_caminho = RAIZ / "saida" / chave / "deteccoes_brutas.json"
        deteccoes = json.loads(brutas_caminho.read_text(encoding="utf-8")).get("deteccoes", [])
        original = trechos[chave].get("obstaculos", [])
        trechos[f"{chave}-retrato"] = {
            "obstaculos": gabarito_do_recorte(original, deteccoes, recorte)
        }
        print(f"{destino} recorte={recorte}")
        for item in trechos[f"{chave}-retrato"]["obstaculos"]:
            marca = " fora do quadro" if item.get("fora_do_quadro") else ""
            print(f"  #{item.get('id')} {item.get('classes')}{marca}")
    GABARITO.write_text(json.dumps(gabarito, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
