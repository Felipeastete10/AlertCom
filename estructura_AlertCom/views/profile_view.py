# =============================================================================
# AlertCom - Pantalla 6: Perfil del Usuario (ProfileScreen)
# =============================================================================
# Rama:         feature/vistas-soporte
# Responsable:  Felipe Salazar (Vistas - Flujo de Soporte)
#
# Propósito:
#   Muestra avatar, datos del vecino, su aporte cívico (reportes enviados y
#   baches reparados) y el botón para cerrar sesión.
#
# Origen de los datos (MVC):
#   - Usuario:   `app.usuario_actual` (objeto Usuario de Allan), si existe.
#   - Reportes:  `app.incidente_controller` (IncidenteController de Roberto).
#   Si alguno no existe todavía, se usan los datos de ejemplo del mockup.
# =============================================================================

import os

from kivy.lang import Builder
from kivy.properties import StringProperty
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen

from views.history_view import marcar_tab_activo

Builder.load_file(os.path.join(os.path.dirname(__file__), "profile.kv"))

# Datos de ejemplo del guion de la presentación
USUARIO_DEMO = {"nombre": "Juan Pérez González", "email": "juan.perez@email.com"}
ESTADISTICAS_DEMO = {"enviados": 3, "reparados": 1}


def _iniciales(nombre: str) -> str:
    """'Juan Pérez González' -> 'JP'."""
    partes = [p for p in nombre.split() if p]
    return "".join(p[0] for p in partes[:2]).upper() or "?"


class ProfileScreen(MDScreen):
    """Pantalla 6 – Perfil del usuario, estadísticas cívicas y logout."""

    nombre = StringProperty(USUARIO_DEMO["nombre"])
    email = StringProperty(USUARIO_DEMO["email"])
    iniciales = StringProperty(_iniciales(USUARIO_DEMO["nombre"]))
    reportes_enviados = StringProperty(str(ESTADISTICAS_DEMO["enviados"]))
    baches_reparados = StringProperty(str(ESTADISTICAS_DEMO["reparados"]))

    def __init__(self, auth_controller=None, incidente_controller=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.auth_controller = auth_controller
        self.incidente_controller = incidente_controller

    # ------------------------------------------------------------------ #
    #  CICLO DE VIDA
    # ------------------------------------------------------------------ #
    def on_pre_enter(self, *args) -> None:
        """Actualiza los datos cada vez que se abre el perfil."""
        self.cargar_usuario()
        self.cargar_estadisticas()
        marcar_tab_activo(self.ids.nav_bar, self.ids.nav_perfil)

    # ------------------------------------------------------------------ #
    #  DATOS
    # ------------------------------------------------------------------ #
    def cargar_usuario(self) -> None:
        app = MDApp.get_running_app()
        usuario = getattr(app, "usuario_actual", None)

        # Prioridad: sesión del AuthController > usuario_actual > datos demo
        auth = self.auth_controller
        nombre = (
            getattr(auth, "usuario_nombre", None)
            or getattr(usuario, "nombre", None)
            or USUARIO_DEMO["nombre"]
        )
        email = (
            getattr(auth, "usuario_email", None)
            or getattr(usuario, "email", None)
            or USUARIO_DEMO["email"]
        )

        self.nombre = nombre
        self.email = email
        self.iniciales = _iniciales(nombre)

    def cargar_estadisticas(self) -> None:
        app = MDApp.get_running_app()
        controller = self.incidente_controller or getattr(app, "incidente_controller", None)

        if controller is None or not hasattr(controller, "obtener_historial"):
            self.reportes_enviados = str(ESTADISTICAS_DEMO["enviados"])
            self.baches_reparados = str(ESTADISTICAS_DEMO["reparados"])
            return

        historial = controller.obtener_historial()

        # Si hay usuario con id, contar solo sus reportes
        usuario = getattr(app, "usuario_actual", None)
        id_usuario = getattr(usuario, "id_usuario", None)
        if id_usuario is not None:
            historial = [i for i in historial if getattr(i, "usuario_id", None) == id_usuario]

        reparados = sum(
            1 for i in historial
            if str(getattr(i, "estado", "")).lower() == "reparado"
        )
        self.reportes_enviados = str(len(historial))
        self.baches_reparados = str(reparados)

    # ------------------------------------------------------------------ #
    #  ACCIONES
    # ------------------------------------------------------------------ #
    def cerrar_sesion(self) -> None:
        """Cierra la sesión del usuario (si existe) y vuelve al Login."""
        app = MDApp.get_running_app()
        usuario = getattr(app, "usuario_actual", None)
        if usuario is not None and hasattr(usuario, "cerrar_sesion"):
            usuario.cerrar_sesion()
        app.logout()
