from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

from app.nota.parametros import (
    GEOCODIFICADOR_PAIS,
    GEOCODIFICADOR_TIMEOUT_S,
    GEOCODIFICADOR_USER_AGENT,
)
from app.registro import registrar_geocodificador


class GeocodificadorNominatim:
    def __init__(self, timeout_s: float = GEOCODIFICADOR_TIMEOUT_S) -> None:
        self.timeout_s = timeout_s
        self._cache_rua: dict[tuple[float, float], str | None] = {}
        self._cache_busca: dict[str, dict | None] = {}

    def nome_da_rua(self, lat: float, lon: float) -> str | None:
        chave = (round(lat, 5), round(lon, 5))
        if chave in self._cache_rua:
            return self._cache_rua[chave]
        nome = self._consultar_reverso(lat, lon)
        self._cache_rua[chave] = nome
        return nome

    def ponto_do_endereco(self, texto: str) -> dict | None:
        chave = " ".join(texto.casefold().split())
        if not chave:
            return None
        if chave in self._cache_busca:
            return self._cache_busca[chave]
        ponto = self._consultar_busca(texto)
        self._cache_busca[chave] = ponto
        return ponto

    def _nome_do_endereco(self, endereco: dict, alternativa: str | None = None) -> str | None:
        for campo in ("road", "pedestrian", "footway", "path", "residential"):
            valor = endereco.get(campo)
            if valor:
                return str(valor)
        if alternativa:
            return alternativa
        return None

    def _consultar_reverso(self, lat: float, lon: float) -> str | None:
        query = urllib.parse.urlencode(
            {
                "lat": f"{lat:.6f}",
                "lon": f"{lon:.6f}",
                "format": "json",
                "zoom": "18",
                "addressdetails": "1",
            }
        )
        corpo = self._get("https://nominatim.openstreetmap.org/reverse?" + query)
        if not corpo:
            return None
        endereco = corpo.get("address") or {}
        return self._nome_do_endereco(endereco)

    def _consultar_busca(self, texto: str) -> dict | None:
        query = urllib.parse.urlencode(
            {
                "q": texto,
                "format": "json",
                "addressdetails": "1",
                "countrycodes": GEOCODIFICADOR_PAIS,
                "limit": "1",
            }
        )
        corpo = self._get("https://nominatim.openstreetmap.org/search?" + query, lista=True)
        if not corpo:
            return None
        primeiro = corpo[0] if isinstance(corpo, list) and corpo else None
        if not primeiro:
            return None
        try:
            lat = float(primeiro.get("lat"))
            lon = float(primeiro.get("lon"))
        except (TypeError, ValueError):
            return None
        nome = self._nome_do_endereco(primeiro.get("address") or {}, primeiro.get("display_name"))
        if not nome:
            return None
        return {"lat": lat, "lon": lon, "nome": nome}

    def _get(self, url: str, lista: bool = False) -> dict | list | None:
        pedido = urllib.request.Request(
            url,
            headers={"User-Agent": GEOCODIFICADOR_USER_AGENT, "Accept": "application/json"},
            method="GET",
        )
        try:
            with urllib.request.urlopen(pedido, timeout=self.timeout_s) as resposta:
                corpo = json.loads(resposta.read().decode("utf-8"))
        except urllib.error.HTTPError as erro:
            registrar_geocodificador(type(erro).__name__, erro.code)
            return None
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError) as erro:
            registrar_geocodificador(type(erro).__name__, getattr(erro, "code", None))
            return None
        if lista:
            return corpo if isinstance(corpo, list) else None
        return corpo if isinstance(corpo, dict) else None
