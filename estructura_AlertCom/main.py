# AlertCom - Punto de entrada. Solo crea la app y el ScreenManager.
# La lógica vive en controllers/ y la interfaz en views/.
from kivy.properties import StringProperty
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

    def build(self):
        self.controlador = AppController(self)
        gestor, self.navegacion = crear_gestor_pantallas(self, self.controlador)
        return gestor

    def on_start(self):
        self.controlador.iniciar()


if __name__ == "__main__":
    AlertComApp().run()
