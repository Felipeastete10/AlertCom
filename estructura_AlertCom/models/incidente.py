# =============================================================================
# AlertCom - Modelo de Dominio: Incidente
# =============================================================================
# Representa un reporte de daño vial (bache, grieta, hundimiento, etc.).
# Es el equivalente a la clase "Tarea" del curso: el objeto del mundo real
# que el vecino crea y que la municipalidad va cerrando.
# Clase pura de dominio: NO importa Kivy ni nada de la interfaz.
# =============================================================================

from datetime import datetime

FORMATO_FECHA = "%Y-%m-%d %H:%M:%S"

# Ciclo de vida de un reporte (mismo texto en modelo, mapa e historial)
ESTADOS = ("Pendiente", "En revisión", "Reparado")


class Incidente:
    """
    Reporte de incidente vial enviado por un usuario.

    Attributes:
        id_incidente: Identificador único del reporte.
        tipo_incidente: Tipo de daño (Bache, Hoyo, Grieta, etc.).
        descripcion: Descripción libre del problema.
        gravedad: Leve, Moderado, Grave o Crítico.
        imagen: Ruta de la foto asociada.
        ubicacion: Coordenadas "lat, lon".
        estado: Pendiente, En revisión o Reparado.
        usuario_id: Usuario que reportó.
        fecha_creacion: Fecha y hora de creación.
    """

    ESTADOS_VALIDOS = ESTADOS

    def __init__(
        self,
        id_incidente: int,
        tipo_incidente: str,
        descripcion: str = "",
        gravedad: str = "",
        imagen: str = "",
        ubicacion: str = "",
        estado: str = "Pendiente",
        usuario_id: int | None = None,
        fecha_creacion: datetime | None = None,
    ) -> None:
        if estado not in self.ESTADOS_VALIDOS:
            raise ValueError(f"Estado inválido: '{estado}'")
        self.id_incidente = id_incidente
        self.tipo_incidente = tipo_incidente
        self.descripcion = descripcion
        self.gravedad = gravedad
        self.imagen = imagen
        self.ubicacion = ubicacion
        self.estado = estado
        self.usuario_id = usuario_id
        self.fecha_creacion = fecha_creacion or datetime.now()

    # ------------------------------------------------------------------
    # Reglas de negocio
    # ------------------------------------------------------------------
    def cambiar_estado(self, nuevo_estado: str) -> None:
        """
        Cambia el estado del reporte.

        Raises:
            ValueError: Si el estado no pertenece a ESTADOS_VALIDOS.
        """
        if nuevo_estado not in self.ESTADOS_VALIDOS:
            raise ValueError(
                f"Estado inválido: '{nuevo_estado}'. "
                f"Estados permitidos: {list(self.ESTADOS_VALIDOS)}"
            )
        self.estado = nuevo_estado

    def siguiente_estado(self) -> str | None:
        """Devuelve el estado que sigue en el ciclo, o None si ya está reparado."""
        posicion = self.ESTADOS_VALIDOS.index(self.estado)
        if posicion + 1 < len(self.ESTADOS_VALIDOS):
            return self.ESTADOS_VALIDOS[posicion + 1]
        return None

    @property
    def esta_reparado(self) -> bool:
        return self.estado == "Reparado"

    def actualizar_descripcion(self, nueva_descripcion: str) -> None:
        self.descripcion = nueva_descripcion

    def coordenadas(self) -> tuple[float, float] | None:
        """Convierte 'lat, lon' en (lat, lon). Devuelve None si no se puede."""
        try:
            lat, lon = (float(parte) for parte in self.ubicacion.split(","))
            return lat, lon
        except (ValueError, AttributeError):
            return None

    def fecha_legible(self) -> str:
        return self.fecha_creacion.strftime("%d/%m/%Y %H:%M")

    # ------------------------------------------------------------------
    # Serialización (para JSON)
    # ------------------------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "id_incidente": self.id_incidente,
            "tipo_incidente": self.tipo_incidente,
            "descripcion": self.descripcion,
            "gravedad": self.gravedad,
            "imagen": self.imagen,
            "ubicacion": self.ubicacion,
            "estado": self.estado,
            "usuario_id": self.usuario_id,
            "fecha_creacion": self.fecha_creacion.strftime(FORMATO_FECHA),
        }

    @classmethod
    def from_dict(cls, datos: dict) -> "Incidente":
        return cls(
            id_incidente=int(datos["id_incidente"]),
            tipo_incidente=datos["tipo_incidente"],
            descripcion=datos.get("descripcion", ""),
            gravedad=datos.get("gravedad", ""),
            imagen=datos.get("imagen", ""),
            ubicacion=datos.get("ubicacion", ""),
            estado=datos.get("estado", "Pendiente"),
            usuario_id=datos.get("usuario_id"),
            fecha_creacion=datetime.strptime(datos["fecha_creacion"], FORMATO_FECHA),
        )

    def __str__(self) -> str:
        return f"Incidente #{self.id_incidente} - {self.tipo_incidente} ({self.estado})"
