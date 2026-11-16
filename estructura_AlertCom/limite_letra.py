# =============================================================================
# AlertCom - Tope a la letra grande del teléfono
# =============================================================================
# Si en Android la persona tiene la letra muy grande (Ajustes → Pantalla →
# Tamaño de fuente), los textos de AlertCom no cabían en sus espacios: títulos
# cortados, filtros fuera de la pantalla, íconos encima del texto.
#
# Aquí se limita ese factor a LETRA_SISTEMA_MAXIMA (config.py). Para letra más
# grande está el control propio de la app: Ajustes → Tamaño de letra.
#
# Se importa en main.py ANTES de KivyMD, porque KivyMD calcula el tamaño de
# sus textos en el momento en que se importa.
# =============================================================================

from kivy.metrics import Metrics

from config import LETRA_SISTEMA_MAXIMA

if Metrics.fontscale > LETRA_SISTEMA_MAXIMA:
    Metrics.fontscale = LETRA_SISTEMA_MAXIMA
