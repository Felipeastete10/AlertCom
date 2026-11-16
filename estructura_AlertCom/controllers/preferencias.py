# =============================================================================
# AlertCom - Preferencias del usuario (preferencias.json)
# =============================================================================
# Un solo archivo para todo lo que la persona elige en la app:
#   {"analitica_activa": true, "tamano_letra": "grande", "fondo": "azul"}
# Al guardar una clave se MEZCLA con lo que ya había (no se borra el resto).
# Python puro: se puede probar sin Kivy.
# =============================================================================

import json
import logging
from pathlib import Path

log = logging.getLogger("alertcom.preferencias")

ARCHIVO_PREFERENCIAS = "preferencias.json"


class Preferencias:
    def __init__(self, ruta: Path | str) -> None:
        self.ruta = Path(ruta)

    def leer(self) -> dict:
        try:
            with open(self.ruta, "r", encoding="utf-8") as archivo:
                datos = json.load(archivo)
            return datos if isinstance(datos, dict) else {}
        except FileNotFoundError:
            return {}
        except (ValueError, OSError) as error:
            log.warning("preferencias.json dañado, se usan valores por defecto: %s", error)
            return {}

    def obtener(self, clave: str, por_defecto=None):
        return self.leer().get(clave, por_defecto)

    def guardar(self, clave: str, valor) -> None:
        datos = self.leer()
        datos[clave] = valor
        try:
            self.ruta.parent.mkdir(parents=True, exist_ok=True)
            with open(self.ruta, "w", encoding="utf-8") as archivo:
                json.dump(datos, archivo, ensure_ascii=False, indent=2)
        except OSError as error:
            log.warning("No se pudo guardar la preferencia %s: %s", clave, error)
