# =============================================================================
# AlertCom - Vista: Pantalla de Aviso de Seguridad (SafetyScreen)
# =============================================================================
# Primera pantalla obligatoria por seguridad vial. El texto del aviso viene de
# app.mensaje_seguridad (puede actualizarse por configuración remota).
# =============================================================================

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen


class SafetyScreen(MDScreen):
    """Pantalla inicial de advertencia para proteger a conductores."""

    def ir_a_login(self) -> None:
        MDApp.get_running_app().navegacion.ir_a("login", "left")
