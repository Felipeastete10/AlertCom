# =============================================================================
# AlertCom - Paquete de Controladores (MVC)
# =============================================================================
# Capa de lógica de negocio. Orquesta entre modelos y vistas.
# No importa módulos de Kivy/KivyMD ni de la interfaz gráfica.
# =============================================================================

from controllers.auth_controller import AuthController
from controllers.incidente_controller import IncidenteController

__all__ = ["AuthController", "IncidenteController"]
