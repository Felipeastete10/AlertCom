# =============================================================================
# AlertCom - Vista: Perfil de Usuario (ProfileScreen)
# =============================================================================
# Muestra los datos REALES del usuario con sesión abierta, sus estadísticas
# cívicas, el interruptor de privacidad de la analítica y, solo para
# funcionarios municipales, el acceso a la pantalla de Métricas.
# =============================================================================

from kivy.metrics import dp
from kivymd.app import MDApp

from config import VERSION_APP
from views.componentes.dialogos import mostrar_aviso
from views.componentes.pantalla_base import PantallaBase


def texto_estado_nube(nube) -> str:
    """Una línea para el perfil: ¿los reportes están compartidos?"""
    if nube is None:
        return "Reportes: solo en este teléfono"
    if nube.pendientes:
        plural = "cambio" if nube.pendientes == 1 else "cambios"
        return f"Reportes compartidos: {nube.pendientes} {plural} por subir (sin conexión)"
    if nube.conectado is False:
        return "Reportes compartidos: sin conexión (se actualizarán solos)"
    return "Reportes compartidos: al día"

class ProfileScreen(PantallaBase):
    """Pantalla de perfil del usuario autenticado."""

    def __init__(self, auth_controller=None, incidente_controller=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.auth_controller = auth_controller
        self.incidente_controller = incidente_controller

    def on_pre_enter(self, *args) -> None:
        self.actualizar_perfil()

    def refrescar(self) -> None:
        self.actualizar_perfil()

    def _eventos(self):
        controlador = getattr(MDApp.get_running_app(), "controlador", None)
        return controlador.eventos if controlador else None

    def actualizar_perfil(self) -> None:
        usuario = self.auth_controller.usuario_actual
        if usuario is None:
            return

        self.ids.profile_name.text = usuario.nombre
        self.ids.profile_email.text = usuario.email
        self.ids.profile_comuna.text = f"{usuario.comuna}, Región de La Araucanía"
        self.ids.profile_rol.text = f"Rol: {usuario.rol_legible}"
        self.ids.version_label.text = f"Versión {VERSION_APP}"
        self.ids.estado_nube.text = texto_estado_nube(MDApp.get_running_app().controlador.nube)

        resumen = self.incidente_controller.resumen(usuario.uid)
        self.ids.stat_enviados.text = str(resumen["total"])
        self.ids.stat_reparados.text = str(resumen["reparados"])

        # Interruptor de privacidad: muestra la preferencia guardada
        eventos = self._eventos()
        self.ids.switch_analitica.active = bool(eventos and eventos.activo)

        # Botón de métricas: solo para funcionarios municipales
        municipal = usuario.es_municipal
        self.ids.caja_metricas.height = dp(56) if municipal else 0
        self.ids.caja_metricas.opacity = 1 if municipal else 0
        self.ids.boton_metricas.disabled = not municipal

    def cambiar_analitica(self, activo: bool) -> None:
        """El usuario activa o desactiva el registro de sus datos de uso."""
        eventos = self._eventos()
        if eventos is None or eventos.activo == activo:
            return  # nada cambió (ej. al cargar la pantalla)
        eventos.cambiar_activo(activo)
        mostrar_aviso("Registro de uso activado" if activo else "Registro de uso desactivado")

    def cerrar_sesion(self) -> None:
        MDApp.get_running_app().navegacion.cerrar_sesion()
