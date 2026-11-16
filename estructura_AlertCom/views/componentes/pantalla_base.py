# =============================================================================
# AlertCom - Pantalla base con analítica
# =============================================================================
# Todas las pantallas heredan de PantallaBase en vez de MDScreen.
# Así, cada vez que el usuario ENTRA a una pantalla, Kivy llama a on_enter()
# y se registra el evento "pantalla_vista" con el nombre de la pantalla.
# Se escribe una sola vez aquí, no en cada pantalla (POO: herencia).
# =============================================================================

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen


class PantallaBase(MDScreen):
    """MDScreen que registra automáticamente las visitas."""

    def on_enter(self, *args) -> None:
        self.registrar_evento("pantalla_vista", {"pantalla": self.name})

    def registrar_evento(self, nombre: str, datos: dict | None = None) -> None:
        """Atajo para que las pantallas registren eventos de interfaz.
        Si la app aún no tiene controlador (ej. en una prueba), no hace nada."""
        app = MDApp.get_running_app()
        controlador = getattr(app, "controlador", None)
        if controlador is not None:
            controlador.eventos.registrar(nombre, datos)
