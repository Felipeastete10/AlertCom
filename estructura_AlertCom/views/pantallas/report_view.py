# =============================================================================
# AlertCom - Vista: Formulario de Reporte (ReportScreen)
# =============================================================================
# Captura ubicación (mapa con pin + GPS), calle, foto (cámara, galería o
# archivo), tipo, gravedad y descripción, y se los entrega al
# IncidenteController. La vista no valida reglas de negocio ni genera IDs:
# si el controlador rechaza los datos, aquí solo se muestra el error.
#
# Hardware (en controllers/): GPS → ServicioUbicacion, cámara → Camara,
# calle desde coordenadas → BuscadorCalles, foto reducida → fotos.py.
# =============================================================================

from functools import partial
from pathlib import Path

from kivy.clock import Clock
from kivy.utils import platform
from kivymd.app import MDApp

from config import (
    CENTRO_TEMUCO,
    GRAVEDADES,
    LIMITES_TEMUCO,
    PRECISION_GPS_BUENA,
    TIPOS_DANO,
    ZOOM_REPORTE,
    ZOOM_UBICACION,
)
from controllers import fotos
from models.incidente import dentro_de_zona
from views.componentes.dialogos import mostrar_aviso, mostrar_dialogo
from views.componentes.estilos import ESTILO_GRAVEDAD, ICONO_TIPO
from views.componentes.interaccion import Pastilla, mostrar_exito, sacudir, vibrar
from views.componentes.mapa import crear_mapa
from views.componentes.pantalla_base import PantallaBase

TEXTO_FOTO_INICIAL = "Toca para tomar una foto del daño"
ESPERA_BUSCAR_CALLE = 1.2         # segundos con el mapa quieto antes de preguntar la calle
EXTENSIONES_IMAGEN = [".jpg", ".jpeg", ".png", ".webp"]

COLOR_PENDIENTE = [0.96, 0.62, 0.04, 1]
COLOR_LISTO = [0.2, 0.66, 0.33, 1]



