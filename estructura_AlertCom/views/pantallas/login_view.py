# =============================================================================
# AlertCom - Vista: Pantalla de Inicio de Sesión (LoginScreen)
# =============================================================================
# Captura correo y contraseña, delega la validación al AuthController
# (que lee usuarios.json) y muestra los errores con MDDialog.
# =============================================================================

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen

from views.componentes.dialogos import mostrar_dialogo


class LoginScreen(MDScreen):
    """Pantalla de inicio de sesión (correo + contraseña)."""

    def __init__(self, auth_controller=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.auth_controller = auth_controller

    def on_pre_enter(self, *args) -> None:
        # Seguridad: nunca dejar la contraseña escrita al volver a esta pantalla.
        self.ids.password_field.text = ""

    def validate_login(self) -> None:
        correo = self.ids.email_field.text
        contrasena = self.ids.password_field.text

        exito, mensaje = self.auth_controller.iniciar_sesion(correo, contrasena)
        if not exito:
            self.ids.password_field.text = ""
            mostrar_dialogo("No pudimos iniciar sesión", mensaje, icono="account-alert-outline")
            return

        self.ids.email_field.text = ""
        self.ids.password_field.text = ""
        MDApp.get_running_app().navegacion.ir_a("home", "left")

    def ir_a_registro(self) -> None:
        MDApp.get_running_app().navegacion.ir_a("register", "left")
