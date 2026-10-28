# =============================================================================
# AlertCom - Vista: Crear Cuenta (RegisterScreen)
# =============================================================================
# Formulario de registro de vecinos. El AuthController valida los datos y
# guarda la cuenta nueva en usuarios.json.
# =============================================================================

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen

from views.componentes.dialogos import mostrar_aviso, mostrar_dialogo


class RegisterScreen(MDScreen):
    """Registro de un vecino nuevo."""

    CAMPOS = ("reg_nombre", "reg_email", "reg_contrasena", "reg_confirmacion")

    def __init__(self, auth_controller=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.auth_controller = auth_controller

    def on_pre_enter(self, *args) -> None:
        for campo in self.CAMPOS:
            self.ids[campo].text = ""

    def registrar(self) -> None:
        exito, mensaje = self.auth_controller.registrar(
            nombre=self.ids.reg_nombre.text,
            correo=self.ids.reg_email.text,
            contrasena=self.ids.reg_contrasena.text,
            confirmacion=self.ids.reg_confirmacion.text,
        )
        if not exito:
            mostrar_dialogo("Revisa tus datos", mensaje, icono="account-alert-outline")
            return

        mostrar_aviso("¡Cuenta creada! Bienvenido a AlertCom.")
        MDApp.get_running_app().navegacion.ir_a("home", "left")

    def volver(self) -> None:
        MDApp.get_running_app().navegacion.ir_a("login", "right")
