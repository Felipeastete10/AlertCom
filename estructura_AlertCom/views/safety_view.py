# =============================================================================
# AlertCom - Pantalla 1: Aviso de Seguridad (SafetyScreen)
# =============================================================================
# Rama:         feature/vistas-soporte
# Responsable:  Felipe Salazar (Vistas - Flujo de Soporte)
#
# Propósito:
#   Bloqueo preventivo obligatorio antes de usar la app. Responde al 70% de
#   encuestados que se movilizan a diario en auto o transporte colectivo.
#   El usuario debe presionar "Entendido" para avanzar al Login.
# =============================================================================

import os

from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen

# El .kv se carga con ruta absoluta para que funcione sin importar
# desde qué carpeta se ejecute main.py.
Builder.load_file(os.path.join(os.path.dirname(__file__), "safety.kv"))


class SafetyScreen(MDScreen):
    """Pantalla 1 – Aviso de seguridad vial (bloqueo preventivo)."""

    def aceptar_aviso(self) -> None:
        """El usuario confirma que no está conduciendo y pasa al Login."""
        app = MDApp.get_running_app()
        app.go_to_screen("login", direction="left")
