# =============================================================================
# AlertCom - Motor Principal (Orquestador de Navegación)
# =============================================================================
# Archivo:      main.py
# Rama:         setup/arquitectura-base
# Responsable:  Felipe Astete (Arquitecto e Integrador)
#
# Propósito:
#   Este archivo actúa ÚNICAMENTE como orquestador de la aplicación.
#   Configura el tema visual, registra las pantallas en el ScreenManager
#   y expone los métodos de navegación que las vistas y controladores
#   invocarán. NO contiene lógica de datos ni diseño de UI.
#
# Tecnologías:
#   Python 3.11.1 | Kivy 2.3.1 | KivyMD 2.0.1.dev0 (Material Design 3)
#
# Patrón:  MVC
#   - models/       → Clases de datos (Allan)
#   - views/        → Pantallas y UI (Nico, Felipe Salazar)
#   - controllers/  → Lógica de negocio (Roberto)
#   - main.py       → Orquestador (Felipe Astete)
# =============================================================================

from kivy.uix.screenmanager import ScreenManager, SlideTransition
from kivy.core.window import Window

from kivymd.app import MDApp

# Importar las 6 pantallas desde el paquete de vistas
from views import (
    SafetyScreen,
    LoginScreen,
    HomeScreen,
    ReportScreen,
    HistoryScreen,
    ProfileScreen,
)

# ---------------------------------------------------------------------------
# Simulación de resolución móvil estándar (360×640) en entorno de escritorio.
# Comentar o eliminar esta línea para despliegue en dispositivo real.
# ---------------------------------------------------------------------------
Window.size = (360, 640)


# =============================================================================
# CLASE PRINCIPAL DE LA APLICACIÓN
# =============================================================================
class AlertComApp(MDApp):
    """
    Gestor principal de AlertCom.

    Responsabilidades exclusivas:
      • Configurar el tema Material Design 3 (Dark / Orange).
      • Inicializar el ScreenManager con las pantallas del paquete views/.
      • Proveer métodos de navegación genéricos (go_to_screen, go_back).
      • Enrutar eventos de la barra de navegación inferior (on_switch_tabs).
    """

    # --------------------------------------------------------------------- #
    #  CICLO DE VIDA
    # --------------------------------------------------------------------- #
    def build(self) -> ScreenManager:
        """Configura el tema y construye el ScreenManager con las 6 pantallas."""

        # Tema visual ─ Material Design 3
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Orange"

        # --- ScreenManager ---
        # Cuando el equipo de Vistas entregue los .kv, se cargará aquí:
        #   Builder.load_file("views/alertcom.kv")
        sm = ScreenManager()

        # Registro ordenado de pantallas (el flujo natural del usuario)
        sm.add_widget(SafetyScreen(name="safety"))
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(ReportScreen(name="report"))
        sm.add_widget(HistoryScreen(name="history"))
        sm.add_widget(ProfileScreen(name="profile"))

        return sm

    # --------------------------------------------------------------------- #
    #  NAVEGACIÓN
    # --------------------------------------------------------------------- #
    def go_to_screen(self, screen_name: str, direction: str = "left") -> None:
        """
        Navega hacia cualquier pantalla con transición deslizante.

        Args:
            screen_name: Nombre registrado de la pantalla destino
                         ("safety", "login", "home", "report",
                          "history", "profile").
            direction:   Dirección del SlideTransition
                         ("left", "right", "up", "down").
        """
        if self.root:
            self.root.transition = SlideTransition(direction=direction)
            self.root.current = screen_name

    def go_back(self) -> None:
        """Regresa a la pantalla Home con transición hacia la derecha."""
        if self.root:
            self.root.transition = SlideTransition(direction="right")
            self.root.current = "home"

    def logout(self) -> None:
        """Cierra sesión y retorna a la pantalla de Login."""
        self.go_to_screen("login", direction="right")

    # --------------------------------------------------------------------- #
    #  BARRA DE NAVEGACIÓN INFERIOR (MDNavigationBar – KivyMD 2.0)
    # --------------------------------------------------------------------- #
    def on_switch_tabs(self, *args) -> None:
        """
        Callback para MDNavigationBar.on_switch_tabs.

        En KivyMD 2.0.1.dev0 la señal envía:
            (bar_instance, item_instance, item_icon, item_text)

        Enruta a la pantalla correspondiente según el texto del tab:
            • "Inicio"       → HomeScreen
            • "Mis Reportes" → HistoryScreen
            • "Perfil"       → ProfileScreen
        """
        # Mapa de rutas: texto del tab → (nombre_pantalla, dirección)
        rutas = {
            "Inicio":       ("home",    "right"),
            "Mis Reportes": ("history", "left"),
            "Perfil":       ("profile", "left"),
        }

        try:
            # El texto del tab llega en la posición args[3]
            item_text = args[3] if len(args) > 3 else ""
            if item_text in rutas:
                pantalla, direccion = rutas[item_text]
                self.go_to_screen(pantalla, direction=direccion)
        except (IndexError, TypeError):
            # Protección ante cambios futuros en la API de KivyMD
            pass


# =============================================================================
# PUNTO DE ENTRADA
# =============================================================================
if __name__ == "__main__":
    AlertComApp().run()
