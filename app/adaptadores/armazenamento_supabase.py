import json
from pathlib import Path
from typing import Any

from app.adaptadores.arquivos_trecho import arquivos_para_guardar, nome_seguro, SUFIXO_QUADRO
from app.nota.parametros import ARQUIVO_COLECAO_TRECHOS
from app.trechos.cadastro import colecao_vazia


class ArmazenamentoSupabase:
    def __init__(self, url: str, chave: str, bucket: str) -> None:
        from supabase import create_client

        self._bucket = bucket
        self._cliente = create_client(url, chave)

    def verificar(self) -> bool:
        try:
            caminho = ".saude"
            self._enviar(caminho, b"ok", "text/plain")
            lido = self._baixar(caminho)
            self._apagar(caminho)
            return lido == b"ok"
        except Exception:
            return False

    def guardar_trecho(self, trecho_id: str, pasta_local: Path) -> None:
        for relativo, origem in arquivos_para_guardar(pasta_local):
            tipo = "image/png" if relativo.endswith(SUFIXO_QUADRO) else "application/json"
            self._enviar(f"{trecho_id}/{relativo}", origem.read_bytes(), tipo)

    def ler_json(self, trecho_id: str, nome: str) -> dict[str, Any] | None:
        seguro = nome_seguro(nome)
        if seguro is None:
            return None
        dados = self._baixar(f"{trecho_id}/{seguro}")
        if dados is None:
            return None
        return json.loads(dados.decode("utf-8"))

    def ler_quadro(self, trecho_id: str, nome: str) -> bytes | None:
        seguro = nome_seguro(nome)
        if seguro is None or not seguro.lower().endswith(SUFIXO_QUADRO):
            return None
        return self._baixar(f"{trecho_id}/quadros/{seguro}")

    def listar_quadros(self, trecho_id: str) -> list[str]:
        try:
            itens = self._cliente.storage.from_(self._bucket).list(f"{trecho_id}/quadros")
        except Exception:
            return []
        nomes = []
        for item in itens or []:
            nome = str(item.get("name") or "")
            if nome.lower().endswith(SUFIXO_QUADRO) and nome_seguro(nome):
                nomes.append(nome)
        return sorted(nomes)

    def ler_colecao_trechos(self) -> dict:
        dados = self._baixar(ARQUIVO_COLECAO_TRECHOS)
        if not dados:
            return colecao_vazia()
        return json.loads(dados.decode("utf-8"))

    def guardar_colecao_trechos(self, colecao: dict) -> None:
        self._enviar(
            ARQUIVO_COLECAO_TRECHOS,
            json.dumps(colecao, ensure_ascii=False, indent=2).encode("utf-8"),
            "application/json",
        )

    def _enviar(self, caminho: str, conteudo: bytes, tipo: str) -> None:
        opcoes = {"content-type": tipo, "upsert": "true"}
        armazenamento = self._cliente.storage.from_(self._bucket)
        try:
            armazenamento.upload(caminho, conteudo, file_options=opcoes)
        except Exception:
            armazenamento.update(caminho, conteudo, file_options=opcoes)

    def _baixar(self, caminho: str) -> bytes | None:
        try:
            dados = self._cliente.storage.from_(self._bucket).download(caminho)
        except Exception:
            return None
        if dados is None:
            return None
        return bytes(dados)

    def _apagar(self, caminho: str) -> None:
        try:
            self._cliente.storage.from_(self._bucket).remove([caminho])
        except Exception:
            return
