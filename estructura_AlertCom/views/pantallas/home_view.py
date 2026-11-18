# =============================================================================
# AlertCom - Vista: Pantalla Principal / Mapa (HomeScreen)
# =============================================================================
# Muestra el mapa de Temuco con un marcador de color por cada reporte, el
# botón "+ Reportar bache" y el botón "Mi ubicación" (punto azul).
# El banner superior viene de app.mensaje_banner (configuración remota).
# El MapView se crea en views/componentes/mapa.py (configuración correcta).
# =============================================================================

from kivy.clock import Clock
from kivy.metrics import dp
from kivymd.app import MDApp

from config import (ANCLA_MARCADOR_Y, CARPETA_IMAGENES, CENTRO_TEMUCO, LIMITES_TEMUCO, ZOOM_INICIAL,
                    ZOOM_UBICACION)
from models.incidente import dentro_de_zona
from views.componentes.acciones_municipio import eliminar_como_municipio
from views.componentes.detalle_reporte import mostrar_detalle_reporte
from views.componentes.dialogos import mostrar_aviso, mostrar_dialogo
from views.componentes.interaccion import Pastilla
from views.componentes.mapa import MAPVIEW_DISPONIBLE, MapMarker, crear_mapa
from views.componentes.pantalla_base import PantallaBase

ICONO_POR_ESTADO = {
    "Pendiente": CARPETA_IMAGENES / "marcador_pendiente.png",
    "En revisión": CARPETA_IMAGENES / "marcador_en_revision.png",
    "Reparado": CARPETA_IMAGENES / "marcador_reparado.png",
}
ICONO_MI_UBICACION = CARPETA_IMAGENES / "mi_ubicacion.png"

# Filtros del mapa: (estado, texto corto, color)
FILTROS = [
    ("Pendiente", "Pendientes", [0.9, 0.28, 0.28, 1]),
    ("En revisión", "Revisión", [0.96, 0.62, 0.04, 1]),
    ("Reparado", "Reparados", [0.2, 0.66, 0.33, 1]),
]


if MAPVIEW_DISPONIBLE:

    class MarcadorIncidente(MapMarker):
        """Marcador del mapa que recuerda a qué reporte pertenece."""

        def __init__(self, incidente, al_tocar, **kwargs) -> None:
            lat, lon = incidente.coordenadas() or CENTRO_TEMUCO
            super().__init__(
                lat=lat,
                lon=lon,
                source=str(ICONO_POR_ESTADO.get(incidente.estado, ICONO_POR_ESTADO["Pendiente"])),
                anchor_x=0.5,
                anchor_y=ANCLA_MARCADOR_Y,  # la PUNTA del marcador en el lugar exacto
                **kwargs,
            )
            self.incidente = incidente
            self.al_tocar = al_tocar
            if not incidente.confirmado:
                self.opacity = 0.55  # por confirmar: más tenue que los públicos

        def on_release(self, *args) -> None:
            self.al_tocar(self.incidente)


