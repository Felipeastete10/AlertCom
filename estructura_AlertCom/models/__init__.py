# =============================================================================
# AlertCom - Capa de Modelos (MVC)
# =============================================================================
# Clases de dominio en Python puro: representan el mundo real del proyecto
# A+S (vecinos y baches). NO importan Kivy/KivyMD ni nada gráfico, por eso
# se pueden probar sin abrir la app (ver pruebas/test_flujo_e3.py).
# =============================================================================

from models.usuario import Usuario
from models.incidente import Incidente, ESTADOS

__all__ = ["Usuario", "Incidente", "ESTADOS"]
