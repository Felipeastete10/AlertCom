# =============================================================================
# AlertCom - Paquete de Modelos (MVC)
# =============================================================================
# Capa de dominio. Contiene únicamente clases de datos y reglas de negocio
# pura. No importa módulos de Kivy/KivyMD ni de la interfaz gráfica.
# =============================================================================

from models.usuario import Usuario
from models.incidente import Incidente

__all__ = ["Usuario", "Incidente"]
