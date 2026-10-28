# =============================================================================
# AlertCom - Controlador: Gestión de Incidentes
# =============================================================================
# Crea, consulta y actualiza reportes. Cada cambio se guarda en
# incidentes.json y, cuando el cambio es importante, se avisa con una
# notificación local (Plyer) desde AQUÍ, la lógica de negocio.
# No importa Kivy.
# =============================================================================

import logging

from config import GRAVEDADES, MAX_CARACTERES_DESCRIPCION, TIPOS_DANO
from controllers.almacenamiento_json import AlmacenamientoJSON
from controllers.notificador import Notificador
from models.incidente import Incidente

log = logging.getLogger("alertcom.incidentes")


class IncidenteController:
    """Lógica de negocio de los reportes de baches."""

    def __init__(
        self,
        almacenamiento: AlmacenamientoJSON,
        notificador: Notificador | None = None,
    ) -> None:
        self.almacenamiento = almacenamiento
        self.notificador = notificador or Notificador(habilitado=False)
        self.incidentes: list[Incidente] = self._cargar()

    # ------------------------------------------------------------------
    # Persistencia
    # ------------------------------------------------------------------
    def _cargar(self) -> list[Incidente]:
        incidentes = []
        for datos in self.almacenamiento.cargar():
            try:
                incidentes.append(Incidente.from_dict(datos))
            except (KeyError, ValueError, TypeError) as error:
                log.warning("Reporte inválido en JSON, se omite: %s", error)
        return incidentes

    def _guardar(self) -> None:
        self.almacenamiento.guardar([i.to_dict() for i in self.incidentes])

    def _siguiente_id(self) -> int:
        return max((i.id_incidente for i in self.incidentes), default=0) + 1

    # ------------------------------------------------------------------
    # Casos de uso (mutaciones → se guardan y notifican)
    # ------------------------------------------------------------------
    def crear_incidente(
        self,
        tipo: str,
        gravedad: str,
        descripcion: str = "",
        foto: str | None = None,
        ubicacion: str = "",
        usuario_id: int | None = None,
    ) -> Incidente:
        """
        Valida, crea, guarda y notifica un reporte nuevo.

        Raises:
            ValueError: con un mensaje listo para mostrar al usuario.
        """
        if tipo not in TIPOS_DANO:
            raise ValueError("Selecciona el tipo de daño.")
        if gravedad not in GRAVEDADES:
            raise ValueError("Selecciona la gravedad del daño.")
        descripcion = (descripcion or "").strip()
        if len(descripcion) > MAX_CARACTERES_DESCRIPCION:
            raise ValueError(
                f"La descripción no puede superar {MAX_CARACTERES_DESCRIPCION} caracteres."
            )

        incidente = Incidente(
            id_incidente=self._siguiente_id(),
            tipo_incidente=tipo,
            descripcion=descripcion,
            gravedad=gravedad,
            imagen=foto or "",
            ubicacion=ubicacion,
            usuario_id=usuario_id,
        )
        self.incidentes.append(incidente)
        self._guardar()

        self.notificador.notificar(
            titulo="Reporte enviado",
            mensaje=f"Tu reporte #{incidente.id_incidente} ({tipo}, {gravedad}) quedó registrado.",
        )
        return incidente

    def cambiar_estado(self, id_incidente: int, nuevo_estado: str) -> Incidente:
        """
        Cambia el estado de un reporte (por su ID, no por su posición).

        Raises:
            ValueError: si el reporte no existe o el estado no es válido.
        """
        incidente = self.buscar(id_incidente)
        if incidente is None:
            raise ValueError(f"No existe el reporte #{id_incidente}.")

        incidente.cambiar_estado(nuevo_estado)
        self._guardar()

        self.notificador.notificar(
            titulo="Actualización de tu reporte",
            mensaje=f"El reporte #{id_incidente} ({incidente.tipo_incidente}) ahora está: {nuevo_estado}.",
        )
        return incidente

    def avanzar_estado(self, id_incidente: int) -> Incidente:
        """Pasa el reporte al siguiente estado: Pendiente → En revisión → Reparado."""
        incidente = self.buscar(id_incidente)
        if incidente is None:
            raise ValueError(f"No existe el reporte #{id_incidente}.")
        siguiente = incidente.siguiente_estado()
        if siguiente is None:
            raise ValueError("Este reporte ya está reparado.")
        return self.cambiar_estado(id_incidente, siguiente)

    # ------------------------------------------------------------------
    # Consultas (no modifican nada)
    # ------------------------------------------------------------------
    def buscar(self, id_incidente: int) -> Incidente | None:
        return next((i for i in self.incidentes if i.id_incidente == id_incidente), None)

    def obtener_historial(self, usuario_id: int | None = None) -> list[Incidente]:
        """Copia de los reportes, del más nuevo al más antiguo.
        Si se indica usuario_id, solo los de ese usuario."""
        reportes = [
            i for i in self.incidentes if usuario_id is None or i.usuario_id == usuario_id
        ]
        return sorted(reportes, key=lambda i: i.fecha_creacion, reverse=True)

    def obtener_por_estado(self, estado: str) -> list[Incidente]:
        return [i for i in self.incidentes if i.estado == estado]

    def resumen(self, usuario_id: int | None = None) -> dict:
        """Contadores para las tarjetas del historial y del perfil."""
        reportes = self.obtener_historial(usuario_id)
        return {
            "total": len(reportes),
            "pendientes": sum(i.estado == "Pendiente" for i in reportes),
            "en_revision": sum(i.estado == "En revisión" for i in reportes),
            "reparados": sum(i.estado == "Reparado" for i in reportes),
        }
