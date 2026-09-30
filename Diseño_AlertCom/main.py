# =============================================================================
# AlertCom - "Reporta. Ubica. Mejora."
# =============================================================================
# Aplicación móvil para reportar baches, hoyos y daños en el pavimento
# mediante fotos y geolocalización GPS.
#
# Tecnologías: Python 3.11.1 | Kivy 2.3.1 | KivyMD 2.0.1.dev0
# Metodología A+S - Justificación basada en 26 encuestas ciudadanas (Temuco)
#
# Pantallas:
#   1. SafetyScreen    -> Aviso de seguridad (protección al conductor)
#   2. LoginScreen     -> Inicio de sesión (correo + contraseña)
#   3. HomeScreen      -> Mapa simulado + botón "+ Reportar bache"
#   4. ReportScreen    -> Formulario de reporte (Foto, Tipo, Gravedad, Desc.)
#   5. HistoryScreen   -> Historial / Seguimiento de reportes
#   6. ProfileScreen   -> Perfil del ciudadano (datos, estadísticas y logout)
# =============================================================================

from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, SlideTransition
from kivy.properties import StringProperty
from kivy.core.window import Window

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.menu import MDDropdownMenu

# Simulación de resolución móvil estándar (360x640) en entorno de escritorio
Window.size = (360, 640)


# =============================================================================
# PANTALLA 1: AVISO DE SEGURIDAD
# =============================================================================
class SafetyScreen(MDScreen):
    """Pantalla inicial de advertencia para proteger a conductores."""
    pass


# =============================================================================
# PANTALLA 2: LOGIN
# =============================================================================
class LoginScreen(MDScreen):
    """Pantalla de inicio de sesión."""

    def validate_login(self):
        """Simula la validación y avanza al Home con transición fluida."""
        app = MDApp.get_running_app()
        app.go_to_screen("home", direction="left")


# =============================================================================
# PANTALLA 3: HOME / MAPA
# =============================================================================
class HomeScreen(MDScreen):
    """Pantalla principal con mapa y botón central de reporte."""
    pass


# =============================================================================
# PANTALLA 4: FORMULARIO DE REPORTE
# =============================================================================
class ReportScreen(MDScreen):
    """Formulario interactivo para registrar un nuevo bache o daño vial."""

    selected_type = StringProperty("Seleccionar tipo")
    selected_severity = StringProperty("Seleccionar gravedad")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.type_menu = None
        self.severity_menu = None

    def open_type_menu(self):
        """Despliega las opciones de tipo de daño según KivyMD 2.0."""
        menu_items = [
            {
                "text": tipo,
                "on_release": lambda x=tipo: self._set_type(x),
            }
            for tipo in ["Bache", "Hoyo", "Grieta", "Hundimiento", "Pavimento roto"]
        ]
        self.type_menu = MDDropdownMenu(
            caller=self.ids.type_selector,
            items=menu_items,
        )
        self.type_menu.open()

    def _set_type(self, text):
        """Actualiza el texto del selector de tipo y cierra el menú."""
        self.selected_type = text
        self.ids.type_label.text = text
        if self.type_menu:
            self.type_menu.dismiss()

    def open_severity_menu(self):
        """Despliega las opciones de gravedad según KivyMD 2.0."""
        menu_items = [
            {
                "text": nivel,
                "on_release": lambda x=nivel: self._set_severity(x),
            }
            for nivel in ["Leve", "Moderado", "Grave", "Crítico"]
        ]
        self.severity_menu = MDDropdownMenu(
            caller=self.ids.severity_selector,
            items=menu_items,
        )
        self.severity_menu.open()

    def _set_severity(self, text):
        """Actualiza el texto del selector de gravedad y cierra el menú."""
        self.selected_severity = text
        self.ids.severity_label.text = text
        if self.severity_menu:
            self.severity_menu.dismiss()

    def simulate_photo(self):
        """Simula la captura de imagen con GPS integrado."""
        self.ids.photo_label.text = "📷  foto_bache_001.jpg\n(GPS: -38.7352, -72.5904)"

    def submit_report(self):
        """Envía el reporte simulado y avanza al historial de reportes."""
        app = MDApp.get_running_app()
        app.go_to_screen("history", direction="left")


# =============================================================================
# PANTALLA 5: HISTORIAL / MIS REPORTES
# =============================================================================
class HistoryScreen(MDScreen):
    """Pantalla de historial y trazabilidad ciudadana."""
    pass


# =============================================================================
# PANTALLA 6: PERFIL DE USUARIO
# =============================================================================
class ProfileScreen(MDScreen):
    """Pantalla de perfil de usuario, estadísticas cívicas y logout."""
    pass


# =============================================================================
# APLICACIÓN PRINCIPAL (KivyMD 2.0)
# =============================================================================
class AlertComApp(MDApp):
    """Gestor principal de la aplicación y flujo de pantallas."""

    def build(self):
        # Configuración visual de Material Design 3
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Orange"

        # Cargar archivo de diseño declarativo
        Builder.load_file("alertcom.kv")

        # Configuración del ScreenManager con las 6 pantallas
        sm = ScreenManager()
        sm.add_widget(SafetyScreen(name="safety"))
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(ReportScreen(name="report"))
        sm.add_widget(HistoryScreen(name="history"))
        sm.add_widget(ProfileScreen(name="profile"))

        return sm

    def go_to_screen(self, screen_name, direction="left"):
        """Navegación genérica hacia adelante."""
        if self.root:
            self.root.transition = SlideTransition(direction=direction)
            self.root.current = screen_name

    def go_back(self):
        """Retorna a la pantalla principal (Home)."""
        if self.root:
            self.root.transition = SlideTransition(direction="right")
            self.root.current = "home"

    def logout(self):
        """Cierra sesión simulada y retorna a la pantalla de Login."""
        self.go_to_screen("login", direction="right")

    def on_switch_tabs(self, *args):
        """Controlador de la barra de navegación inferior."""
        try:
            # En KivyMD 2.0 on_switch_tabs pasa: bar, item, item_icon, item_text
            item_text = args[3] if len(args) > 3 else ""
            if item_text == "Mis Reportes":
                self.go_to_screen("history", direction="left")
            elif item_text == "Inicio":
                self.go_to_screen("home", direction="right")
            elif item_text == "Perfil":
                self.go_to_screen("profile", direction="left")
        except Exception:
            pass


# =============================================================================
# PUNTO DE ENTRADA
# =============================================================================
if __name__ == "__main__":
    AlertComApp().run()
