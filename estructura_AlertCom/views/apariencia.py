# =============================================================================
# AlertCom - Apariencia elegida por la persona (tamaño de letra y fondo)
# =============================================================================
# • Tamaño de letra: KivyMD toma el tamaño de cada texto de
#   app.theme_cls.font_styles. Si se reemplaza ese diccionario por uno
#   escalado, TODOS los textos de la app cambian al instante.
#   app.factor_letra guarda el factor elegido: lo usan los textos con tope
#   (títulos, botones, barra de navegación) en _comunes.kv.
# • Letra del teléfono: main.py la limita a LETRA_SISTEMA_MAXIMA (config.py).
# • Fondo: las pantallas usan app.color_fondo; al cambiarlo, cambian todas.
# Las elecciones se guardan en preferencias.json (controllers/preferencias.py).
# =============================================================================

from copy import deepcopy

from kivymd.font_definitions import theme_font_styles

from config import FONDOS, TAMANOS_LETRA

_ESTILOS_BASE = deepcopy(theme_font_styles)   # tamaños originales (factor 1)
FACTORES = {clave: factor for clave, _, factor in TAMANOS_LETRA}
COLORES_FONDO = {clave: color for clave, _, color in FONDOS}


def aplicar_tamano_letra(app, clave: str) -> None:
    factor = FACTORES.get(clave, 1.0)
    app.factor_letra = factor
    # Copia simple (el diccionario de KivyMD no admite deepcopy)
    escalados = {estilo: {rol: dict(datos) for rol, datos in roles.items()}
                 for estilo, roles in app.theme_cls.font_styles.items()}
    for estilo, roles in _ESTILOS_BASE.items():
        if estilo == "Icon":          # los íconos mantienen su tamaño
            continue
        for rol, datos in roles.items():
            escalados[estilo][rol]["font-size"] = datos["font-size"] * factor
    app.theme_cls.font_styles = escalados  # nuevo diccionario → la app se actualiza


def aplicar_fondo(app, clave: str) -> None:
    color = COLORES_FONDO.get(clave)
    app.color_fondo = color if color else app.theme_cls.surfaceColor


def aplicar_apariencia(app, preferencias) -> None:
    """Al abrir la app: aplica lo que la persona eligió la última vez."""
    aplicar_tamano_letra(app, preferencias.obtener("tamano_letra", "normal"))
    aplicar_fondo(app, preferencias.obtener("fondo", "original"))
