# =============================================================================
# AlertCom - Fotos de los reportes
# =============================================================================
# La foto que llega de la cámara (o de la galería) puede pesar 5 MB o más.
# Aquí se guarda una COPIA reducida en datos/fotos/:
#   • Lado mayor de 1280 px y calidad JPEG 80 → unos 200 KB.
#   • Se endereza según la orientación del teléfono (EXIF), así no queda
#     acostada.
#   • Se guarda SIN metadatos EXIF: la foto original puede traer la ubicación
#     GPS exacta y el modelo del teléfono (privacidad).
#
# En el reporte se guarda la ruta RELATIVA ("fotos/reporte_...jpg"), nunca
# una ruta absoluta del computador o del teléfono.
# Python puro + Pillow: no importa Kivy, así que se puede probar.
# =============================================================================

import logging
from datetime import datetime
from pathlib import Path

from config import CALIDAD_FOTO, CARPETA_FOTOS, LADO_MAXIMO_FOTO

log = logging.getLogger("alertcom.fotos")


def guardar_foto_reducida(origen, carpeta_datos, lado_maximo: int = LADO_MAXIMO_FOTO,
                          calidad: int = CALIDAD_FOTO) -> str:
    """
    Copia la imagen `origen` reducida a carpeta_datos/fotos/.

    Returns:
        La ruta relativa, ej. "fotos/reporte_20261112_101500_123456.jpg".
    Raises:
        ValueError: si el archivo no es una imagen que se pueda abrir.
    """
    from PIL import Image, ImageOps, UnidentifiedImageError

    carpeta = Path(carpeta_datos) / CARPETA_FOTOS
    carpeta.mkdir(parents=True, exist_ok=True)
    nombre = f"reporte_{datetime.now():%Y%m%d_%H%M%S_%f}.jpg"

    try:
        with Image.open(origen) as imagen:
            imagen = ImageOps.exif_transpose(imagen)   # endereza la foto
            imagen = imagen.convert("RGB")             # PNG con transparencia → JPEG
            imagen.thumbnail((lado_maximo, lado_maximo))
            imagen.save(carpeta / nombre, "JPEG", quality=calidad, optimize=True)
    except (UnidentifiedImageError, OSError) as error:
        log.warning("No se pudo procesar la foto %s: %s", origen, error)
        raise ValueError("El archivo elegido no es una imagen válida.") from error

    log.info("Foto guardada: %s", nombre)
    return f"{CARPETA_FOTOS}/{nombre}"


def ruta_foto(carpeta_datos, imagen: str) -> Path | None:
    """Ruta completa de la foto de un reporte, o None si no existe
    (reportes antiguos con foto simulada, o foto borrada)."""
    if not imagen:
        return None
    ruta = Path(carpeta_datos) / imagen
    return ruta if ruta.is_file() else None


def borrar_foto(carpeta_datos, imagen: str) -> None:
    """Borra una foto que no se llegó a enviar (formulario abandonado)."""
    ruta = ruta_foto(carpeta_datos, imagen)
    if ruta is not None:
        try:
            ruta.unlink()
        except OSError as error:
            log.warning("No se pudo borrar %s: %s", ruta, error)
