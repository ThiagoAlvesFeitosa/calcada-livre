import os
from dataclasses import dataclass
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Configuracao:
    armazenamento: str
    pasta_saida: str
    pasta_modelos: Path
    tamanho_maximo_video_mb: int
    caminho_trechos: Path


def obter_configuracao() -> Configuracao:
    return Configuracao(
        armazenamento=os.getenv("ARMAZENAMENTO", "local"),
        pasta_saida=os.getenv("PASTA_SAIDA", "saida"),
        pasta_modelos=RAIZ / "modelos",
        tamanho_maximo_video_mb=int(os.getenv("TAMANHO_MAXIMO_VIDEO_MB", "200")),
        caminho_trechos=Path(os.getenv("CAMINHO_TRECHOS", str(RAIZ / "dados" / "trechos.geojson"))),
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
