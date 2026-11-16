# =============================================================================
# AlertCom - Ubicación actual del usuario (GPS del teléfono)
# =============================================================================
# Pasos en Android:
#   1. Pedir el permiso de ubicación (la primera vez aparece el aviso).
#   2. Revisar que la ubicación del teléfono esté encendida.
#   3. Usar la última ubicación conocida (si tiene menos de 2 minutos) para
#      mover el mapa de inmediato.
#   4. Escuchar el GPS hasta tener una precisión de 30 m o menos, o hasta
#      20 segundos. Después se apaga el GPS (ahorra batería).
#
# ¿Por qué no plyer.gps? En Android 12 o superior el teléfono entrega las
# ubicaciones como una LISTA (onLocationChanged(List)) y Plyer solo sabe
# recibir una sola: la ubicación nunca llegaba y la app podía cerrarse.
# El "escuchador" de abajo (_crear_escuchador) recibe las dos formas.
#
# En el computador no hay GPS: se avisa y el usuario mueve el mapa a mano.
# Todo el acceso al hardware está protegido con try/except: si algo falla,
# se informa con un mensaje claro y la app sigue funcionando.
#
# Los resultados se entregan con dos funciones:
#   al_obtener(lat, lon, precision_m, definitiva)   definitiva=False → aproximada
#   al_fallar(motivo, mensaje)
# =============================================================================

import logging
import time

from kivy.clock import Clock, mainthread
from kivy.utils import platform

from config import PRECISION_GPS_BUENA, TIEMPO_MAXIMO_GPS

log = logging.getLogger("alertcom.ubicacion")

EDAD_MAXIMA_ULTIMA_UBICACION = 120  # segundos

MENSAJES = {
    "no_disponible": "Este equipo no tiene GPS. Mueve el mapa hasta que el pin quede sobre el daño.",
    "sin_permiso": ("AlertCom no tiene permiso de ubicación. Puedes darlo en Ajustes → Apps → "
                    "AlertCom → Permisos, o mover el mapa a mano."),
    "sin_precision": ("Para marcar el bache se necesita la ubicación PRECISA. Vuelve a intentarlo y "
                      "elige «Precisa» en el aviso, o mueve el mapa a mano."),
    "ubicacion_apagada": "La ubicación del teléfono está apagada. Actívala y vuelve a intentarlo.",
    "sin_senal": "No se encontró señal GPS. Sal a un lugar abierto o mueve el mapa a mano.",
    "error": "No se pudo usar el GPS. Mueve el mapa hasta que el pin quede sobre el daño.",
}


def _crear_escuchador(al_recibir):
    """Objeto Java que Android llama cada vez que hay una ubicación nueva.

    Se crea solo en Android (necesita pyjnius). Ningún error puede salir de
    estas funciones: si saliera, Android cerraría la app.
    """
    from jnius import PythonJavaClass, java_method

    class Escuchador(PythonJavaClass):
        __javainterfaces__ = ["android/location/LocationListener"]

        def __init__(self):
            super().__init__()

        def _entregar(self, ubicacion):
            try:
                if ubicacion is not None:
                    # Se copian los números aquí (hilo de Android) y se
                    # entregan como datos simples al hilo de Kivy.
                    al_recibir(float(ubicacion.getLatitude()),
                               float(ubicacion.getLongitude()),
                               float(ubicacion.getAccuracy()) if ubicacion.hasAccuracy() else None)
            except Exception as error:
                log.warning("Ubicación recibida con error: %s", error)

        @java_method("(Landroid/location/Location;)V")
        def onLocationChanged(self, ubicacion):
            self._entregar(ubicacion)

        # Android 12+: varias ubicaciones juntas (la última es la más nueva)
        @java_method("(Ljava/util/List;)V", name="onLocationChanged")
        def onLocationChangedLista(self, lista):
            try:
                if lista is not None and lista.size() > 0:
                    self._entregar(lista.get(lista.size() - 1))
            except Exception as error:
                log.warning("Lista de ubicaciones con error: %s", error)

        @java_method("(I)V")
        def onFlushComplete(self, _codigo):
            pass

        @java_method("(Ljava/lang/String;)V")
        def onProviderEnabled(self, _proveedor):
            pass

        @java_method("(Ljava/lang/String;)V")
        def onProviderDisabled(self, _proveedor):
            pass

        @java_method("(Ljava/lang/String;ILandroid/os/Bundle;)V")
        def onStatusChanged(self, _proveedor, _estado, _extras):
            pass

    return Escuchador()


