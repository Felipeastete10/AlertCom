# =============================================================================
# AlertCom - Librerías incluidas dentro de la app
# =============================================================================
# KivyMD 2.0 necesita materialyoucolor >= 3.0.3, pero Buildozer (python-for-
# android) solo trae una receta con la versión 2.0.10, que NO tiene el módulo
# "dynamiccolor.color_spec". Con esa versión la app se cerraba al abrir:
#     ModuleNotFoundError: No module named 'materialyoucolor.dynamiccolor.color_spec'
#
# Solución: incluimos aquí materialyoucolor 3.0.4 en Python puro (licencia en
# librerias/materialyoucolor/LICENSE) y ponemos esta carpeta PRIMERA en la
# lista de búsqueda de Python, antes de que se cargue KivyMD.
# En Android la carpeta de la app queda al final de esa lista, por eso hay que
# hacerlo a mano. La parte compilada (quantize) es opcional: KivyMD no la usa.
#
# 2) materialshapes: KivyMD lo carga al importar sus listas (vía FitImage) y
#    necesita cairo, que no existe en Android. Si cairo no está disponible,
#    se usa un sustituto liviano (librerias/sustitutos/), suficiente porque
#    AlertCom no usa imágenes con formas. En el computador, con cairo
#    instalado, se sigue usando el materialshapes original.
# =============================================================================

import os
import sys

_CARPETA = os.path.dirname(os.path.abspath(__file__))
if _CARPETA not in sys.path:
    sys.path.insert(0, _CARPETA)

try:
    import cairo  # noqa: F401
except ImportError:
    _SUSTITUTOS = os.path.join(_CARPETA, "sustitutos")
    if _SUSTITUTOS not in sys.path:
        sys.path.insert(0, _SUSTITUTOS)
