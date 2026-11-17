from fastapi import Depends, FastAPI

from app.adaptadores.armazenamento_local import ArmazenamentoLocal
from app.config import obter_configuracao
from app.portas.armazenamento import Armazenamento

app = FastAPI(title="FIAP Calçada Livre")


def obter_armazenamento() -> Armazenamento:
    configuracao = obter_configuracao()
    if configuracao.armazenamento == "local":
        return ArmazenamentoLocal(pasta=configuracao.pasta_saida)
    raise RuntimeError("Armazenamento ainda não implementado.")


@app.get("/saude")
def saude(armazenamento: Armazenamento = Depends(obter_armazenamento)) -> dict[str, str]:
    try:
        disponivel = armazenamento.verificar()
    except Exception:
        disponivel = False
    return {
        "status": "ok",
        "armazenamento": "ok" if disponivel else "falha",
    }
