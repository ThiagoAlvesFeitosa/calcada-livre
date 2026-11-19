from typing import Protocol


class Geocodificador(Protocol):
    def nome_da_rua(self, lat: float, lon: float) -> str | None:
        """Devolve o nome da rua ou None se não achar."""
        ...

    def ponto_do_endereco(self, texto: str) -> dict | None:
        """Devolve lat, lon e nome, ou None se não achar."""
        ...
