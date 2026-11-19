"""Copia os trechos 01 e 02 de dados/trechos.geojson para o armazenamento."""

from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from app.config import RAIZ as RAIZ_APP, criar_armazenamento, obter_configuracao
from app.trechos.cadastro import colecao_vazia


def main() -> None:
    origem = RAIZ_APP / "dados" / "trechos.geojson"
    colecao = json.loads(origem.read_text(encoding="utf-8"))
    ids = {
        "marilia_2026-11-17_trecho-01",
        "marilia_2026-11-17_trecho-02",
    }
    filtrada = colecao_vazia()
    for feature in colecao.get("features", []):
        identificador = str(feature.get("id") or "")
        if identificador in ids:
            filtrada["features"].append(feature)
    armazenamento = criar_armazenamento(obter_configuracao())
    armazenamento.guardar_colecao_trechos(filtrada)
    print(f"importados {len(filtrada['features'])} trecho(s)")


if __name__ == "__main__":
    main()
