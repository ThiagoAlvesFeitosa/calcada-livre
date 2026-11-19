from __future__ import annotations

from typing import Any

from app.visao.parametros import (
    CONFIANCA_MINIMA_OBSTACULO,
    PROPORCAO_RECORTE_RETRATO,
    SEGUNDOS_TOLERANCIA_GABARITO,
    classe_nossa,
)


def recorte_central_9_16(largura: int, altura: int) -> tuple[int, int, int, int]:
    numerador, denominador = PROPORCAO_RECORTE_RETRATO
    alvo = numerador / denominador
    atual = largura / max(altura, 1)
    if atual > alvo:
        nova_largura = max(1, int(round(altura * alvo)))
        x1 = max(0, (largura - nova_largura) // 2)
        return x1, 0, x1 + nova_largura, altura
    nova_altura = max(1, int(round(largura / alvo)))
    y1 = max(0, (altura - nova_altura) // 2)
    return 0, y1, largura, min(y1 + nova_altura, altura)


def caixa_no_recorte(deteccao: dict[str, Any], recorte: tuple[int, int, int, int]) -> bool:
    x1, y1, x2, y2 = recorte
    cx = (int(deteccao["x1"]) + int(deteccao["x2"])) / 2
    cy = (int(deteccao["y1"]) + int(deteccao["y2"])) / 2
    return x1 <= cx < x2 and y1 <= cy < y2


def _no_intervalo(instante: float, item: dict[str, Any], tolerancia: float) -> bool:
    return (item["inicio_s"] - tolerancia) <= instante <= (item["fim_s"] + tolerancia)


def gabarito_do_recorte(
    obstaculos: list[dict[str, Any]],
    deteccoes: list[dict[str, Any]],
    recorte: tuple[int, int, int, int],
    tolerancia_s: float = SEGUNDOS_TOLERANCIA_GABARITO,
) -> list[dict[str, Any]]:
    saida: list[dict[str, Any]] = []
    for item in obstaculos:
        novo = dict(item)
        classes = {classe_nossa(str(nome)) for nome in item.get("classes", [item.get("classe", "")])}
        casadas = []
        for det in deteccoes:
            if classe_nossa(str(det["classe"])) not in classes:
                continue
            if not _no_intervalo(float(det["instante_s"]), item, tolerancia_s):
                continue
            if det.get("na_calcada") is False:
                continue
            if float(det.get("confianca", 1.0)) < CONFIANCA_MINIMA_OBSTACULO:
                continue
            casadas.append(det)
        if casadas and not any(caixa_no_recorte(det, recorte) for det in casadas):
            novo["fora_do_quadro"] = True
        saida.append(novo)
    return saida
