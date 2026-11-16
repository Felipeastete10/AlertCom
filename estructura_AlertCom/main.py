# AlertCom - Punto de entrada (lógica en controllers/, vistas en views/).
import librerias, limite_letra  # noqa: F401, E401 ← ANTES de KivyMD: materialyoucolor 3.0.4 y tope de letra
from kivy.properties import ColorProperty, NumericProperty, StringProperty
from kivymd.app import MDApp
from config import VALORES_POR_DEFECTO
from controllers.app_controller import AppController
from views import crear_gestor_pantallas


class AlertComApp(MDApp):
    # Textos de la Configuración Remota: parten con valores locales (fallback)
    mensaje_banner = StringProperty(VALORES_POR_DEFECTO["mensaje_banner"])
    mensaje_seguridad = StringProperty(VALORES_POR_DEFECTO["mensaje_seguridad"])
    texto_boton_reporte = StringProperty(VALORES_POR_DEFECTO["texto_boton_reporte"])
    origen_config = StringProperty("Textos locales")
    color_fondo = ColorProperty([0.08, 0.07, 0.07, 1])  # fondo y letra: los elige la persona en Ajustes
    factor_letra = NumericProperty(1.0)

    def build(self):  # el ScreenManager con todas las pantallas
        self.controlador = AppController(self)
        gestor, self.navegacion = crear_gestor_pantallas(self, self.controlador)
        return gestor

    def on_start(self):
        self.controlador.iniciar()


if __name__ == "__main__":
    AlertComApp().run()
