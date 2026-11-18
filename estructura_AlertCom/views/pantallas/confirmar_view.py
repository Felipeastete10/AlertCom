# =============================================================================
# AlertCom - Vista: Confirmar reportes (ConfirmarScreen) — solo funcionario
# =============================================================================
# Un espacio dedicado a revisar los reportes nuevos de los vecinos:
#   • Solo aparecen los reportes "Por confirmar".
#   • Primero los más graves (Crítico → Leve) y, entre iguales, el más antiguo.
#   • Filtro por gravedad arriba.
#   • Cada tarjeta trae la foto y los botones Confirmar / No aprobar: se
#     decide sin abrir ventanas. Tocar la foto abre el detalle completo.
# La navegación protege la pantalla: un vecino que intente entrar vuelve al
# inicio (views/navegador.py).
# =============================================================================

from kivy.animation import Animation
from kivy.factory import Factory
from kivymd.app import MDApp
from kivymd.uix.label import MDLabel

from config import MOTIVOS_NO_APROBAR
from controllers.fotos import ruta_foto
from views.componentes.detalle_reporte import mostrar_detalle_reporte
from views.componentes.dialogos import mostrar_aviso, mostrar_dialogo
from views.componentes.estilos import ESTILO_GRAVEDAD, GRIS, ICONO_TIPO
from views.componentes.filtros import PRIORIDAD_GRAVEDAD, FiltroGravedad
from views.componentes.formulario import elegir_opcion
from views.componentes.interaccion import aparecer_en_cascada
from views.componentes.pantalla_base import PantallaBase


class ConfirmarScreen(PantallaBase):
    # Se crea en on_kv_post, que Kivy llama ANTES de terminar __init__: por
    # eso no se asigna en __init__ (lo borraría).
    filtro = None

    def __init__(self, incidente_controller=None, auth_controller=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.incidente_controller = incidente_controller
        self.auth_controller = auth_controller

    def on_kv_post(self, base_widget) -> None:
        super().on_kv_post(base_widget)
        self.filtro = FiltroGravedad(self.ids.filtro_gravedad, al_cambiar=self.cargar_lista)

    @property
    def _usuario(self):
        return self.auth_controller.usuario_actual if self.auth_controller else None

    def on_pre_enter(self, *args) -> None:
        self.filtro.reiniciar()
        self.cargar_lista(animar=True)
        MDApp.get_running_app().controlador.sincronizar()  # trae los reportes más nuevos

    def refrescar(self) -> None:
        """Llegaron reportes de la nube."""
        self.cargar_lista()

    # ------------------------------------------------------------------
    # Lista
    # ------------------------------------------------------------------
    def _por_confirmar(self) -> list:
        """Primero los más graves; entre iguales, el que lleva más esperando."""
        return sorted(self.incidente_controller.por_confirmar(),
                      key=lambda i: (PRIORIDAD_GRAVEDAD.get(i.gravedad, 99), i.fecha_creacion))

    def cargar_lista(self, animar: bool = False) -> None:
        todos = self._por_confirmar()
        self.filtro.actualizar(todos)
        reportes = self.filtro.aplicar(todos)

        if not todos:
            self.ids.resumen.text = "No hay reportes nuevos por revisar."
        else:
            plural = "reporte espera" if len(todos) == 1 else "reportes esperan"
            self.ids.resumen.text = f"{len(todos)} {plural} tu revisión. Primero los más graves."

        lista = self.ids.lista
        lista.clear_widgets()
        if not reportes:
            texto = ("¡Todo al día! Cuando un vecino envíe un reporte, aparecerá aquí."
                     if not todos else f"No hay reportes «{self.filtro.elegida}» por confirmar.")
            lista.add_widget(MDLabel(text=texto, halign="center", theme_text_color="Secondary",
                                     adaptive_height=True, padding=("16dp", "32dp")))
            return

        carpeta_datos = MDApp.get_running_app().controlador.carpeta_datos
        tarjetas = []
        for incidente in reportes:
            icono_gravedad, color_gravedad = ESTILO_GRAVEDAD.get(incidente.gravedad, ("gauge", GRIS))
            foto = ruta_foto(carpeta_datos, incidente.imagen)
            tarjeta = Factory.TarjetaConfirmar()
            # Las propiedades de una clase del .kv se asignan después de crearla
            for propiedad, valor in dict(
                titulo=f"#{incidente.id_incidente} · {incidente.tipo_incidente}",
                calle=incidente.calle or "Sin calle registrada",
                gravedad=incidente.gravedad or "Sin gravedad",
                icono_gravedad=icono_gravedad,
                color_gravedad=color_gravedad,
                fecha=f"Llegó {incidente.antiguedad_legible()}",
                descripcion=incidente.descripcion or "",
                icono_tipo=ICONO_TIPO.get(incidente.tipo_incidente, "alert-circle-outline"),
                foto=str(foto) if foto else "",
            ).items():
                setattr(tarjeta, propiedad, valor)
            id_reporte = incidente.id_incidente
            tarjeta.ids.boton_confirmar.bind(on_release=lambda _b, n=id_reporte, t=tarjeta: self.confirmar(n, t))
            tarjeta.ids.boton_no_aprobar.bind(on_release=lambda _b, n=id_reporte, t=tarjeta: self.no_aprobar(n, t))
            tarjeta.ids.zona_foto.bind(on_release=lambda _z, inc=incidente: mostrar_detalle_reporte(
                inc, icono="shield-search"))
            lista.add_widget(tarjeta)
            tarjetas.append(tarjeta)
        if animar:
            aparecer_en_cascada(tarjetas)

    # ------------------------------------------------------------------
    # Decisiones
    # ------------------------------------------------------------------
    def _quitar(self, tarjeta, mensaje: str) -> None:
        """La tarjeta se desvanece y la lista se vuelve a armar."""
        animacion = Animation(opacity=0, duration=0.2)
        animacion.bind(on_complete=lambda *_: self.cargar_lista())
        animacion.start(tarjeta)
        mostrar_aviso(mensaje)

    def confirmar(self, id_incidente: int, tarjeta) -> None:
        try:
            self.incidente_controller.confirmar_reporte(id_incidente, self._usuario)
        except (ValueError, PermissionError) as error:
            mostrar_dialogo("No se pudo confirmar", str(error), icono="alert-circle-outline")
            self.cargar_lista()
            return
        self._quitar(tarjeta, f"Reporte #{id_incidente} confirmado y publicado.")

    def no_aprobar(self, id_incidente: int, tarjeta) -> None:
        def decidir(motivo):
            try:
                self.incidente_controller.no_aprobar_reporte(id_incidente, self._usuario, motivo)
            except (ValueError, PermissionError) as error:
                return False, str(error)
            self._quitar(tarjeta, f"Reporte #{id_incidente} no aprobado.")
            return True, ""

        elegir_opcion(
            f"¿No aprobar el reporte #{id_incidente}?", "shield-remove-outline",
            MOTIVOS_NO_APROBAR, decidir,
            texto_boton="No aprobar",
            explicacion=("El reporte y su foto se borrarán y nunca aparecerán en el mapa. "
                         "El vecino recibirá un aviso. ¿Por qué no se aprueba?"),
        )
