class GeocodificadorFalso:
    def __init__(self, nome: str | None = "Rua de teste", ponto: dict | None = None) -> None:
        self.nome = nome
        self.ponto = ponto
        self.chamadas: list[tuple[float, float]] = []
        self.buscas: list[str] = []

    def nome_da_rua(self, lat: float, lon: float) -> str | None:
        self.chamadas.append((lat, lon))
        return self.nome

    def ponto_do_endereco(self, texto: str) -> dict | None:
        self.buscas.append(texto)
        return self.ponto
