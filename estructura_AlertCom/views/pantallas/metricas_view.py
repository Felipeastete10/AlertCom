# =============================================================================
# AlertCom - Vista: Métricas de uso (MetricasScreen) · solo municipal
# =============================================================================
# Lee los eventos guardados en el teléfono y muestra los 3 KPIs y las
# métricas descriptivas. El cálculo NO está aquí: lo hace
# controllers/analitica.py (el mismo código que usa el script del PC),
# así lo que se ve en pantalla coincide con lo que se explica en el informe.
# =============================================================================

from kivy.clock import Clock
from kivy.factory import Factory
from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivymd.uix.list import MDListItem, MDListItemHeadlineText, MDListItemSupportingText

from controllers import analitica
from views.componentes.pantalla_base import PantallaBase

COLOR_ESTADO = {
    True: ([0.2, 0.66, 0.33, 1], "Cumple la meta"),
    False: ([0.96, 0.62, 0.04, 1], "No cumple la meta"),
    None: ([0.6, 0.6, 0.6, 1], "Sin datos suficientes"),
}


def formato_numero(valor) -> str:
    """85.7 → '85,7' (coma decimal, como se escribe en Chile)."""
    if valor is None:
        return "—"
    texto = f"{valor:.1f}".replace(".", ",")
    return texto[:-2] if texto.endswith(",0") else texto


class MetricasScreen(PantallaBase):
    """KPIs calculados en vivo desde eventos.jsonl."""

    def __init__(self, auth_controller=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.auth_controller = auth_controller

    def on_pre_enter(self, *args) -> None:
        usuario = self.auth_controller.usuario_actual if self.auth_controller else None
        if usuario is None or not usuario.es_municipal:
            # Protección: un vecino no ve las métricas aunque llegue a esta pantalla
            Clock.schedule_once(lambda _dt: MDApp.get_running_app().navegacion.volver())
            return
        self.actualizar()

    def actualizar(self) -> None:
        controlador = MDApp.get_running_app().controlador
        datos = analitica.resumen_desde_carpeta(controlador.eventos.carpeta)
        metricas = datos["metricas"]

        # --- Periodo de los datos ---
        if datos["periodo"]:
            self.ids.periodo_label.text = (
                f"Datos del {datos['periodo']['desde']} al {datos['periodo']['hasta']} · "
                f"{metricas['total_eventos']} eventos"
            )
        else:
            self.ids.periodo_label.text = "Aún no hay eventos registrados en este teléfono."

        # --- KPIs ---
        lista_kpis = self.ids.lista_kpis
        lista_kpis.clear_widgets()
        for kpi in datos["kpis"]:
            color, texto_estado = COLOR_ESTADO[kpi["cumple"]]
            comparador = "≤" if kpi["unidad"] == "s" else "≥"
            tarjeta = Factory.TarjetaKPI()
            tarjeta.titulo = kpi["nombre"]
            tarjeta.valor = f"{formato_numero(kpi['valor'])} {kpi['unidad']}"
            tarjeta.meta = f"Meta: {comparador} {formato_numero(kpi['meta'])} {kpi['unidad']}"
            tarjeta.estado = texto_estado
            tarjeta.color_estado = color
            tarjeta.detalle = " · ".join(f"{k.replace('_', ' ')}: {v}" for k, v in kpi["detalle"].items())
            lista_kpis.add_widget(tarjeta)

        # --- Métricas descriptivas ---
        pantallas = metricas["pantallas_vistas"]
        filas = [
            ("Sesiones (aperturas de la app)", metricas["sesiones"]),
            ("Usuarios activos", metricas["usuarios_activos"]),
            ("Usuarios que volvieron otro día (retención)", metricas["usuarios_recurrentes"]),
            ("Reportes enviados", metricas["reportes_enviados"]),
            ("Reportes rechazados por datos incompletos", metricas["reportes_rechazados"]),
            ("Inicios de sesión fallidos", metricas["logins_fallidos"]),
            ("Pantalla más visitada", next(iter(pantallas), "—")),
        ]
        lista = self.ids.lista_metricas
        lista.clear_widgets()
        if not metricas["total_eventos"]:
            lista.add_widget(MDLabel(text="Usa la app y vuelve aquí para ver las métricas.",
                                     halign="center", theme_text_color="Secondary",
                                     adaptive_height=True, padding=("16dp", "16dp")))
            return
        for titulo, valor in filas:
            lista.add_widget(MDListItem(
                MDListItemHeadlineText(text=str(valor)),
                MDListItemSupportingText(text=titulo),
            ))
