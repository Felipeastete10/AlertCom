# =============================================================================
# AlertCom - Vista: Pantalla de Aviso de Seguridad (SafetyScreen)
# =============================================================================
# Primera pantalla obligatoria por seguridad vial. El texto del aviso viene de
# app.mensaje_seguridad (puede actualizarse por configuración remota).
#
# Para continuar hay que DESLIZAR "estoy detenido" (un toque no basta): el
# camino animado frena y luego se pasa al login. Las animaciones se apagan
# al salir de la pantalla para no gastar batería.
# =============================================================================

from kivy.clock import Clock
from kivymd.app import MDApp

from views.componentes.pantalla_base import PantallaBase
from views.componentes.seguridad import (  # noqa: F401  (registra las clases para el .kv)
    CarreteraAnimada,
    DeslizadorConfirmar,
    HaloPulsante,
)


class SafetyScreen(PantallaBase):
    """Pantalla inicial de advertencia para proteger a conductores."""

    def on_pre_enter(self, *args) -> None:
        self.ids.deslizador.reiniciar()
        self.ids.carretera.arrancar()
        self.ids.halo.encender()

    def on_leave(self, *args) -> None:
        self.ids.carretera.detener()
        self.ids.halo.apagar()

    def confirmar(self) -> None:
        """La persona deslizó hasta el final: el camino frena y se continúa."""
        self.ids.carretera.frenar()
        self.ids.halo.apagar()
        Clock.schedule_once(lambda _dt: self.ir_a_login(), 0.9)

    def ir_a_login(self) -> None:
        MDApp.get_running_app().navegacion.ir_a("login", "left")
