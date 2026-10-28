# =============================================================================
# AlertCom - Persistencia local con JSON (Sesiones 19 y 20)
# =============================================================================
# Guarda y lee listas de diccionarios en un archivo .json del disco, para que
# los datos NO se pierdan al cerrar la app (la RAM es memoria volátil).
#
#   • Serialización   → json.dump  (objeto Python  → texto en disco)
#   • Deserialización → json.load  (texto en disco → objeto Python)
#   • Siempre con el bloque seguro  with open(...)  que cierra el archivo
#     aunque ocurra un error.
#   • try/except FileNotFoundError: en una instalación nueva el archivo aún
#     no existe; en vez de un cierre forzado, partimos con una lista vacía.
#
# Python puro: no importa Kivy.
# =============================================================================

import json
import logging
import os
from pathlib import Path

log = logging.getLogger("alertcom.datos")


class AlmacenamientoJSON:
    """Lee y escribe una lista de registros (dicts) en un archivo JSON."""

    def __init__(self, ruta_archivo: Path | str) -> None:
        self.ruta = Path(ruta_archivo)

    def cargar(self) -> list[dict]:
        """
        Deserializa el archivo. Nunca lanza excepción hacia la interfaz:
        si el archivo no existe o está dañado, devuelve una lista vacía.
        """
        try:
            with open(self.ruta, "r", encoding="utf-8") as archivo:
                datos = json.load(archivo)
        except FileNotFoundError:
            log.info("No existe %s todavía (instalación nueva).", self.ruta.name)
            return []
        except json.JSONDecodeError as error:
            # Archivo dañado: lo respaldamos para no perderlo y seguimos.
            respaldo = self.ruta.with_name(self.ruta.stem + ".corrupto.json")
            os.replace(self.ruta, respaldo)
            log.warning("%s estaba dañado (%s). Respaldo en %s", self.ruta.name, error, respaldo.name)
            return []

        if not isinstance(datos, list):
            log.warning("%s no contiene una lista; se ignora.", self.ruta.name)
            return []
        return datos

    def guardar(self, registros: list[dict]) -> None:
        """
        Serializa la lista completa en disco.

        Escribe primero en un archivo temporal y luego lo reemplaza: si la app
        se cierra a mitad de la escritura, el JSON anterior queda intacto.
        """
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        temporal = self.ruta.with_name(self.ruta.name + ".tmp")
        with open(temporal, "w", encoding="utf-8") as archivo:
            json.dump(registros, archivo, ensure_ascii=False, indent=2)
        os.replace(temporal, self.ruta)
