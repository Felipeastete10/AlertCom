# =============================================================================
# AlertCom - Controlador principal de la aplicación
# =============================================================================
# Todo lo que antes estaba en main.py y NO es interfaz:
#   • Elegir la carpeta de datos (computador o Android).
#   • Configurar el registro (log) y guardar los errores no controlados.
#   • Crear UNA vez cada controlador (inyección de dependencias).
#   • Pedir la configuración remota y aplicarla a la app.
#
# No crea widgets ni cambia de pantalla (eso es views/).
# =============================================================================

import logging
from pathlib import Path

from kivy.base import ExceptionHandler, ExceptionManager
from kivy.utils import platform

import config
from controllers.almacenamiento_json import AlmacenamientoJSON
from controllers.auth_controller import AuthController
from controllers.config_remota import ConfiguracionRemota
from controllers.incidente_controller import IncidenteController
from controllers.notificador import Notificador

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

        # --- Controladores (se crean una sola vez y se comparten) ---
        self.auth = AuthController(
            AlmacenamientoJSON(self.carpeta_datos / config.ARCHIVO_USUARIOS)
        )
        self.incidentes = IncidenteController(
            AlmacenamientoJSON(self.carpeta_datos / config.ARCHIVO_INCIDENTES),
            notificador=Notificador(nombre_app="AlertCom"),
        )
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
        self.config_remota.cargar()

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
