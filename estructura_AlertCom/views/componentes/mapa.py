# =============================================================================
# AlertCom - Mapa compartido (pantalla de inicio y formulario de reporte)
# =============================================================================
# Un solo lugar para crear el MapView con la configuración correcta:
#   • Imágenes por https (Android 9+ bloquea http).
#   • subdomains="abc": la librería elige al azar un subdominio de esta lista
#     ANTES de descargar cada imagen. Con una lista vacía fallaba cada
#     descarga (IndexError) y el mapa quedaba gris. Como la URL no tiene
#     {s}, el valor no cambia la dirección: solo evita el error.
#   • User-Agent propio: OpenStreetMap bloquea a las apps que no se
#     identifican.
#   • Caché en datos/cache_mapa: lo ya visto se muestra sin internet.
#   • pos_hint {"x": 0, "y": 0}: dentro de un MDFloatLayout, un widget sin
#     pos_hint queda en la posición (0, 0) de la VENTANA, no de su caja.
#     Sin esto el mapa se dibujaba en otro lugar y su centro quedaba corrido.
#   • Solo Temuco: el mapa no deja arrastrarse fuera de LIMITES_TEMUCO
#     (map_source.bounds) y no se puede alejar más de lo necesario para
#     ver la ciudad completa (zoom mínimo según el tamaño de la pantalla).
# =============================================================================

import math

from kivymd.app import MDApp

from config import LIMITES_TEMUCO, URL_MAPA, USER_AGENT

TAMANO_CUADRO = 256      # pixeles de cada imagen del mapa (sin escalar)
ZOOM_MAXIMO = 19

try:
    import kivy_garden.mapview.downloader as descargador
    from kivy_garden.mapview import MapMarker, MapSource, MapView

    descargador.USER_AGENT = USER_AGENT  # la librería lo lee en cada descarga
    MAPVIEW_DISPONIBLE = True
except ImportError:  # sin kivy_garden.mapview se muestra un mapa simulado
    MapMarker = MapSource = MapView = None
    MAPVIEW_DISPONIBLE = False


def carpeta_cache_mapa() -> str:
    return str(MDApp.get_running_app().controlador.carpeta_datos / "cache_mapa")


def zoom_minimo_para(ancho_px: float, alto_px: float, limites=LIMITES_TEMUCO,
                     tamano_cuadro: float = TAMANO_CUADRO) -> int:
    """Zoom más alejado en que la pantalla todavía cabe DENTRO de la zona.

    Si se pudiera alejar más, la pantalla sería más grande que Temuco y se
    vería lo que hay afuera. (Fórmula de los mapas web: en el zoom z el mundo
    mide 256·2^z pixeles de ancho.)
    """
    oeste, sur, este, norte = limites

    def y_mercator(lat):  # 0 arriba del mundo, 1 abajo
        rad = math.radians(lat)
        return (1 - math.log(math.tan(rad) + 1 / math.cos(rad)) / math.pi) / 2

    ancho_zona = (este - oeste) / 360            # fracción del mundo
    alto_zona = y_mercator(sur) - y_mercator(norte)
    for zoom in range(1, ZOOM_MAXIMO + 1):
        mundo = tamano_cuadro * 2 ** zoom
        if ancho_zona * mundo >= ancho_px and alto_zona * mundo >= alto_px:
            return zoom
    return ZOOM_MAXIMO


def _ajustar_zoom_minimo(mapa, *_args) -> None:
    if mapa.width <= 1 or mapa.height <= 1:
        return
    # Cada imagen se dibuja con dp_tile_size pixeles (más en pantallas densas)
    minimo = zoom_minimo_para(mapa.width, mapa.height, tamano_cuadro=mapa.map_source.dp_tile_size)
    mapa.map_source.min_zoom = minimo
    if mapa.zoom < minimo:
        mapa.zoom = minimo


def _mantener_en_zona(mapa, _zoom, _coordenada) -> None:
    """Si el código movió el centro fuera de Temuco (center_on no respeta
    los límites), se devuelve al punto más cercano dentro de la zona."""
    oeste, sur, este, norte = LIMITES_TEMUCO
    # Media pantalla de margen: así el BORDE de la pantalla queda en la zona
    lat_min, lon_min, lat_max, lon_max = mapa.get_bbox()
    medio_alto = min((lat_max - lat_min) / 2, (norte - sur) / 2)
    medio_ancho = min((lon_max - lon_min) / 2, (este - oeste) / 2)
    lat = min(max(mapa.lat, sur + medio_alto), norte - medio_alto)
    lon = min(max(mapa.lon, oeste + medio_ancho), este - medio_ancho)
    if abs(lat - mapa.lat) > 1e-6 or abs(lon - mapa.lon) > 1e-6:
        mapa.center_on(lat, lon)


def crear_mapa(lat: float, lon: float, zoom: int):
    """Devuelve un MapView listo (limitado a Temuco), o None si mapview no
    está instalado."""
    if not MAPVIEW_DISPONIBLE:
        return None
    # La carpeta se indica dos veces porque MapView copia su caché al
    # MapSource antes de leer el parámetro cache_dir.
    cache = carpeta_cache_mapa()
    oeste, sur, este, norte = LIMITES_TEMUCO
    mapa = MapView(
        lat=lat,
        lon=lon,
        zoom=zoom,
        cache_dir=cache,
        double_tap_zoom=True,
        pos_hint={"x": 0, "y": 0},
        map_source=MapSource(
            url=URL_MAPA,
            cache_key="osm_https",
            subdomains="abc",
            attribution="© OpenStreetMap",
            min_zoom=12,
            max_zoom=ZOOM_MAXIMO,
            cache_dir=cache,
        ),
    )
    # (lon mínima, lat mínima, lon máxima, lat máxima). MapSource no lo
    # recibe al crearse: se asigna después.
    mapa.map_source.bounds = (oeste, sur, este, norte)
    mapa.bind(size=lambda *a: _ajustar_zoom_minimo(mapa))
    mapa.bind(on_map_relocated=_mantener_en_zona)
    return mapa
