# =============================================================================
# AlertCom - Utilidades visuales: diálogos y avisos
# =============================================================================
# • mostrar_dialogo → MDDialog para errores o confirmaciones (bloquea hasta
#   que el usuario lo cierre, ideal para credenciales inválidas).
# • mostrar_aviso   → MDSnackbar para confirmaciones breves.
# =============================================================================

from kivy.metrics import dp
from kivy.uix.widget import Widget

from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.dialog import (
    MDDialog,
    MDDialogButtonContainer,
    MDDialogHeadlineText,
    MDDialogIcon,
    MDDialogSupportingText,
)
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText


def mostrar_dialogo(
    titulo: str,
    mensaje: str,
    icono: str = "alert-circle-outline",
    botones: list[tuple[str, callable]] | None = None,
) -> MDDialog:
    """
    Muestra un MDDialog (KivyMD 2.0).

    Args:
        titulo: Encabezado del diálogo.
        mensaje: Texto explicativo.
        icono: Ícono superior (nombre de Material Design Icons).
        botones: Lista de (texto, funcion). Si no se indica, se muestra
                 un único botón "Entendido" que cierra el diálogo.
    """
    dialogo = None

    def crear_boton(texto, accion):
        def al_presionar(*_):
            dialogo.dismiss()
            if accion:
                accion()

        return MDButton(MDButtonText(text=texto), style="text", on_release=al_presionar)

    lista_botones = [crear_boton(t, a) for t, a in (botones or [("Entendido", None)])]

    dialogo = MDDialog(
        MDDialogIcon(icon=icono),
        MDDialogHeadlineText(text=titulo),
        MDDialogSupportingText(text=mensaje),
        MDDialogButtonContainer(Widget(), *lista_botones, spacing="8dp"),
    )
    dialogo.open()
    return dialogo


def mostrar_aviso(texto: str) -> None:
    """Mensaje breve en la parte inferior (MDSnackbar)."""
    MDSnackbar(
        MDSnackbarText(text=texto),
        y=dp(24),
        pos_hint={"center_x": 0.5},
        size_hint_x=0.9,
    ).open()
