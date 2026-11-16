# =============================================================================
# AlertCom - Vista: Historial de Reportes (HistoryScreen)
# =============================================================================
# Llena SOLO la lista y los contadores definidos en views/kv/history.kv (ya no borra
# la pantalla completa). Un vecino ve sus reportes; un funcionario municipal
# ve todos y puede avanzar su estado (lo que dispara una notificación).
# =============================================================================

from kivy.factory import Factory
from kivy.metrics import dp
from kivymd.app import MDApp
from kivymd.uix.label import MDLabel

from config import MOTIVOS_ELIMINACION
from controllers.fotos import ruta_foto
from views.componentes.formulario import elegir_opcion
from views.componentes.estilos import COLOR_ESTADO, ESTILO_GRAVEDAD, GRIS, ICONO_ESTADO, ICONO_TIPO
from views.componentes.pantalla_base import PantallaBase

from views.componentes.detalle_reporte import mostrar_detalle_reporte
from views.componentes.dialogos import mostrar_aviso, mostrar_dialogo
from views.componentes.interaccion import aparecer_en_cascada, contar_hasta



class HistoryScreen(PantallaBase):
    """Pantalla de historial y trazabilidad de reportes."""

    def __init__(self, incidente_controller=None, auth_controller=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.incidente_controller = incidente_controller
        self.auth_controller = auth_controller
        self.filtro_estado = None   # None = todos

    @property
    def _usuario(self):
        return self.auth_controller.usuario_actual if self.auth_controller else None

    def _id_a_filtrar(self):
        """None = todos los reportes (funcionario municipal)."""
        usuario = self._usuario
        if usuario is None or usuario.es_municipal:
            return None
        return usuario.uid

    def on_pre_enter(self, *args) -> None:
        self.filtro_estado = None
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

    def filtrar(self, estado) -> None:
        """Tocar un contador filtra la lista; tocarlo de nuevo vuelve a 'Total'."""
        self.filtro_estado = None if estado == self.filtro_estado else estado
        self.cargar_historial()

    def cargar_historial(self, animar: bool = False) -> None:
        id_filtro = self._id_a_filtrar()
        self.ids.titulo_historial.text = "Todos los reportes" if id_filtro is None else "Mis Reportes"

        # --- Contadores (suben desde 0 al entrar a la pantalla) ---
        resumen = self.incidente_controller.resumen(id_filtro)
        valores = {None: resumen["total"], "Pendiente": resumen["pendientes"],
                   "En revisión": resumen["en_revision"], "Reparado": resumen["reparados"]}
        for estado, tarjeta in self._tarjetas().items():
            tarjeta.activa = estado == self.filtro_estado
            if animar:
                contar_hasta(tarjeta, valores[estado])
            else:
                tarjeta.text = str(valores[estado])

        self._mostrar_aviso_solicitudes()

        # --- Lista (solo se limpia la lista, no la pantalla) ---
        lista = self.ids.lista_reportes
        lista.clear_widgets()
        reportes = self.incidente_controller.obtener_historial(id_filtro)
        if self.filtro_estado == "eliminacion":
            reportes = [r for r in reportes if r.eliminacion_pendiente]
            self.ids.texto_filtro.text = (f"Mostrando: solicitudes de eliminación ({len(reportes)}). "
                                          "Toca una para decidir.")
        elif self.filtro_estado:
            reportes = [r for r in reportes if r.estado == self.filtro_estado]
            self.ids.texto_filtro.text = f"Mostrando: {self.filtro_estado} ({len(reportes)}). Toca de nuevo para ver todos."
        else:
            self.ids.texto_filtro.text = "Toca un contador para filtrar la lista"

        if not reportes:
            texto = ("Aún no hay reportes. ¡Envía el primero desde el mapa!" if not self.filtro_estado
                     else f"No hay reportes en estado «{self.filtro_estado}».")
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
                estado=incidente.estado,
                icono_estado=ICONO_ESTADO.get(incidente.estado, "help-circle"),
                color_estado=COLOR_ESTADO.get(incidente.estado, GRIS),
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
            if incidente.eliminacion_pendiente:
                # El funcionario decide sobre la solicitud del vecino. Solo dos
                # botones (tres no caben); tocar fuera de la ventana la cierra.
                # "Aprobar" pide confirmar antes de borrar.
                botones = [("Rechazar", lambda: self._rechazar_eliminacion(id_reporte)),
                           ("Aprobar", lambda: self._confirmar_eliminacion(incidente))]
            else:
                siguiente = incidente.siguiente_estado()
                if siguiente:
                    botones.append((f"Marcar: {siguiente}", lambda: self._avanzar_estado(id_reporte)))
                # Sus propios reportes los puede borrar directo (él autoriza)
                if incidente.usuario_id == usuario.uid:
                    if siguiente:
                        botones.pop(0)  # tres botones no caben: se cierra tocando fuera
                    botones.append(("Eliminar", lambda: self._confirmar_eliminacion_propia(incidente)))
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

    def _confirmar_eliminacion_propia(self, incidente) -> None:
        mostrar_dialogo(
            f"¿Eliminar tu reporte #{incidente.id_incidente}?",
            "Como es tu propio reporte, se elimina sin solicitud.\n\n"
            "Se borrarán el reporte y su foto. Esta acción no se puede deshacer.",
            icono="delete-alert-outline",
            botones=[("Cancelar", None),
                     ("Sí, eliminar", lambda: self._mostrar_resultado(self._ejecutar(
                         lambda: self.incidente_controller.eliminar_reporte_propio(
                             incidente.id_incidente, self._usuario),
                         f"Reporte #{incidente.id_incidente} eliminado.",
                     )))],
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
