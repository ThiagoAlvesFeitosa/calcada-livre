from typing import Protocol


class Armazenamento(Protocol):
    def verificar(self) -> bool:
        """Tenta gravar e ler. Devolve True se o armazenamento responde."""
        ...
