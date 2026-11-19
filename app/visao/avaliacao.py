from __future__ import annotations

from typing import Any

from app.visao.parametros import SEGUNDOS_TOLERANCIA_GABARITO


def _no_intervalo(instante: float, item: dict[str, Any], tolerancia: float) -> bool:
    return (item["inicio_s"] - tolerancia) <= instante <= (item["fim_s"] + tolerancia)


def _casar(
    marcacoes: list[dict[str, Any]],
    gabarito: list[dict[str, Any]],
    exigir_classe: bool,
    tolerancia: float,
) -> int:
    usados_gabarito: set[int] = set()
    acertos = 0
    for marcacao in marcacoes:
        instante = float(marcacao["instante_s"])
        classe = str(marcacao["classe"])
        for indice, item in enumerate(gabarito):
            if indice in usados_gabarito:
                continue
            if not _no_intervalo(instante, item, tolerancia):
                continue
            classes = [str(nome) for nome in item.get("classes", [item.get("classe", "")])]
            if exigir_classe and classe not in classes:
                continue
            usados_gabarito.add(indice)
            acertos += 1
            break
    return acertos


def avaliar(
    resultado: dict[str, Any],
    gabarito: list[dict[str, Any]],
    tolerancia_s: float = SEGUNDOS_TOLERANCIA_GABARITO,
) -> dict[str, float | int]:
    marcacoes = list(resultado.get("obstaculos", []))
    gabarito_visivel = [item for item in gabarito if not item.get("fora_do_quadro")]
    total_marcacoes = len(marcacoes)
    total_gabarito = len(gabarito_visivel)
    acertos_posicao = _casar(marcacoes, gabarito_visivel, exigir_classe=False, tolerancia=tolerancia_s)
    acertos_classe = _casar(marcacoes, gabarito_visivel, exigir_classe=True, tolerancia=tolerancia_s)
    falsos_positivos = total_marcacoes - acertos_posicao

    def razao(numerador: int, denominador: int) -> float:
        if denominador == 0:
            return 0.0
        return numerador / denominador

    return {
        "marcacoes": total_marcacoes,
        "itens_gabarito": total_gabarito,
        "acertos_posicao": acertos_posicao,
        "acertos_classe": acertos_classe,
        "falsos_positivos": falsos_positivos,
        "precisao_posicao": razao(acertos_posicao, total_marcacoes),
        "revocacao_posicao": razao(acertos_posicao, total_gabarito),
        "precisao_classe": razao(acertos_classe, total_marcacoes),
        "revocacao_classe": razao(acertos_classe, total_gabarito),
    }
