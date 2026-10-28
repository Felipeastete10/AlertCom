# =============================================================================
# AlertCom - Capa de Controladores / Lógica (MVC)
# =============================================================================
# Conectan las acciones de la interfaz con los modelos y manejan el flujo:
#   • AuthController         → login, registro y sesión (usuarios.json)
#   • IncidenteController    → reportes de baches (incidentes.json)
#   • AlmacenamientoJSON     → lectura/escritura segura de JSON
#   • Notificador            → notificaciones locales con Plyer
#   • ConfiguracionRemota    → textos remotos con UrlRequest + fallback
#   • AppController          → (app_controller.py) arma todo lo anterior; se
#                              importa directo desde main.py porque usa Kivy
#
# Ningún controlador navega entre pantallas ni crea widgets.
# Este __init__ no carga Kivy: las pruebas pueden importar la capa sin abrir la app.
# =============================================================================

from controllers.almacenamiento_json import AlmacenamientoJSON
from controllers.notificador import Notificador
from controllers.auth_controller import AuthController
from controllers.incidente_controller import IncidenteController
from controllers.config_remota import ConfiguracionRemota, filtrar_config

__all__ = [
    "AlmacenamientoJSON",
    "Notificador",
    "AuthController",
    "IncidenteController",
    "ConfiguracionRemota",
    "filtrar_config",
]
