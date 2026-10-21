# =============================================================================
# AlertCom - Modelo de Dominio: Incidente
# =============================================================================
# Representa un reporte de incidencia vial (bache, grieta, hundimiento, etc.).
# Clase pura de dominio: no depende de Kivy, KivyMD ni de la interfaz.
# =============================================================================

from datetime import datetime


class Incidente:
    """
    Clase que representa un reporte de incidente enviado por un usuario.

    Attributes:
        id_incidente: Identificador único del reporte.
        tipo_incidente: Tipo de daño (Bache, Hoyo, Grieta, etc.).
        descripcion: Descripción libre del problema.
        gravedad: Nivel de gravedad (Leve, Moderado, Grave, Crítico).
        imagen: Ruta o identificador de la foto asociada.
        ubicacion: Coordenadas GPS o dirección legible.
        estado: Estado del reporte (Pendiente, En proceso, Reparado).
        fecha_creacion: Fecha y hora de creación automática.
        usuario_id: Identificador del usuario que reportó.
    """

    ESTADOS_VALIDOS = ("Pendiente", "En proceso", "Reparado")

    def __init__(
        self,
        id_incidente: int,
        tipo_incidente: str,
        descripcion: str,
        gravedad: str = "",
        imagen: str = "",
        ubicacion: str = "",
        estado: str = "Pendiente",
        usuario_id: int = None,
    ) -> None:
        self.id_incidente = id_incidente
        self.tipo_incidente = tipo_incidente
        self.descripcion = descripcion
        self.gravedad = gravedad
        self.imagen = imagen
        self.ubicacion = ubicacion
        self.estado = estado
        self.fecha_creacion = datetime.now()
        self.usuario_id = usuario_id

    def cambiar_estado(self, nuevo_estado: str) -> None:
        """
        Cambia el estado del reporte de incidente.

        Raises:
            ValueError: Si el nuevo estado no pertenece a los estados válidos.
        """
        if nuevo_estado not in self.ESTADOS_VALIDOS:
            raise ValueError(
                f"Estado inválido: '{nuevo_estado}'. "
                f"Estados permitidos: {list(self.ESTADOS_VALIDOS)}"
            )
        self.estado = nuevo_estado

    def actualizar_descripcion(self, nueva_descripcion: str) -> None:
        """Permite modificar o corregir la descripción del incidente."""
        self.descripcion = nueva_descripcion

    def to_dict(self) -> dict:
        """Retorna un diccionario con los detalles del incidente."""
        return {
            "id_incidente": self.id_incidente,
            "tipo_incidente": self.tipo_incidente,
            "descripcion": self.descripcion,
            "gravedad": self.gravedad,
            "imagen": self.imagen,
            "ubicacion": self.ubicacion,
            "estado": self.estado,
            "fecha_creacion": self.fecha_creacion.strftime("%Y-%m-%d %H:%M:%S"),
            "usuario_id": self.usuario_id,
        }

    def __str__(self) -> str:
        return f"Incidente #{self.id_incidente} - {self.tipo_incidente} ({self.estado})"
