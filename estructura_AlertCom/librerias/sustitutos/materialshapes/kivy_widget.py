# =============================================================================
# Sustituto de materialshapes.kivy_widget.MaterialShape (sin cairo)
# =============================================================================
# KivyMD importa FitImage al cargar sus listas, y FitImage hereda de
# MaterialShape, que dibuja formas con la librería gráfica cairo. Cairo no
# viene en Android, así que la app se cerraba con:
#     ModuleNotFoundError: No module named 'materialshapes'
#
# AlertCom no usa formas (shape=None): en ese caso FitImage funciona como una
# imagen normal (AsyncImage) y de MaterialShape solo necesita la propiedad
# "image". Esta clase entrega solo eso.
# =============================================================================

from kivy.event import EventDispatcher
from kivy.properties import ColorProperty, StringProperty


class MaterialShape(EventDispatcher):
    """Mismas propiedades básicas, sin dibujar formas."""

    image = StringProperty("")
    fill_color = ColorProperty([0, 0, 0, 0])
    bg_color = ColorProperty([0, 0, 0, 0])
