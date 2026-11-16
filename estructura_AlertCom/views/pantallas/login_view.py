# =============================================================================
# AlertCom - Vista: Pantalla de Inicio de Sesión (LoginScreen)
# =============================================================================
# Captura correo y contraseña y delega la validación al AuthController (que
# lee usuarios.json).
#
# Interacción:
#   • El logo "rebota" al entrar.
#   • El ojo del campo contraseña la muestra u oculta.
#   • Si los datos no coinciden: los campos se sacuden, el teléfono vibra y
#     el error aparece debajo (sin una ventana que interrumpa). El error se
#     borra apenas la persona vuelve a escribir.
# =============================================================================

from kivy.animation import Animation
from kivy.metrics import dp, sp
from kivymd.app import MDApp

from views.componentes.interaccion import sacudir, vibrar
from views.componentes.pantalla_base import PantallaBase


class LoginScreen(PantallaBase):
    """Pantalla de inicio de sesión (correo + contraseña)."""

    def __init__(self, auth_controller=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.auth_controller = auth_controller

    def on_kv_post(self, base_widget) -> None:
        super().on_kv_post(base_widget)
        self.ids.password_field.bind(on_touch_down=self._tocar_ojo)
        for campo in (self.ids.email_field, self.ids.password_field):
            campo.bind(text=lambda *_: self._ocultar_error())

    def on_pre_enter(self, *args) -> None:
        # Seguridad: nunca dejar la contraseña escrita al volver a esta pantalla.
        self.ids.password_field.text = ""
        self._mostrar_contrasena(False)
        self._ocultar_error()

    def on_enter(self, *args) -> None:
        super().on_enter(*args)
        logo = self.ids.logo
        logo.opacity = 0
        logo.font_size = sp(40)
        (Animation(opacity=1, font_size=sp(76), d=0.3, t="out_quad")
         + Animation(font_size=sp(64), d=0.35, t="out_bounce")).start(logo)

    # ------------------------------------------------------------------
    # Mostrar / ocultar contraseña
    # ------------------------------------------------------------------
    def _tocar_ojo(self, campo, toque):
        """El ícono del ojo está dibujado dentro del campo: si el toque cae
        en su zona (los últimos 48 dp a la derecha), alterna la contraseña."""
        if campo.collide_point(*toque.pos) and toque.x >= campo.right - dp(48):
            self._mostrar_contrasena(campo.password)  # si estaba oculta, mostrarla
            return True  # el toque no abre el teclado
        return None

    def _mostrar_contrasena(self, mostrar: bool) -> None:
        self.ids.password_field.password = not mostrar
        self.ids.ojo.icon = "eye-outline" if mostrar else "eye-off-outline"

    # ------------------------------------------------------------------
    # Error en línea
    # ------------------------------------------------------------------
    def _mostrar_error(self, mensaje: str) -> None:
        etiqueta = self.ids.error_label
        etiqueta.text = mensaje
        Animation.cancel_all(etiqueta)
        Animation(opacity=1, d=0.2).start(etiqueta)
        sacudir(self.ids.caja_campos)
        vibrar(80)

    def _ocultar_error(self) -> None:
        etiqueta = self.ids.error_label
        if etiqueta.opacity:
            Animation(opacity=0, d=0.15).start(etiqueta)

    # ------------------------------------------------------------------
    # Acciones
    # ------------------------------------------------------------------
    def validate_login(self) -> None:
        correo = self.ids.email_field.text
        contrasena = self.ids.password_field.text

        exito, mensaje = self.auth_controller.iniciar_sesion(correo, contrasena)
        if not exito:
            self.ids.password_field.text = ""
            self._mostrar_error(mensaje)
            return

        self.ids.email_field.text = ""
        self.ids.password_field.text = ""
        MDApp.get_running_app().navegacion.ir_a("home", "left")

    def ir_a_registro(self) -> None:
        MDApp.get_running_app().navegacion.ir_a("register", "left")
