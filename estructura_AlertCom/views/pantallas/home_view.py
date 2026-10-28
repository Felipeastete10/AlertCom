# =============================================================================
# AlertCom - Vista: Pantalla Principal / Mapa (HomeScreen)
# =============================================================================
# Muestra el mapa de Temuco con un marcador de color por cada reporte y el
# botón "+ Reportar bache". El banner superior viene de app.mensaje_banner
# (configuración remota).
# =============================================================================

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen

from config import CARPETA_IMAGENES, CENTRO_TEMUCO, ZOOM_INICIAL
from views.componentes.dialogos import mostrar_dialogo

try:
    from kivy_garden.mapview import MapMarker, MapSource, MapView
    MAPVIEW_DISPONIBLE = True
except ImportError:  # Sin kivy_garden.mapview se usa la simulación del KV
    MAPVIEW_DISPONIBLE = False

ICONO_POR_ESTADO = {
    "Pendiente": CARPETA_IMAGENES / "marcador_pendiente.png",
    "En revisión": CARPETA_IMAGENES / "marcador_en_revision.png",
    "Reparado": CARPETA_IMAGENES / "marcador_reparado.png",
}


if MAPVIEW_DISPONIBLE:

    class MarcadorIncidente(MapMarker):
        """Marcador del mapa que recuerda a qué reporte pertenece."""

        def __init__(self, incidente, al_tocar, **kwargs) -> None:
            lat, lon = incidente.coordenadas() or CENTRO_TEMUCO
            super().__init__(
                lat=lat,
                lon=lon,
                source=str(ICONO_POR_ESTADO.get(incidente.estado, ICONO_POR_ESTADO["Pendiente"])),
                **kwargs,
            )
            self.incidente = incidente
            self.al_tocar = al_tocar

        def on_release(self, *args) -> None:
            self.al_tocar(self.incidente)


class HomeScreen(MDScreen):
    """Pantalla principal: mapa de Temuco y acceso al formulario de reporte."""

    def __init__(self, incidente_controller=None, auth_controller=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.incidente_controller = incidente_controller
        self.auth_controller = auth_controller
        self.map_view = None
        self.marcadores = []

    def on_pre_enter(self, *args) -> None:
        self._marcar_pestana_inicio()
        self._inicializar_mapa()
        self._cargar_marcadores()

    # ------------------------------------------------------------------
    # Barra inferior
    # ------------------------------------------------------------------
    def _marcar_pestana_inicio(self) -> None:
        """Al volver a Home, la pestaña activa debe ser 'Inicio'."""
        barra = self.ids.barra_navegacion
        for item in barra.children:
            item.active = item is self.ids.item_inicio

    # ------------------------------------------------------------------
    # Mapa
    # ------------------------------------------------------------------
    def _inicializar_mapa(self) -> None:
        """Crea el MapView UNA sola vez (no en cada visita)."""
        if not MAPVIEW_DISPONIBLE or self.map_view is not None:
            return

        contenedor = self.ids.map_container
        # Las imágenes del mapa se guardan en datos/cache_mapa (no en una
        # carpeta "cache" suelta). Se indica dos veces porque MapView copia
        # la carpeta a su MapSource antes de leer el parámetro cache_dir.
        carpeta_cache = str(MDApp.get_running_app().controlador.carpeta_datos / "cache_mapa")
        self.map_view = MapView(
            lat=CENTRO_TEMUCO[0],
            lon=CENTRO_TEMUCO[1],
            zoom=ZOOM_INICIAL,
            cache_dir=carpeta_cache,
            map_source=MapSource(cache_dir=carpeta_cache),
        )

        # En Kivy, index=0 deja el widget ENCIMA de todo. Con el índice más
        # alto queda DEBAJO del banner, la leyenda y el botón de reporte.
        contenedor.add_widget(self.map_view, index=len(contenedor.children))

        # Con mapa real ya no se necesita la simulación.
        contenedor.remove_widget(self.ids.simulacion_mapa)

    def _cargar_marcadores(self) -> None:
        if self.map_view is None or self.incidente_controller is None:
            return

        for marcador in self.marcadores:
            self.map_view.remove_marker(marcador)
        self.marcadores.clear()

        for incidente in self.incidente_controller.obtener_historial():
            marcador = MarcadorIncidente(incidente, al_tocar=self._mostrar_detalle)
            self.map_view.add_marker(marcador)
            self.marcadores.append(marcador)

    def _mostrar_detalle(self, incidente) -> None:
        mostrar_dialogo(
            f"#{incidente.id_incidente} · {incidente.tipo_incidente}",
            f"Gravedad: {incidente.gravedad}\n"
            f"Estado: {incidente.estado}\n"
            f"Fecha: {incidente.fecha_legible()}\n"
            f"{incidente.descripcion or 'Sin descripción.'}",
            icono="map-marker-alert",
        )

    # ------------------------------------------------------------------
    # Acciones
    # ------------------------------------------------------------------
    def ir_a_reporte(self) -> None:
        MDApp.get_running_app().navegacion.ir_a("report", "left")
