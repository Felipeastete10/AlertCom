# =============================================================================
# AlertCom - Paquete de Vistas (MVC)
# =============================================================================
# Contiene las pantallas (MDScreen) de la aplicación.
# Las vistas solo capturan eventos de usuario y los delegan a los
# controladores inyectados desde main.py. No contienen lógica de negocio.
# =============================================================================

from views.safety_view import SafetyScreen
from views.login_view import LoginScreen
from views.Home_views import HomeScreen
from views.report_view import ReportScreen
from views.history_view import HistoryScreen
from views.profile_view import ProfileScreen

__all__ = [
    "SafetyScreen",
    "LoginScreen",
    "HomeScreen",
    "ReportScreen",
    "HistoryScreen",
    "ProfileScreen",
]
