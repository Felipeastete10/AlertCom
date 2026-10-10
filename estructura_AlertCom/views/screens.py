# =============================================================================
# AlertCom - Pantallas Esqueleto (Dummy Screens)
# =============================================================================
# Archivo generado por el Arquitecto (Felipe Astete) como parte de la
# rama setup/arquitectura-base.
#
# Estas clases son cascarones vacíos que heredan de MDScreen.
# Su único propósito es que el ScreenManager arranque sin errores
# mientras los compañeros de Vistas desarrollan el contenido visual.
#
# INSTRUCCIONES PARA EL EQUIPO DE VISTAS (Nico / Felipe Salazar):
#   1. Reemplacen el 'pass' de cada clase con su lógica de UI.
#   2. Si necesitan Properties de Kivy, impórtenlas aquí.
#   3. Los archivos .kv correspondientes se cargarán desde main.py
#      o desde un Builder.load_file() dedicado.
# =============================================================================

from kivymd.uix.screen import MDScreen


class SafetyScreen(MDScreen):
    """Pantalla 1 – Aviso de seguridad vial (bloqueo preventivo)."""
    pass


class LoginScreen(MDScreen):
    """Pantalla 2 – Inicio de sesión (correo + contraseña)."""
    pass


class HomeScreen(MDScreen):
    """Pantalla 3 – Mapa principal + botón '+ Reportar bache'."""
    pass


class ReportScreen(MDScreen):
    """Pantalla 4 – Formulario de reporte (Foto, Tipo, Gravedad, Desc.)."""
    pass


class HistoryScreen(MDScreen):
    """Pantalla 5 – Historial y trazabilidad de reportes ciudadanos."""
    pass


class ProfileScreen(MDScreen):
    """Pantalla 6 – Perfil del usuario, estadísticas cívicas y logout."""
    pass
