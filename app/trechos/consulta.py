from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from app.nota.parametros import FUSO_BRASILIA, QUADROS_NO_DETALHE
from app.nota.regras import calcular_nota
from app.portas.armazenamento import Armazenamento
from app.visao.parametros import nome_em_portugues
from app.trechos.geometria import (
    carregar_colecao,
    comprimento_do_trecho,
    feature_por_id,
    id_da_feature,
    ponto_na_linha,
)


def formatar_data_brasilia(valor: str | datetime | None) -> str | None:
    if valor is None:
        return None
    if isinstance(valor, datetime):
        momento = valor
    else:
        texto = str(valor)
        if texto.endswith("Z"):
            texto = texto[:-1] + "+00:00"
        try:
            momento = datetime.fromisoformat(texto)
        except ValueError:
            return str(valor)
    if momento.tzinfo is None:
        momento = momento.replace(tzinfo=timezone.utc)
    return momento.astimezone(ZoneInfo(FUSO_BRASILIA)).strftime("%d/%m/%Y %H:%M")


def nota_do_trecho(
    armazenamento: Armazenamento,
    colecao: dict[str, Any],
    trecho_id: str,
) -> dict[str, Any] | None:
    comprimento = comprimento_do_trecho(colecao, trecho_id)
    if comprimento <= 0:
        return None
    gravada = armazenamento.ler_json(trecho_id, "nota.json")
    if gravada:
        gravada = dict(gravada)
        gravada["comprimento_m"] = comprimento
        gravada["data"] = formatar_data_brasilia(gravada.get("data"))
        return gravada
    resultado = armazenamento.ler_json(trecho_id, "resultado.json")
    if resultado is None:
        return None
    calculada = calcular_nota(list(resultado.get("obstaculos", [])), comprimento)
    calculada["comprimento_m"] = comprimento
    calculada["data"] = None
    return calculada


def pontos_dos_obstaculos(
    geometria: dict[str, Any] | None,
    obstaculos: list[dict[str, Any]],
    duracao_s: float,
) -> list[dict[str, Any]]:
    if not geometria or geometria.get("type") != "LineString":
        return []
    coordenadas = geometria.get("coordinates") or []
    duracao = float(duracao_s or 0)
    pontos: list[dict[str, Any]] = []
    for item in obstaculos:
        instante = float(item.get("instante_s") or 0)
        fracao = 0.0 if duracao <= 0 else min(max(instante / duracao, 0.0), 1.0)
        lon, lat = ponto_na_linha(coordenadas, fracao)
        pontos.append(
            {
                "lon": lon,
                "lat": lat,
                "classe": nome_em_portugues(str(item.get("classe", ""))),
                "instante_s": instante,
            }
        )
    return pontos


def _obstaculos_por_tipo(obstaculos: list[dict[str, Any]]) -> dict[str, int]:
    contagem: dict[str, int] = {}
    for item in obstaculos:
        classe = nome_em_portugues(str(item.get("classe", "desconhecido")))
        contagem[classe] = contagem.get(classe, 0) + 1
    return contagem


def _tres_quadros(armazenamento: Armazenamento, trecho_id: str) -> list[str]:
    arquivos = armazenamento.listar_quadros(trecho_id)
    if not arquivos:
        return []
    if len(arquivos) <= QUADROS_NO_DETALHE:
        escolhidos = arquivos
    else:
        ultimo = len(arquivos) - 1
        indices = [round(i * ultimo / (QUADROS_NO_DETALHE - 1)) for i in range(QUADROS_NO_DETALHE)]
        escolhidos = [arquivos[indice] for indice in indices]
    return [f"/quadros/{trecho_id}/{arquivo}" for arquivo in escolhidos]


def detalhe_do_trecho(
    armazenamento: Armazenamento,
    colecao: dict[str, Any],
    trecho_id: str,
) -> dict[str, Any] | None:
    feature = feature_por_id(colecao, trecho_id)
    if feature is None:
        return None
    propriedades = feature.get("properties") or {}
    resultado = armazenamento.ler_json(trecho_id, "resultado.json") or {"obstaculos": []}
    obstaculos = list(resultado.get("obstaculos", []))
    nota = nota_do_trecho(armazenamento, colecao, trecho_id)
    duracao = float(resultado.get("duracao_s") or 0)
    return {
        "id": trecho_id,
        "nome": propriedades.get("nome", trecho_id),
        "nota": None if nota is None else nota.get("nota"),
        "cor": None if nota is None else nota.get("cor"),
        "data": None if nota is None else nota.get("data"),
        "comprimento_m": comprimento_do_trecho(colecao, trecho_id),
        "obstaculos_por_100m": None if nota is None else nota.get("obstaculos_por_100m"),
        "faixa_livre_media": None if nota is None else nota.get("faixa_livre_media"),
        "obstaculos_por_tipo": _obstaculos_por_tipo(obstaculos) if nota is not None else {},
        "quadros": _tres_quadros(armazenamento, trecho_id) if nota is not None else [],
        "obstaculos": obstaculos if nota is not None else [],
        "duracao_s": duracao if nota is not None else None,
    }


def geojson_com_notas(armazenamento: Armazenamento, colecao: dict[str, Any]) -> dict[str, Any]:
    saida = {"type": "FeatureCollection", "features": []}
    for feature in colecao.get("features", []):
        trecho_id = id_da_feature(feature)
        copia = json.loads(json.dumps(feature))
        propriedades = dict(copia.get("properties") or {})
        propriedades["id"] = trecho_id
        nota = nota_do_trecho(armazenamento, colecao, trecho_id) if trecho_id else None
        if nota is None:
            propriedades["nota"] = None
            propriedades["cor"] = None
            propriedades["data"] = None
            propriedades["filmado"] = False
        else:
            propriedades["nota"] = nota.get("nota")
            propriedades["cor"] = nota.get("cor")
            propriedades["data"] = nota.get("data")
            propriedades["filmado"] = True
            propriedades["obstaculos_por_100m"] = nota.get("obstaculos_por_100m")
            resultado = armazenamento.ler_json(trecho_id, "resultado.json") or {}
            obstaculos = list(resultado.get("obstaculos", []))
            duracao = float(resultado.get("duracao_s") or 0)
            propriedades["duracao_s"] = duracao
            propriedades["pontos_obstaculos"] = pontos_dos_obstaculos(
                copia.get("geometry"), obstaculos, duracao
            )
        copia["properties"] = propriedades
        saida["features"].append(copia)
    return saida


def resumo_censo(armazenamento: Armazenamento, colecao: dict[str, Any]) -> dict[str, int]:
    filmados = 0
    sem_obstaculo = 0
    for feature in colecao.get("features", []):
        trecho_id = id_da_feature(feature)
        resultado = armazenamento.ler_json(trecho_id, "resultado.json")
        if resultado is None:
            continue
        filmados += 1
        if not resultado.get("obstaculos"):
            sem_obstaculo += 1
    return {"sem_obstaculo": sem_obstaculo, "filmados": filmados}


def carregar_trechos(caminho: Path) -> dict[str, Any]:
    return carregar_colecao(caminho)
