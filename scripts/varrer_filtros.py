from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from app.visao.avaliacao import avaliar
from app.visao.parametros import (
    CLASSES_CORTE_MENOR,
    CONFIANCA_MINIMA_BRUTA,
    CONFIANCAS_VARREDURA,
    FRACOES_CAMINHO_VARREDURA,
)
from app.visao.pipeline import filtrar_obstaculos

TRECHO_01 = "marilia_2026-11-17_trecho-01"
TRECHO_02 = "marilia_2026-11-17_trecho-02"
MAXIMO_FP_TRECHO_01 = 1


def _carregar(caminho: Path) -> dict:
    return json.loads(caminho.read_text(encoding="utf-8"))


def _achar_brutas(pasta_saida: Path, trecho: str) -> Path:
    candidatos = [
        pasta_saida / trecho / "deteccoes_brutas.json",
        pasta_saida / f"{trecho}-s" / "deteccoes_brutas.json",
    ]
    for caminho in candidatos:
        if caminho.exists():
            return caminho
    raise FileNotFoundError(
        f"Não achei deteccoes_brutas.json de {trecho}. Rode processar.py antes."
    )


def _metricas(
    deteccoes: list[dict],
    gabarito: list[dict],
    confianca: float,
    fracao: float,
    por_classe: dict[str, float] | None = None,
) -> dict:
    filtrado = filtrar_obstaculos(
        deteccoes,
        confianca_padrao=confianca,
        fracao_caminho=fracao,
        confianca_por_classe=por_classe,
    )
    return avaliar(filtrado, gabarito)


def _linha(
    confianca: float,
    fracao: float,
    m01: dict,
    m02: dict,
    extra: str = "",
) -> dict:
    return {
        "confianca": confianca,
        "recorte": fracao,
        "extra": extra,
        "acertos_02": int(m02["acertos_posicao"]),
        "fp_02": int(m02["falsos_positivos"]),
        "marcacoes_02": int(m02["marcacoes"]),
        "precisao_02": float(m02["precisao_posicao"]),
        "revocacao_02": float(m02["revocacao_posicao"]),
        "fp_01": int(m01["falsos_positivos"]),
        "marcacoes_01": int(m01["marcacoes"]),
    }


def _imprimir(linhas: list[dict]) -> None:
    print(
        f"{'conf':>5} {'recorte':>7} {'acertos02':>9} {'fp02':>5} {'prec02':>7} {'rev02':>6} {'fp01':>5}  extra"
    )
    for linha in linhas:
        extra = linha["extra"] or "—"
        print(
            f"{linha['confianca']:>5.2f} {linha['recorte']:>6.0%} "
            f"{linha['acertos_02']:>9} {linha['fp_02']:>5} "
            f"{linha['precisao_02']:>6.0%} {linha['revocacao_02']:>5.0%} "
            f"{linha['fp_01']:>5}  {extra}"
        )


def _melhor(linhas: list[dict]) -> dict | None:
    candidatas = [linha for linha in linhas if linha["fp_01"] <= MAXIMO_FP_TRECHO_01]
    if not candidatas:
        return None
    return max(
        candidatas,
        key=lambda linha: (
            linha["acertos_02"],
            -linha["fp_02"],
            linha["confianca"],
            linha["recorte"],
        ),
    )


def main() -> int:
    pasta_saida = RAIZ / "saida"
    gabarito = _carregar(RAIZ / "dados" / "gabarito.json")["trechos"]
    det01 = _carregar(_achar_brutas(pasta_saida, TRECHO_01))["deteccoes"]
    det02 = _carregar(_achar_brutas(pasta_saida, TRECHO_02))["deteccoes"]
    gab01 = gabarito[TRECHO_01]["obstaculos"]
    gab02 = gabarito[TRECHO_02]["obstaculos"]

    linhas: list[dict] = []
    for confianca in CONFIANCAS_VARREDURA:
        for fracao in FRACOES_CAMINHO_VARREDURA:
            m01 = _metricas(det01, gab01, confianca, fracao)
            m02 = _metricas(det02, gab02, confianca, fracao)
            linhas.append(_linha(confianca, fracao, m01, m02))

    escolhida = _melhor(linhas)
    if escolhida is not None:
        por_classe = {classe: CONFIANCA_MINIMA_BRUTA for classe in CLASSES_CORTE_MENOR}
        m01 = _metricas(
            det01,
            gab01,
            escolhida["confianca"],
            escolhida["recorte"],
            por_classe=por_classe,
        )
        m02 = _metricas(
            det02,
            gab02,
            escolhida["confianca"],
            escolhida["recorte"],
            por_classe=por_classe,
        )
        linhas.append(
            _linha(
                escolhida["confianca"],
                escolhida["recorte"],
                m01,
                m02,
                extra="entulho/areia 0,05",
            )
        )
        escolhida = _melhor(linhas)

    print("Varredura (acertos por posição, qualquer classe):")
    _imprimir(linhas)
    if escolhida is None:
        print("Nenhuma combinação ficou com no máximo 1 falso positivo no trecho 01.")
        return 1
    print()
    print(
        "Melhor: confiança "
        f"{escolhida['confianca']:.2f}, recorte {escolhida['recorte']:.0%}, "
        f"acertos no 02 = {escolhida['acertos_02']}, FP no 01 = {escolhida['fp_01']}"
        + (f" ({escolhida['extra']})" if escolhida["extra"] else "")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
