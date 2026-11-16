# =============================================================================
# AlertCom - Controlador principal de la aplicación
# =============================================================================
# Todo lo que antes estaba en main.py y NO es interfaz:
#   • Elegir la carpeta de datos (computador o Android).
#   • Configurar el registro (log) y guardar los errores no controlados.
#   • Crear UNA vez cada controlador (inyección de dependencias).
#   • Pedir la configuración remota y aplicarla a la app.
#   • Crear el registro de eventos (analítica) y pedir los permisos de
#     Android que la app necesita.
#   • Crear los servicios de hardware: GPS, cámara y búsqueda de calles.
#   • Conectar los reportes con la nube (Firebase), si hay URL configurada.
#
# No crea widgets ni cambia de pantalla (eso es views/).
# =============================================================================

import logging
from pathlib import Path

from kivy.base import ExceptionHandler, ExceptionManager
from kivy.clock import Clock
from kivy.utils import platform

import config
from controllers.almacenamiento_json import AlmacenamientoJSON
from controllers.auth_controller import AuthController
from controllers.camara import Camara
from controllers.config_remota import ConfiguracionRemota
from controllers.direcciones import BuscadorCalles
from controllers.incidente_controller import IncidenteController
from controllers.nube import ClienteFirebase, SincronizadorReportes
from controllers.notificador import Notificador
from controllers.preferencias import ARCHIVO_PREFERENCIAS, Preferencias
from controllers.registro_eventos import RegistroEventos
from controllers.ubicacion import ServicioUbicacion

log = logging.getLogger("alertcom")


class RegistroDeErrores(ExceptionHandler):
    """Guarda en alertcom.log el traceback de cualquier error no controlado.
    No lo oculta: la app se detiene igual, pero queda el registro."""

    def handle_exception(self, excepcion):
        log.critical("Error no controlado", exc_info=excepcion)
        return ExceptionManager.RAISE


class AppController:
    """Arma la capa de lógica y la conecta con la app."""

    def __init__(self, app) -> None:
        self.app = app
        self.carpeta_datos = self._preparar_carpeta_datos()
        self._configurar_registro()
        ExceptionManager.add_handler(RegistroDeErrores())

        # --- Analítica: un registro por apertura de la app (= una sesión) ---
        self.eventos = RegistroEventos(self.carpeta_datos)
        self.eventos.registrar("app_abierta", {"plataforma": platform, "version": config.VERSION_APP})

        # --- Controladores (se crean una sola vez y se comparten) ---
        self.auth = AuthController(
            AlmacenamientoJSON(self.carpeta_datos / config.ARCHIVO_USUARIOS),
            eventos=self.eventos,
        )
        self.incidentes = IncidenteController(
            AlmacenamientoJSON(self.carpeta_datos / config.ARCHIVO_INCIDENTES),
            notificador=Notificador(nombre_app="AlertCom"),
            eventos=self.eventos,
        )
        # Reportes de versiones anteriores: el autor pasa de número a uid
        self.incidentes.migrar_autores({u.id_usuario: u.uid for u in self.auth.usuarios})

        # --- Preferencias de la persona (letra, fondo, analítica) ---
        self.preferencias = Preferencias(self.carpeta_datos / ARCHIVO_PREFERENCIAS)

        # --- Nube: reportes compartidos entre todos los teléfonos ---
        self.nube = None
        if config.URL_FIREBASE:
            self.nube = SincronizadorReportes(
                self.incidentes,
                ClienteFirebase(config.URL_FIREBASE),
                self.carpeta_datos,
                uid_actual=lambda: self.auth.usuario_actual.uid if self.auth.usuario_actual else None,
                al_actualizar=self._refrescar_pantalla,
            )
            if not self.preferencias.obtener("nube_iniciada", False):
                self.nube.subir_todo_lo_local()   # lo que ya había en el teléfono
                self.preferencias.guardar("nube_iniciada", True)

        # --- Hardware y servicios de ubicación (Android; en PC avisan) ---
        self.ubicacion = ServicioUbicacion()
        self.camara = Camara(self.carpeta_datos / "temporal")
        self.buscador_calles = BuscadorCalles()

        self.config_remota = ConfiguracionRemota(
            url=config.URL_CONFIG_REMOTA,
            claves_permitidas=config.VALORES_POR_DEFECTO.keys(),
            al_actualizar=self.aplicar_config_remota,
            timeout=config.TIEMPO_ESPERA_RED,
            largo_maximo=config.LARGO_MAX_TEXTO_REMOTO,
        )
        log.info("AlertCom iniciado. Datos en: %s", self.carpeta_datos)

    def iniciar(self) -> None:
        """Se llama cuando la ventana ya es visible (on_start)."""
        self._pedir_permisos_android()
        self.config_remota.cargar()
        if self.nube is not None:
            self.nube.sincronizar()
            Clock.schedule_interval(lambda _dt: self.sincronizar(),
                                    config.SEGUNDOS_ENTRE_SINCRONIZACIONES)

    def sincronizar(self, al_terminar=None) -> None:
        """Trae los reportes de los demás (y sube los propios pendientes)."""
        if self.nube is not None:
            self.nube.sincronizar(al_terminar)
        elif al_terminar:
            al_terminar(False)

    def _refrescar_pantalla(self) -> None:
        """Llegaron reportes nuevos: si se está viendo el mapa o el
        historial, se vuelven a dibujar."""
        gestor = self.app.root
        pantalla = gestor.current_screen if gestor is not None else None
        if pantalla is not None and hasattr(pantalla, "refrescar"):
            pantalla.refrescar()

    def _pedir_permisos_android(self) -> None:
        """Android 13+ exige pedir permiso para mostrar notificaciones.
        Protegido con try/except: si falla, la app sigue sin notificaciones."""
        if platform != "android":
            return
        try:
            from android.permissions import Permission, request_permissions
            request_permissions([Permission.POST_NOTIFICATIONS])
        except Exception as error:  # módulo o permiso no disponible
            log.warning("No se pudo pedir el permiso de notificaciones: %s", error)

    # ------------------------------------------------------------------
    # Configuración
    # ------------------------------------------------------------------
    def _preparar_carpeta_datos(self) -> Path:
        """Computador: estructura_AlertCom/datos · Android: carpeta privada."""
        carpeta = Path(self.app.user_data_dir) if platform == "android" else config.CARPETA_DATOS
        carpeta.mkdir(parents=True, exist_ok=True)
        return carpeta

    def _configurar_registro(self) -> None:
        """Mensajes a la consola (vía Kivy) y a datos/alertcom.log."""
        log.setLevel(logging.INFO)
        if not any(isinstance(h, logging.FileHandler) for h in log.handlers):
            archivo = logging.FileHandler(self.carpeta_datos / config.ARCHIVO_LOG, encoding="utf-8")
            archivo.setFormatter(
                logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
            )
            log.addHandler(archivo)

    def aplicar_config_remota(self, datos: dict) -> None:
        """Callback de ConfiguracionRemota. Cambiar una StringProperty de la
        app actualiza el KV automáticamente (binding)."""
        for clave, valor in datos.items():
            setattr(self.app, clave, valor)
        self.app.origen_config = "Textos actualizados desde la nube"
        self.eventos.registrar("config_remota_aplicada", {"claves": len(datos)})
