from __future__ import annotations

import threading
import uuid
from typing import Any

from app.nota.parametros import DISTANCIA_MESMO_TRECHO_M
from app.trechos.geometria import id_da_feature

_trava = threading.Lock()


def trava_cadastro() -> threading.Lock:
    return _trava


def colecao_vazia() -> dict[str, Any]:
    return {"type": "FeatureCollection", "features": []}


def normalizar_rua(nome: str | None) -> str:
    return " ".join(str(nome or "").casefold().split())


def pontas(geometria: dict[str, Any] | None) -> tuple[list[float], list[float]] | None:
    if not geometria:
        return None
    tipo = geometria.get("type")
    coordenadas = geometria.get("coordinates") or []
    if tipo == "Point" and len(coordenadas) >= 2:
        ponto = [float(coordenadas[0]), float(coordenadas[1])]
        return ponto, ponto
    if tipo == "LineString" and len(coordenadas) >= 1:
        inicio = coordenadas[0]
        fim = coordenadas[-1]
        return [float(inicio[0]), float(inicio[1])], [float(fim[0]), float(fim[1])]
    return None


def _perto(a: list[float], b: list[float], maximo_m: float) -> bool:
    from app.trechos.geometria import _haversine

    return _haversine(a[0], a[1], b[0], b[1]) <= maximo_m


def pontas_combinam(
    inicio: list[float],
    fim: list[float],
    geometria: dict[str, Any] | None,
    maximo_m: float = DISTANCIA_MESMO_TRECHO_M,
) -> bool:
    pares = pontas(geometria)
    if pares is None:
        return False
    a, b = pares
    mesmo = _perto(inicio, a, maximo_m) and _perto(fim, b, maximo_m)
    invertido = _perto(inicio, b, maximo_m) and _perto(fim, a, maximo_m)
    return mesmo or invertido


def candidato_mesmo_trecho(
    colecao: dict[str, Any],
    lon_inicio: float,
    lat_inicio: float,
    lon_fim: float | None,
    lat_fim: float | None,
    rua: str,
    maximo_m: float = DISTANCIA_MESMO_TRECHO_M,
) -> dict[str, Any] | None:
    rua_n = normalizar_rua(rua)
    if not rua_n:
        return None
    inicio = [lon_inicio, lat_inicio]
    if lon_fim is None or lat_fim is None:
        fim = inicio
    else:
        fim = [lon_fim, lat_fim]
    for feature in colecao.get("features", []):
        propriedades = feature.get("properties") or {}
        if normalizar_rua(str(propriedades.get("nome") or propriedades.get("rua") or "")) != rua_n:
            continue
        if pontas_combinam(inicio, fim, feature.get("geometry"), maximo_m):
            return {
                "id": id_da_feature(feature),
                "nome": propriedades.get("nome", id_da_feature(feature)),
                "data": propriedades.get("data"),
            }
    return None


def geometria_do_relato(
    lon_inicio: float,
    lat_inicio: float,
    lon_fim: float | None,
    lat_fim: float | None,
) -> dict[str, Any]:
    if lon_fim is None or lat_fim is None:
        return {"type": "Point", "coordinates": [lon_inicio, lat_inicio]}
    if lon_fim == lon_inicio and lat_fim == lat_inicio:
        return {"type": "Point", "coordinates": [lon_inicio, lat_inicio]}
    return {
        "type": "LineString",
        "coordinates": [[lon_inicio, lat_inicio], [lon_fim, lat_fim]],
    }


def nova_feature(nome: str, geometria: dict[str, Any], trecho_id: str | None = None) -> dict[str, Any]:
    identificador = trecho_id or uuid.uuid4().hex
    return {
        "type": "Feature",
        "id": identificador,
        "properties": {"id": identificador, "nome": nome, "rua": nome},
        "geometry": geometria,
    }


def acrescentar_feature(colecao: dict[str, Any], feature: dict[str, Any]) -> dict[str, Any]:
    saida = {"type": "FeatureCollection", "features": list(colecao.get("features") or [])}
    saida["features"].append(feature)
    return saida