class ReportScreen(PantallaBase):
    """Formulario para registrar un nuevo daño vial."""

    def __init__(self, incidente_controller=None, auth_controller=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.incidente_controller = incidente_controller
        self.auth_controller = auth_controller
        self.tipo = None
        self.gravedad = None
        self.foto = None                 # ruta relativa: "fotos/reporte_....jpg"
        self.origen_ubicacion = None     # None, "gps", "mapa" o "calle"
        self.calle_exacta = False        # la búsqueda encontró el número de casa
        self.precision_gps = None
        self.mapa = None
        self._movido_por_persona = False # True cuando un dedo arrastra el mapa
        self._calle_automatica = ""      # última calle que escribió la app
        self._busqueda_calle = None
        self._selector_archivos = None

    @property
    def _controlador(self):
        return MDApp.get_running_app().controlador

    def on_kv_post(self, base_widget) -> None:
        super().on_kv_post(base_widget)
        self._crear_pastillas()
        self.ids.calle_field.bind(text=lambda *_: self.actualizar_progreso())
        # En el computador no hay cámara de teléfono: se elige un archivo.
        if platform != "android":
            self.ids.texto_boton_camara.text = "Elegir imagen"
            self.ids.icono_boton_camara.icon = "image-plus"
            self.ids.photo_label.text = TEXTO_FOTO_INICIAL.replace("tomar", "elegir")
            self.ids.botones_foto.remove_widget(self.ids.boton_galeria)

    # ------------------------------------------------------------------
    # Ciclo de la pantalla
    # ------------------------------------------------------------------
    def on_pre_enter(self, *args) -> None:
        self._inicializar_mapa()
        self.limpiar_formulario()

    def on_enter(self, *args) -> None:
        super().on_enter(*args)  # registra pantalla_vista
        # Inicio del flujo principal: con este evento y "reporte_enviado" se
        # calculan la tasa de finalización y el tiempo para reportar.
        self.registrar_evento("reporte_iniciado")
        # Ahora que el mapa ya tiene su tamaño final, se centra bien.
        if not self.origen_ubicacion:
            Clock.schedule_once(lambda _dt: self._mover_mapa(*CENTRO_TEMUCO, zoom=ZOOM_REPORTE), 0)
        # En el teléfono se busca la ubicación de inmediato (ahorra un paso).
        if self._controlador.ubicacion.disponible:
            self.usar_mi_ubicacion(automatico=True)

    def on_leave(self, *args) -> None:
        self._controlador.ubicacion.detener()
        if self._busqueda_calle is not None:
            self._busqueda_calle.cancel()
            self._busqueda_calle = None

    def limpiar_formulario(self) -> None:
        if self.foto:  # foto de un reporte que no se envió
            fotos.borrar_foto(self._controlador.carpeta_datos, self.foto)
        self.tipo = None
        self.gravedad = None
        self.foto = None
        self.origen_ubicacion = None
        self.calle_exacta = False
        self.precision_gps = None
        self._calle_automatica = ""
        self._marcar(self.ids.grupo_tipo, None)
        self._marcar(self.ids.grupo_gravedad, None)
        self.ids.description_field.text = ""
        self.ids.calle_field.text = ""
        self._mostrar_foto()
        self._mover_mapa(*CENTRO_TEMUCO, zoom=ZOOM_REPORTE)
        self._mostrar_estado_ubicacion()

    # ------------------------------------------------------------------
    # Mapa con pin fijo
    # ------------------------------------------------------------------
    def _inicializar_mapa(self) -> None:
        if self.mapa is not None:
            return
        self.mapa = crear_mapa(*CENTRO_TEMUCO, ZOOM_REPORTE)
        if self.mapa is None:
            return
        contenedor = self.ids.contenedor_mapa
        contenedor.remove_widget(self.ids.mapa_no_disponible)
        contenedor.add_widget(self.mapa, index=len(contenedor.children))  # debajo del pin
        self.mapa.bind(on_map_relocated=self._al_mover_mapa,
                       on_touch_move=self._al_tocar_mapa,
                       on_touch_up=self._al_tocar_mapa)

    def _mover_mapa(self, lat: float, lon: float, zoom: int | None = None) -> None:
        if self.mapa is None:
            return
        if zoom is not None:
            self.mapa.zoom = zoom
        self.mapa.center_on(lat, lon)
        self._movido_por_persona = False

    def _al_tocar_mapa(self, mapa, toque) -> None:
        """Un dedo arrastró el mapa (o tocó dos veces para hacer zoom).
        Así se distingue de los movimientos del código (GPS, centrar):
        comparar coordenadas no sirve, porque el mapa se reacomoda al abrir."""
        if mapa.collide_point(*toque.pos) and (toque.dx or toque.dy or toque.is_double_tap):
            self._movido_por_persona = True

    def _al_mover_mapa(self, *_args) -> None:
        if self._movido_por_persona:
            # La persona movió el mapa: ella manda sobre el GPS.
            self._movido_por_persona = False
            self._controlador.ubicacion.detener()
            self.origen_ubicacion = "mapa"
        if self.origen_ubicacion:
            self._mostrar_estado_ubicacion()
            if self.origen_ubicacion != "calle":  # la calle ya la escribió la persona
                self._programar_busqueda_calle()

    def _mostrar_estado_ubicacion(self) -> None:
        if self.origen_ubicacion == "gps":
            metros = int(self.precision_gps or 0)
            if self.precision_gps and self.precision_gps > PRECISION_GPS_BUENA:
                texto = f"Ubicación aproximada con GPS (±{metros} m). Ajusta el mapa si hace falta."
            else:
                texto = f"Ubicación marcada con GPS (±{metros} m)"
            icono, color = "crosshairs-gps", COLOR_LISTO
        elif self.origen_ubicacion == "mapa":
            texto, icono, color = "Ubicación marcada en el mapa", "map-marker-check", COLOR_LISTO
        elif self.origen_ubicacion == "calle" and self.calle_exacta:
            texto = "Ubicación según la calle escrita. Revisa que el pin esté sobre el daño."
            icono, color = "map-marker-check", COLOR_LISTO
        elif self.origen_ubicacion == "calle":
            texto = "Calle encontrada, pero sin el número: mueve el mapa hasta el punto exacto."
            icono, color = "map-marker-alert-outline", COLOR_PENDIENTE
        else:
            texto = "Ubicación sin marcar: usa el GPS o mueve el mapa"
            icono, color = "map-marker-question-outline", COLOR_PENDIENTE
        self.ids.estado_ubicacion.text = texto
        self.ids.icono_ubicacion.icon = icono
        self.ids.icono_ubicacion.text_color = color
        self.actualizar_progreso()

    # ------------------------------------------------------------------
    # GPS
    # ------------------------------------------------------------------
    def usar_mi_ubicacion(self, automatico: bool = False) -> None:
        servicio = self._controlador.ubicacion
        if servicio.disponible:
            self.ids.estado_ubicacion.text = "Buscando tu ubicación…"
            self.ids.icono_ubicacion.icon = "crosshairs-question"
        servicio.pedir(self._al_obtener_ubicacion, partial(self._al_fallar_ubicacion, automatico))

    def _al_obtener_ubicacion(self, lat, lon, precision, definitiva) -> None:
        if self.manager is None or self.manager.current != self.name:
            return  # la persona ya salió del formulario
        if not dentro_de_zona(lat, lon, LIMITES_TEMUCO):
            # AlertCom es solo para Temuco: no se marca un lugar de afuera
            self._controlador.ubicacion.detener()
            self.registrar_evento("ubicacion_solicitada",
                                  {"pantalla": "report", "metodo": "gps", "resultado": "fuera_de_temuco"})
            self._mostrar_estado_ubicacion()
            mostrar_dialogo("Estás fuera de Temuco",
                            "AlertCom recibe reportes solo de Temuco y Padre Las Casas. "
                            "Mueve el mapa hasta el lugar del daño dentro de la ciudad.",
                            icono="map-marker-off-outline")
            return
        self.origen_ubicacion = "gps"
        self.precision_gps = precision
        self._mover_mapa(lat, lon, zoom=ZOOM_UBICACION)
        self._mostrar_estado_ubicacion()
        self._programar_busqueda_calle()
        if definitiva:
            self.registrar_evento("ubicacion_solicitada", {
                "pantalla": "report", "metodo": "gps",
                "resultado": "ok" if precision <= PRECISION_GPS_BUENA else "aproximada",
            })

    def _al_fallar_ubicacion(self, automatico, motivo, mensaje) -> None:
        self.registrar_evento("ubicacion_solicitada", {"pantalla": "report", "metodo": "gps", "resultado": motivo})
        self._mostrar_estado_ubicacion()
        if automatico:
            mostrar_aviso(mensaje)  # no interrumpe: la persona puede mover el mapa
        else:
            mostrar_dialogo("Ubicación no disponible", mensaje, icono="crosshairs-off")

    # ------------------------------------------------------------------
    # Calle automática
    # ------------------------------------------------------------------
    def _programar_busqueda_calle(self) -> None:
        if self._busqueda_calle is not None:
            self._busqueda_calle.cancel()
        self._busqueda_calle = Clock.schedule_once(self._buscar_calle, ESPERA_BUSCAR_CALLE)

    def _buscar_calle(self, _dt) -> None:
        self._busqueda_calle = None
        if self.mapa is None or not self.origen_ubicacion:
            return
        self._controlador.buscador_calles.buscar(self.mapa.lat, self.mapa.lon, self._al_encontrar_calle)

    def _al_encontrar_calle(self, calle) -> None:
        if not calle:
            return
        campo = self.ids.calle_field
        # Solo se reemplaza si está vacía o si la escribió la app: nunca se
        # borra lo que escribió la persona.
        if campo.text.strip() in ("", self._calle_automatica):
            campo.text = calle
            self._calle_automatica = calle

    # ------------------------------------------------------------------
    # Calle escrita → mapa (el pin va a la calle que escribió la persona)
    # ------------------------------------------------------------------
    def buscar_calle_en_mapa(self, despues=None) -> None:
        calle = " ".join(self.ids.calle_field.text.split())
        if not calle:
            mostrar_aviso("Escribe primero la calle, por ejemplo: Avenida Alemania 450")
            return
        if calle == self._calle_automatica and self.origen_ubicacion:
            mostrar_aviso("El pin ya está en esa calle")  # la calle salió del mismo mapa
            return
        self.ids.estado_ubicacion.text = "Buscando la calle en el mapa…"
        self.ids.icono_ubicacion.icon = "map-search-outline"
        self._controlador.buscador_calles.buscar_lugar(
            calle, partial(self._al_encontrar_lugar, despues))

    def _al_encontrar_lugar(self, despues, lugar) -> None:
        if self.manager is None or self.manager.current != self.name:
            return
        if lugar is None:
            self._mostrar_estado_ubicacion()
            self.registrar_evento("ubicacion_solicitada",
                                  {"pantalla": "report", "metodo": "calle", "resultado": "no_encontrada"})
            mostrar_dialogo(
                "No encontramos esa calle",
                "Revisa cómo está escrita (ej: «Manuel Montt 850») o mueve el mapa hasta el "
                "lugar del daño. Sin internet, la búsqueda no funciona.",
                icono="map-marker-question-outline",
            )
            return
        lat, lon, exacta = lugar
        self._controlador.ubicacion.detener()  # la calle escrita manda sobre el GPS
        self.origen_ubicacion = "calle"
        self.calle_exacta = exacta
        self._mover_mapa(lat, lon, zoom=ZOOM_UBICACION)
        self._mostrar_estado_ubicacion()
        self.registrar_evento("ubicacion_solicitada", {
            "pantalla": "report", "metodo": "calle",
            "resultado": "ok" if exacta else "sin_numero",
        })
        if despues:
            despues()

    # ------------------------------------------------------------------
    # Foto
    # ------------------------------------------------------------------
    def tomar_foto(self) -> None:
        camara = self._controlador.camara
        if camara.disponible:
            camara.tomar_foto(partial(self._al_recibir_foto, "camara"))
        else:
            self._abrir_selector_archivos()

    def elegir_de_galeria(self) -> None:
        self._controlador.camara.elegir_de_galeria(partial(self._al_recibir_foto, "galeria"))

    def _al_recibir_foto(self, origen: str, ruta, error) -> None:
        if error:
            mostrar_dialogo("No se pudo adjuntar la foto", error, icono="camera-off")
            return
        if ruta is None:
            return  # la persona canceló
        carpeta_datos = self._controlador.carpeta_datos
        try:
            nueva = fotos.guardar_foto_reducida(ruta, carpeta_datos)
        except ValueError as problema:
            mostrar_dialogo("No se pudo adjuntar la foto", str(problema), icono="image-broken-variant")
            return
        finally:
            if origen != "archivo":  # copia temporal de la cámara/galería
                Path(ruta).unlink(missing_ok=True)

        if self.foto:  # reemplaza a la foto anterior
            fotos.borrar_foto(carpeta_datos, self.foto)
        self.foto = nueva
        self._mostrar_foto()
        self.actualizar_progreso()
        self.registrar_evento("foto_adjuntada", {"origen": origen})

    def _mostrar_foto(self) -> None:
        ruta = fotos.ruta_foto(self._controlador.carpeta_datos, self.foto) if self.foto else None
        vista_previa = self.ids.foto_preview
        if ruta is None:
            vista_previa.source = ""
            vista_previa.opacity = 0
            self.ids.foto_vacia.opacity = 1
            self.ids.texto_boton_camara.text = "Tomar foto" if platform == "android" else "Elegir imagen"
        else:
            vista_previa.source = str(ruta)
            vista_previa.opacity = 1
            self.ids.foto_vacia.opacity = 0
            self.ids.texto_boton_camara.text = "Cambiar foto"

    # --- Computador: selector de archivos de KivyMD ---
    def _abrir_selector_archivos(self) -> None:
        from kivymd.uix.filemanager import MDFileManager

        if self._selector_archivos is None:
            self._selector_archivos = MDFileManager(
                exit_manager=self._cerrar_selector,
                select_path=self._al_elegir_archivo,
                ext=EXTENSIONES_IMAGEN,
                preview=False,
            )
        imagenes = Path.home() / "Pictures"
        self._selector_archivos.show(str(imagenes if imagenes.is_dir() else Path.home()))

    def _al_elegir_archivo(self, ruta: str) -> None:
        self._cerrar_selector()
        if Path(ruta).suffix.lower() in EXTENSIONES_IMAGEN and Path(ruta).is_file():
            self._al_recibir_foto("archivo", Path(ruta), None)
        else:
            mostrar_aviso("Elige un archivo de imagen (.jpg o .png)")

    def _cerrar_selector(self, *_args) -> None:
        if self._selector_archivos is not None:
            self._selector_archivos.close()

    # ------------------------------------------------------------------
    # Tipo y gravedad: pastillas que se tocan
    # ------------------------------------------------------------------
    def _crear_pastillas(self) -> None:
        for tipo in TIPOS_DANO:
            pastilla = Pastilla(texto=tipo, valor=tipo, icono=ICONO_TIPO.get(tipo, "alert-circle-outline"))
            pastilla.bind(on_release=lambda p: self.elegir_tipo(p.valor))
            self.ids.grupo_tipo.add_widget(pastilla)
        for gravedad in GRAVEDADES:
            icono, color = ESTILO_GRAVEDAD.get(gravedad, ("alert-circle-outline", [1, 0.6, 0, 1]))
            pastilla = Pastilla(texto=gravedad, valor=gravedad, icono=icono, color=color)
            pastilla.bind(on_release=lambda p: self.elegir_gravedad(p.valor))
            self.ids.grupo_gravedad.add_widget(pastilla)

    @staticmethod
    def _marcar(grupo, valor) -> None:
        for pastilla in grupo.children:
            pastilla.seleccionada = pastilla.valor == valor

    def elegir_tipo(self, valor: str) -> None:
        self.tipo = valor
        self._marcar(self.ids.grupo_tipo, valor)
        self.actualizar_progreso()

    def elegir_gravedad(self, valor: str) -> None:
        self.gravedad = valor
        self._marcar(self.ids.grupo_gravedad, valor)
        self.actualizar_progreso()

    # ------------------------------------------------------------------
    # Avance del formulario
    # ------------------------------------------------------------------
    def _pendientes(self) -> list[str]:
        faltan = []
        if not self.origen_ubicacion and self.mapa is not None:
            faltan.append("ubicación")
        if not self.ids.calle_field.text.strip():
            faltan.append("calle")
        if not self.tipo:
            faltan.append("tipo")
        if not self.gravedad:
            faltan.append("gravedad")
        return faltan

    def actualizar_progreso(self) -> None:
        faltan = self._pendientes()
        listos = 4 - len(faltan)
        self.ids.cuenta_progreso.text = f"{listos}/4"
        self.ids.barra_progreso.animar_a(listos / 4)
        if not faltan:
            self.ids.texto_progreso.text = "¡Todo listo! Ya puedes enviar" + ("" if self.foto else " (la foto ayuda)")
            self.ids.barra_progreso.color = COLOR_LISTO
            self.ids.cuenta_progreso.text_color = COLOR_LISTO
        else:
            lista = faltan[0] if len(faltan) == 1 else ", ".join(faltan[:-1]) + " y " + faltan[-1]
            self.ids.texto_progreso.text = f"Falta: {lista}"
            self.ids.barra_progreso.color = [1, 0.6, 0, 1]
            self.ids.cuenta_progreso.text_color = [1, 0.6, 0, 1]

    # ------------------------------------------------------------------
    # Envío
    # ------------------------------------------------------------------
    def _ubicacion_marcada(self) -> str | None:
        if self.mapa is None:  # sin mapview instalado (solo computador)
            return "{}, {}".format(*CENTRO_TEMUCO)
        if not self.origen_ubicacion:
            return None
        return f"{self.mapa.lat:.6f}, {self.mapa.lon:.6f}"

    def enviar_reporte(self) -> None:
        # Escribió la calle pero no marcó el mapa: primero se busca la calle
        # y se le muestra dónde quedó el pin, para que confirme antes de enviar.
        if self.mapa is not None and not self.origen_ubicacion and self.ids.calle_field.text.strip():
            self.buscar_calle_en_mapa(despues=lambda: mostrar_aviso(
                "Revisa el pin y toca Enviar otra vez"))
            return
        usuario = self.auth_controller.usuario_actual if self.auth_controller else None
        try:
            incidente = self.incidente_controller.crear_incidente(
                tipo=self.tipo,
                gravedad=self.gravedad,
                descripcion=self.ids.description_field.text,
                foto=self.foto,
                ubicacion=self._ubicacion_marcada(),
                calle=self.ids.calle_field.text,
                usuario_id=usuario.uid if usuario else None,
                # El funcionario publica directo; el vecino espera su revisión
                confirmado=bool(usuario and usuario.es_municipal),
            )
        except ValueError as error:
            sacudir(self.ids.fila_progreso)
            vibrar(80)
            mostrar_dialogo("Falta información", str(error), icono="clipboard-alert-outline")
            return

        self.foto = None  # ya pertenece al reporte: no se borra al limpiar
        mostrar_exito(
            "¡Reporte enviado!",
            f"#{incidente.id_incidente} · {incidente.tipo_incidente} en {incidente.calle}\n"
            + ("Te avisaremos cuando cambie su estado." if incidente.confirmado else
               "El municipio lo revisará: cuando lo confirme, aparecerá en el mapa de todos."),
            al_terminar=lambda: MDApp.get_running_app().navegacion.ir_a("history", "left"),
        )
