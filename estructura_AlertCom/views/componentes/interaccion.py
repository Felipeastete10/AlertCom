# =============================================================================
# AlertCom - Piezas interactivas compartidas
# =============================================================================
#   • Pastilla          → opción que se toca (tipo, gravedad, filtros).
#   • BarraProgreso     → barra que se llena suave (avance del formulario).
#   • mostrar_exito()   → animación de "listo" con check verde.
#   • sacudir()         → sacude un widget (ej. contraseña incorrecta).
#   • contar_hasta()    → los números suben de 0 a su valor.
#   • aparecer_en_cascada() → la lista aparece elemento por elemento.
#   • vibrar()          → vibración corta en el teléfono (en PC no hace nada).
# Los colores y la forma se definen en views/kv/_comunes.kv.
# =============================================================================

import logging

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse
from kivy.metrics import dp, sp
from kivy.properties import BooleanProperty, ColorProperty, NumericProperty, StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.modalview import ModalView
from kivy.uix.widget import Widget
from kivy.utils import platform
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.label import MDIcon, MDLabel

log = logging.getLogger("alertcom.interaccion")

NARANJA = (1, 0.6, 0, 1)
VERDE = (0.2, 0.66, 0.33, 1)


class Pastilla(ButtonBehavior, MDBoxLayout):
    """Opción redondeada: se ilumina con su color al quedar seleccionada."""

    texto = StringProperty("")
    icono = StringProperty("")
    seleccionada = BooleanProperty(False)
    color = ColorProperty(NARANJA)
    valor = StringProperty("")
    brillo = NumericProperty(0)   # destello breve al tocar
    compacta = BooleanProperty(False)  # versión chica (filtros del mapa)

    def on_kv_post(self, base_widget):
        super().on_kv_post(base_widget)
        self.bind(compacta=self._tope_compacta)
        self._tope_compacta()

    def _tope_compacta(self, *_args):
        """La versión compacta (filtros del mapa) va en una sola fila: su
        texto crece con Ajustes, pero con un tope para que quepan las tres."""
        if not self.compacta:
            return
        app = MDApp.get_running_app()
        etiqueta = self.ids.etiqueta
        etiqueta.theme_font_size = "Custom"

        def ajustar(*_):
            etiqueta.font_size = min(sp(11) * app.factor_letra, dp(12))
        app.bind(factor_letra=ajustar)
        ajustar()

    def on_press(self):
        self.brillo = 1
        Animation(brillo=0, d=0.35, t="out_quad").start(self)


class BarraProgreso(Widget):
    """Barra delgada; animar_a(0.75) la llena hasta el 75 %."""

    valor = NumericProperty(0)
    color = ColorProperty(NARANJA)

    def animar_a(self, destino: float) -> None:
        Animation.cancel_all(self, "valor")
        Animation(valor=destino, d=0.35, t="out_cubic").start(self)


# -----------------------------------------------------------------------------
# Animación de éxito
# -----------------------------------------------------------------------------
class _CirculoExito(Widget):
    escala = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self._dibujar, size=self._dibujar, escala=self._dibujar)

    def _dibujar(self, *_):
        self.canvas.before.clear()
        lado = min(self.size) * self.escala
        with self.canvas.before:
            Color(*VERDE[:3], 0.25)
            Ellipse(pos=(self.center_x - lado * 0.65, self.center_y - lado * 0.65), size=(lado * 1.3, lado * 1.3))
            Color(*VERDE)
            Ellipse(pos=(self.center_x - lado / 2, self.center_y - lado / 2), size=(lado, lado))


