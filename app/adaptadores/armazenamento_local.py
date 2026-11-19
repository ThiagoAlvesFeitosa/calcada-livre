import json
from pathlib import Path
from typing import Any

from app.adaptadores.arquivos_trecho import arquivos_para_guardar, nome_seguro, SUFIXO_QUADRO
from app.nota.parametros import ARQUIVO_COLECAO_TRECHOS
from app.trechos.cadastro import colecao_vazia


class ArmazenamentoLocal:
    def __init__(self, pasta: str = "saida") -> None:
        self.pasta = Path(pasta)

    def verificar(self) -> bool:
        try:
            self.pasta.mkdir(parents=True, exist_ok=True)
            arquivo = self.pasta / ".saude"
            arquivo.write_text("ok", encoding="utf-8")
            lido = arquivo.read_text(encoding="utf-8")
            arquivo.unlink(missing_ok=True)
            return lido == "ok"
        except OSError:
            return False

    def guardar_trecho(self, trecho_id: str, pasta_local: Path) -> None:
        destino = self.pasta / trecho_id
        destino.mkdir(parents=True, exist_ok=True)
        (destino / "quadros").mkdir(parents=True, exist_ok=True)
        for relativo, origem in arquivos_para_guardar(pasta_local):
            alvo = destino / relativo
            alvo.parent.mkdir(parents=True, exist_ok=True)
            if origem.resolve() != alvo.resolve():
                alvo.write_bytes(origem.read_bytes())

    def ler_json(self, trecho_id: str, nome: str) -> dict[str, Any] | None:
        caminho = self._caminho(trecho_id, nome)
        if caminho is None or not caminho.is_file():
            return None
        return json.loads(caminho.read_text(encoding="utf-8"))

    def ler_quadro(self, trecho_id: str, nome: str) -> bytes | None:
        seguro = nome_seguro(nome)
        if seguro is None or not seguro.lower().endswith(SUFIXO_QUADRO):
            return None
        caminho = self.pasta / trecho_id / "quadros" / seguro
        if not caminho.is_file():
            return None
        return caminho.read_bytes()

    def listar_quadros(self, trecho_id: str) -> list[str]:
        pasta = self.pasta / trecho_id / "quadros"
        if not pasta.is_dir():
            return []
        return sorted(caminho.name for caminho in pasta.glob(f"*{SUFIXO_QUADRO}"))

    def ler_colecao_trechos(self) -> dict:
        caminho = self.pasta / ARQUIVO_COLECAO_TRECHOS
        if not caminho.is_file():
            return colecao_vazia()
        return json.loads(caminho.read_text(encoding="utf-8"))

    def guardar_colecao_trechos(self, colecao: dict) -> None:
        self.pasta.mkdir(parents=True, exist_ok=True)
        (self.pasta / ARQUIVO_COLECAO_TRECHOS).write_text(
            json.dumps(colecao, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _caminho(self, trecho_id: str, nome: str) -> Path | None:
        seguro = nome_seguro(nome)
        if seguro is None:
            return None
        return self.pasta / trecho_id / seguro
