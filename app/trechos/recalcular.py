from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.nota.regras import calcular_nota
from app.portas.armazenamento import Armazenamento
from app.trechos.geometria import comprimento_do_trecho
from app.visao.pipeline import filtrar_obstaculos


def _ler_json(caminho: Path) -> dict[str, Any]:
    if not caminho.is_file():
        return {}
    return json.loads(caminho.read_text(encoding="utf-8"))


def _comprimento_gravado(nota: dict[str, Any], trecho_id: str, armazenamento: Armazenamento) -> float:
    gravado = nota.get("comprimento_m")
    if gravado is not None and float(gravado) > 0:
        return float(gravado)
    comprimento = comprimento_do_trecho(armazenamento.ler_colecao_trechos(), trecho_id)
    if comprimento > 0:
        return float(comprimento)
    raise ValueError(f"Trecho '{trecho_id}' não tem comprimento gravado.")


def recalcular_trecho(
    trecho_id: str,
    pasta_saida: Path | str,
    armazenamento: Armazenamento,
) -> dict[str, Any]:
    pasta = Path(pasta_saida) / trecho_id
    brutas_caminho = pasta / "deteccoes_brutas.json"
    if not brutas_caminho.is_file():
        raise FileNotFoundError(f"Não achei deteccoes_brutas.json em {pasta}")
    brutas = json.loads(brutas_caminho.read_text(encoding="utf-8"))
    deteccoes = brutas.get("deteccoes", brutas if isinstance(brutas, list) else [])
    nota_antiga = _ler_json(pasta / "nota.json")
    resultado_antigo = _ler_json(pasta / "resultado.json")
    comprimento = _comprimento_gravado(nota_antiga, trecho_id, armazenamento)
    resultado = filtrar_obstaculos(deteccoes)
    if "duracao_s" in resultado_antigo:
        resultado["duracao_s"] = resultado_antigo["duracao_s"]
    nota_nova = calcular_nota(list(resultado.get("obstaculos", [])), comprimento)
    nota_nova["data"] = datetime.now(timezone.utc).isoformat()
    nota_nova["comprimento_m"] = comprimento
    if nota_antiga.get("comprimento_origem"):
        nota_nova["comprimento_origem"] = nota_antiga["comprimento_origem"]
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / "resultado.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (pasta / "nota.json").write_text(
        json.dumps(nota_nova, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    armazenamento.guardar_trecho(trecho_id, pasta)
    return {"nota_antiga": nota_antiga, "nota_nova": nota_nova, "resultado": resultado}
