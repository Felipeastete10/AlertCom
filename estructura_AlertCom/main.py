# =============================================================================
# AlertCom - Motor Principal (Orquestador de Navegación MVC)
# =============================================================================
# Archivo:      estructura_AlertCom/main.py
# Responsable:  Arquitectura MVC / Orquestador
#
# Propósito:
#   Punto de entrada único de la aplicación. Configura el tema, registra las
#   pantallas en el ScreenManager, inyecta los controladores en las vistas y
#   expone los métodos de navegación. No contiene lógica de negocio ni diseño
#   de UI (todo el diseño declarativo vive en alertcom.kv).
#
# Patrón: MVC
#   - models/       → Clases de dominio (Usuario, Incidente)
#   - controllers/  → Lógica de negocio (AuthController, IncidenteController)
#   - views/        → Pantallas y UI (Safety, Login, Home, Report, History,
#                     Profile)
#   - main.py       → Orquestador / Compositor
# =============================================================================

from pathlib import Path

from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, SlideTransition
from kivy.core.window import Window

from kivymd.app import MDApp

# ---------------------------------------------------------------------------
# Rutas absolutas dinámicas (independientes del CWD)
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
KV_FILE = BASE_DIR / "Diseño_AlertCom" / "alertcom.kv"

# ---------------------------------------------------------------------------
# Importación de paquetes internos
# ---------------------------------------------------------------------------
from models import Usuario, Incidente  # noqa: E402  (modelos de dominio)
from controllers import (  # noqa: E402
    AuthController,
    IncidenteController,
)
from views import (  # noqa: E402
    SafetyScreen,
    LoginScreen,
    HomeScreen,
    ReportScreen,
    HistoryScreen,
    ProfileScreen,
)

# Simulación de resolución móvil estándar (360×640) en entorno de escritorio.
Window.size = (360, 640)


class AlertComApp(MDApp):
    """
    Gestor principal de AlertCom.

    Responsabilidades exclusivas:
      • Configurar el tema Material Design 3.
      • Cargar el archivo KV declarativo con rutas absolutas.
      • Instanciar controladores y inyectarlos en las vistas.
      • Registrar pantallas en el ScreenManager.
      • Proveer métodos de navegación genéricos.
    """

    def build(self) -> ScreenManager:
        # Tema visual ─ Material Design 3
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Orange"

        # Cargar diseño declarativo con ruta absoluta (evita FileNotFoundError
        # por dependencia del directorio de trabajo actual).
        Builder.load_file(str(KV_FILE))

        # --- Capa de controladores (inyección de dependencias) ---
        self.auth_controller = AuthController()
        self.incidente_controller = IncidenteController()

        # Usuario de demostración para el MVP (en producción vendría de la API)
        self.usuario_demo = Usuario(
            id_usuario=1,
            nombre="Usuario Demo",
            email="demo@alertcom.cl",
            contrasena="demo123",
        )

        # --- ScreenManager con las 6 pantallas del flujo MVP ---
        sm = ScreenManager()
        sm.add_widget(SafetyScreen(name="safety"))
        sm.add_widget(
            LoginScreen(
                name="login",
                usuario=self.usuario_demo,
                auth_controller=self.auth_controller,
                on_login_success=lambda: self.go_to_screen("home", "left"),
            )
        )
        sm.add_widget(
            HomeScreen(
                name="home",
                incidente_controller=self.incidente_controller,
            )
        )
        sm.add_widget(
            ReportScreen(
                name="report",
                incidente_controller=self.incidente_controller,
            )
        )
        sm.add_widget(
            HistoryScreen(
                name="history",
                incidente_controller=self.incidente_controller,
            )
        )
        sm.add_widget(
            ProfileScreen(
                name="profile",
                auth_controller=self.auth_controller,
            )
        )

        return sm

    # ------------------------------------------------------------------
    # NAVEGACIÓN
    # ------------------------------------------------------------------
    def go_to_screen(self, screen_name: str, direction: str = "left") -> None:
        """Navega hacia cualquier pantalla con transición deslizante."""
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
        if self.auth_controller:
            self.auth_controller.cerrar_sesion()
        self.go_to_screen("login", direction="right")

    def on_switch_tabs(self, *args) -> None:
        """
        Callback para MDNavigationBar.on_switch_tabs (KivyMD 2.0).

        Señal: (bar_instance, item_instance, item_icon, item_text)
        """
        rutas = {
            "Inicio": ("home", "right"),
            "Mis Reportes": ("history", "left"),
            "Perfil": ("profile", "left"),
        }
        try:
            item_text = args[3] if len(args) > 3 else ""
            if item_text in rutas:
                pantalla, direccion = rutas[item_text]
                self.go_to_screen(pantalla, direction=direccion)
        except (IndexError, TypeError):
            pass


# =============================================================================
# PUNTO DE ENTRADA
# =============================================================================
if __name__ == "__main__":
    AlertComApp().run()
