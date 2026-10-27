# =============================================================================
# AlertCom - Pantalla 2: Inicio de Sesión (LoginScreen)
# =============================================================================
# Rama:         feature/vistas-soporte
# Responsable:  Felipe Salazar (Vistas - Flujo de Soporte)
#
# Propósito:
#   Login simplificado (solo correo + contraseña) para reducir la deserción
#   inicial. Hace validaciones VISUALES del formato; la verificación real de
#   credenciales le corresponde al controlador cuando exista.
# =============================================================================

import os
import re

from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen

Builder.load_file(os.path.join(os.path.dirname(__file__), "login.kv"))

# Formato básico de correo: algo@algo.algo
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class LoginScreen(MDScreen):
    """Pantalla 2 – Inicio de sesión (correo + contraseña)."""

    def __init__(
        self,
        auth_controller=None,
        usuario=None,
        on_login_success=None,
        **kwargs,
    ) -> None:
        # main.py inyecta el AuthController, el usuario demo y el callback
        super().__init__(**kwargs)
        self.auth_controller = auth_controller
        self.usuario = usuario
        self._on_login_success_callback = on_login_success

    # ------------------------------------------------------------------ #
    #  VALIDACIÓN VISUAL
    # ------------------------------------------------------------------ #
    def _validar_campos(self) -> bool:
        """Marca en rojo los campos inválidos. Devuelve True si todo está ok."""
        email_field = self.ids.email_field
        password_field = self.ids.password_field

        email = email_field.text.strip()
        password = password_field.text

        email_ok = bool(_EMAIL_RE.match(email))
        password_ok = len(password) >= 4

        email_field.error = not email_ok
        password_field.error = not password_ok
        self.ids.error_label.text = ""

        return email_ok and password_ok

    def limpiar_error(self, field) -> None:
        """Quita el color de error apenas el usuario vuelve a escribir."""
        field.error = False
        self.ids.error_label.text = ""

    # ------------------------------------------------------------------ #
    #  ACCIONES
    # ------------------------------------------------------------------ #
    def validate_login(self) -> None:
        """Valida el formulario y, si es correcto, avanza al Home."""
        if not self._validar_campos():
            return

        app = MDApp.get_running_app()
        email = self.ids.email_field.text.strip()
        password = self.ids.password_field.text

        # AuthController.iniciar_sesion devuelve (exito, mensaje). Si no hay
        # controlador inyectado, el login es simulado.
        if self.auth_controller is not None:
            exito, mensaje = self.auth_controller.iniciar_sesion(email, password)
            if not exito:
                self.ids.error_label.text = mensaje or "Correo o contraseña incorrectos"
                return

        self._limpiar_formulario()
        # El controlador deja la app en "safety" al validar; aquí se fuerza el Home
        if callable(self._on_login_success_callback):
            self._on_login_success_callback()
        else:
            app.go_to_screen("home", direction="left")

    def crear_cuenta(self) -> None:
        """Crea la cuenta con el correo y la contraseña escritos y entra a la app."""
        if not self._validar_campos():
            return

        email = self.ids.email_field.text.strip()
        password = self.ids.password_field.text

        registrar = getattr(self.auth_controller, "registrar", None)
        if callable(registrar):
            exito, mensaje = registrar(email, password)
            if not exito:
                self.ids.error_label.text = mensaje or "No se pudo crear la cuenta"
                return

        # Cuenta creada: inicia sesión con esas mismas credenciales
        self.validate_login()

    def _limpiar_formulario(self) -> None:
        """Deja el formulario vacío para cuando el usuario cierre sesión."""
        self.ids.password_field.text = ""
        self.ids.email_field.error = False
        self.ids.password_field.error = False
        self.ids.error_label.text = ""
