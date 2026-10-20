from models.incidente import Incidente


class IncidenteController:
    def __init__(self):
        self.incidentes = []

    def crear_incidente(self, tipo, foto, descripcion, gravedad=None):
        """Crea un Incidente con los datos del formulario y lo guarda en la lista."""
        incidente = Incidente(tipo, foto, descripcion)
        if gravedad is not None:
            incidente.gravedad = gravedad
        self.incidentes.append(incidente)
        return incidente

    def obtener_historial(self):
        """Devuelve todos los reportes (para la pantalla de Historial)."""
        return list(self.incidentes)

    def obtener_por_estado(self, estado):
        """Devuelve solo los reportes con cierto estado (ej: 'Pendiente', 'Reparado')."""
        return [i for i in self.incidentes if i.estado == estado]

    def cambiar_estado(self, indice, nuevo_estado):
        """Cambia el estado de un reporte usando el método de la clase de Allan."""
        if 0 <= indice < len(self.incidentes):
            self.incidentes[indice].cambiar_estado(nuevo_estado)
            return True
        return False