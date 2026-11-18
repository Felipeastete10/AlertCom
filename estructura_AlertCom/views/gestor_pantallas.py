# =============================================================================
# AlertCom - Gestor de pantallas
# =============================================================================
# Arma toda la interfaz:
#   1. Tema visual y tamaño de ventana (solo en computador).
#   2. Ajustes de compatibilidad para Android (views/compatibilidad.py) y
#      carga de los archivos .kv de views/kv/ (una sola vez cada uno).
#   3. Crea el ScreenManager con las 8 pantallas y les entrega sus
#      controladores.
#   4. Devuelve también el Navegador que usan el KV y las pantallas.
# =============================================================================

from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager
from kivy.utils import platform

from config import CARPETA_KV
from views.apariencia import aplicar_apariencia
from views.compatibilidad import aplicar_compatibilidad
from views.navegador import Navegador
from views.pantallas import (
    HistoryScreen,
    HomeScreen,
    LoginScreen,
    MetricasScreen,
    AjustesScreen,
    ConfirmarScreen,
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

    # En Android: apaga el efecto de onda de KivyMD que cierra la app
    aplicar_compatibilidad()

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
    gestor.add_widget(MetricasScreen(name="metricas", auth_controller=auth))
    gestor.add_widget(AjustesScreen(name="ajustes", auth_controller=auth, incidente_controller=incidentes))
    gestor.add_widget(ConfirmarScreen(name="confirmar", incidente_controller=incidentes, auth_controller=auth))

    # Tamaño de letra y fondo que la persona eligió la última vez
    aplicar_apariencia(app, controlador.preferencias)

    return gestor, Navegador(gestor, auth)
