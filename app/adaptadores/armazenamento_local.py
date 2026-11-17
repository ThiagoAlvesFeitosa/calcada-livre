from pathlib import Path


class ArmazenamentoLocal:
    def __init__(self, pasta: str = "saida") -> None:
        self.pasta = Path(pasta)

    def verificar(self) -> bool:
        try:
            self.pasta.mkdir(parents=True, exist_ok=True)
            arquivo = self.pasta / ".saude"
            arquivo.write_text("ok", encoding="utf-8")
            lido = arquivo.read_text(encoding="utf-8")
            arquivo.unlink(missing_ok=True)
            return lido == "ok"
        except OSError:
            return False
