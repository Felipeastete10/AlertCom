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

from views.screens import (
    SafetyScreen,
    LoginScreen,
    HomeScreen,
    ReportScreen,
    HistoryScreen,
    ProfileScreen,
)

__all__ = [
    "SafetyScreen",
    "LoginScreen",
    "HomeScreen",
    "ReportScreen",
    "HistoryScreen",
    "ProfileScreen",
]
