import os
from dataclasses import dataclass
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

VARIAVEIS_SUPABASE = ("SUPABASE_URL", "SUPABASE_KEY", "SUPABASE_BUCKET")
TAMANHO_MAXIMO_VIDEO_MB_PADRAO = 95
INTERVALO_ANDAMENTO_S = 3


def carregar_arquivo_env() -> None:
    caminho = RAIZ / ".env"
    if not caminho.is_file():
        return
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        texto = linha.strip()
        if not texto or texto.startswith("#") or "=" not in texto:
            continue
        chave, _, valor = texto.partition("=")
        chave = chave.strip()
        valor = valor.strip().strip('"').strip("'")
        if chave and chave not in os.environ:
            os.environ[chave] = valor


@dataclass(frozen=True)
class Configuracao:
    armazenamento: str
    pasta_saida: str
    pasta_modelos: Path
    tamanho_maximo_video_mb: int
    caminho_trechos: Path


def nomes_variaveis_faltando(armazenamento: str, ambiente: dict[str, str] | None = None) -> list[str]:
    if armazenamento != "supabase":
        return []
    origem = os.environ if ambiente is None else ambiente
    faltando: list[str] = []
    for nome in VARIAVEIS_SUPABASE:
        if not str(origem.get(nome, "")).strip():
            faltando.append(nome)
    return faltando


def conferir_configuracao() -> None:
    carregar_arquivo_env()
    modo = os.getenv("ARMAZENAMENTO", "local")
    faltando = nomes_variaveis_faltando(modo)
    if faltando:
        raise RuntimeError("Faltam variáveis: " + ", ".join(faltando))


def obter_configuracao() -> Configuracao:
    carregar_arquivo_env()
    return Configuracao(
        armazenamento=os.getenv("ARMAZENAMENTO", "local"),
        pasta_saida=os.getenv("PASTA_SAIDA", "saida"),
        pasta_modelos=RAIZ / "modelos",
        tamanho_maximo_video_mb=int(os.getenv("TAMANHO_MAXIMO_VIDEO_MB", str(TAMANHO_MAXIMO_VIDEO_MB_PADRAO))),
        caminho_trechos=Path(os.getenv("CAMINHO_TRECHOS", str(RAIZ / "dados" / "trechos.geojson"))),
    )


def criar_armazenamento(configuracao: Configuracao | None = None):
    from app.adaptadores.armazenamento_local import ArmazenamentoLocal

    carregar_arquivo_env()
    atual = configuracao or obter_configuracao()
    if atual.armazenamento == "local":
        return ArmazenamentoLocal(pasta=atual.pasta_saida)
    if atual.armazenamento == "supabase":
        conferir_configuracao()
        from app.adaptadores.armazenamento_supabase import ArmazenamentoSupabase

        return ArmazenamentoSupabase(
            url=os.environ["SUPABASE_URL"],
            chave=os.environ["SUPABASE_KEY"],
            bucket=os.environ["SUPABASE_BUCKET"],
        )
    raise RuntimeError("Armazenamento desconhecido.")


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
