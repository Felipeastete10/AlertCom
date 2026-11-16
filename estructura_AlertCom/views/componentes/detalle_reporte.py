# =============================================================================
# AlertCom - Detalle de un reporte (mapa e historial muestran lo mismo)
# =============================================================================

from kivymd.app import MDApp

from controllers.fotos import ruta_foto
from views.componentes.dialogos import mostrar_dialogo


def mostrar_detalle_reporte(incidente, botones=None, icono="map-marker-alert"):
    """Diálogo con calle, gravedad, estado, fecha, descripción y foto."""
    carpeta_datos = MDApp.get_running_app().controlador.carpeta_datos
    foto = ruta_foto(carpeta_datos, incidente.imagen)

    mensaje = (
        f"Calle: {incidente.calle or 'Sin calle registrada'}\n"
        f"Gravedad: {incidente.gravedad}\n"
        f"Estado: {incidente.estado}\n"
        f"Fecha: {incidente.fecha_legible()}\n\n"
        f"{incidente.descripcion or 'Sin descripción.'}"
    )
    if foto is None:
        mensaje += "\n\n(Este reporte no tiene foto.)"
    if incidente.eliminacion_pendiente:
        motivo = incidente.solicitud_eliminacion.get("motivo", "")
        mensaje += (f"\n\nEliminación solicitada · Motivo: {motivo}.\n"
                    "Esperando la decisión del municipio.")

    return mostrar_dialogo(
        f"#{incidente.id_incidente} · {incidente.tipo_incidente}",
        mensaje,
        icono=icono,
        botones=botones,
        imagen=str(foto) if foto else None,
    )
