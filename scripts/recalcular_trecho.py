from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from app.config import criar_armazenamento, obter_configuracao
from app.trechos.recalcular import recalcular_trecho


def _texto_nota(nota: dict) -> str:
    if not nota:
        return "sem nota"
    valor = nota.get("nota")
    cor = nota.get("cor")
    if valor is None:
        return "sem nota"
    if cor:
        return f"{valor} {cor}"
    return str(valor)


def main() -> int:
    if len(sys.argv) < 2:
        print("Uso: uv run python scripts/recalcular_trecho.py <trecho_id>")
        return 1
    trecho_id = sys.argv[1].strip()
    configuracao = obter_configuracao()
    pasta_saida = Path(configuracao.pasta_saida)
    if not pasta_saida.is_dir():
        pasta_saida = RAIZ / configuracao.pasta_saida
    armazenamento = criar_armazenamento(configuracao)
    try:
        saida = recalcular_trecho(trecho_id, pasta_saida, armazenamento)
    except (FileNotFoundError, ValueError) as erro:
        print(erro)
        return 1
    antiga = saida["nota_antiga"]
    nova = saida["nota_nova"]
    print(f"Trecho {trecho_id}")
    print(f"Nota antiga: {_texto_nota(antiga)}")
    print(f"Nota nova: {_texto_nota(nova)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
