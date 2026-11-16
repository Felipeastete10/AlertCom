# =============================================================================
# AlertCom - Cámara y galería del teléfono
# =============================================================================
# ¿Por qué no plyer.camera? En Android 7 o superior, plyer.camera le pasa a la
# cámara una ruta "file://" y Android la bloquea (FileUriExposedException):
# la app se cierra. Por eso usamos el método recomendado por Android:
#
#   1. Se crea un espacio para la foto en la galería (MediaStore).
#   2. Se abre la app de cámara del teléfono con esa dirección "content://".
#   3. Al volver, se copia la foto a la carpeta privada de AlertCom y se
#      borra de la galería (queda solo la copia reducida del reporte).
#
# No necesita el permiso CAMERA: la foto la toma la app de cámara del
# teléfono. En Android 9 o anterior sí se pide permiso de almacenamiento.
#
# En el computador no hay cámara del teléfono: la vista muestra un selector
# de archivos para elegir una imagen.
#
# Resultado: al_terminar(ruta_temporal, error)
#   • ruta_temporal: archivo copiado, listo para reducir (o None).
#   • error: texto para mostrar, o None si todo salió bien o se canceló.
# =============================================================================

import logging
import os
import shutil
from pathlib import Path

from kivy.clock import mainthread
from kivy.utils import platform

log = logging.getLogger("alertcom.camara")

CODIGO_CAMARA = 4301
CODIGO_GALERIA = 4302
RESULTADO_OK = -1  # Activity.RESULT_OK


class Camara:
    """Abre la cámara o la galería de Android y devuelve la foto elegida."""

    def __init__(self, carpeta_temporal) -> None:
        self.carpeta_temporal = Path(carpeta_temporal)
        self._al_terminar = None
        self._uri_foto = None
        self._codigo = None

    @property
    def disponible(self) -> bool:
        return platform == "android"

    # ------------------------------------------------------------------
    # Uso
    # ------------------------------------------------------------------
    def tomar_foto(self, al_terminar) -> None:
        self._al_terminar = al_terminar
        try:
            from jnius import autoclass

            version_android = autoclass("android.os.Build$VERSION").SDK_INT
            if version_android < 29:
                # Android 9 o anterior: guardar en la galería pide permiso.
                from android.permissions import Permission, check_permission, request_permissions
                if not check_permission(Permission.WRITE_EXTERNAL_STORAGE):
                    request_permissions([Permission.WRITE_EXTERNAL_STORAGE], self._al_responder_permiso)
                    return
            self._abrir_camara()
        except Exception as error:
            self._terminar_con_error(error)

    def elegir_de_galeria(self, al_terminar) -> None:
        self._al_terminar = al_terminar
        try:
            from jnius import autoclass

            Intent = autoclass("android.content.Intent")
            intento = Intent(Intent.ACTION_GET_CONTENT)
            intento.setType("image/*")
            intento.addCategory(Intent.CATEGORY_OPENABLE)
            self._lanzar(intento, CODIGO_GALERIA)
        except Exception as error:
            self._terminar_con_error(error)

    # ------------------------------------------------------------------
    # Android
    # ------------------------------------------------------------------
    @mainthread
    def _al_responder_permiso(self, _permisos, concedidos) -> None:
        if any(concedidos):
            try:
                self._abrir_camara()
            except Exception as error:
                self._terminar_con_error(error)
        else:
            self._entregar(None, "Sin permiso de almacenamiento no se puede guardar la foto.")

    def _abrir_camara(self) -> None:
        from jnius import autoclass, cast

        actividad = autoclass("org.kivy.android.PythonActivity").mActivity
        Intent = autoclass("android.content.Intent")
        MediaStore = autoclass("android.provider.MediaStore")
        ImagenesGaleria = autoclass("android.provider.MediaStore$Images$Media")
        ContentValues = autoclass("android.content.ContentValues")

        valores = ContentValues()
        valores.put("_display_name", "alertcom_reporte.jpg")
        valores.put("mime_type", "image/jpeg")
        resolver = actividad.getContentResolver()
        self._uri_foto = resolver.insert(ImagenesGaleria.EXTERNAL_CONTENT_URI, valores)
        if self._uri_foto is None:
            raise RuntimeError("Android no entregó un espacio para la foto")

        intento = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
        intento.putExtra(MediaStore.EXTRA_OUTPUT, cast("android.os.Parcelable", self._uri_foto))
        intento.addFlags(Intent.FLAG_GRANT_WRITE_URI_PERMISSION | Intent.FLAG_GRANT_READ_URI_PERMISSION)
        self._lanzar(intento, CODIGO_CAMARA)

    def _lanzar(self, intento, codigo: int) -> None:
        from android import activity as eventos_android
        from jnius import autoclass

        self._codigo = codigo
        eventos_android.bind(on_activity_result=self._al_volver)
        autoclass("org.kivy.android.PythonActivity").mActivity.startActivityForResult(intento, codigo)

    def _al_volver(self, codigo, resultado, intento) -> None:
        """Android avisa aquí cuando la persona sale de la cámara o galería."""
        if codigo != self._codigo:
            return
        from android import activity as eventos_android
        eventos_android.unbind(on_activity_result=self._al_volver)

        try:
            if resultado != RESULTADO_OK:
                self._borrar_de_galeria()
                self._entregar(None, None)  # canceló: no es un error
                return
            if codigo == CODIGO_CAMARA:
                uri = self._uri_foto
            else:
                uri = intento.getData() if intento is not None else None
            if uri is None:
                raise RuntimeError("No llegó ninguna imagen")
            destino = self._copiar(uri)
            self._borrar_de_galeria()
            self._entregar(destino, None)
        except Exception as error:
            self._borrar_de_galeria()
            self._terminar_con_error(error)

    def _copiar(self, uri) -> Path:
        """Copia el contenido de un 'content://' a un archivo de la app."""
        from jnius import autoclass

        resolver = autoclass("org.kivy.android.PythonActivity").mActivity.getContentResolver()
        descriptor = resolver.openFileDescriptor(uri, "r")
        numero = descriptor.detachFd()  # Python lee el archivo directamente
        self.carpeta_temporal.mkdir(parents=True, exist_ok=True)
        destino = self.carpeta_temporal / "foto_temporal"
        with os.fdopen(numero, "rb") as origen, open(destino, "wb") as salida:
            shutil.copyfileobj(origen, salida)
        return destino

    def _borrar_de_galeria(self) -> None:
        """La foto ya está copiada en AlertCom: no se deja duplicada."""
        if self._uri_foto is None:
            return
        try:
            from jnius import autoclass
            resolver = autoclass("org.kivy.android.PythonActivity").mActivity.getContentResolver()
            resolver.delete(self._uri_foto, None, None)
        except Exception as error:
            log.info("No se pudo borrar la copia de la galería: %s", error)
        self._uri_foto = None

    # ------------------------------------------------------------------
    # Resultado (siempre en el hilo de Kivy)
    # ------------------------------------------------------------------
    def _terminar_con_error(self, error) -> None:
        log.warning("Error con la cámara o galería: %s", error)
        self._entregar(None, "No se pudo obtener la foto. Inténtalo de nuevo o elige una de la galería.")

    @mainthread
    def _entregar(self, ruta, error) -> None:
        if self._al_terminar:
            self._al_terminar(ruta, error)
