from kivy.lang import Builder
from kivy.metrics import dp
from kivymd.uix.screen import MDScreen
from kivymd.uix.menu import MDDropdownMenu

Builder.load_file('views/report.kv')

class ReportScreen(MDScreen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tipo_seleccionado = None
        self.gravedad_seleccionada = None

        self.menu_tipo = MDDropdownMenu(
            caller=None,
            items=[
                {"text": "Bache", "on_release": lambda x="Bache": self.set_tipo(x)},
                {"text": "Luminaria", "on_release": lambda x="Luminaria": self.set_tipo(x)},
                {"text": "Basura", "on_release": lambda x="Basura": self.set_tipo(x)},
            ],
            width_mult=3,
        )

        self.menu_gravedad = MDDropdownMenu(
            caller=None,
            items=[
                {"text": "Baja", "on_release": lambda x="Baja": self.set_gravedad(x)},
                {"text": "Media", "on_release": lambda x="Media": self.set_gravedad(x)},
                {"text": "Alta", "on_release": lambda x="Alta": self.set_gravedad(x)},
            ],
            width_mult=3,
        )

    def abrir_menu_tipo(self, caller):
        self.menu_tipo.caller = caller
        self.menu_tipo.open()

    def abrir_menu_gravedad(self, caller):
        self.menu_gravedad.caller = caller
        self.menu_gravedad.open()

    def set_tipo(self, valor):
        self.tipo_seleccionado = valor
        self.ids.campo_tipo.text = valor
        self.menu_tipo.dismiss()

    def set_gravedad(self, valor):
        self.gravedad_seleccionada = valor
        self.ids.campo_gravedad.text = valor
        self.menu_gravedad.dismiss()

    def enviar_reporte(self):
        descripcion = self.ids.campo_descripcion.text
        # Aquí llamas a Roberto (ajusta el import según cómo armó su controlador)
        try:
            from controllers.incident_controller import IncidentController
            controller = IncidentController()
            controller.crear_incidente(
                self.tipo_seleccionado,
                None,  # foto por ahora
                descripcion
            )
            print("Reporte enviado correctamente")
        except Exception as e:
            print("Error al enviar reporte:", e)