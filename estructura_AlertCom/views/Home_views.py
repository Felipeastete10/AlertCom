# =============================================================================
# AlertCom - Vista: Pantalla Principal / Mapa (HomeScreen)
# =============================================================================
# Integra el mapa de Temuco con marcadores de incidentes y expone la acción
# del FAB extendido "+ Reportar bache" definido en alertcom.kv.
# =============================================================================

from kivymd.uix.screen import MDScreen
from kivymd.app import MDApp

try:
    from kivy_garden.mapview import MapView, MapMarker
    MAPVIEW_DISPONIBLE = True
except Exception:  # pragma: no cover - fallback si kivy_garden no está instalado
    MAPVIEW_DISPONIBLE = False


class HomeScreen(MDScreen):
    """Pantalla principal: mapa de Temuco y acceso al formulario de reporte."""

    def __init__(self, incidente_controller=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.incidente_controller = incidente_controller
        self.map_view = None
        self.marcadores = []

    def on_pre_enter(self) -> None:
        """Inicializa el mapa y refresca los marcadores al entrar a la pantalla."""
        self._inicializar_mapa()
        self._cargar_marcadores()

    def _inicializar_mapa(self) -> None:
        """Añade el MapView real al contenedor del KV si kivy_garden existe."""
        if not MAPVIEW_DISPONIBLE:
            # Sin kivy_garden se conserva la simulación visual definida en el KV.
            return

        contenedor = self.ids.get("map_container") if hasattr(self, "ids") else None
        if contenedor is None:
            return

        if self.map_view is not None:
            try:
                contenedor.remove_widget(self.map_view)
            except Exception:
                pass

        self.map_view = MapView(
            lat=-38.7359,
            lon=-72.5904,
            zoom=14,
        )
        # index=0: el mapa queda detrás de la simulación, la leyenda y el FAB.
        contenedor.add_widget(self.map_view, index=0)

    def _cargar_marcadores(self) -> None:
        """Genera un MapMarker por cada incidente del controlador."""
        if not MAPVIEW_DISPONIBLE or self.map_view is None:
            return

        for marker in self.marcadores:
            try:
                self.map_view.remove_marker(marker)
            except Exception:
                pass
        self.marcadores.clear()

        if self.incidente_controller is None:
            return

        for inc in self.incidente_controller.obtener_historial():
            lat, lon = self._parsear_ubicacion(inc.ubicacion)
            if lat is None or lon is None:
                lat, lon = -38.7359, -72.5904  # Centro de Temuco por defecto

            marker = MapMarker(lat=lat, lon=lon)
            self.map_view.add_marker(marker)
            self.marcadores.append(marker)

    @staticmethod
    def _parsear_ubicacion(ubicacion: str):
        """Convierte 'lat, lon' en una tupla de floats; (None, None) si falla."""
        try:
            partes = ubicacion.split(",")
            if len(partes) >= 2:
                return float(partes[0].strip()), float(partes[1].strip())
        except Exception:
            pass
        return None, None

    def ir_a_reporte(self) -> None:
        """Navega a ReportScreen (acción del FAB '+ Reportar bache')."""
        app = MDApp.get_running_app()
        if app is not None and app.root is not None:
            app.root.current = "report"
