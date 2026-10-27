# =============================================================================
# AlertCom - Paquete de Vistas (MVC)
# =============================================================================
# Este paquete contiene las pantallas (MDScreen) de la aplicación.
# Actualmente solo expone clases esqueleto (dummy) para que el
# ScreenManager arranque sin errores.
#
# Los compañeros llenarán la lógica visual de cada pantalla:
#   - Nico: SafetyScreen, LoginScreen, HomeScreen
#   - Felipe Salazar: ReportScreen, HistoryScreen, ProfileScreen
# =============================================================================

# Pantallas de Nico (todavía esqueleto en screens.py)
from views.screens import (
    HomeScreen,
    ReportScreen,
)

# Pantallas de Felipe Salazar (feature/vistas-soporte)
from views.safety_view import SafetyScreen
from views.login_view import LoginScreen
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
