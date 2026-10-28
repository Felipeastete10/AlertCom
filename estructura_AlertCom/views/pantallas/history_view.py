# =============================================================================
# AlertCom - Vista: Historial de Reportes (HistoryScreen)
# =============================================================================
# Llena SOLO la lista y los contadores definidos en views/kv/history.kv (ya no borra
# la pantalla completa). Un vecino ve sus reportes; un funcionario municipal
# ve todos y puede avanzar su estado (lo que dispara una notificación).
# =============================================================================

from kivymd.uix.label import MDLabel
from kivymd.uix.list import (
    MDListItem,
    MDListItemHeadlineText,
    MDListItemLeadingIcon,
    MDListItemSupportingText,
    MDListItemTertiaryText,
    MDListItemTrailingIcon,
)
from kivymd.uix.screen import MDScreen

from views.componentes.dialogos import mostrar_aviso, mostrar_dialogo

ICONO_POR_ESTADO = {
    "Pendiente": ("alert-circle", [0.9, 0.28, 0.28, 1]),
    "En revisión": ("clock-outline", [0.96, 0.62, 0.04, 1]),
    "Reparado": ("check-circle", [0.2, 0.66, 0.33, 1]),
}


class HistoryScreen(MDScreen):
    """Pantalla de historial y trazabilidad de reportes."""

    def __init__(self, incidente_controller=None, auth_controller=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.incidente_controller = incidente_controller
        self.auth_controller = auth_controller

    @property
    def _usuario(self):
        return self.auth_controller.usuario_actual if self.auth_controller else None

    def _id_a_filtrar(self):
        """None = todos los reportes (funcionario municipal)."""
        usuario = self._usuario
        if usuario is None or usuario.es_municipal:
            return None
        return usuario.id_usuario

    def on_pre_enter(self, *args) -> None:
        self.cargar_historial()

    def cargar_historial(self) -> None:
        id_filtro = self._id_a_filtrar()
        self.ids.titulo_historial.text = "Todos los reportes" if id_filtro is None else "Mis Reportes"

        # --- Contadores reales ---
        resumen = self.incidente_controller.resumen(id_filtro)
        self.ids.total_label.text = str(resumen["total"])
        self.ids.revision_label.text = str(resumen["en_revision"])
        self.ids.reparados_label.text = str(resumen["reparados"])

        # --- Lista (solo se limpia la lista, no la pantalla) ---
        lista = self.ids.lista_reportes
        lista.clear_widgets()

        reportes = self.incidente_controller.obtener_historial(id_filtro)
        if not reportes:
            lista.add_widget(
                MDLabel(
                    text="Aún no hay reportes. ¡Envía el primero desde el mapa!",
                    halign="center",
                    theme_text_color="Secondary",
                    adaptive_height=True,
                    padding=("16dp", "24dp"),
                )
            )
            return

        for incidente in reportes:
            icono, color = ICONO_POR_ESTADO.get(incidente.estado, ("help-circle", [0.6, 0.6, 0.6, 1]))
            item = MDListItem(
                MDListItemLeadingIcon(icon=icono, theme_icon_color="Custom", icon_color=color),
                MDListItemHeadlineText(text=f"#{incidente.id_incidente} · {incidente.tipo_incidente}"),
                MDListItemSupportingText(text=f"Gravedad: {incidente.gravedad}  |  {incidente.estado}"),
                MDListItemTertiaryText(text=incidente.fecha_legible()),
                MDListItemTrailingIcon(icon="chevron-right"),
            )
            item.bind(on_release=lambda _item, inc=incidente: self.mostrar_detalle(inc))
            lista.add_widget(item)

    def mostrar_detalle(self, incidente) -> None:
        mensaje = (
            f"Gravedad: {incidente.gravedad}\n"
            f"Estado: {incidente.estado}\n"
            f"Fecha: {incidente.fecha_legible()}\n"
            f"Ubicación: {incidente.ubicacion or 'Sin GPS'}\n\n"
            f"{incidente.descripcion or 'Sin descripción.'}"
        )
        botones = [("Cerrar", None)]

        # Solo un funcionario municipal puede avanzar el estado.
        usuario = self._usuario
        siguiente = incidente.siguiente_estado()
        if usuario and usuario.es_municipal and siguiente:
            botones.append(
                (f"Marcar: {siguiente}", lambda: self._avanzar_estado(incidente.id_incidente))
            )

        mostrar_dialogo(
            f"#{incidente.id_incidente} · {incidente.tipo_incidente}",
            mensaje,
            icono="clipboard-text-outline",
            botones=botones,
        )

    def _avanzar_estado(self, id_incidente: int) -> None:
        try:
            incidente = self.incidente_controller.avanzar_estado(id_incidente)
        except ValueError as error:
            mostrar_dialogo("No se pudo actualizar", str(error))
            return
        mostrar_aviso(f"Reporte #{id_incidente}: {incidente.estado}")
        self.cargar_historial()
