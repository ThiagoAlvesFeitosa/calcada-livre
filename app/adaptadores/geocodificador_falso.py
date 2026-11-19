class GeocodificadorFalso:
    def __init__(self, nome: str | None = "Rua de teste") -> None:
        self.nome = nome
        self.chamadas: list[tuple[float, float]] = []

    def nome_da_rua(self, lat: float, lon: float) -> str | None:
        self.chamadas.append((lat, lon))
        return self.nome
