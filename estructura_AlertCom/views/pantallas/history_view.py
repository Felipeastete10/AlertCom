# =============================================================================
# AlertCom - Vista: Historial de Reportes (HistoryScreen)
# =============================================================================
# Llena SOLO la lista y los contadores definidos en views/kv/history.kv (ya no borra
# la pantalla completa).
#   • Vecino: dos pestañas, "Mis reportes" (incluye los por confirmar) y
#     "Confirmados" (todos los baches ya confirmados de Temuco).
#   • Funcionario: todos los reportes; puede avanzar su estado.
#   • Todos: contadores por estado y filtro por gravedad.
# =============================================================================

from kivy.factory import Factory
from kivy.metrics import dp
from kivymd.app import MDApp
from kivymd.uix.label import MDLabel

from config import MOTIVOS_ELIMINACION, MOTIVOS_NO_APROBAR
from controllers.fotos import ruta_foto
from views.componentes.formulario import elegir_opcion
from views.componentes.estilos import (COLOR_ESTADO, COLOR_POR_CONFIRMAR, ESTILO_GRAVEDAD, GRIS, ICONO_ESTADO,
                                       ICONO_POR_CONFIRMAR, ICONO_TIPO)
from views.componentes.pantalla_base import PantallaBase

from views.componentes.acciones_municipio import eliminar_como_municipio
from views.componentes.detalle_reporte import mostrar_detalle_reporte
from views.componentes.dialogos import mostrar_aviso, mostrar_dialogo
from views.componentes.filtros import FiltroGravedad
from views.componentes.interaccion import aparecer_en_cascada, contar_hasta