def mostrar_exito(titulo: str, detalle: str = "", al_terminar=None, duracion: float = 1.6) -> ModalView:
    """Check verde que aparece con rebote; se cierra solo y llama a al_terminar."""
    vista = ModalView(size_hint=(1, 1), background="", background_color=(0, 0, 0, 0.72),
                      auto_dismiss=True, overlay_color=(0, 0, 0, 0))
    capa = MDFloatLayout()
    circulo = _CirculoExito(size_hint=(None, None), size=(dp(110), dp(110)),
                            pos_hint={"center_x": 0.5, "center_y": 0.58})
    check = MDIcon(icon="check-bold", theme_font_size="Custom", font_size="56sp",
                   theme_text_color="Custom", text_color=(1, 1, 1, 1), opacity=0,
                   size_hint=(None, None), pos_hint={"center_x": 0.5, "center_y": 0.58})
    check.bind(texture_size=lambda w, s: setattr(w, "size", s))
    textos = MDBoxLayout(orientation="vertical", adaptive_height=True, spacing=dp(6), opacity=0,
                         size_hint_x=0.85, pos_hint={"center_x": 0.5, "top": 0.47})
    textos.add_widget(MDLabel(text=titulo, halign="center", font_style="Headline", role="small",
                              bold=True, adaptive_height=True, theme_text_color="Custom",
                              text_color=(1, 1, 1, 1)))
    if detalle:
        textos.add_widget(MDLabel(text=detalle, halign="center", font_style="Body", role="large",
                                  adaptive_height=True, theme_text_color="Custom",
                                  text_color=(1, 1, 1, 0.75)))
    for widget in (circulo, check, textos):
        capa.add_widget(widget)
    vista.add_widget(capa)
    if al_terminar:
        vista.bind(on_dismiss=lambda *_: al_terminar())
    vista.open()

    Animation(escala=1, d=0.45, t="out_back").start(circulo)
    Clock.schedule_once(lambda _dt: Animation(opacity=1, d=0.25).start(check), 0.25)
    Clock.schedule_once(lambda _dt: Animation(opacity=1, d=0.3).start(textos), 0.35)
    Clock.schedule_once(lambda _dt: vista.dismiss(), duracion)
    vibrar(60)
    return vista


# -----------------------------------------------------------------------------
# Pequeñas animaciones
# -----------------------------------------------------------------------------
def sacudir(widget, distancia: float = dp(12)) -> None:
    """Movimiento de "no": izquierda-derecha que se apaga."""
    origen = widget.x
    anim = Animation(x=origen, d=0)
    for paso in (1, -1, 0.6, -0.6, 0.25, 0):
        anim += Animation(x=origen + distancia * paso, d=0.05)
    anim.start(widget)


def contar_hasta(etiqueta, valor: int, duracion: float = 0.6) -> None:
    """La etiqueta muestra 0, 1, 2… hasta llegar a `valor`."""
    if getattr(etiqueta, "_conteo", None) is not None:
        etiqueta._conteo.cancel()
    if valor <= 0:
        etiqueta.text = "0"
        return
    pasos = min(valor, 20)
    estado = {"paso": 0}

    def avanzar(_dt):
        estado["paso"] += 1
        etiqueta.text = str(round(valor * estado["paso"] / pasos))
        if estado["paso"] >= pasos:
            etiqueta._conteo.cancel()
            etiqueta._conteo = None

    etiqueta.text = "0"
    etiqueta._conteo = Clock.schedule_interval(avanzar, duracion / pasos)


def aparecer_en_cascada(widgets, retraso: float = 0.05) -> None:
    """Cada elemento aparece un poco después del anterior."""
    for indice, widget in enumerate(widgets):
        widget.opacity = 0
        Clock.schedule_once(lambda _dt, w=widget: Animation(opacity=1, d=0.25).start(w),
                            min(indice, 12) * retraso)


def vibrar(milisegundos: int = 40) -> None:
    """Vibración corta (Android). Si no hay vibrador, no pasa nada."""
    if platform != "android":
        return
    try:
        from plyer import vibrator
        vibrator.vibrate(milisegundos / 1000)
    except Exception as error:
        log.info("No se pudo vibrar: %s", error)
