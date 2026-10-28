# =============================================================================
# AlertCom - Gestor de pantallas
# =============================================================================
# Arma toda la interfaz:
#   1. Tema visual y tamaño de ventana (solo en computador).
#   2. Carga los archivos .kv de views/kv/ (una sola vez cada uno).
#   3. Crea el ScreenManager con las 7 pantallas y les entrega sus
#      controladores.
#   4. Devuelve también el Navegador que usan el KV y las pantallas.
# =============================================================================

from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager
from kivy.utils import platform

from config import CARPETA_KV
from views.navegador import Navegador
from views.pantallas import (
    HistoryScreen,
    HomeScreen,
    LoginScreen,
    ProfileScreen,
    RegisterScreen,
    ReportScreen,
    SafetyScreen,
)


def crear_gestor_pantallas(app, controlador):
    """Devuelve (ScreenManager, Navegador)."""
    app.title = "AlertCom"
    app.theme_cls.theme_style = "Dark"
    app.theme_cls.primary_palette = "Orange"
    if platform in ("win", "linux", "macosx"):
        Window.size = (360, 640)  # simula un teléfono en el computador

    # Orden alfabético: _comunes.kv (plantillas) se carga primero.
    for archivo in sorted(CARPETA_KV.glob("*.kv")):
        Builder.load_file(str(archivo))

    auth = controlador.auth
    incidentes = controlador.incidentes

    gestor = ScreenManager()
    gestor.add_widget(SafetyScreen(name="safety"))
    gestor.add_widget(LoginScreen(name="login", auth_controller=auth))
    gestor.add_widget(RegisterScreen(name="register", auth_controller=auth))
    gestor.add_widget(HomeScreen(name="home", incidente_controller=incidentes, auth_controller=auth))
    gestor.add_widget(ReportScreen(name="report", incidente_controller=incidentes, auth_controller=auth))
    gestor.add_widget(HistoryScreen(name="history", incidente_controller=incidentes, auth_controller=auth))
    gestor.add_widget(ProfileScreen(name="profile", auth_controller=auth, incidente_controller=incidentes))

    return gestor, Navegador(gestor, auth)
