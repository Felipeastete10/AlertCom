# =============================================================================
# AlertCom - Ajustes de compatibilidad para Android
# =============================================================================
# En el teléfono (Motorola, GPU Adreno 610, Android 11) la app se cerraba con
# un error nativo:
#     Fatal signal 11 (SIGSEGV) ... kivy/graphics/vbo.so ... fbo.so
#
# Causa: el efecto "ripple" de Material 3 (la onda al tocar un botón) dibuja
# con un Fbo (imagen oculta) y un shader, y eso se cae en esa GPU.
#   1) Primer cierre: al tocar "Iniciar sesión" (se dibujaba la onda).
#   2) Segundo cierre: al pedir la ubicación. KivyMD crea el Fbo en CADA
#      botón aunque la onda esté apagada; el aviso de permiso pone la app en
#      pausa y, al volver, la GPU se caía al redibujar esos Fbo. Las sombras
#      de KivyMD (BoxShadow) también usan un Fbo cada una.
#
# Solución: en Android no se crea ningún Fbo:
#   - los botones de KivyMD no crean la onda (funcionan igual, sin la onda);
#   - las sombras se reemplazan por una "sombra vacía" que no dibuja nada
#     (con el fondo oscuro de AlertCom casi no se notaban).
# En el computador no se cambia nada.
# =============================================================================

from kivy.factory import Factory
from kivy.graphics.instructions import Instruction
from kivy.lang import Builder
from kivy.utils import platform

# Una regla para la clase base M3CommonRipple alcanza a TODOS los widgets que
# la heredan: botones, tarjetas, ítems de lista y la barra de navegación.
REGLAS_ANDROID = """
<M3CommonRipple>:
    ripple_effect: False
"""

_aplicada = False


def _sin_fbo(widget) -> None:
    """Reemplaza a init_fbos: no crea la imagen oculta ni el shader."""
    widget._phase = 0.0
    widget.ripple_pos = (0, 0)
    widget.fbo = None   # KivyMD ya revisa "if self.fbo is None" antes de usarlo
    widget.rect = None


def _nada(*_args, **_kwargs) -> None:
    return None


class SombraVacia(Instruction):
    """Ocupa el lugar de BoxShadow en las reglas de KivyMD: acepta los mismos
    valores (posición, tamaño, desenfoque...) pero no dibuja nada."""
    pos = (0, 0)
    size = (0, 0)
    offset = (0, 0)
    spread_radius = (0, 0)
    border_radius = (0, 0, 0, 0)
    blur_radius = 0
    inset = False


def aplicar_compatibilidad(forzar: bool = False) -> None:
    """Llamar ANTES de crear las pantallas (afecta a los widgets que se creen
    después)."""
    global _aplicada
    if _aplicada or not (platform == "android" or forzar):
        return
    from kivymd.uix.behaviors.ripple_behavior import M3CommonRipple

    M3CommonRipple.init_fbos = _sin_fbo                      # no crea el Fbo
    M3CommonRipple.call_ripple_animation_methods = _nada     # no inicia la onda
    M3CommonRipple.lay_canvas_instructions = _nada           # no la dibuja
    # Las reglas .kv buscan "BoxShadow" por nombre al crear cada widget
    Factory.unregister("BoxShadow")
    Factory.register("BoxShadow", cls=SombraVacia)

    Builder.load_string(REGLAS_ANDROID, filename="compatibilidad_android")
    _aplicada = True
