# AlertCom - Pantallas (heredan de PantallaBase, que registra pantalla_vista).
# Cada una tiene su diseño en views/kv/.
from views.pantallas.safety_view import SafetyScreen
from views.pantallas.login_view import LoginScreen
from views.pantallas.register_view import RegisterScreen
from views.pantallas.home_view import HomeScreen
from views.pantallas.report_view import ReportScreen
from views.pantallas.history_view import HistoryScreen
from views.pantallas.profile_view import ProfileScreen
from views.pantallas.metricas_view import MetricasScreen
from views.pantallas.ajustes_view import AjustesScreen

__all__ = [
    "SafetyScreen",
    "LoginScreen",
    "RegisterScreen",
    "HomeScreen",
    "ReportScreen",
    "HistoryScreen",
    "ProfileScreen",
    "MetricasScreen",
    "AjustesScreen",
]
