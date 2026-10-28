# =============================================================================
# AlertCom - Notificaciones locales con Plyer (Sesión 21)
# =============================================================================
# Plyer da acceso al hardware nativo con el mismo código en Windows, Android,
# Linux y macOS:   pip install plyer
#
# Esta clase envuelve notification.notify(title=..., message=..., timeout=...)
# para que la lógica de negocio (IncidenteController) la llame SOLO cuando
# ocurre un cambio de estado importante. Las vistas nunca notifican directo.
#
# Si Plyer no está instalado o la plataforma no lo soporta, NO se cae la app:
# se registra la notificación en el log y se sigue funcionando.
# =============================================================================

import logging

try:
    from plyer import notification
except ImportError:  # Plyer no instalado: modo silencioso
    notification = None

log = logging.getLogger("alertcom.notificaciones")


class Notificador:
    """Envía notificaciones locales del sistema operativo."""

    def __init__(self, nombre_app: str = "AlertCom", habilitado: bool = True) -> None:
        self.nombre_app = nombre_app
        self.habilitado = habilitado

    def notificar(self, titulo: str, mensaje: str, timeout: int = 5) -> bool:
        """
        Muestra una notificación. Devuelve True si se envió al sistema.
        """
        if not self.habilitado or notification is None:
            log.info("[Notificación simulada] %s: %s", titulo, mensaje)
            return False

        try:
            notification.notify(
                title=titulo,
                message=mensaje,
                app_name=self.nombre_app,
                timeout=timeout,
            )
            log.info("Notificación enviada: %s", titulo)
            return True
        except Exception as error:  # NotImplementedError en plataformas sin soporte
            log.warning("No se pudo mostrar la notificación (%s): %s", type(error).__name__, error)
            return False
