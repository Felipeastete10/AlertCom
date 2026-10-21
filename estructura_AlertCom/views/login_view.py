# =============================================================================
# AlertCom - Vista: Pantalla de Inicio de Sesión (LoginScreen)
# =============================================================================
# Captura credenciales y delega la validación al AuthController inyectado.
# No contiene lógica de autenticación ni generación de tokens.
# Compatible con KivyMD 2.0.1.dev0 (usa MDSnackbar, sin Snackbar obsoleto).
# =============================================================================

from kivymd.uix.screen import MDScreen
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText


class LoginScreen(MDScreen):
    """Pantalla de inicio de sesión (correo + contraseña)."""

    def __init__(
        self,
        auth_controller=None,
        usuario=None,
        on_login_success=None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.auth_controller = auth_controller
        self.usuario = usuario
        self._on_login_success_callback = on_login_success

    def validate_login(self) -> None:
        """Captura el texto de los campos y delega la autenticación al controlador."""
        correo = self.ids.email_field.text if hasattr(self, "ids") else ""
        contrasena = self.ids.password_field.text if hasattr(self, "ids") else ""

        if not correo or not contrasena:
            print("Error: Ingrese correo y contraseña")
            self._mostrar_error("Ingrese correo y contraseña")
            return

        if self.auth_controller is not None:
            exito, mensaje = self.auth_controller.iniciar_sesion(correo, contrasena)
            if exito:
                # El controlador ya navegó a la pantalla 'safety'.
                self._on_login_success()
            else:
                self._mostrar_error(mensaje or "Credenciales inválidas.")
        else:
            print("Error: auth_controller no inyectado")
            self._mostrar_error("Error interno: controlador de autenticación no disponible.")

    def _on_login_success(self) -> None:
        """Callback de éxito. El controlador ya cambió la pantalla a 'safety'."""
        print("Inicio de sesión correcto. Pantalla activa: aviso de seguridad (safety).")
        if callable(self._on_login_success_callback):
            self._on_login_success_callback()

    def _mostrar_error(self, mensaje: str) -> None:
        """Muestra el mensaje de error usando MDSnackbar de KivyMD 2.0."""
        print(f"Error de login: {mensaje}")
        try:
            MDSnackbar(
                MDSnackbarText(text=mensaje),
            ).open()
        except Exception as exc:
            print(f"No se pudo mostrar el MDSnackbar: {exc}")
