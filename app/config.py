import os
from dataclasses import dataclass
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Configuracao:
    armazenamento: str
    pasta_saida: str
    pasta_modelos: Path


def obter_configuracao() -> Configuracao:
    return Configuracao(
        armazenamento=os.getenv("ARMAZENAMENTO", "local"),
        pasta_saida="saida",
        pasta_modelos=RAIZ / "modelos",
    )


def preparar_pastas_modelos() -> Path:
    configuracao = obter_configuracao()
    pasta = configuracao.pasta_modelos
    huggingface = pasta / "huggingface"
    pasta.mkdir(parents=True, exist_ok=True)
    huggingface.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("HF_HOME", str(huggingface))
    os.environ.setdefault("TRANSFORMERS_CACHE", str(huggingface))
    os.environ.setdefault("HF_HUB_CACHE", str(huggingface / "hub"))
    return pasta