class HomeScreen(PantallaBase):
    """Pantalla principal: mapa de Temuco y acceso al formulario de reporte."""

    def __init__(self, incidente_controller=None, auth_controller=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.incidente_controller = incidente_controller
        self.auth_controller = auth_controller
        self.map_view = None
        self.marcadores = []
        self.marcador_usuario = None

    def on_kv_post(self, base_widget) -> None:
        # Ojo: Kivy llama a on_kv_post ANTES de que termine __init__, por eso
        # los filtros se crean aquí y no en __init__.
        super().on_kv_post(base_widget)
        self.estados_visibles = {estado for estado, _, _ in FILTROS}
        self.filtros = {}
        self.ids.filtros_estado.spacing = dp(4)
        for estado, texto, color in FILTROS:
            filtro = Pastilla(texto=texto, valor=estado, icono="circle-outline", color=color,
                              seleccionada=True, compacta=True,
                              padding=[dp(7), dp(6), dp(9), dp(6)], spacing=dp(4))
            filtro.bind(on_release=lambda f: self.alternar_filtro(f.valor))
            self.ids.filtros_estado.add_widget(filtro)
            self.filtros[estado] = filtro

    def on_pre_enter(self, *args) -> None:
        usuario = self.auth_controller.usuario_actual if self.auth_controller else None
        municipal = bool(usuario and usuario.es_municipal)
        self.ids.boton_confirmar.opacity = 1 if municipal else 0
        self.ids.boton_confirmar.disabled = not municipal
        self._marcar_pestana_inicio()
        self._inicializar_mapa()
        self._cargar_marcadores()
        # Trae los reportes nuevos de los demás (al llegar se llama refrescar)
        MDApp.get_running_app().controlador.sincronizar()

    def refrescar(self) -> None:
        """Llegaron reportes de la nube: se redibujan los marcadores."""
        self._cargar_marcadores()

    def on_enter(self, *args) -> None:
        super().on_enter(*args)  # registra pantalla_vista
        # La primera vez, centrar cuando el mapa ya tiene su tamaño final
        # (si se centra antes, el centro queda corrido).
        if self.map_view is not None and not getattr(self, "_mapa_centrado", False):
            self._mapa_centrado = True
            Clock.schedule_once(lambda _dt: self.map_view.center_on(*CENTRO_TEMUCO), 0)

    def on_leave(self, *args) -> None:
        MDApp.get_running_app().controlador.ubicacion.detener()

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
        if self.map_view is not None:
            return
        self.map_view = crear_mapa(*CENTRO_TEMUCO, ZOOM_INICIAL)
        if self.map_view is None:
            return

        contenedor = self.ids.map_container
        # En Kivy, index=0 deja el widget ENCIMA de todo. Con el índice más
        # alto queda DEBAJO del banner, la leyenda y los botones.
        contenedor.add_widget(self.map_view, index=len(contenedor.children))
        # Con mapa real ya no se necesita la simulación.
        contenedor.remove_widget(self.ids.simulacion_mapa)

    def _cargar_marcadores(self) -> None:
        if self.map_view is None or self.incidente_controller is None:
            return

        for marcador in self.marcadores:
            self.map_view.remove_marker(marcador)
        self.marcadores.clear()

        # Confirmados + los propios por confirmar (el funcionario ve todos)
        usuario = self.auth_controller.usuario_actual if self.auth_controller else None
        reportes = self.incidente_controller.visibles_para(usuario)
        for estado, texto, _ in FILTROS:
            cantidad = sum(r.estado == estado for r in reportes)
            self.filtros[estado].texto = f"{texto} {cantidad}"

        for incidente in reportes:
            if incidente.estado not in self.estados_visibles:
                continue
            marcador = MarcadorIncidente(incidente, al_tocar=self._mostrar_detalle)
            self.map_view.add_marker(marcador)
            self.marcadores.append(marcador)

    def alternar_filtro(self, estado: str) -> None:
        """Muestra u oculta los marcadores de un estado."""
        if estado in self.estados_visibles:
            self.estados_visibles.discard(estado)
        else:
            self.estados_visibles.add(estado)
        self.filtros[estado].seleccionada = estado in self.estados_visibles
        self._cargar_marcadores()
        if not self.estados_visibles:
            mostrar_aviso("Todos los filtros apagados: toca uno para ver reportes")

    def _mostrar_detalle(self, incidente) -> None:
        usuario = self.auth_controller.usuario_actual if self.auth_controller else None
        botones = None
        if usuario and usuario.es_municipal:
            # Desde el mapa, el funcionario también puede eliminar el reporte
            botones = [("Cerrar", None),
                       ("Eliminar", lambda: eliminar_como_municipio(
                           self.incidente_controller, usuario, incidente, al_terminar=self._cargar_marcadores))]
        mostrar_detalle_reporte(incidente, botones=botones)

    # ------------------------------------------------------------------
    # Mi ubicación
    # ------------------------------------------------------------------
    def centrar_en_mi_ubicacion(self) -> None:
        servicio = MDApp.get_running_app().controlador.ubicacion
        if servicio.disponible:
            mostrar_aviso("Buscando tu ubicación…")
        servicio.pedir(self._al_obtener_ubicacion, self._al_fallar_ubicacion)

    def _al_obtener_ubicacion(self, lat, lon, _precision, definitiva) -> None:
        if self.map_view is None:
            return
        if not dentro_de_zona(lat, lon, LIMITES_TEMUCO):
            MDApp.get_running_app().controlador.ubicacion.detener()
            mostrar_dialogo("Estás fuera de Temuco",
                            "El mapa de AlertCom muestra solo Temuco y Padre Las Casas.",
                            icono="map-marker-off-outline")
            return
        if self.marcador_usuario is None:
            self.marcador_usuario = MapMarker(lat=lat, lon=lon, source=str(ICONO_MI_UBICACION),
                                              anchor_x=0.5, anchor_y=0.5)
            self.map_view.add_marker(self.marcador_usuario)
        else:
            self.marcador_usuario.lat, self.marcador_usuario.lon = lat, lon
            self.map_view.trigger_update(True)
        self.map_view.zoom = ZOOM_UBICACION
        self.map_view.center_on(lat, lon)
        if definitiva:
            self.registrar_evento("ubicacion_solicitada", {"pantalla": "home", "metodo": "gps", "resultado": "ok"})

    def _al_fallar_ubicacion(self, motivo, mensaje) -> None:
        self.registrar_evento("ubicacion_solicitada", {"pantalla": "home", "metodo": "gps", "resultado": motivo})
        mostrar_dialogo("Ubicación no disponible", mensaje, icono="crosshairs-off")

    # ------------------------------------------------------------------
    # Acciones
    # ------------------------------------------------------------------
    def ir_a_reporte(self) -> None:
        MDApp.get_running_app().navegacion.ir_a("report", "left")
