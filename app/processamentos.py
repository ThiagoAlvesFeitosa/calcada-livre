from __future__ import annotations

import threading
from typing import Any

_trava = threading.Lock()
_registros: dict[str, dict[str, Any]] = {}
trava_visao = threading.Lock()


def resetar() -> None:
    with _trava:
        _registros.clear()


def registrar(codigo: str) -> None:
    with _trava:
        _registros[codigo] = {"status": "processando"}


def marcar_pronto(codigo: str, corpo: dict[str, Any]) -> None:
    with _trava:
        _registros[codigo] = {"status": "pronto", **corpo}


def marcar_erro(codigo: str, mensagem: str) -> None:
    with _trava:
        _registros[codigo] = {"status": "erro", "mensagem": mensagem}


def obter(codigo: str) -> dict[str, Any] | None:
    with _trava:
        registro = _registros.get(codigo)
        if registro is None:
            return None
        return dict(registro)
