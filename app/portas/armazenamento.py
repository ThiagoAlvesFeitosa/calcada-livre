from pathlib import Path
from typing import Any, Protocol


class Armazenamento(Protocol):
    def verificar(self) -> bool:
        """Tenta gravar e ler. Devolve True se o armazenamento responde."""
        ...

    def guardar_trecho(self, trecho_id: str, pasta_local: Path) -> None:
        """Grava resultado.json, nota.json e PNG. Nunca grava vídeo."""
        ...

    def ler_json(self, trecho_id: str, nome: str) -> dict[str, Any] | None:
        ...

    def ler_quadro(self, trecho_id: str, nome: str) -> bytes | None:
        ...

    def listar_quadros(self, trecho_id: str) -> list[str]:
        ...

    def ler_colecao_trechos(self) -> dict:
        ...

    def guardar_colecao_trechos(self, colecao: dict) -> None:
        ...
