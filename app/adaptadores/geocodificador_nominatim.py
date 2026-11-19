from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

from app.nota.parametros import GEOCODIFICADOR_TIMEOUT_S, GEOCODIFICADOR_USER_AGENT


class GeocodificadorNominatim:
    def __init__(self, timeout_s: float = GEOCODIFICADOR_TIMEOUT_S) -> None:
        self.timeout_s = timeout_s
        self._cache: dict[tuple[float, float], str | None] = {}

    def nome_da_rua(self, lat: float, lon: float) -> str | None:
        chave = (round(lat, 5), round(lon, 5))
        if chave in self._cache:
            return self._cache[chave]
        nome = self._consultar(lat, lon)
        self._cache[chave] = nome
        return nome

    def _consultar(self, lat: float, lon: float) -> str | None:
        query = urllib.parse.urlencode(
            {
                "lat": f"{lat:.6f}",
                "lon": f"{lon:.6f}",
                "format": "json",
                "zoom": "18",
                "addressdetails": "1",
            }
        )
        pedido = urllib.request.Request(
            "https://nominatim.openstreetmap.org/reverse?" + query,
            headers={"User-Agent": GEOCODIFICADOR_USER_AGENT, "Accept": "application/json"},
            method="GET",
        )
        try:
            with urllib.request.urlopen(pedido, timeout=self.timeout_s) as resposta:
                corpo = json.loads(resposta.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError):
            return None
        endereco = corpo.get("address") or {}
        for chave in ("road", "pedestrian", "footway", "path", "residential"):
            valor = endereco.get(chave)
            if valor:
                return str(valor)
        return None
