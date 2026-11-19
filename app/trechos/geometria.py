from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from app.nota.parametros import COMPRIMENTO_PONTO_M, DISTANCIA_MAXIMA_TRECHO_M, RAIO_TERRA_M


def carregar_colecao(caminho: Path) -> dict[str, Any]:
    if not caminho.exists():
        return {"type": "FeatureCollection", "features": []}
    return json.loads(caminho.read_text(encoding="utf-8"))


def id_da_feature(feature: dict[str, Any]) -> str:
    if feature.get("id") is not None:
        return str(feature["id"])
    propriedades = feature.get("properties") or {}
    return str(propriedades.get("id", ""))


def feature_por_id(colecao: dict[str, Any], trecho_id: str) -> dict[str, Any] | None:
    for feature in colecao.get("features", []):
        if id_da_feature(feature) == trecho_id:
            return feature
    return None


def ids_dos_trechos(colecao: dict[str, Any]) -> set[str]:
    return {id_da_feature(feature) for feature in colecao.get("features", []) if id_da_feature(feature)}


def _haversine(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * RAIO_TERRA_M * math.asin(math.sqrt(a))


def comprimento_da_geometria(geometria: dict[str, Any] | None) -> float:
    if not geometria:
        return 0.0
    tipo = geometria.get("type")
    coordenadas = geometria.get("coordinates") or []
    def comprimento_linha(pontos: list) -> float:
        total = 0.0
        for (lon1, lat1), (lon2, lat2) in zip(pontos, pontos[1:]):
            total += _haversine(float(lon1), float(lat1), float(lon2), float(lat2))
        return total

    if tipo == "Point":
        return float(COMPRIMENTO_PONTO_M)
    if tipo == "LineString":
        medido = comprimento_linha(coordenadas)
        return medido if medido > 0 else float(COMPRIMENTO_PONTO_M)
    if tipo == "MultiLineString":
        return sum(comprimento_linha(linha) for linha in coordenadas)
    return 0.0


def _xy_metros(lon: float, lat: float, lon0: float, lat0: float) -> tuple[float, float]:
    x = math.radians(lon - lon0) * RAIO_TERRA_M * math.cos(math.radians(lat0))
    y = math.radians(lat - lat0) * RAIO_TERRA_M
    return x, y


def _distancia_ponto_segmento(
    lon: float, lat: float, lon1: float, lat1: float, lon2: float, lat2: float
) -> float:
    px, py = _xy_metros(lon, lat, lon, lat)
    ax, ay = _xy_metros(lon1, lat1, lon, lat)
    bx, by = _xy_metros(lon2, lat2, lon, lat)
    abx, aby = bx - ax, by - ay
    apx, apy = px - ax, py - ay
    comprimento2 = abx * abx + aby * aby
    if comprimento2 == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, (apx * abx + apy * aby) / comprimento2))
    return math.hypot(px - (ax + t * abx), py - (ay + t * aby))


def _distancia_ponto_geometria(lon: float, lat: float, geometria: dict[str, Any] | None) -> float:
    if not geometria:
        return float("inf")
    tipo = geometria.get("type")
    coordenadas = geometria.get("coordinates") or []
    linhas = [coordenadas] if tipo == "LineString" else coordenadas if tipo == "MultiLineString" else []
    menor = float("inf")
    for linha in linhas:
        for (lon1, lat1), (lon2, lat2) in zip(linha, linha[1:]):
            menor = min(menor, _distancia_ponto_segmento(lon, lat, float(lon1), float(lat1), float(lon2), float(lat2)))
    return menor


def trecho_mais_proximo(
    colecao: dict[str, Any],
    lon: float,
    lat: float,
    maximo_m: float = DISTANCIA_MAXIMA_TRECHO_M,
) -> dict[str, Any] | None:
    melhor: dict[str, Any] | None = None
    menor = float("inf")
    for feature in colecao.get("features", []):
        distancia = _distancia_ponto_geometria(lon, lat, feature.get("geometry"))
        if distancia < menor:
            menor = distancia
            propriedades = feature.get("properties") or {}
            melhor = {
                "id": id_da_feature(feature),
                "nome": propriedades.get("nome", id_da_feature(feature)),
                "distancia_m": distancia,
            }
    if melhor is None or menor > maximo_m:
        return None
    return melhor


def ponto_na_linha(coordenadas: list, fracao: float) -> list[float]:
    if not coordenadas:
        return [0.0, 0.0]
    trecho = min(max(float(fracao), 0.0), 1.0)
    if len(coordenadas) == 1:
        ponto = coordenadas[0]
        return [float(ponto[0]), float(ponto[1])]
    trechos: list[tuple[list, list, float]] = []
    total = 0.0
    for origem, destino in zip(coordenadas, coordenadas[1:]):
        distancia = _haversine(
            float(origem[0]), float(origem[1]), float(destino[0]), float(destino[1])
        )
        trechos.append((origem, destino, distancia))
        total += distancia
    if total <= 0:
        ponto = coordenadas[0]
        return [float(ponto[0]), float(ponto[1])]
    alvo = trecho * total
    acumulado = 0.0
    for origem, destino, distancia in trechos:
        if acumulado + distancia >= alvo:
            parte = 0.0 if distancia == 0 else (alvo - acumulado) / distancia
            return [
                float(origem[0]) + parte * (float(destino[0]) - float(origem[0])),
                float(origem[1]) + parte * (float(destino[1]) - float(origem[1])),
            ]
        acumulado += distancia
    ultimo = coordenadas[-1]
    return [float(ultimo[0]), float(ultimo[1])]


def comprimento_do_trecho(colecao: dict[str, Any], trecho_id: str) -> float:
    feature = feature_por_id(colecao, trecho_id)
    if feature is None:
        return 0.0
    return comprimento_da_geometria(feature.get("geometry"))
