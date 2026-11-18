# =============================================================================
# AlertCom - Navegación entre pantallas
# =============================================================================
# Único lugar que cambia la pantalla visible. Protege las pantallas privadas:
# si no hay sesión, redirige al login; si la pantalla es solo municipal y el
# usuario es vecino, redirige al inicio.
#
# Desde el KV:      app.navegacion.ir_a("profile")
# Desde Python:     MDApp.get_running_app().navegacion.ir_a("history")
# =============================================================================

import logging

from kivy.uix.screenmanager import SlideTransition

log = logging.getLogger("alertcom.navegacion")


class Navegador:
    """Cambia de pantalla con transición y control de acceso."""

    PANTALLAS_PUBLICAS = {"safety", "login", "register"}
    PANTALLAS_MUNICIPALES = {"metricas", "confirmar"}  # solo funcionario municipal
    PESTANAS = {
        "Inicio": ("home", "right"),
        "Mis Reportes": ("history", "left"),
        "Perfil": ("profile", "left"),
    }

    def __init__(self, gestor, auth_controller) -> None:
        self.gestor = gestor
        self.auth = auth_controller

    def ir_a(self, pantalla: str, direccion: str = "left") -> None:
        usuario = self.auth.usuario_actual
        if pantalla not in self.PANTALLAS_PUBLICAS and usuario is None:
            log.info("Acceso a '%s' sin sesión: redirigido a login.", pantalla)
            pantalla, direccion = "login", "right"
        elif pantalla in self.PANTALLAS_MUNICIPALES and not usuario.es_municipal:
            log.info("Acceso a '%s' sin permiso: redirigido al inicio.", pantalla)
            pantalla, direccion = "home", "right"
        self.gestor.transition = SlideTransition(direction=direccion)
        self.gestor.current = pantalla

    def volver(self) -> None:
        """Flecha "atrás" y botón "Volver al Inicio"."""
        self.ir_a("home", "right")

    def cerrar_sesion(self) -> None:
        self.auth.cerrar_sesion()
        self.ir_a("login", "right")

    def al_cambiar_pestana(self, *args) -> None:
        """MDNavigationBar.on_switch_tabs envía (barra, item, icono, texto)."""
        texto = args[3] if len(args) > 3 else ""
        if texto in self.PESTANAS and self.gestor.current != self.PESTANAS[texto][0]:
            self.ir_a(*self.PESTANAS[texto])
