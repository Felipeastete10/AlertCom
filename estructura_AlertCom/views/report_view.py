# =============================================================================
# AlertCom - Vista: Formulario de Reporte (ReportScreen)
# =============================================================================
# Captura los datos del formulario y los envía al IncidenteController
# inyectado desde main.py. La Vista no instancia su propio controlador
# ni genera IDs de dominio.
# =============================================================================

from kivymd.uix.screen import MDScreen
from kivymd.uix.menu import MDDropdownMenu
from kivymd.app import MDApp


class ReportScreen(MDScreen):
    """Formulario interactivo para registrar un nuevo daño vial."""

    def __init__(
        self,
        incidente_controller=None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.incidente_controller = incidente_controller
        self.tipo_seleccionado: str | None = None
        self.gravedad_seleccionada: str | None = None
        self.foto_seleccionada: str | None = None

        # Menú desplegable de tipo de daño
        self.menu_tipo = MDDropdownMenu(
            caller=None,
            items=[
                {"text": "Bache", "on_release": lambda x="Bache": self.set_tipo(x)},
                {"text": "Hoyo", "on_release": lambda x="Hoyo": self.set_tipo(x)},
                {"text": "Grieta", "on_release": lambda x="Grieta": self.set_tipo(x)},
                {
                    "text": "Hundimiento",
                    "on_release": lambda x="Hundimiento": self.set_tipo(x),
                },
                {
                    "text": "Pavimento roto",
                    "on_release": lambda x="Pavimento roto": self.set_tipo(x),
                },
            ],
            width_mult=3,
        )

        # Menú desplegable de gravedad
        self.menu_gravedad = MDDropdownMenu(
            caller=None,
            items=[
                {"text": "Leve", "on_release": lambda x="Leve": self.set_gravedad(x)},
                {
                    "text": "Moderado",
                    "on_release": lambda x="Moderado": self.set_gravedad(x),
                },
                {"text": "Grave", "on_release": lambda x="Grave": self.set_gravedad(x)},
                {
                    "text": "Crítico",
                    "on_release": lambda x="Crítico": self.set_gravedad(x),
                },
            ],
            width_mult=3,
        )

    def abrir_menu_tipo(self, caller) -> None:
        """Abre el menú de tipo de daño asociado al widget llamador."""
        self.menu_tipo.caller = caller
        self.menu_tipo.open()

    def abrir_menu_gravedad(self, caller) -> None:
        """Abre el menú de gravedad asociado al widget llamador."""
        self.menu_gravedad.caller = caller
        self.menu_gravedad.open()

    # Nombres que usa alertcom.kv (on_release de los botones del formulario)
    def open_type_menu(self) -> None:
        self.abrir_menu_tipo(self.ids.type_selector)

    def open_severity_menu(self) -> None:
        self.abrir_menu_gravedad(self.ids.severity_selector)

    def simulate_photo(self) -> None:
        """Simula la captura de foto y lo indica en la tarjeta."""
        self.foto_seleccionada = self.capturar_foto_mock()
        if "photo_label" in self.ids:
            self.ids.photo_label.text = "Foto adjuntada (simulada)"

    def submit_report(self) -> None:
        self.enviar_reporte()

    def set_tipo(self, valor: str) -> None:
        """Selecciona el tipo de daño y actualiza la etiqueta del campo."""
        self.tipo_seleccionado = valor
        if hasattr(self, "ids") and "campo_tipo" in self.ids:
            self.ids.campo_tipo.text = valor
        if hasattr(self, "ids") and "type_label" in self.ids:
            self.ids.type_label.text = valor
        self.menu_tipo.dismiss()

    def set_gravedad(self, valor: str) -> None:
        """Selecciona la gravedad y actualiza la etiqueta del campo."""
        self.gravedad_seleccionada = valor
        if hasattr(self, "ids") and "campo_gravedad" in self.ids:
            self.ids.campo_gravedad.text = valor
        if hasattr(self, "ids") and "severity_label" in self.ids:
            self.ids.severity_label.text = valor
        self.menu_gravedad.dismiss()

    def capturar_gps_mock(self) -> str:
        """
        Mockup de captura de GPS.
        Retorna coordenadas simuladas de Temuco hasta que se conecte Plyer.
        """
        lat = -38.7352
        lon = -72.5904
        print(f"[MOCK GPS] Capturada ubicación: {lat}, {lon}")
        return f"{lat}, {lon}"

    def capturar_foto_mock(self) -> str:
        """
        Mockup de captura de foto.
        Retorna una ruta simulada hasta que se conecte la cámara real.
        """
        print("[MOCK CAMARA] Captura de foto simulada.")
        return "mock_foto_reporte.jpg"

    def enviar_reporte(self) -> None:
        """
        Envía el reporte al controlador y navega al historial.

        La Vista no crea el Incidente ni genera su id_incidente; eso es
        responsabilidad del IncidenteController y del Modelo.
        """
        descripcion = ""
        if hasattr(self, "ids"):
            for campo in ("campo_descripcion", "description_field"):
                if campo in self.ids:
                    descripcion = self.ids[campo].text
                    break

        if self.incidente_controller is not None:
            self.incidente_controller.crear_incidente(
                tipo=self.tipo_seleccionado or "",
                foto=self.foto_seleccionada,
                descripcion=descripcion,
                gravedad=self.gravedad_seleccionada,
                ubicacion="-38.7352, -72.5904",  # GPS simulado Temuco
            )

        app = MDApp.get_running_app()
        if app is not None:
            app.go_to_screen("history", direction="left")
