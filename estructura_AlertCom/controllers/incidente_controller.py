# =============================================================================
# AlertCom - Controlador: Gestión de Incidentes
# =============================================================================
# Orquesta la creación y consulta de incidentes. No depende de Kivy/KivyMD.
# =============================================================================

from models.incidente import Incidente


class IncidenteController:
    """
    Controlador de incidentes.

    Responsabilidades:
      • Crear incidentes con datos válidos y auto-generar su ID.
      • Proveer el historial de reportes a la vista de Historial.
      • Cambiar el estado de un reporte existente.
    """

    def __init__(self) -> None:
        self.incidentes: list[Incidente] = []
        self._next_id: int = 1

    def crear_incidente(
        self,
        tipo: str,
        foto: str,
        descripcion: str,
        gravedad: str | None = None,
        ubicacion: str = "",
    ) -> Incidente:
        """
        Crea un Incidente con los datos del formulario y lo registra.

        Args:
            tipo: Tipo de daño (ej. "Bache").
            foto: Ruta o identificador de la imagen (puede ser None en MVP).
            descripcion: Descripción del problema.
            gravedad: Nivel de gravedad opcional.
            ubicacion: Ubicación GPS o dirección.

        Returns:
            La instancia de Incidente creada.
        """
        incidente = Incidente(
            id_incidente=self._next_id,
            tipo_incidente=tipo,
            descripcion=descripcion,
            gravedad=gravedad or "",
            imagen=foto or "",
            ubicacion=ubicacion,
            estado="Pendiente",
        )
        self._next_id += 1
        self.incidentes.append(incidente)
        return incidente

    def obtener_historial(self) -> list[Incidente]:
        """Devuelve una copia de todos los reportes registrados."""
        return list(self.incidentes)

    def obtener_por_estado(self, estado: str) -> list[Incidente]:
        """Devuelve solo los reportes con el estado indicado."""
        return [i for i in self.incidentes if i.estado == estado]

    def cambiar_estado(self, indice: int, nuevo_estado: str) -> bool:
        """
        Cambia el estado de un reporte por su índice en la lista interna.

        Returns:
            True si se cambió el estado, False si el índice es inválido.
        """
        if 0 <= indice < len(self.incidentes):
            self.incidentes[indice].cambiar_estado(nuevo_estado)
            return True
        return False
