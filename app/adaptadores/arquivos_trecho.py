from pathlib import Path

NOMES_JSON = ("resultado.json", "nota.json")
SUFIXO_QUADRO = ".png"
SUFIXO_VIDEO = ".mp4"


def arquivos_para_guardar(pasta_local: Path) -> list[tuple[str, Path]]:
    pasta = Path(pasta_local)
    saida: list[tuple[str, Path]] = []
    for nome in NOMES_JSON:
        caminho = pasta / nome
        if caminho.is_file():
            saida.append((nome, caminho))
    quadros = pasta / "quadros"
    if quadros.is_dir():
        for caminho in sorted(quadros.glob(f"*{SUFIXO_QUADRO}")):
            saida.append((f"quadros/{caminho.name}", caminho))
    return saida


def nome_seguro(nome: str) -> str | None:
    if not nome or Path(nome).name != nome or ".." in nome:
        return None
    return nome
