# =============================================================================
# AlertCom - Piezas animadas de la pantalla de seguridad
# =============================================================================
#   • CarreteraAnimada  → camino nocturno en perspectiva; las líneas del
#                         centro avanzan como si el auto se moviera.
#                         frenar() las detiene suavemente: "el auto se detuvo".
#   • HaloPulsante      → anillo de luz que late detrás de la señal.
#   • DeslizadorConfirmar → "Desliza si estás detenido": hay que arrastrar
#                         la perilla hasta el final (un toque accidental no
#                         basta). Al completar dispara el evento on_confirmar.
# Todo se dibuja con el canvas de Kivy: no usa imágenes externas.
# =============================================================================

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Line, Mesh, Rectangle
from kivy.metrics import dp
from kivy.properties import BooleanProperty, ColorProperty, NumericProperty, StringProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget

AMBAR = (0.96, 0.71, 0.0, 1)
VERDE = (0.18, 0.64, 0.36, 1)


class CarreteraAnimada(Widget):
    """Camino en perspectiva con líneas centrales en movimiento."""

    velocidad = NumericProperty(0.9)      # unidades de camino por segundo
    desplazamiento = NumericProperty(0)

    ESPACIO = 1.0      # distancia entre el inicio de dos líneas
    LARGO = 0.5        # largo de cada línea
    PROFUNDIDAD = 9.0  # cuánto camino se ve hasta el horizonte

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._reloj = None
        self.bind(pos=self._dibujar, size=self._dibujar, desplazamiento=self._dibujar)

    # --- Animación -----------------------------------------------------------
    def arrancar(self) -> None:
        Animation.cancel_all(self, "velocidad")
        self.velocidad = 0.9
        if self._reloj is None:
            self._reloj = Clock.schedule_interval(self._avanzar, 1 / 45)

    def frenar(self, duracion: float = 0.7) -> None:
        Animation(velocidad=0, d=duracion, t="out_cubic").start(self)

    def detener(self) -> None:
        if self._reloj is not None:
            self._reloj.cancel()
            self._reloj = None

    def _avanzar(self, dt) -> None:
        if self.velocidad > 0:
            self.desplazamiento = (self.desplazamiento + self.velocidad * dt) % self.ESPACIO

    # --- Dibujo --------------------------------------------------------------
    def _a_pantalla(self, z: float) -> float:
        """Distancia en el camino (z) → altura en pantalla (0 abajo, 1 horizonte)."""
        return z / (z + 2.2)

    def _ancho(self, s: float) -> float:
        return self.width * (1.25 * (1 - s) + 0.04 * s)

    def _dibujar(self, *_args) -> None:
        if self.width <= 1:
            return
        x0, y0, w, h = self.x, self.y, self.width, self.height
        cx = x0 + w / 2
        tope = self._a_pantalla(self.PROFUNDIDAD)
        self.canvas.clear()
        with self.canvas:
            # Asfalto (trapecio hasta el horizonte)
            Color(0.15, 0.15, 0.18, 1)
            ab, ar = self._ancho(0) / 2, self._ancho(tope) / 2
            yt = y0 + h * tope
            Mesh(vertices=[cx - ab, y0, 0, 0, cx + ab, y0, 0, 0, cx + ar, yt, 0, 0, cx - ar, yt, 0, 0],
                 indices=[0, 1, 2, 3], mode="triangle_fan")
            # Bordes del camino
            Color(1, 1, 1, 0.35)
            Line(points=[cx - ab * 0.92, y0, cx - ar * 0.92, yt], width=dp(1.2))
            Line(points=[cx + ab * 0.92, y0, cx + ar * 0.92, yt], width=dp(1.2))
            # Líneas centrales en movimiento (más tenues al alejarse)
            z = -self.desplazamiento
            while z < self.PROFUNDIDAD:
                z1, z2 = max(z, 0), min(z + self.LARGO, self.PROFUNDIDAD)
                if z2 > z1:
                    s1, s2 = self._a_pantalla(z1), self._a_pantalla(z2)
                    m1, m2 = self._ancho(s1) * 0.018, self._ancho(s2) * 0.018
                    ya, yb = y0 + h * s1, y0 + h * s2
                    Color(*AMBAR[:3], 0.95 - 0.8 * s1)
                    Mesh(vertices=[cx - m1, ya, 0, 0, cx + m1, ya, 0, 0, cx + m2, yb, 0, 0, cx - m2, yb, 0, 0],
                         indices=[0, 1, 2, 3], mode="triangle_fan")
                z += self.ESPACIO
            # Niebla del horizonte: funde el camino con el fondo
            for i in range(12):
                Color(0.06, 0.06, 0.08, 0.08)
                Rectangle(pos=(x0, yt - dp(4) * i), size=(w, dp(4) * i + dp(2)))


