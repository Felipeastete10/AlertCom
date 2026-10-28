# =============================================================================
# AlertCom - Vista: Formulario de Reporte (ReportScreen)
# =============================================================================
# Captura foto (simulada), tipo, gravedad y descripción, y se los entrega al
# IncidenteController. La vista no valida reglas de negocio ni genera IDs:
# si el controlador rechaza los datos, aquí solo se muestra el error.
# =============================================================================

from kivymd.app import MDApp
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.screen import MDScreen

from config import CENTRO_TEMUCO, GRAVEDADES, TIPOS_DANO
from views.componentes.dialogos import mostrar_aviso, mostrar_dialogo

TEXTO_FOTO_INICIAL = "Toca para tomar o seleccionar una foto"


class ReportScreen(MDScreen):
    """Formulario para registrar un nuevo daño vial."""

    def __init__(self, incidente_controller=None, auth_controller=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.incidente_controller = incidente_controller
        self.auth_controller = auth_controller
        self.tipo = None
        self.gravedad = None
        self.foto = None
        self.ubicacion = None
        self.menu_tipo = self._crear_menu(TIPOS_DANO, self.elegir_tipo)
        self.menu_gravedad = self._crear_menu(GRAVEDADES, self.elegir_gravedad)

    def _crear_menu(self, opciones, al_elegir) -> MDDropdownMenu:
        items = [{"text": opcion, "on_release": lambda o=opcion: al_elegir(o)} for opcion in opciones]
        return MDDropdownMenu(items=items)

    def on_pre_enter(self, *args) -> None:
        self.limpiar_formulario()

    def limpiar_formulario(self) -> None:
        self.tipo = None
        self.gravedad = None
        self.foto = None
        self.ubicacion = None
        self.ids.type_label.text = "Seleccionar tipo"
        self.ids.severity_label.text = "Seleccionar gravedad"
        self.ids.description_field.text = ""
        self.ids.photo_label.text = TEXTO_FOTO_INICIAL

    # ------------------------------------------------------------------
    # Menús desplegables
    # ------------------------------------------------------------------
    def abrir_menu_tipo(self) -> None:
        self.menu_tipo.caller = self.ids.type_selector
        self.menu_tipo.open()

    def abrir_menu_gravedad(self) -> None:
        self.menu_gravedad.caller = self.ids.severity_selector
        self.menu_gravedad.open()

    def elegir_tipo(self, valor: str) -> None:
        self.tipo = valor
        self.ids.type_label.text = valor
        self.menu_tipo.dismiss()

    def elegir_gravedad(self, valor: str) -> None:
        self.gravedad = valor
        self.ids.severity_label.text = valor
        self.menu_gravedad.dismiss()

    # ------------------------------------------------------------------
    # Foto y GPS simulados (se reemplazan por Plyer camera/gps más adelante)
    # ------------------------------------------------------------------
    def simular_foto(self) -> None:
        self.foto = "mock_foto_reporte.jpg"
        lat, lon = CENTRO_TEMUCO
        self.ubicacion = f"{lat}, {lon}"
        self.ids.photo_label.text = f"Foto lista · GPS {self.ubicacion}"

    # ------------------------------------------------------------------
    # Envío
    # ------------------------------------------------------------------
    def enviar_reporte(self) -> None:
        usuario = self.auth_controller.usuario_actual if self.auth_controller else None
        try:
            incidente = self.incidente_controller.crear_incidente(
                tipo=self.tipo,
                gravedad=self.gravedad,
                descripcion=self.ids.description_field.text,
                foto=self.foto,
                ubicacion=self.ubicacion or "{}, {}".format(*CENTRO_TEMUCO),
                usuario_id=usuario.id_usuario if usuario else None,
            )
        except ValueError as error:
            mostrar_dialogo("Falta información", str(error), icono="clipboard-alert-outline")
            return

        mostrar_aviso(f"Reporte #{incidente.id_incidente} enviado")
        MDApp.get_running_app().navegacion.ir_a("history", "left")