class HistoryScreen(PantallaBase):
    """Pantalla de historial y trazabilidad de reportes."""

    # Se crea en on_kv_post (Kivy lo llama ANTES de terminar __init__)
    filtro_gravedad = None

    def __init__(self, incidente_controller=None, auth_controller=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.incidente_controller = incidente_controller
        self.auth_controller = auth_controller
        self.filtro_estado = None   # None = todos
        self.vista = "mios"         # vecino: "mios" | "confirmados"

    def on_kv_post(self, base_widget) -> None:
        super().on_kv_post(base_widget)
        self.filtro_gravedad = FiltroGravedad(self.ids.filtro_gravedad, al_cambiar=self.cargar_historial)

    @property
    def _usuario(self):
        return self.auth_controller.usuario_actual if self.auth_controller else None

    def on_pre_enter(self, *args) -> None:
        self.filtro_estado = None
        self.vista = "mios"
        self.filtro_gravedad.reiniciar()
        usuario = self._usuario
        vecino = bool(usuario and not usuario.es_municipal)
        caja = self.ids.caja_pestanas
        caja.height = dp(56) if vecino else 0
        caja.opacity = 1 if vecino else 0
        caja.disabled = not vecino
        self.cargar_historial(animar=True)
        MDApp.get_running_app().controlador.sincronizar()

    def refrescar(self) -> None:
        """Llegaron cambios de la nube (otro teléfono): se redibuja la lista."""
        self.cargar_historial()

    def _tarjetas(self) -> dict:
        return {
            None: self.ids.filtro_todos,
            "Pendiente": self.ids.filtro_pendiente,
            "En revisión": self.ids.filtro_revision,
            "Reparado": self.ids.filtro_reparado,
        }

    def _mostrar_aviso_por_confirmar(self) -> None:
        """Al funcionario le avisa cuántos reportes nuevos esperan su revisión."""
        usuario = self._usuario
        cantidad = len(self.incidente_controller.por_confirmar())
        caja = self.ids.caja_confirmar
        visible = bool(usuario and usuario.es_municipal and cantidad)
        caja.height = dp(64) if visible else 0
        caja.opacity = 1 if visible else 0
        caja.disabled = not visible
        if visible:
            plural = "reporte nuevo" if cantidad == 1 else "reportes nuevos"
            self.ids.aviso_confirmar.texto = f"{cantidad} {plural} por confirmar"
            self.ids.aviso_confirmar.activo = self.filtro_estado == "confirmar"
        elif self.filtro_estado == "confirmar":
            self.filtro_estado = None

    def _mostrar_aviso_solicitudes(self) -> None:
        """Al funcionario le avisa cuántas solicitudes de eliminación hay."""
        usuario = self._usuario
        cantidad = len(self.incidente_controller.solicitudes_pendientes())
        caja = self.ids.caja_solicitudes
        visible = bool(usuario and usuario.es_municipal and cantidad)
        caja.height = dp(64) if visible else 0
        caja.opacity = 1 if visible else 0
        caja.disabled = not visible
        if visible:
            plural = "solicitud" if cantidad == 1 else "solicitudes"
            self.ids.aviso_solicitudes.texto = f"{cantidad} {plural} de eliminación por revisar"
            self.ids.aviso_solicitudes.activo = self.filtro_estado == "eliminacion"
        elif self.filtro_estado == "eliminacion":
            self.filtro_estado = None

    def cambiar_vista(self, vista: str) -> None:
        """Pestañas del vecino: sus reportes o los confirmados de la ciudad."""
        if vista != self.vista:
            self.vista = vista
            self.filtro_estado = None
            self.filtro_gravedad.reiniciar()
            self.cargar_historial(animar=True)

    def _reportes_base(self) -> list:
        """Qué lista se está mirando (antes de los filtros)."""
        usuario = self._usuario
        if usuario is None or usuario.es_municipal:
            return self.incidente_controller.obtener_historial()
        if self.vista == "confirmados":
            return [i for i in self.incidente_controller.obtener_historial() if i.confirmado]
        return self.incidente_controller.obtener_historial(usuario.uid)

    def filtrar(self, estado) -> None:
        """Tocar un contador filtra la lista; tocarlo de nuevo vuelve a 'Total'."""
        self.filtro_estado = None if estado == self.filtro_estado else estado
        self.cargar_historial()

    def cargar_historial(self, animar: bool = False) -> None:
        usuario = self._usuario
        vecino = bool(usuario and not usuario.es_municipal)
        if not vecino:
            self.ids.titulo_historial.text = "Todos los reportes"
        else:
            self.ids.titulo_historial.text = ("Confirmados en Temuco" if self.vista == "confirmados"
                                              else "Mis Reportes")
            self.ids.pestana_mios.seleccionada = self.vista == "mios"
            self.ids.pestana_confirmados.seleccionada = self.vista == "confirmados"

        # --- Contadores (suben desde 0 al entrar a la pantalla) ---
        base = self._reportes_base()
        valores = {None: len(base)}
        for estado in ("Pendiente", "En revisión", "Reparado"):
            valores[estado] = sum(r.estado == estado for r in base)
        for estado, tarjeta in self._tarjetas().items():
            tarjeta.activa = estado == self.filtro_estado
            if animar:
                contar_hasta(tarjeta, valores[estado])
            else:
                tarjeta.text = str(valores[estado])

        self._mostrar_aviso_por_confirmar()
        self._mostrar_aviso_solicitudes()

        # --- Lista (solo se limpia la lista, no la pantalla) ---
        lista = self.ids.lista_reportes
        lista.clear_widgets()
        reportes = list(base)
        if self.filtro_estado == "confirmar":
            reportes = [r for r in reportes if not r.confirmado]
            self.ids.texto_filtro.text = (f"Mostrando: reportes por confirmar ({len(reportes)}). "
                                          "Toca uno para revisarlo.")
        elif self.filtro_estado == "eliminacion":
            reportes = [r for r in reportes if r.eliminacion_pendiente]
            self.ids.texto_filtro.text = (f"Mostrando: solicitudes de eliminación ({len(reportes)}). "
                                          "Toca una para decidir.")
        elif self.filtro_estado:
            reportes = [r for r in reportes if r.estado == self.filtro_estado]
            self.ids.texto_filtro.text = f"Mostrando: {self.filtro_estado} ({len(reportes)}). Toca de nuevo para ver todos."
        else:
            self.ids.texto_filtro.text = "Toca un contador para filtrar la lista"

        # --- Filtro por gravedad (cuenta sobre lo que ya filtró el estado) ---
        self.filtro_gravedad.actualizar(reportes)
        reportes = self.filtro_gravedad.aplicar(reportes)
        if self.filtro_gravedad.elegida:
            self.ids.texto_filtro.text += f" · Gravedad: {self.filtro_gravedad.elegida}"

        if not reportes:
            if self.filtro_gravedad.elegida or self.filtro_estado:
                texto = "No hay reportes con esos filtros."
            elif vecino and self.vista == "confirmados":
                texto = "Todavía no hay baches confirmados en Temuco."
            else:
                texto = "Aún no hay reportes. ¡Envía el primero desde el mapa!"
            lista.add_widget(MDLabel(text=texto, halign="center", theme_text_color="Secondary",
                                     adaptive_height=True, padding=("16dp", "24dp")))
            return

        items = []
        carpeta_datos = MDApp.get_running_app().controlador.carpeta_datos
        for incidente in reportes:
            icono_gravedad, color_gravedad = ESTILO_GRAVEDAD.get(incidente.gravedad, ("gauge", GRIS))
            foto = ruta_foto(carpeta_datos, incidente.imagen)
            # Las propiedades de una clase del .kv se asignan después de crearla
            tarjeta = Factory.TarjetaReporte()
            datos = dict(
                titulo=f"#{incidente.id_incidente} · {incidente.tipo_incidente}",
                calle=incidente.calle or "Sin calle registrada",
                gravedad=incidente.gravedad or "Sin gravedad",
                icono_gravedad=icono_gravedad,
                color_gravedad=color_gravedad,
                estado=incidente.estado if incidente.confirmado else "Por confirmar",
                icono_estado=(ICONO_ESTADO.get(incidente.estado, "help-circle") if incidente.confirmado
                              else ICONO_POR_CONFIRMAR),
                color_estado=(COLOR_ESTADO.get(incidente.estado, GRIS) if incidente.confirmado
                              else COLOR_POR_CONFIRMAR),
                icono_tipo=ICONO_TIPO.get(incidente.tipo_incidente, "alert-circle-outline"),
                paso=incidente.paso_estado(),
                fecha=incidente.antiguedad_legible(),
                foto=str(foto) if foto else "",
                por_eliminar=incidente.eliminacion_pendiente,
            )
            for propiedad, valor in datos.items():
                setattr(tarjeta, propiedad, valor)
            tarjeta.bind(on_release=lambda _t, inc=incidente: self.mostrar_detalle(inc))
            lista.add_widget(tarjeta)
            items.append(tarjeta)
        aparecer_en_cascada(items)

    def mostrar_detalle(self, incidente) -> None:
        """Los botones dependen de quién mira el reporte."""
        botones = [("Cerrar", None)]
        usuario = self._usuario
        id_reporte = incidente.id_incidente

        if usuario and usuario.es_municipal:
            if not incidente.confirmado:
                # Reporte nuevo: el funcionario decide si se publica
                botones = [("No aprobar", lambda: self._no_aprobar(id_reporte)),
                           ("Confirmar", lambda: self._confirmar_reporte(id_reporte))]
            elif incidente.eliminacion_pendiente:
                # El funcionario decide sobre la solicitud del vecino. Solo dos
                # botones (tres no caben); tocar fuera de la ventana la cierra.
                # "Aprobar" pide confirmar antes de borrar.
                botones = [("Rechazar", lambda: self._rechazar_eliminacion(id_reporte)),
                           ("Aprobar", lambda: self._confirmar_eliminacion(incidente))]
            else:
                # El funcionario puede eliminar CUALQUIER reporte (con motivo).
                # Tres botones no caben: si hay "Marcar", se cierra tocando fuera.
                siguiente = incidente.siguiente_estado()
                if siguiente:
                    botones = [(f"Marcar: {siguiente}", lambda: self._avanzar_estado(id_reporte))]
                botones.append(("Eliminar", lambda: eliminar_como_municipio(
                    self.incidente_controller, usuario, incidente, al_terminar=self.cargar_historial)))
        elif usuario and incidente.usuario_id == usuario.uid:
            # El dueño del reporte puede pedir (o retirar) la eliminación
            if incidente.eliminacion_pendiente:
                botones.append(("Retirar solicitud", lambda: self._cancelar_solicitud(id_reporte)))
            else:
                botones.append(("Pedir eliminación", lambda: self._pedir_eliminacion(id_reporte)))

        mostrar_detalle_reporte(incidente, botones=botones, icono="clipboard-text-outline")

    # ------------------------------------------------------------------
    # Eliminación: el vecino pide, el funcionario decide
    # ------------------------------------------------------------------
    def _ejecutar(self, accion, mensaje_exito: str) -> tuple[bool, str]:
        """Corre una acción del controlador y traduce los errores a texto."""
        try:
            accion()
        except (ValueError, PermissionError) as error:
            return False, str(error)
        self.cargar_historial()
        return True, mensaje_exito

    def _mostrar_resultado(self, resultado) -> None:
        exito, mensaje = resultado
        if exito:
            mostrar_aviso(mensaje)
        else:
            mostrar_dialogo("No se pudo completar", mensaje, icono="alert-circle-outline")

    def _pedir_eliminacion(self, id_incidente: int) -> None:
        elegir_opcion(
            f"¿Eliminar el reporte #{id_incidente}?", "delete-clock-outline",
            MOTIVOS_ELIMINACION,
            lambda motivo: self._ejecutar(
                lambda: self.incidente_controller.solicitar_eliminacion(id_incidente, self._usuario, motivo),
                "Solicitud enviada. El municipio la revisará.",
            ),
            texto_boton="Enviar solicitud",
            explicacion=("Un funcionario municipal revisará tu solicitud. Mientras tanto, "
                         "el reporte sigue visible. ¿Por qué quieres eliminarlo?"),
        )

    def _cancelar_solicitud(self, id_incidente: int) -> None:
        self._mostrar_resultado(self._ejecutar(
            lambda: self.incidente_controller.cancelar_solicitud_eliminacion(id_incidente, self._usuario),
            "Retiraste la solicitud: el reporte se mantiene.",
        ))

    def _confirmar_eliminacion(self, incidente) -> None:
        motivo = incidente.solicitud_eliminacion.get("motivo", "")
        mostrar_dialogo(
            f"¿Eliminar el reporte #{incidente.id_incidente}?",
            f"Motivo del vecino: {motivo}.\n\nSe borrarán el reporte y su foto. "
            "Esta acción no se puede deshacer.",
            icono="delete-alert-outline",
            botones=[("Cancelar", None),
                     ("Sí, eliminar", lambda: self._mostrar_resultado(self._ejecutar(
                         lambda: self.incidente_controller.aprobar_eliminacion(
                             incidente.id_incidente, self._usuario),
                         f"Reporte #{incidente.id_incidente} eliminado.",
                     )))],
        )

    def _confirmar_reporte(self, id_incidente: int) -> None:
        self._mostrar_resultado(self._ejecutar(
            lambda: self.incidente_controller.confirmar_reporte(id_incidente, self._usuario),
            f"Reporte #{id_incidente} confirmado y publicado.",
        ))

    def _no_aprobar(self, id_incidente: int) -> None:
        elegir_opcion(
            f"¿No aprobar el reporte #{id_incidente}?", "shield-remove-outline",
            MOTIVOS_NO_APROBAR,
            lambda motivo: self._ejecutar(
                lambda: self.incidente_controller.no_aprobar_reporte(id_incidente, self._usuario, motivo),
                f"Reporte #{id_incidente} no aprobado.",
            ),
            texto_boton="No aprobar",
            explicacion=("El reporte y su foto se borrarán y nunca aparecerán en el mapa. "
                         "El vecino recibirá un aviso. ¿Por qué no se aprueba?"),
        )

    def _rechazar_eliminacion(self, id_incidente: int) -> None:
        self._mostrar_resultado(self._ejecutar(
            lambda: self.incidente_controller.rechazar_eliminacion(id_incidente, self._usuario),
            f"Solicitud rechazada: el reporte #{id_incidente} se mantiene.",
        ))

    def _avanzar_estado(self, id_incidente: int) -> None:
        try:
            incidente = self.incidente_controller.avanzar_estado(id_incidente)
        except ValueError as error:
            mostrar_dialogo("No se pudo actualizar", str(error))
            return
        mostrar_aviso(f"Reporte #{id_incidente}: {incidente.estado}")
        self.cargar_historial()
