from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from app.config import criar_armazenamento, obter_configuracao
from app.nota.regras import calcular_nota
from app.trechos.consulta import carregar_trechos, nota_do_trecho
from app.trechos.geometria import comprimento_do_trecho, ids_dos_trechos


def _carregar_obstaculos(caminho: Path) -> list[dict]:
    return list(json.loads(caminho.read_text(encoding="utf-8")).get("obstaculos", []))


def _mostrar(nome: str, comprimento_m: float, resultado: dict) -> None:
    print(f"{nome} ({comprimento_m:.1f} m)")
    print(f"  nota {resultado['nota']}  cor {resultado['cor']}")
    print(f"  obstáculos por 100 m: {resultado['obstaculos_por_100m']:.1f}")
    print(f"  faixa livre média: {resultado['faixa_livre_media']:.0%}")


def main() -> int:
    configuracao = obter_configuracao()
    colecao = carregar_trechos(configuracao.caminho_trechos)
    armazenamento = criar_armazenamento(configuracao)

    if len(sys.argv) >= 3:
        caminho = Path(sys.argv[1])
        comprimento = float(sys.argv[2])
        if not caminho.exists():
            print(f"Arquivo não encontrado: {caminho}")
            return 1
        _mostrar(caminho.parent.name, comprimento, calcular_nota(_carregar_obstaculos(caminho), comprimento))
        return 0

    faltando = False
    for trecho in sorted(ids_dos_trechos(colecao)):
        nota = nota_do_trecho(armazenamento, colecao, trecho)
        if nota is None:
            continue
        _mostrar(trecho, comprimento_do_trecho(colecao, trecho), nota)
    if not any(nota_do_trecho(armazenamento, colecao, trecho) for trecho in ids_dos_trechos(colecao)):
        print("Nenhum trecho com resultado.json.")
        faltando = True
    return 1 if faltando else 0


if __name__ == "__main__":
    raise SystemExit(main())
