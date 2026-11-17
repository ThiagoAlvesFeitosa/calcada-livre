import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Configuracao:
    armazenamento: str
    pasta_saida: str


def obter_configuracao() -> Configuracao:
    return Configuracao(
        armazenamento=os.getenv("ARMAZENAMENTO", "local"),
        pasta_saida="saida",
    )
