# =============================================================================
# AlertCom - Vista: Historial de Reportes (HistoryScreen)
# =============================================================================
# Muestra la lista de reportes obtenida del IncidenteController en tarjetas
# MDCard dentro de un MDScrollView.
# =============================================================================

from kivymd.uix.screen import MDScreen
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel


class HistoryScreen(MDScreen):
    """Pantalla de historial y trazabilidad de reportes."""

    def __init__(self, incidente_controller=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.incidente_controller = incidente_controller

    def on_pre_enter(self) -> None:
        """Carga los reportes antes de mostrar la pantalla."""
        self._cargar_historial()

    def _cargar_historial(self) -> None:
        """Solicita incidentes al IncidenteController y los muestra en tarjetas."""
        self.clear_widgets()

        if self.incidente_controller is None:
            self.add_widget(
                MDLabel(
                    text="Controlador de incidentes no disponible",
                    halign="center",
                    theme_text_color="Error",
                )
            )
            return

        incidentes = self.incidente_controller.obtener_historial()

        layout_principal = MDBoxLayout(
            orientation="vertical",
            spacing="10dp",
            padding="10dp",
            size_hint=(1, 1),
        )

        scroll = MDScrollView()
        lista = MDBoxLayout(
            orientation="vertical",
            spacing="10dp",
            size_hint_y=None,
            height=dp_autosize(len(incidentes)),
        )
        lista.bind(minimum_height=lista.setter("height"))

        if not incidentes:
            lista.add_widget(
                MDLabel(
                    text="No hay reportes registrados.",
                    halign="center",
                    theme_text_color="Secondary",
                    size_hint_y=None,
                    height="40dp",
                )
            )
        else:
            for inc in incidentes:
                tarjeta = MDCard(
                    size_hint_y=None,
                    height="72dp",
                    elevation=1,
                    radius=[8, 8, 8, 8],
                    padding="8dp",
                )
                tarjeta_layout = MDBoxLayout(
                    orientation="vertical",
                    spacing="2dp",
                    size_hint_y=None,
                    height="56dp",
                )
                tarjeta_layout.add_widget(
                    MDLabel(
                        text=f"#{inc.id_incidente} - {inc.tipo_incidente}",
                        font_style="Body",
                        theme_text_color="Primary",
                        bold=True,
                    )
                )
                tarjeta_layout.add_widget(
                    MDLabel(
                        text=f"Gravedad: {inc.gravedad}  |  Estado: {inc.estado}  |  {inc.ubicacion}",
                        font_style="Caption",
                        theme_text_color="Secondary",
                    )
                )
                tarjeta.add_widget(tarjeta_layout)
                lista.add_widget(tarjeta)

        scroll.add_widget(lista)
        layout_principal.add_widget(scroll)
        self.add_widget(layout_principal)


def dp_autosize(cantidad: int) -> int:
    """Calcula una altura aproximada para el contenedor de tarjetas del historial."""
    return max(200, cantidad * 82 + 40)
