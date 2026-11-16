# =============================================================================
# AlertCom - Registro de eventos de uso (analítica in-house, RA3)
# =============================================================================
# Guarda cada evento como UNA línea JSON en "eventos.jsonl" (formato JSON
# Lines). Decisiones:
#   • Modo "a" (append): agrega al final sin reescribir lo anterior.
#     Con "w" se borraría todo el historial en cada evento.
#   • Una línea por evento: si la app se cierra a mitad de una escritura,
#     solo se pierde esa línea; el resto del archivo sigue legible.
#   • encoding="utf-8": guarda bien tildes y ñ ("En revisión", "Ñielol").
#   • Carpeta de datos de la app (user_data_dir en Android), nunca la del
#     código: en el teléfono la carpeta del código es de solo lectura.
#   • Rotación: sobre 2 MB, el archivo se renombra con la fecha y se empieza
#     uno nuevo, para que no crezca sin control.
#   • Privacidad: se puede desactivar desde el Perfil; la preferencia se
#     guarda en preferencias.json.
#
# Registrar NUNCA debe cerrar la app: cualquier error se anota en el log y
# la función devuelve None.
# =============================================================================

import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path

from controllers.preferencias import Preferencias
from models.evento import Evento

log = logging.getLogger("alertcom.eventos")

ARCHIVO_EVENTOS = "eventos.jsonl"
ARCHIVO_PREFERENCIAS = "preferencias.json"
TAMANO_MAXIMO_BYTES = 2_000_000  # ~10.000 eventos


class RegistroEventos:
    """Escribe eventos en un archivo local, uno por línea."""

    def __init__(self, carpeta: Path | str, sesion_id: str | None = None) -> None:
        self.carpeta = Path(carpeta)
        self.carpeta.mkdir(parents=True, exist_ok=True)
        self.ruta = self.carpeta / ARCHIVO_EVENTOS
        self.ruta_preferencias = self.carpeta / ARCHIVO_PREFERENCIAS
        self.sesion_id = sesion_id or uuid.uuid4().hex[:8]
        self.usuario_id: int | None = None
        self.activo = self._leer_preferencia()

    # ------------------------------------------------------------------
    # Registrar
    # ------------------------------------------------------------------
    def registrar(self, nombre: str, datos: dict | None = None) -> Evento | None:
        """Crea el evento y lo agrega al final del archivo."""
        if not self.activo:
            return None
        try:
            evento = Evento(nombre, datos, self.usuario_id, self.sesion_id)
        except ValueError as error:
            log.warning("Evento ignorado: %s", error)
            return None

        try:
            self._rotar_si_es_necesario()
            linea = json.dumps(evento.to_dict(), ensure_ascii=False)
            with open(self.ruta, "a", encoding="utf-8") as archivo:
                archivo.write(linea + "\n")
        except OSError as error:
            log.warning("No se pudo guardar el evento %s: %s", nombre, error)
            return None
        return evento

    def _rotar_si_es_necesario(self) -> None:
        if self.ruta.exists() and self.ruta.stat().st_size > TAMANO_MAXIMO_BYTES:
            sello = datetime.now().strftime("%Y%m%d_%H%M%S")
            destino = self.carpeta / f"eventos_{sello}.jsonl"
            numero = 1
            while destino.exists():  # nunca sobrescribir un archivo ya archivado
                destino = self.carpeta / f"eventos_{sello}_{numero}.jsonl"
                numero += 1
            os.replace(self.ruta, destino)
            log.info("eventos.jsonl superó el límite: se archivó y se empezó uno nuevo.")

    # ------------------------------------------------------------------
    # Sesión y privacidad
    # ------------------------------------------------------------------
    def asignar_usuario(self, usuario_id: int | None) -> None:
        """Lo llama el AuthController al iniciar o cerrar sesión."""
        self.usuario_id = usuario_id

    def cambiar_activo(self, activo: bool) -> None:
        """El usuario decide si se registran sus eventos de uso.
        Se mezcla con las demás preferencias (letra, fondo): no las borra."""
        self.activo = bool(activo)
        Preferencias(self.ruta_preferencias).guardar("analitica_activa", self.activo)

    def _leer_preferencia(self) -> bool:
        # Activo por defecto; se informa en el Perfil.
        return bool(Preferencias(self.ruta_preferencias).obtener("analitica_activa", True))

    # ------------------------------------------------------------------
    # Lectura
    # ------------------------------------------------------------------
    def archivos(self) -> list[Path]:
        """El archivo actual y los archivados por rotación, del más antiguo al más nuevo."""
        archivados = sorted(self.carpeta.glob("eventos_*.jsonl"))
        actual = [self.ruta] if self.ruta.exists() else []
        return archivados + actual


class RegistroNulo:
    """Registro que no guarda nada. Se usa cuando un controlador se crea sin
    analítica (por ejemplo, en las pruebas): así el código de negocio llama
    a registrar() siempre, sin llenarse de "if eventos is not None"."""

    activo = False
    usuario_id = None

    def registrar(self, nombre: str, datos: dict | None = None) -> None:
        return None

    def asignar_usuario(self, usuario_id: int | None) -> None:
        return None
