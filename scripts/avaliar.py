from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from app.visao.avaliacao import avaliar


def _carregar(caminho: Path) -> dict:
    return json.loads(caminho.read_text(encoding="utf-8"))


def _percentual(valor: float) -> str:
    return f"{valor * 100:.0f}%"


def main() -> int:
    if len(sys.argv) < 2:
        print("Uso: uv run python scripts/avaliar.py saida/<id>/resultado.json")
        return 1
    caminho_resultado = Path(sys.argv[1])
    if not caminho_resultado.exists():
        print(f"Arquivo não encontrado: {caminho_resultado}")
        return 1

    pasta = caminho_resultado.parent.name
    gabarito_completo = _carregar(RAIZ / "dados" / "gabarito.json")
    trechos = gabarito_completo.get("trechos", {})
    trecho = pasta if pasta in trechos else next((chave for chave in trechos if pasta.startswith(chave)), None)
    if trecho is None:
        print(f"Trecho '{pasta}' não está no gabarito.")
        return 1

    metricas = avaliar(
        _carregar(caminho_resultado),
        trechos[trecho].get("obstaculos", []),
    )
    print(f"Trecho: {trecho}")
    print(f"Marcações do sistema: {metricas['marcacoes']}")
    print(f"Itens do gabarito: {metricas['itens_gabarito']}")
    print(
        f"Acertos por posição (qualquer classe): {metricas['acertos_posicao']}"
        f"  precisão {_percentual(float(metricas['precisao_posicao']))}"
        f"  revocação {_percentual(float(metricas['revocacao_posicao']))}"
    )
    print(
        f"Acertos com a classe certa: {metricas['acertos_classe']}"
        f"  precisão {_percentual(float(metricas['precisao_classe']))}"
        f"  revocação {_percentual(float(metricas['revocacao_classe']))}"
    )
    print(f"Falsos positivos: {metricas['falsos_positivos']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
