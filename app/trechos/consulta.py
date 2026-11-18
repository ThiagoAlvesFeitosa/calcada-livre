from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.nota.parametros import QUADROS_NO_DETALHE
from app.nota.regras import calcular_nota
from app.trechos.geometria import (
    carregar_colecao,
    comprimento_do_trecho,
    feature_por_id,
    id_da_feature,
)


def _pasta_trecho(pasta_saida: Path, trecho_id: str) -> Path:
    return pasta_saida / trecho_id


def _ler_json(caminho: Path) -> dict[str, Any] | None:
    if not caminho.exists():
        return None
    return json.loads(caminho.read_text(encoding="utf-8"))


def _data_da_varredura(pasta: Path, nota: dict[str, Any] | None) -> str | None:
    if nota and nota.get("data"):
        return str(nota["data"])
    resultado = pasta / "resultado.json"
    if resultado.exists():
        return datetime.fromtimestamp(resultado.stat().st_mtime, tz=timezone.utc).isoformat()
    return None


def nota_do_trecho(pasta_saida: Path, colecao: dict[str, Any], trecho_id: str) -> dict[str, Any] | None:
    pasta = _pasta_trecho(pasta_saida, trecho_id)
    comprimento = comprimento_do_trecho(colecao, trecho_id)
    if comprimento <= 0:
        return None
    gravada = _ler_json(pasta / "nota.json")
    if gravada:
        gravada = dict(gravada)
        gravada["comprimento_m"] = comprimento
        return gravada
    resultado = _ler_json(pasta / "resultado.json")
    if resultado is None:
        return None
    calculada = calcular_nota(list(resultado.get("obstaculos", [])), comprimento)
    calculada["comprimento_m"] = comprimento
    calculada["data"] = _data_da_varredura(pasta, None)
    return calculada


def _obstaculos_por_tipo(obstaculos: list[dict[str, Any]]) -> dict[str, int]:
    contagem: dict[str, int] = {}
    for item in obstaculos:
        classe = str(item.get("classe", "desconhecido"))
        contagem[classe] = contagem.get(classe, 0) + 1
    return contagem


def _tres_quadros(pasta: Path, trecho_id: str) -> list[str]:
    arquivos = sorted((pasta / "quadros").glob("*.png"))
    if not arquivos:
        return []
    if len(arquivos) <= QUADROS_NO_DETALHE:
        escolhidos = arquivos
    else:
        ultimo = len(arquivos) - 1
        indices = [round(i * ultimo / (QUADROS_NO_DETALHE - 1)) for i in range(QUADROS_NO_DETALHE)]
        escolhidos = [arquivos[indice] for indice in indices]
    return [f"/quadros/{trecho_id}/{arquivo.name}" for arquivo in escolhidos]


def detalhe_do_trecho(pasta_saida: Path, colecao: dict[str, Any], trecho_id: str) -> dict[str, Any] | None:
    feature = feature_por_id(colecao, trecho_id)
    if feature is None:
        return None
    propriedades = feature.get("properties") or {}
    pasta = _pasta_trecho(pasta_saida, trecho_id)
    resultado = _ler_json(pasta / "resultado.json") or {"obstaculos": []}
    obstaculos = list(resultado.get("obstaculos", []))
    nota = nota_do_trecho(pasta_saida, colecao, trecho_id)
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
        "quadros": _tres_quadros(pasta, trecho_id) if nota is not None else [],
        "obstaculos": obstaculos if nota is not None else [],
    }


def geojson_com_notas(pasta_saida: Path, colecao: dict[str, Any]) -> dict[str, Any]:
    saida = {"type": "FeatureCollection", "features": []}
    for feature in colecao.get("features", []):
        trecho_id = id_da_feature(feature)
        copia = json.loads(json.dumps(feature))
        propriedades = dict(copia.get("properties") or {})
        propriedades["id"] = trecho_id
        nota = nota_do_trecho(pasta_saida, colecao, trecho_id) if trecho_id else None
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
        copia["properties"] = propriedades
        saida["features"].append(copia)
    return saida


def resumo_censo(pasta_saida: Path, colecao: dict[str, Any]) -> dict[str, int]:
    filmados = 0
    sem_obstaculo = 0
    for feature in colecao.get("features", []):
        trecho_id = id_da_feature(feature)
        resultado = _ler_json(_pasta_trecho(pasta_saida, trecho_id) / "resultado.json")
        if resultado is None:
            continue
        filmados += 1
        if not resultado.get("obstaculos"):
            sem_obstaculo += 1
    return {"sem_obstaculo": sem_obstaculo, "filmados": filmados}


def carregar_trechos(caminho: Path) -> dict[str, Any]:
    return carregar_colecao(caminho)
