import json
from pathlib import Path
from typing import Any

from app.adaptadores.arquivos_trecho import arquivos_para_guardar, nome_seguro, SUFIXO_QUADRO
from app.trechos.cadastro import colecao_vazia


class ArmazenamentoFalso:
    def __init__(self, disponivel: bool = True) -> None:
        self.disponivel = disponivel
        self.arquivos: dict[str, bytes] = {}
        self.colecao: dict = colecao_vazia()

    def verificar(self) -> bool:
        return self.disponivel

    def guardar_trecho(self, trecho_id: str, pasta_local: Path) -> None:
        for relativo, caminho in arquivos_para_guardar(pasta_local):
            self.arquivos[f"{trecho_id}/{relativo}"] = caminho.read_bytes()

    def ler_json(self, trecho_id: str, nome: str) -> dict[str, Any] | None:
        dados = self._ler(trecho_id, nome)
        if dados is None:
            return None
        return json.loads(dados.decode("utf-8"))

    def ler_quadro(self, trecho_id: str, nome: str) -> bytes | None:
        seguro = nome_seguro(nome)
        if seguro is None or not seguro.lower().endswith(SUFIXO_QUADRO):
            return None
        return self.arquivos.get(f"{trecho_id}/quadros/{seguro}")

    def listar_quadros(self, trecho_id: str) -> list[str]:
        prefixo = f"{trecho_id}/quadros/"
        nomes = [
            chave[len(prefixo) :]
            for chave in self.arquivos
            if chave.startswith(prefixo) and chave.lower().endswith(SUFIXO_QUADRO)
        ]
        return sorted(nomes)

    def ler_colecao_trechos(self) -> dict:
        return json.loads(json.dumps(self.colecao))

    def guardar_colecao_trechos(self, colecao: dict) -> None:
        self.colecao = json.loads(json.dumps(colecao))

    def _ler(self, trecho_id: str, nome: str) -> bytes | None:
        seguro = nome_seguro(nome)
        if seguro is None:
            return None
        return self.arquivos.get(f"{trecho_id}/{seguro}")
