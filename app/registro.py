from __future__ import annotations

import logging
import sys
import traceback
from pathlib import Path

LOGGER = logging.getLogger("calcada_livre")
_destino: str | None = None


def configurar_registro(pasta_saida: str) -> None:
    global _destino
    pasta = Path(pasta_saida) / "logs"
    pasta.mkdir(parents=True, exist_ok=True)
    arquivo = str((pasta / "app.log").resolve())
    if _destino == arquivo:
        return
    LOGGER.setLevel(logging.INFO)
    LOGGER.handlers.clear()
    formato = logging.Formatter("%(asctime)s %(message)s")
    arquivo_handler = logging.FileHandler(arquivo, encoding="utf-8")
    arquivo_handler.setFormatter(formato)
    terminal = logging.StreamHandler(sys.stderr)
    terminal.setFormatter(formato)
    LOGGER.addHandler(arquivo_handler)
    LOGGER.addHandler(terminal)
    LOGGER.propagate = False
    _destino = arquivo


def registrar_falha(pasta_saida: str, codigo: str, etapa: str, erro: BaseException) -> None:
    configurar_registro(pasta_saida)
    tipo = type(erro).__name__
    texto = traceback.format_exc()
    LOGGER.error("codigo=%s etapa=%s tipo=%s\n%s", codigo, etapa, tipo, texto)


def registrar_gps(pasta_saida: str, codigo: int) -> None:
    configurar_registro(pasta_saida)
    LOGGER.info("gps codigo=%s", int(codigo))


def registrar_geocodificador(tipo: str, status: int | None) -> None:
    if not LOGGER.handlers:
        terminal = logging.StreamHandler(sys.stderr)
        terminal.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
        LOGGER.addHandler(terminal)
        LOGGER.setLevel(logging.INFO)
        LOGGER.propagate = False
    LOGGER.info("geocodificador tipo=%s status=%s", tipo, status)
