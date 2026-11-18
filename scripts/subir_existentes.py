"""Envia resultado.json, nota.json e quadros de saida/ para o armazenamento configurado."""

from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from app.config import criar_armazenamento, obter_configuracao
from app.trechos.consulta import carregar_trechos
from app.trechos.geometria import ids_dos_trechos


def main() -> None:
    configuracao = obter_configuracao()
    armazenamento = criar_armazenamento(configuracao)
    ids = ids_dos_trechos(carregar_trechos(configuracao.caminho_trechos))
    raiz = Path(configuracao.pasta_saida)
    if not raiz.is_dir():
        raiz = RAIZ / configuracao.pasta_saida
    if not raiz.is_dir():
        print("pasta saida/ não encontrada")
        return
    enviados = 0
    for pasta in sorted(raiz.iterdir()):
        if not pasta.is_dir() or pasta.name not in ids:
            continue
        if not (pasta / "resultado.json").is_file() and not (pasta / "nota.json").is_file():
            continue
        armazenamento.guardar_trecho(pasta.name, pasta)
        enviados += 1
        print(f"enviado {pasta.name}")
    print(f"pronto: {enviados} trecho(s)")


if __name__ == "__main__":
    main()
