# =============================================================================
# AlertCom - Acciones del funcionario municipal (compartidas por pantallas)
# =============================================================================
# Eliminar un reporte se puede hacer desde el historial o desde el mapa: la
# ventana y las reglas son las mismas, por eso viven en un solo lugar.
# =============================================================================

from config import MOTIVOS_ELIMINACION_MUNICIPIO
from views.componentes.formulario import elegir_opcion


def eliminar_como_municipio(incidentes, usuario, incidente, al_terminar=None) -> None:
    """Pide el motivo y elimina el reporte (cualquiera, propio o de un vecino).

    Args:
        incidentes: IncidenteController.
        usuario: el funcionario con sesión abierta.
        incidente: el reporte a eliminar.
        al_terminar: función sin argumentos para refrescar la pantalla.
    """
    numero = incidente.id_incidente
    propio = incidente.usuario_id == usuario.uid
    aviso = "" if propio else " El vecino que lo envió recibirá un aviso."

    def eliminar(motivo):
        try:
            incidentes.eliminar_reporte(numero, usuario, motivo)
        except (ValueError, PermissionError) as error:
            return False, str(error)
        if al_terminar:
            al_terminar()
        return True, f"Reporte #{numero} eliminado."

    elegir_opcion(
        f"¿Eliminar el reporte #{numero}?", "delete-alert-outline",
        MOTIVOS_ELIMINACION_MUNICIPIO, eliminar,
        texto_boton="Eliminar",
        explicacion=("Se borrarán el reporte y su foto para todos los usuarios. "
                     "Esta acción no se puede deshacer." + aviso + " ¿Por qué se elimina?"),
    )
