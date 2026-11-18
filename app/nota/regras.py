from __future__ import annotations

from app.nota.parametros import (
    CLASSES_BARREIRA,
    DESCONTO_BARREIRA,
    DESCONTO_BLOQUEIO,
    DESCONTO_PARCIAL,
    LIMITE_AMARELO,
    LIMITE_OCUPACAO_BLOQUEIO,
    LIMITE_VERDE,
    METROS_REFERENCIA,
    NOTA_INICIAL,
    NOTA_MINIMA,
)


def cor_da_nota(nota: float) -> str:
    if nota >= LIMITE_VERDE:
        return "verde"
    if nota >= LIMITE_AMARELO:
        return "amarelo"
    return "vermelho"


def _desconto_do_obstaculo(obstaculo: dict) -> float:
    classe = str(obstaculo.get("classe", "")).strip().lower()
    if classe in CLASSES_BARREIRA:
        return DESCONTO_BARREIRA
    ocupacao = float(obstaculo.get("ocupacao_faixa", 0.0))
    if ocupacao > LIMITE_OCUPACAO_BLOQUEIO:
        return DESCONTO_BLOQUEIO
    return DESCONTO_PARCIAL


def calcular_nota(obstaculos: list[dict], comprimento_m: float) -> dict:
    if comprimento_m <= 0:
        raise ValueError("O comprimento do trecho precisa ser maior que zero.")
    fator = METROS_REFERENCIA / comprimento_m
    desconto = sum(_desconto_do_obstaculo(item) for item in obstaculos) * fator
    nota = max(NOTA_MINIMA, round(NOTA_INICIAL - desconto))
    quantidade = len(obstaculos)
    if quantidade == 0:
        faixa_livre = 1.0
    else:
        ocupacoes = [float(item.get("ocupacao_faixa", 0.0)) for item in obstaculos]
        faixa_livre = max(0.0, 1.0 - (sum(ocupacoes) / quantidade))
    return {
        "nota": int(nota),
        "cor": cor_da_nota(nota),
        "obstaculos_por_100m": quantidade * fator,
        "faixa_livre_media": faixa_livre,
    }