class ServicioUbicacion:
    """Pide UNA ubicación al GPS y luego lo apaga."""

    def __init__(self, precision_buena: float = PRECISION_GPS_BUENA,
                 tiempo_maximo: float = TIEMPO_MAXIMO_GPS) -> None:
        self.precision_buena = precision_buena
        self.tiempo_maximo = tiempo_maximo
        self.buscando = False
        self._al_obtener = None
        self._al_fallar = None
        self._mejor = None          # (lat, lon, precision)
        self._temporizador = None
        self._gestor = None         # LocationManager de Android
        self._escuchador = None     # se guarda: si Python lo borrara, la app se cae

    @property
    def disponible(self) -> bool:
        return platform == "android"

    # ------------------------------------------------------------------
    # Uso
    # ------------------------------------------------------------------
    def pedir(self, al_obtener, al_fallar) -> None:
        self._al_obtener, self._al_fallar = al_obtener, al_fallar
        if not self.disponible:
            self._fallar("no_disponible")
            return
        if self.buscando:
            return
        self.buscando = True
        self._mejor = None
        try:
            from android.permissions import Permission, check_permission, request_permissions
            if check_permission(Permission.ACCESS_FINE_LOCATION):
                self._iniciar_gps()
            else:
                request_permissions(
                    [Permission.ACCESS_FINE_LOCATION, Permission.ACCESS_COARSE_LOCATION],
                    self._al_responder_permiso,
                )
        except Exception as error:
            log.warning("Error al pedir el permiso de ubicación: %s", error)
            self._fallar("error")

    def detener(self) -> None:
        """Apaga el GPS (al salir de la pantalla o al terminar)."""
        if self._temporizador is not None:
            self._temporizador.cancel()
            self._temporizador = None
        if self._gestor is not None and self._escuchador is not None:
            try:
                self._gestor.removeUpdates(self._escuchador)
            except Exception as error:
                log.info("No se pudo detener el GPS: %s", error)
        self.buscando = False

    # ------------------------------------------------------------------
    # Android
    # ------------------------------------------------------------------
    @mainthread
    def _al_responder_permiso(self, _permisos, concedidos) -> None:
        # concedidos va en el mismo orden: [precisa, aproximada]
        try:
            concedidos = list(concedidos or [])
            if concedidos and concedidos[0]:
                self._iniciar_gps()
            elif any(concedidos):
                # Android 12+: con solo "aproximada" el sensor GPS no se puede usar.
                self._fallar("sin_precision")
            else:
                self._fallar("sin_permiso")
        except Exception as error:
            log.warning("Error con la respuesta del permiso: %s", error)
            self._fallar("error")

    def _iniciar_gps(self) -> None:
        if not self.buscando:  # la persona salió mientras respondía el permiso
            return
        try:
            from jnius import autoclass

            actividad = autoclass("org.kivy.android.PythonActivity").mActivity
            Context = autoclass("android.content.Context")
            Looper = autoclass("android.os.Looper")
            gestor = actividad.getSystemService(Context.LOCATION_SERVICE)
            self._gestor = gestor

            proveedores = [p for p in ("gps", "network") if gestor.isProviderEnabled(p)]
            if not proveedores:
                self._fallar("ubicacion_apagada")
                return

            self._usar_ultima_conocida(gestor)
            if not self.buscando:  # la última ubicación ya era precisa
                return

            if self._escuchador is None:
                self._escuchador = _crear_escuchador(self._al_recibir_ubicacion)
            for proveedor in proveedores:
                # cada 1 s, sin distancia mínima; avisa en el hilo principal de Android
                gestor.requestLocationUpdates(proveedor, 1000, 0.0, self._escuchador,
                                              Looper.getMainLooper())
            self._temporizador = Clock.schedule_once(self._al_vencer_tiempo, self.tiempo_maximo)
        except Exception as error:
            log.warning("No se pudo iniciar el GPS: %s", error)
            self._fallar("error")

    def _usar_ultima_conocida(self, gestor) -> None:
        """Mueve el mapa al tiro con la última ubicación, si es reciente."""
        ahora_ms = time.time() * 1000
        for proveedor in ("gps", "network"):
            try:
                ubicacion = gestor.getLastKnownLocation(proveedor)
            except Exception:
                ubicacion = None
            if ubicacion is None:
                continue
            try:
                reciente = (ahora_ms - ubicacion.getTime()) / 1000 <= EDAD_MAXIMA_ULTIMA_UBICACION
                if reciente:
                    self._procesar(float(ubicacion.getLatitude()), float(ubicacion.getLongitude()),
                                   float(ubicacion.getAccuracy()))
                    return
            except Exception as error:
                log.info("Última ubicación no usable: %s", error)

    @mainthread
    def _al_recibir_ubicacion(self, lat, lon, precision) -> None:
        # Android llama desde su propio hilo: @mainthread lo pasa al de Kivy.
        if not self.buscando:
            return
        try:
            self._procesar(lat, lon, precision)
        except Exception as error:
            log.warning("No se pudo usar la ubicación recibida: %s", error)
            self._fallar("error")

    def _procesar(self, lat, lon, precision) -> None:
        if lat is None or lon is None:
            return
        precision = float(precision) if precision else 9999.0
        if self._mejor is None or precision < self._mejor[2]:
            self._mejor = (lat, lon, precision)

        if precision <= self.precision_buena:
            self._terminar_con_exito(definitiva=True)
        elif self._al_obtener:
            self._al_obtener(lat, lon, precision, False)  # aproximada: el mapa se mueve igual

    def _al_vencer_tiempo(self, _dt) -> None:
        self._temporizador = None
        if self._mejor is not None:
            self._terminar_con_exito(definitiva=True)
        else:
            self._fallar("sin_senal")

    def _terminar_con_exito(self, definitiva: bool) -> None:
        lat, lon, precision = self._mejor
        self.detener()
        if self._al_obtener:
            self._al_obtener(lat, lon, precision, definitiva)

    def _fallar(self, motivo: str) -> None:
        self.detener()
        log.info("Ubicación no disponible: %s", motivo)
        if self._al_fallar:
            self._al_fallar(motivo, MENSAJES[motivo])
