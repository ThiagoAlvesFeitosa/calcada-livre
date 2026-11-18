from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from app.nota.parametros import COMPRIMENTO_PROVISORIO_M
from app.nota.regras import calcular_nota

TRECHOS_PADRAO = (
    "marilia_2026-11-17_trecho-01",
    "marilia_2026-11-17_trecho-02",
)


def _carregar_obstaculos(caminho: Path) -> list[dict]:
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    return list(dados.get("obstaculos", []))


def _achar_resultado(pasta_saida: Path, trecho: str) -> Path:
    caminho = pasta_saida / trecho / "resultado.json"
    if caminho.exists():
        return caminho
    raise FileNotFoundError(f"Não achei resultado.json de {trecho}. Rode processar.py antes.")


def _mostrar(nome: str, comprimento_m: float, resultado: dict) -> None:
    print(f"{nome} ({comprimento_m:g} m)")
    print(f"  nota {resultado['nota']}  cor {resultado['cor']}")
    print(f"  obstáculos por 100 m: {resultado['obstaculos_por_100m']:.1f}")
    print(f"  faixa livre média: {resultado['faixa_livre_media']:.0%}")


def main() -> int:
    pasta_saida = RAIZ / "saida"
    if len(sys.argv) >= 3:
        caminho = Path(sys.argv[1])
        comprimento = float(sys.argv[2])
        if not caminho.exists():
            print(f"Arquivo não encontrado: {caminho}")
            return 1
        _mostrar(caminho.parent.name, comprimento, calcular_nota(_carregar_obstaculos(caminho), comprimento))
        return 0

    faltando = False
    for trecho in TRECHOS_PADRAO:
        comprimento = COMPRIMENTO_PROVISORIO_M[trecho]
        try:
            obstaculos = _carregar_obstaculos(_achar_resultado(pasta_saida, trecho))
        except FileNotFoundError as erro:
            print(erro)
            faltando = True
            continue
        _mostrar(trecho, comprimento, calcular_nota(obstaculos, comprimento))
    return 1 if faltando else 0


if __name__ == "__main__":
    raise SystemExit(main())