class HaloPulsante(Widget):
    """Anillo que crece y se desvanece, como una baliza."""

    color = ColorProperty(AMBAR)
    fase = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._animacion = None
        self.bind(pos=self._dibujar, size=self._dibujar, fase=self._dibujar, color=self._dibujar)

    def encender(self) -> None:
        self.apagar()
        self.fase = 0
        self._animacion = Animation(fase=1, d=1.8, t="out_quad") + Animation(fase=0, d=0)
        self._animacion.repeat = True
        self._animacion.start(self)

    def apagar(self) -> None:
        if self._animacion is not None:
            self._animacion.cancel(self)
            self._animacion = None

    def _dibujar(self, *_args) -> None:
        self.canvas.clear()
        lado = min(self.width, self.height)
        with self.canvas:
            for retraso in (0.0, 0.5):  # dos ondas desfasadas
                f = (self.fase + retraso) % 1
                r = lado * (0.42 + 0.58 * f) / 2
                Color(*self.color[:3], 0.45 * (1 - f))
                Line(circle=(self.center_x, self.center_y, r), width=dp(2))
            Color(*self.color[:3], 0.10)
            Ellipse(pos=(self.center_x - lado * 0.36, self.center_y - lado * 0.36), size=(lado * 0.72, lado * 0.72))


class DeslizadorConfirmar(FloatLayout):
    """Pista con una perilla que se arrastra hasta el final para confirmar."""

    texto = StringProperty("Desliza si estás detenido")
    progreso = NumericProperty(0)            # 0 → 1
    completado = BooleanProperty(False)
    color_perilla = ColorProperty(AMBAR)
    UMBRAL = 0.8

    __events__ = ("on_confirmar",)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._arrastrando = False

    @property
    def recorrido(self) -> float:
        return max(self.width - self.height, 1)

    def reiniciar(self) -> None:
        Animation.cancel_all(self)
        self.completado = False
        self.progreso = 0
        self.color_perilla = AMBAR

    def insinuar(self) -> None:
        """Un toque sin arrastrar: la perilla avanza un poco y vuelve (pista)."""
        (Animation(progreso=0.22, d=0.25, t="out_quad")
         + Animation(progreso=0, d=0.45, t="out_bounce")).start(self)

    def on_touch_down(self, toque):
        if self.completado or not self.collide_point(*toque.pos):
            return super().on_touch_down(toque)
        toque.grab(self)
        self._arrastrando = False
        self._inicio_x = toque.x
        self._inicio_progreso = self.progreso
        Animation.cancel_all(self, "progreso")
        return True

    def on_touch_move(self, toque):
        if toque.grab_current is not self:
            return super().on_touch_move(toque)
        avance = (toque.x - self._inicio_x) / self.recorrido
        if abs(toque.x - self._inicio_x) > dp(6):
            self._arrastrando = True
        self.progreso = min(max(self._inicio_progreso + avance, 0), 1)
        return True

    def on_touch_up(self, toque):
        if toque.grab_current is not self:
            return super().on_touch_up(toque)
        toque.ungrab(self)
        if self.progreso >= self.UMBRAL:
            self.completado = True
            self.color_perilla = VERDE
            Animation(progreso=1, d=0.15).start(self)
            self.dispatch("on_confirmar")
        elif not self._arrastrando:
            self.insinuar()
        else:
            Animation(progreso=0, d=0.35, t="out_back").start(self)
        return True

    def on_confirmar(self, *args):
        pass
