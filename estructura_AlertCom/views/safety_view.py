# =============================================================================
# AlertCom - Vista: Pantalla de Aviso de Seguridad (SafetyScreen)
# =============================================================================
# Primera pantalla obligatoria por regla de seguridad vial.
# Solo captura el evento "Entendido" y delega la navegación al Controlador/App.
# =============================================================================

from kivymd.uix.screen import MDScreen
from kivymd.app import MDApp


class SafetyScreen(MDScreen):
    """Pantalla inicial de advertencia para proteger a conductores."""

    def ir_a_login(self) -> None:
        """Notifica al usuario que aceptó el aviso y navega al Login."""
        app = MDApp.get_running_app()
        if app is not None:
            app.go_to_screen("login", direction="left")
