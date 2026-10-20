from datetime import datetime

class Incidente:
    """
    Clase que representa un reporte de incidente o bache enviado por un usuario.
    """
    def __init__(self, id_incidente: int, tipo_incidente: str, descripcion: str, 
                 gravedad: str, imagen: str = "", ubicacion: str = "", 
                 estado: str = "Pendiente", usuario_id: int = None):
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
        """Cambia el estado del reporte de incidente."""
        estados_validos = ["Pendiente", "En proceso", "Reparado"]
        if nuevo_estado in estados_validos:
            self.estado = nuevo_estado
        else:
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
            "usuario_id": self.usuario_id
        }

    def __str__(self) -> str:
        return f"Incidente #{self.id_incidente} - {self.tipo_incidente} ({self.estado})"