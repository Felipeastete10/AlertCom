# =============================================================================
# AlertCom - Ventana con campos (gestor de cuenta)
# =============================================================================
# pedir_datos() abre un MDDialog con uno o más campos de texto. Al tocar el
# botón de confirmar llama a al_confirmar(valores) → (exito, mensaje):
#   • si falla: el error aparece dentro de la ventana y los campos se sacuden;
#   • si funciona: la ventana se cierra y aparece un aviso.
# =============================================================================

from kivy.metrics import dp
from kivy.uix.widget import Widget
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.dialog import (
    MDDialog,
    MDDialogButtonContainer,
    MDDialogContentContainer,
    MDDialogHeadlineText,
    MDDialogIcon,
    MDDialogSupportingText,
)
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField, MDTextFieldHintText

from views.componentes.dialogos import mostrar_aviso
from views.componentes.interaccion import sacudir, vibrar


def pedir_datos(titulo, icono, campos, al_confirmar, texto_boton="Guardar",
                explicacion="", peligro=False):
    """
    campos: lista de (clave, texto_de_ayuda, es_contrasena, valor_inicial).
    al_confirmar: función(valores: dict) → (exito: bool, mensaje: str).
    """
    entradas = {}
    caja = MDBoxLayout(orientation="vertical", spacing=dp(12), adaptive_height=True,
                       padding=(0, dp(8), 0, 0))
    for clave, ayuda, es_contrasena, inicial in campos:
        campo = MDTextField(MDTextFieldHintText(text=ayuda), mode="outlined",
                            password=es_contrasena, text=inicial or "", write_tab=False)
        entradas[clave] = campo
        caja.add_widget(campo)
    error = MDLabel(text="", adaptive_height=True, font_style="Body", role="medium",
                    theme_text_color="Custom", text_color=(1, 0.45, 0.42, 1), halign="center")
    caja.add_widget(error)

    color_boton = (0.8, 0.25, 0.25, 1) if peligro else None
    boton_ok = MDButton(MDButtonText(text=texto_boton), style="filled")
    if color_boton:
        boton_ok.theme_bg_color = "Custom"
        boton_ok.md_bg_color = color_boton
    boton_cancelar = MDButton(MDButtonText(text="Cancelar"), style="text")

    partes = [MDDialogIcon(icon=icono), MDDialogHeadlineText(text=titulo)]
    if explicacion:
        partes.append(MDDialogSupportingText(text=explicacion))
    partes += [MDDialogContentContainer(caja),
               MDDialogButtonContainer(Widget(), boton_cancelar, boton_ok, spacing=dp(8))]
    dialogo = MDDialog(*partes)

    def confirmar(*_):
        valores = {clave: campo.text for clave, campo in entradas.items()}
        exito, mensaje = al_confirmar(valores)
        if exito:
            dialogo.dismiss()
            if mensaje:
                mostrar_aviso(mensaje)
        else:
            error.text = mensaje
            sacudir(caja)
            vibrar(80)

    boton_ok.bind(on_release=confirmar)
    boton_cancelar.bind(on_release=lambda *_: dialogo.dismiss())
    for campo in entradas.values():
        campo.bind(text=lambda *_: setattr(error, "text", ""))
    dialogo.open()
    return dialogo


def elegir_opcion(titulo, icono, opciones, al_confirmar, texto_boton="Enviar", explicacion=""):
    """
    Ventana con opciones que se tocan (pastillas). al_confirmar(opcion) →
    (exito, mensaje). Si no se elige nada, se pide elegir antes de seguir.
    """
    from kivymd.uix.stacklayout import MDStackLayout

    from views.componentes.interaccion import Pastilla

    elegida = {"valor": None}
    caja = MDBoxLayout(orientation="vertical", spacing=dp(10), adaptive_height=True,
                       padding=(0, dp(8), 0, 0))
    grupo = MDStackLayout(adaptive_height=True, spacing=dp(8))
    for opcion in opciones:
        pastilla = Pastilla(texto=opcion, valor=opcion, icono="circle-outline")

        def tocar(p):
            elegida["valor"] = p.valor
            for otra in grupo.children:
                otra.seleccionada = otra is p
            error.text = ""
        pastilla.bind(on_release=tocar)
        grupo.add_widget(pastilla)
    caja.add_widget(grupo)
    error = MDLabel(text="", adaptive_height=True, font_style="Body", role="medium",
                    theme_text_color="Custom", text_color=(1, 0.45, 0.42, 1), halign="center")
    caja.add_widget(error)

    boton_ok = MDButton(MDButtonText(text=texto_boton), style="filled")
    boton_cancelar = MDButton(MDButtonText(text="Cancelar"), style="text")
    partes = [MDDialogIcon(icon=icono), MDDialogHeadlineText(text=titulo)]
    if explicacion:
        partes.append(MDDialogSupportingText(text=explicacion))
    partes += [MDDialogContentContainer(caja),
               MDDialogButtonContainer(Widget(), boton_cancelar, boton_ok, spacing=dp(8))]
    dialogo = MDDialog(*partes)

    def confirmar(*_):
        if elegida["valor"] is None:
            error.text = "Elige una opción."
            sacudir(grupo)
            return
        exito, mensaje = al_confirmar(elegida["valor"])
        if exito:
            dialogo.dismiss()
            if mensaje:
                mostrar_aviso(mensaje)
        else:
            error.text = mensaje
            sacudir(grupo)
            vibrar(80)

    boton_ok.bind(on_release=confirmar)
    boton_cancelar.bind(on_release=lambda *_: dialogo.dismiss())
    dialogo.open()
    return dialogo
