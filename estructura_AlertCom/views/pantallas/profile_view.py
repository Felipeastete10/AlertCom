# =============================================================================
# AlertCom - Vista: Perfil de Usuario (ProfileScreen)
# =============================================================================
# Muestra los datos REALES del usuario con sesión abierta y sus estadísticas
# cívicas calculadas por el IncidenteController.
# =============================================================================

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen


class ProfileScreen(MDScreen):
    """Pantalla de perfil del usuario autenticado."""

    def __init__(self, auth_controller=None, incidente_controller=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.auth_controller = auth_controller
        self.incidente_controller = incidente_controller

    def on_pre_enter(self, *args) -> None:
        self.actualizar_perfil()

    def actualizar_perfil(self) -> None:
        usuario = self.auth_controller.usuario_actual
        if usuario is None:
            return

        self.ids.profile_name.text = usuario.nombre
        self.ids.profile_email.text = usuario.email
        self.ids.profile_comuna.text = f"{usuario.comuna}, Región de La Araucanía"
        self.ids.profile_rol.text = f"Rol: {usuario.rol_legible}"

        resumen = self.incidente_controller.resumen(usuario.id_usuario)
        self.ids.stat_enviados.text = str(resumen["total"])
        self.ids.stat_reparados.text = str(resumen["reparados"])

    def cerrar_sesion(self) -> None:
        MDApp.get_running_app().navegacion.cerrar_sesion()
