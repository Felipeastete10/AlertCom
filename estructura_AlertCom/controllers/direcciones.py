# =============================================================================
# AlertCom - Calle a partir de coordenadas (geocodificación inversa)
# =============================================================================
# Cuando el vecino marca el lugar del daño (con GPS o moviendo el mapa), se
# pregunta a Nominatim (servicio gratuito de OpenStreetMap) qué calle hay en
# ese punto, y se completa el campo "Calle" para ahorrarle escribir.
# El vecino SIEMPRE puede corregir la calle a mano.
#
# Reglas de uso de Nominatim que respetamos:
#   • Identificar la app con un User-Agent propio.
#   • Máximo 1 consulta por segundo (la vista espera a que el mapa se quede
#     quieto antes de preguntar).
# Sin internet no pasa nada: el campo queda vacío para escribirlo.
#
# También al revés: si el vecino ESCRIBE la calle, se busca en el mapa
# (solo dentro de Temuco) y el pin se mueve a ese lugar.
# =============================================================================

import json
import logging
from urllib.parse import quote

from config import CIUDAD_BUSQUEDA, URL_BUSCAR_CALLE, URL_DIRECCION, USER_AGENT

log = logging.getLogger("alertcom.direcciones")

# Nombres que usa OpenStreetMap para las vías, en orden de preferencia
CLAVES_DE_VIA = ("road", "pedestrian", "footway", "residential", "path", "cycleway")


def calle_desde_respuesta(datos) -> str | None:
    """Extrae 'Calle Número' de la respuesta de Nominatim.
    Ej: {"address": {"road": "Avenida Alemania", "house_number": "0450"}}
        → "Avenida Alemania 0450"."""
    if not isinstance(datos, dict):
        return None
    direccion = datos.get("address") or {}
    via = next((direccion[c] for c in CLAVES_DE_VIA if direccion.get(c)), None)
    if not via:
        return None
    numero = direccion.get("house_number")
    return f"{via} {numero}" if numero else via


def lugar_desde_busqueda(datos) -> tuple[float, float, bool] | None:
    """Primer resultado de una búsqueda de Nominatim → (lat, lon, exacto).
    exacto=True si encontró el número de casa; si no, el punto es el centro
    de la calle y el vecino debe ajustar el pin."""
    if not isinstance(datos, list) or not datos or not isinstance(datos[0], dict):
        return None
    primero = datos[0]
    try:
        lat, lon = float(primero["lat"]), float(primero["lon"])
    except (KeyError, TypeError, ValueError):
        return None
    exacto = bool((primero.get("address") or {}).get("house_number"))
    return lat, lon, exacto


def texto_de_busqueda(calle: str) -> str:
    """'Prat 450' → 'Prat 450, Temuco' (para que no busque en otra ciudad)."""
    calle = " ".join((calle or "").split())
    if CIUDAD_BUSQUEDA.lower() not in calle.lower():
        calle = f"{calle}, {CIUDAD_BUSQUEDA}"
    return calle


class BuscadorCalles:
    """Consulta asíncrona (no congela la app) a Nominatim."""

    def __init__(self, timeout: int = 6) -> None:
        self.timeout = timeout
        self._ultima_consulta = {}  # una cuenta por tipo de búsqueda

    def buscar(self, lat: float, lon: float, al_encontrar) -> None:
        """Coordenadas → calle. Llama a al_encontrar(calle) o al_encontrar(None)."""
        self._consultar("calle", URL_DIRECCION.format(lat=lat, lon=lon), calle_desde_respuesta, al_encontrar)

    def buscar_lugar(self, calle: str, al_encontrar) -> None:
        """Calle escrita → coordenadas. Llama a al_encontrar((lat, lon, exacto))
        o al_encontrar(None) si no la encontró o no hay internet."""
        url = URL_BUSCAR_CALLE.format(texto=quote(texto_de_busqueda(calle)))
        self._consultar("lugar", url, lugar_desde_busqueda, al_encontrar)

    def _consultar(self, tipo: str, url: str, interpretar, al_encontrar) -> None:
        from kivy.network.urlrequest import UrlRequest

        # Si llega una consulta nueva del mismo tipo, la anterior ya no sirve.
        numero = self._ultima_consulta.get(tipo, 0) + 1
        self._ultima_consulta[tipo] = numero

        def vigente() -> bool:
            return self._ultima_consulta.get(tipo) == numero

        def al_recibir(_peticion, resultado):
            if not vigente():
                return
            if isinstance(resultado, (bytes, str)):
                try:
                    resultado = json.loads(resultado)
                except ValueError:
                    resultado = None
            al_encontrar(interpretar(resultado))

        def al_fallar(_peticion, error):
            log.info("Consulta a Nominatim (%s) sin respuesta: %s", tipo, error)
            if vigente():
                al_encontrar(None)

        try:
            import certifi
            certificados = certifi.where()
        except ImportError:
            certificados = None

        UrlRequest(
            url,
            req_headers={"User-Agent": USER_AGENT},
            on_success=al_recibir,
            on_failure=al_fallar,
            on_error=al_fallar,
            timeout=self.timeout,
            ca_file=certificados,
            verify=True,
        )
