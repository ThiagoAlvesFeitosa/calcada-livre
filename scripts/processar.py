from __future__ import annotations

import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from app.config import preparar_pastas_modelos

preparar_pastas_modelos()

from app.adaptadores.detector_real import DetectorReal
from app.config import obter_configuracao
from app.visao.pipeline import processar_video


def _formatar_tempo(segundos: float) -> str:
    total = int(round(segundos))
    minutos, resto = divmod(total, 60)
    if minutos:
        return f"{minutos} min {resto} s"
    return f"{resto} s"


def main() -> int:
    if len(sys.argv) < 2:
        print("Uso: uv run python scripts/processar.py CAMINHO.mp4")
        return 1
    caminho = Path(sys.argv[1])
    if not caminho.exists():
        print(f"Arquivo não encontrado: {caminho}")
        return 1

    inicio = time.perf_counter()
    print("Carregando modelos (primeira vez baixa os pesos para modelos/)...")
    detector = DetectorReal()
    pasta_saida = obter_configuracao().pasta_saida
    resultado = processar_video(caminho, detector, pasta_saida)
    duracao = time.perf_counter() - inicio

    obstaculos = resultado["obstaculos"]
    if not obstaculos:
        print("Nenhum obstáculo na faixa da calçada.")
    else:
        print("Obstáculos:")
        for indice, item in enumerate(obstaculos, start=1):
            print(
                f"{indice}. {item['classe']:<22} {item['instante_s']:>5.1f} s"
                f"   confiança {item['confianca']:.2f}"
                f"   ocupacao {item['ocupacao_faixa']:.2f}"
            )
    print(f"Tempo total: {_formatar_tempo(duracao)}")
    print(f"Resultado em {Path(pasta_saida) / caminho.stem}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
