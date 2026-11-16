# =============================================================================
# AlertCom - Capa de Modelos (MVC)
# =============================================================================
# Clases de dominio en Python puro: representan el mundo real del proyecto
# A+S (vecinos, baches y los eventos de uso que medimos). NO importan
# Kivy/KivyMD ni nada gráfico, por eso se pueden probar sin abrir la app
# (ver pruebas/test_flujo_e3.py).
# =============================================================================

from models.usuario import Usuario
from models.incidente import Incidente, ESTADOS
from models.evento import Evento, CATALOGO_EVENTOS

__all__ = ["Usuario", "Incidente", "ESTADOS", "Evento", "CATALOGO_EVENTOS"]
