from fastapi.testclient import TestClient

from app.adaptadores.armazenamento_falso import ArmazenamentoFalso
from app.main import app, obter_armazenamento


def test_saude_devolve_ok_quando_armazenamento_responde():
    # preparar
    armazenamento = ArmazenamentoFalso(disponivel=True)
    app.dependency_overrides[obter_armazenamento] = lambda: armazenamento
    cliente = TestClient(app)

    # executar
    resposta = cliente.get("/saude")

    # verificar
    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok", "armazenamento": "ok"}

    app.dependency_overrides.clear()


def test_saude_devolve_falha_quando_armazenamento_indisponivel():
    # preparar
    armazenamento = ArmazenamentoFalso(disponivel=False)
    app.dependency_overrides[obter_armazenamento] = lambda: armazenamento
    cliente = TestClient(app)

    # executar
    resposta = cliente.get("/saude")

    # verificar
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["status"] == "ok"
    assert corpo["armazenamento"] == "falha"

    app.dependency_overrides.clear()
