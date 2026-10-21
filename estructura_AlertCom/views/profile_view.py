# =============================================================================
# AlertCom - Vista: Perfil de Usuario (ProfileScreen)
# =============================================================================
# Muestra el avatar, nombre y correo del usuario autenticado obtenidos del
# auth_controller inyectado. El botón "Cerrar Sesión" limpia la sesión y
# devuelve al usuario a la pantalla de Login.
# La interfaz visual vive en alertcom.kv (regla <ProfileScreen>).
# =============================================================================

from kivymd.uix.screen import MDScreen
from kivymd.app import MDApp


class ProfileScreen(MDScreen):
    """Pantalla de perfil del usuario autenticado."""

    def __init__(self, auth_controller=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.auth_controller = auth_controller

    def on_pre_enter(self) -> None:
        """Actualiza los datos del usuario antes de mostrar la pantalla."""
        self.actualizar_perfil()

    def actualizar_perfil(self) -> None:
        """Lee nombre y correo del auth_controller y los refleja en el KV."""
        nombre = (
            getattr(self.auth_controller, "usuario_nombre", None)
            or "Usuario"
        )
        correo = (
            getattr(self.auth_controller, "usuario_email", None)
            or "correo@ejemplo.cl"
        )

        if "profile_name" in self.ids:
            self.ids.profile_name.text = nombre
        if "profile_email" in self.ids:
            self.ids.profile_email.text = correo
        if "profile_avatar" in self.ids:
            self.ids.profile_avatar.icon = "account-circle"

    def cerrar_sesion(self, *args) -> None:
        """Limpia los datos de sesión y regresa a la pantalla de Login."""
        if self.auth_controller is not None:
            self.auth_controller.cerrar_sesion()

        app = MDApp.get_running_app()
        if app is not None:
            app.go_to_screen("login", direction="right")
