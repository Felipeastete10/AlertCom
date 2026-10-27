# =============================================================================
# AlertCom - Pantalla 5: Historial y Trazabilidad (HistoryScreen)
# =============================================================================
# Rama:         feature/vistas-soporte
# Responsable:  Felipe Salazar (Vistas - Flujo de Soporte)
#
# Propósito:
#   Cierra el ciclo de confianza: el ciudadano ve si su reporte fue recibido,
#   si está en revisión o si ya fue reparado (código de colores semáforo).
#
# Origen de los datos (MVC):
#   - Si la app tiene `app.incidente_controller` (IncidenteController de
#     Roberto), se usa su método obtener_historial().
#   - Si todavía no existe, se muestran los reportes de ejemplo del mockup
#     para que la pantalla funcione en la demo.
#   Esta vista NO crea ni modifica incidentes; solo los muestra.
# =============================================================================

import os
from datetime import datetime

from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.list import (
    MDListItem,
    MDListItemLeadingIcon,
    MDListItemHeadlineText,
    MDListItemSupportingText,
    MDListItemTertiaryText,
)

Builder.load_file(os.path.join(os.path.dirname(__file__), "history.kv"))


# ---------------------------------------------------------------------------
# Estilo por estado: (ícono, color RGBA)
# Acepta los estados de la clase Incidente de Allan: "Pendiente",
# "En proceso", "Reparado" (y "En revisión" del mockup).
# ---------------------------------------------------------------------------
COLOR_PENDIENTE = [1, 0.3, 0.3, 1]
COLOR_REVISION = [1, 0.75, 0.2, 1]
COLOR_REPARADO = [0.3, 0.85, 0.3, 1]

ESTILOS_ESTADO = {
    "pendiente":   ("alert-circle",  COLOR_PENDIENTE),
    "en proceso":  ("clock-outline", COLOR_REVISION),
    "en revisión": ("clock-outline", COLOR_REVISION),
    "en revision": ("clock-outline", COLOR_REVISION),
    "reparado":    ("check-circle",  COLOR_REPARADO),
}
ESTILO_DESCONOCIDO = ("help-circle-outline", [0.6, 0.6, 0.6, 1])

# Reportes de ejemplo (mismos datos del guion de la presentación)
REPORTES_DEMO = [
    {"titulo": "Bache en Av. Alemania #450", "tipo": "Bache",
     "gravedad": "Grave", "estado": "En revisión", "fecha": "28/09/2026"},
    {"titulo": "Hoyo en calle Manuel Montt", "tipo": "Hoyo",
     "gravedad": "Moderado", "estado": "Reparado", "fecha": "15/09/2026"},
    {"titulo": "Grieta en Av. Caupolicán", "tipo": "Grieta",
     "gravedad": "Leve", "estado": "En revisión", "fecha": "20/09/2026"},
    {"titulo": "Hundimiento en calle Vicuña Mackenna", "tipo": "Hundimiento",
     "gravedad": "Crítico", "estado": "Pendiente", "fecha": "29/09/2026"},
]


def marcar_tab_activo(nav_bar, item) -> None:
    """
    Resalta un tab de la barra inferior SIN disparar on_switch_tabs
    (set_active_item() de KivyMD sí lo dispara y provocaría otra navegación).
    """
    # self.ids entrega proxies débiles; __self__ obtiene el widget real
    item = getattr(item, "__self__", item)
    for widget in nav_bar.children:
        widget.active = widget is item


def _incidente_a_dict(incidente) -> dict:
    """
    Convierte un objeto Incidente (de Allan) al formato que usa esta vista.
    Usa getattr con valores por defecto para no caerse si algún atributo
    cambia de nombre o todavía no existe.
    """
    tipo = getattr(incidente, "tipo_incidente", None) or getattr(incidente, "tipo", "Incidente")
    ubicacion = getattr(incidente, "ubicacion", "") or ""
    fecha = getattr(incidente, "fecha_creacion", None)
    if isinstance(fecha, datetime):
        fecha = fecha.strftime("%d/%m/%Y")

    return {
        "titulo": f"{tipo} en {ubicacion}" if ubicacion else str(tipo),
        "tipo": str(tipo),
        "gravedad": getattr(incidente, "gravedad", None) or "Sin definir",
        "estado": getattr(incidente, "estado", None) or "Pendiente",
        "fecha": fecha or "Sin fecha",
    }


class HistoryScreen(MDScreen):
    """Pantalla 5 – Historial y trazabilidad de reportes ciudadanos."""

    # ------------------------------------------------------------------ #
    #  CICLO DE VIDA
    # ------------------------------------------------------------------ #
    def on_pre_enter(self, *args) -> None:
        """Se recarga cada vez que el usuario entra (ej: tras enviar un reporte)."""
        self.cargar_historial()
        marcar_tab_activo(self.ids.nav_bar, self.ids.nav_reportes)

    # ------------------------------------------------------------------ #
    #  DATOS
    # ------------------------------------------------------------------ #
    def obtener_reportes(self) -> list:
        """Pide los reportes al controlador; si no existe, usa los de ejemplo."""
        app = MDApp.get_running_app()
        controller = getattr(app, "incidente_controller", None)
        if controller is not None and hasattr(controller, "obtener_historial"):
            # Más recientes primero
            return [_incidente_a_dict(i) for i in reversed(controller.obtener_historial())]
        return list(REPORTES_DEMO)

    # ------------------------------------------------------------------ #
    #  UI
    # ------------------------------------------------------------------ #
    def cargar_historial(self) -> None:
        """Dibuja los contadores y la lista de reportes."""
        reportes = self.obtener_reportes()

        # Contadores superiores
        estados = [r["estado"].lower() for r in reportes]
        self.ids.total_card.valor = str(len(reportes))
        self.ids.revision_card.valor = str(
            sum(e in ("en proceso", "en revisión", "en revision") for e in estados)
        )
        self.ids.reparados_card.valor = str(estados.count("reparado"))

        # Lista
        lista = self.ids.lista_reportes
        lista.clear_widgets()

        if not reportes:
            lista.add_widget(
                MDLabel(
                    text="Aún no tienes reportes.\nPresiona \"+ Reportar bache\" en el Inicio.",
                    halign="center",
                    theme_text_color="Secondary",
                    adaptive_height=True,
                    padding=[0, "32dp"],
                )
            )
            return

        for reporte in reportes:
            lista.add_widget(self._crear_item(reporte))

    def _crear_item(self, reporte: dict) -> MDListItem:
        """Crea una fila MDListItem (KivyMD 2.0, sintaxis composicional)."""
        icono, color = ESTILOS_ESTADO.get(reporte["estado"].lower(), ESTILO_DESCONOCIDO)

        return MDListItem(
            MDListItemLeadingIcon(
                icon=icono,
                theme_icon_color="Custom",
                icon_color=color,
            ),
            MDListItemHeadlineText(text=reporte["titulo"]),
            MDListItemSupportingText(
                text=f"Tipo: {reporte['tipo']}  |  Gravedad: {reporte['gravedad']}"
            ),
            MDListItemTertiaryText(
                text=f"{reporte['fecha']}  •  {reporte['estado']}",
                theme_text_color="Custom",
                text_color=color,
            ),
        )
