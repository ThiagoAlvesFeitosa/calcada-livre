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


def _percentual(valor: float, marcacoes: int, gabarito: int) -> str:
    if marcacoes == 0 and gabarito == 0:
        return "—"
    return f"{valor * 100:.0f}%"


def _trecho_do_caminho(caminho: Path, trechos: dict) -> str | None:
    pasta = caminho.parent.name
    if pasta in trechos:
        return pasta
    candidatos = [
        chave for chave in trechos if pasta.startswith(chave) or chave in pasta
    ]
    if not candidatos:
        return None
    return max(candidatos, key=len)


def _metricas(caminho: Path, trechos: dict) -> tuple[str, dict] | None:
    trecho = _trecho_do_caminho(caminho, trechos)
    if trecho is None:
        print(f"Trecho '{caminho.parent.name}' não está no gabarito.")
        return None
    return trecho, avaliar(_carregar(caminho), trechos[trecho].get("obstaculos", []))


def _imprimir_um(trecho: str, metricas: dict) -> None:
    print(f"Trecho: {trecho}")
    print(f"Marcações do sistema: {metricas['marcacoes']}")
    print(f"Itens do gabarito: {metricas['itens_gabarito']}")
    print(
        f"Acertos por posição (qualquer classe): {metricas['acertos_posicao']}"
        f"  precisão {_percentual(float(metricas['precisao_posicao']), int(metricas['marcacoes']), int(metricas['itens_gabarito']))}"
        f"  revocação {_percentual(float(metricas['revocacao_posicao']), int(metricas['marcacoes']), int(metricas['itens_gabarito']))}"
    )
    print(
        f"Acertos com a classe certa: {metricas['acertos_classe']}"
        f"  precisão {_percentual(float(metricas['precisao_classe']), int(metricas['marcacoes']), int(metricas['itens_gabarito']))}"
        f"  revocação {_percentual(float(metricas['revocacao_classe']), int(metricas['marcacoes']), int(metricas['itens_gabarito']))}"
    )
    print(f"Falsos positivos: {metricas['falsos_positivos']}")


def _imprimir_tabela(linhas: list[tuple[str, dict]]) -> None:
    print("| Vídeo | Precisão (posição) | Revocação (posição) | Precisão (classe) | Revocação (classe) | FP |")
    print("| --- | --- | --- | --- | --- | --- |")
    for trecho, metricas in linhas:
        print(
            f"| {trecho} | "
            f"{_percentual(float(metricas['precisao_posicao']), int(metricas['marcacoes']), int(metricas['itens_gabarito']))} | "
            f"{_percentual(float(metricas['revocacao_posicao']), int(metricas['marcacoes']), int(metricas['itens_gabarito']))} | "
            f"{_percentual(float(metricas['precisao_classe']), int(metricas['marcacoes']), int(metricas['itens_gabarito']))} | "
            f"{_percentual(float(metricas['revocacao_classe']), int(metricas['marcacoes']), int(metricas['itens_gabarito']))} | "
            f"{metricas['falsos_positivos']} |"
        )


def main() -> int:
    if len(sys.argv) < 2:
        print("Uso: uv run python scripts/avaliar.py saida/<id>/resultado.json [mais arquivos...]")
        return 1
    gabarito_completo = _carregar(RAIZ / "dados" / "gabarito.json")
    trechos = gabarito_completo.get("trechos", {})
    linhas: list[tuple[str, dict]] = []
    for argumento in sys.argv[1:]:
        caminho = Path(argumento)
        if not caminho.exists():
            print(f"Arquivo não encontrado: {caminho}")
            return 1
        lido = _metricas(caminho, trechos)
        if lido is None:
            return 1
        trecho, metricas = lido
        if len(sys.argv) == 2:
            _imprimir_um(trecho, metricas)
        linhas.append((trecho, metricas))
    if len(linhas) > 1:
        _imprimir_tabela(linhas)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
