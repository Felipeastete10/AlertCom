# =============================================================================
# AlertCom - Vista: Ajustes (AjustesScreen)
# =============================================================================
# • Apariencia: tamaño de letra y color de fondo. Se aplican al instante a
#   toda la app y se guardan en preferencias.json.
# • Mi cuenta: cambiar nombre, correo o contraseña y eliminar la cuenta.
#   Las reglas (validar, pedir la contraseña actual, guardar) están en el
#   AuthController; esta vista solo pide los datos y muestra el resultado.
# =============================================================================

from kivy.factory import Factory
from kivymd.app import MDApp

from config import FONDOS, TAMANOS_LETRA
from views.apariencia import aplicar_fondo, aplicar_tamano_letra
from views.componentes.formulario import pedir_datos
from views.componentes.interaccion import Pastilla
from views.componentes.pantalla_base import PantallaBase


class AjustesScreen(PantallaBase):

    def __init__(self, auth_controller=None, incidente_controller=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.auth_controller = auth_controller
        self.incidente_controller = incidente_controller

    @property
    def _app(self):
        return MDApp.get_running_app()

    @property
    def _preferencias(self):
        return self._app.controlador.preferencias

    def on_kv_post(self, base_widget) -> None:
        super().on_kv_post(base_widget)
        for clave, texto, _ in TAMANOS_LETRA:
            pastilla = Pastilla(texto=texto, valor=clave, icono="format-letter-case")
            pastilla.bind(on_release=lambda p: self.elegir_letra(p.valor))
            self.ids.grupo_letra.add_widget(pastilla)
        for clave, texto, color in FONDOS:
            # Las propiedades de una clase del .kv se asignan después de crearla
            muestra = Factory.MuestraFondo()
            muestra.clave, muestra.texto = clave, texto
            muestra.color = color or [0.08, 0.07, 0.07, 1]
            muestra.bind(on_release=lambda m: self.elegir_fondo(m.clave))
            self.ids.grupo_fondo.add_widget(muestra)

    def on_pre_enter(self, *args) -> None:
        # La muestra "Original" usa el color real del tema.
        for muestra in self.ids.grupo_fondo.children:
            if muestra.clave == "original":
                muestra.color = self._app.theme_cls.surfaceColor
        self._marcar_seleccion()
        self._mostrar_cuenta()

    def _marcar_seleccion(self) -> None:
        letra = self._preferencias.obtener("tamano_letra", "normal")
        fondo = self._preferencias.obtener("fondo", "original")
        for pastilla in self.ids.grupo_letra.children:
            pastilla.seleccionada = pastilla.valor == letra
        for muestra in self.ids.grupo_fondo.children:
            muestra.seleccionada = muestra.clave == fondo

    def _mostrar_cuenta(self) -> None:
        usuario = self.auth_controller.usuario_actual if self.auth_controller else None
        if usuario is None:
            return
        self.ids.inicial.text = (usuario.nombre[:1] or "?").upper()
        self.ids.nombre_cuenta.text = usuario.nombre
        self.ids.correo_cuenta.text = usuario.email
        self.ids.rol_cuenta.text = usuario.rol_legible

    # ------------------------------------------------------------------
    # Apariencia
    # ------------------------------------------------------------------
    def elegir_letra(self, clave: str) -> None:
        aplicar_tamano_letra(self._app, clave)
        self._preferencias.guardar("tamano_letra", clave)
        self._marcar_seleccion()

    def elegir_fondo(self, clave: str) -> None:
        aplicar_fondo(self._app, clave)
        self._preferencias.guardar("fondo", clave)
        self._marcar_seleccion()

    # ------------------------------------------------------------------
    # Gestor de cuenta
    # ------------------------------------------------------------------
    def _y_refrescar(self, resultado):
        self._mostrar_cuenta()
        return resultado

    def cambiar_nombre(self) -> None:
        actual = self.auth_controller.usuario_actual
        pedir_datos(
            "Cambiar nombre", "account-edit-outline",
            [("nombre", "Nombre", False, actual.nombre if actual else "")],
            lambda v: self._y_refrescar(self.auth_controller.cambiar_nombre(v["nombre"])),
        )

    def cambiar_correo(self) -> None:
        pedir_datos(
            "Cambiar correo", "email-edit-outline",
            [("correo", "Correo nuevo", False, ""), ("clave", "Contraseña actual", True, "")],
            lambda v: self._y_refrescar(self.auth_controller.cambiar_correo(v["correo"], v["clave"])),
            explicacion="Por seguridad, confirma con tu contraseña actual.",
        )

    def cambiar_contrasena(self) -> None:
        pedir_datos(
            "Cambiar contraseña", "lock-reset",
            [("actual", "Contraseña actual", True, ""),
             ("nueva", "Contraseña nueva (mín. 6)", True, ""),
             ("repetir", "Repite la contraseña nueva", True, "")],
            lambda v: self.auth_controller.cambiar_contrasena(v["actual"], v["nueva"], v["repetir"]),
        )

    def eliminar_cuenta(self) -> None:
        def confirmar(valores):
            usuario = self.auth_controller.usuario_actual
            uid = usuario.uid if usuario else None
            exito, mensaje = self.auth_controller.eliminar_cuenta(valores["clave"])
            if exito and uid is not None:
                self.incidente_controller.desvincular_usuario(uid)
                self._app.navegacion.ir_a("login", "right")
            return exito, mensaje

        pedir_datos(
            "¿Eliminar tu cuenta?", "account-remove-outline",
            [("clave", "Contraseña actual", True, "")],
            confirmar,
            texto_boton="Eliminar",
            explicacion=("Se borrarán tu nombre, correo y contraseña. Tus reportes seguirán en "
                         "el mapa (sin tu nombre) para que la municipalidad los repare. "
                         "Esta acción no se puede deshacer."),
            peligro=True,
        )
