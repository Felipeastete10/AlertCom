# =============================================================================
# AlertCom - Capa de Controladores / Lógica (MVC)
# =============================================================================
# Conectan las acciones de la interfaz con los modelos y manejan el flujo:
#   • AuthController         → login, registro y sesión (usuarios.json)
#   • IncidenteController    → reportes de baches (incidentes.json)
#   • AlmacenamientoJSON     → lectura/escritura segura de JSON
#   • Notificador            → notificaciones locales con Plyer
#   • ConfiguracionRemota    → textos remotos con UrlRequest + fallback
#   • RegistroEventos        → eventos de uso en eventos.jsonl (analítica)
#   • analitica (módulo)     → métricas y KPIs calculados desde los eventos
#   • fotos (módulo)         → copia reducida y sin metadatos de cada foto
#   • direcciones (módulo)   → calle a partir de coordenadas (Nominatim)
#   • ServicioUbicacion      → (ubicacion.py) GPS del teléfono con Plyer
#   • Camara                 → (camara.py) cámara y galería de Android
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
from controllers.registro_eventos import RegistroEventos, RegistroNulo
from controllers import analitica

__all__ = [
    "AlmacenamientoJSON",
    "Notificador",
    "AuthController",
    "IncidenteController",
    "ConfiguracionRemota",
    "filtrar_config",
    "RegistroEventos",
    "RegistroNulo",
    "analitica",
]
