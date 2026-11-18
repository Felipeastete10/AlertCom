# =============================================================================
# AlertCom - Controlador: Gestión de Incidentes
# =============================================================================
# Crea, consulta y actualiza reportes. Cada cambio se guarda en
# incidentes.json y, cuando el cambio es importante, se avisa con una
# notificación local (Plyer) desde AQUÍ, la lógica de negocio.
# También registra los eventos de analítica del flujo de reporte
# (reporte_enviado, reporte_rechazado, estado_cambiado).
# Privacidad: el evento guarda tipo y gravedad, NUNCA la descripción, la
# calle ni la ubicación, que pueden identificar a la persona.
# No importa Kivy.
# =============================================================================

import logging

from datetime import datetime

from config import (
    GRAVEDADES,
    LIMITES_TEMUCO,
    MAX_CARACTERES_CALLE,
    MAX_CARACTERES_DESCRIPCION,
    MOTIVOS_ELIMINACION,
    MOTIVOS_ELIMINACION_MUNICIPIO,
    MOTIVOS_NO_APROBAR,
    TIPOS_DANO,
)
from controllers import fotos
from controllers.almacenamiento_json import AlmacenamientoJSON
from controllers.notificador import Notificador
from controllers.registro_eventos import RegistroEventos, RegistroNulo
from models.incidente import FORMATO_FECHA, Incidente, dentro_de_zona, leer_coordenadas

log = logging.getLogger("alertcom.incidentes")


class IncidenteController:
    """Lógica de negocio de los reportes de baches."""

    def __init__(
        self,
        almacenamiento: AlmacenamientoJSON,
        notificador: Notificador | None = None,
        eventos: RegistroEventos | None = None,
    ) -> None:
        self.almacenamiento = almacenamiento
        self.notificador = notificador or Notificador(habilitado=False)
        self.eventos = eventos or RegistroNulo()
        self.incidentes: list[Incidente] = self._cargar()
        # Quien quiera enterarse de cada cambio (la nube) se anota aquí:
        #   funcion(tipo, incidente, campos)  tipo = "nuevo" | "modificado" | "borrado"
        self.al_cambiar = None

    # ------------------------------------------------------------------
    # Persistencia
    # ------------------------------------------------------------------
    def _cargar(self) -> list[Incidente]:
        incidentes = []
        for datos in self.almacenamiento.cargar():
            try:
                incidentes.append(Incidente.from_dict(datos))
            except (KeyError, ValueError, TypeError) as error:
                log.warning("Reporte inválido en JSON, se omite: %s", error)
        return incidentes

    def _guardar(self) -> None:
        self.almacenamiento.guardar([i.to_dict() for i in self.incidentes])

    def _siguiente_id(self) -> int:
        return max((i.id_incidente for i in self.incidentes), default=0) + 1

    def _avisar_cambio(self, tipo: str, incidente: Incidente, campos=None) -> None:
        if self.al_cambiar is not None:
            try:
                self.al_cambiar(tipo, incidente, campos)
            except Exception as error:  # la nube nunca debe romper un reporte
                log.warning("No se pudo avisar el cambio a la nube: %s", error)

    # ------------------------------------------------------------------
    # Casos de uso (mutaciones → se guardan y notifican)
    # ------------------------------------------------------------------
    def crear_incidente(
        self,
        tipo: str,
        gravedad: str,
        descripcion: str = "",
        foto: str | None = None,
        ubicacion: str | None = "",
        usuario_id: str | None = None,   # uid de la cuenta
        confirmado: bool = False,        # True solo si lo crea un funcionario
        calle: str = "",
    ) -> Incidente:
        """
        Valida, crea, guarda y notifica un reporte nuevo.

        Raises:
            ValueError: con un mensaje listo para mostrar al usuario.
        """
        descripcion = (descripcion or "").strip()
        calle = " ".join((calle or "").split())  # sin espacios repetidos
        # (motivo para la analítica, mensaje para la persona)
        error = None
        if tipo not in TIPOS_DANO:
            error = ("sin_tipo", "Selecciona el tipo de daño.")
        elif gravedad not in GRAVEDADES:
            error = ("sin_gravedad", "Selecciona la gravedad del daño.")
        elif leer_coordenadas(ubicacion) is None:
            # Antes se usaba el centro de Temuco por defecto y todos los
            # marcadores quedaban uno encima de otro.
            error = ("sin_ubicacion",
                     "Marca dónde está el daño: usa tu ubicación o mueve el mapa "
                     "hasta que el pin quede encima.")
        elif not dentro_de_zona(*leer_coordenadas(ubicacion), LIMITES_TEMUCO):
            error = ("fuera_de_temuco",
                     "AlertCom recibe reportes solo de Temuco y Padre Las Casas. "
                     "Mueve el pin hasta el lugar del daño dentro de la ciudad.")
        elif not calle:
            error = ("sin_calle", "Escribe la calle o una referencia del lugar.")
        elif len(calle) > MAX_CARACTERES_CALLE:
            error = ("calle_larga", f"La calle no puede superar {MAX_CARACTERES_CALLE} caracteres.")
        elif len(descripcion) > MAX_CARACTERES_DESCRIPCION:
            error = ("descripcion_larga",
                     f"La descripción no puede superar {MAX_CARACTERES_DESCRIPCION} caracteres.")
        if error:
            self.eventos.registrar("reporte_rechazado", {"motivo": error[0]})
            raise ValueError(error[1])

        incidente = Incidente(
            id_incidente=self._siguiente_id(),
            tipo_incidente=tipo,
            descripcion=descripcion,
            gravedad=gravedad,
            imagen=foto or "",
            ubicacion=ubicacion,
            calle=calle,
            usuario_id=usuario_id,
            confirmado=confirmado,
        )
        self.incidentes.append(incidente)
        self._guardar()
        self._avisar_cambio("nuevo", incidente)

        self.eventos.registrar("reporte_enviado", {
            "id_incidente": incidente.id_incidente,
            "tipo": tipo,
            "gravedad": gravedad,
            "con_foto": bool(foto),
        })
        self.notificador.notificar(
            titulo="Reporte enviado",
            mensaje=(f"Tu reporte #{incidente.id_incidente} ({tipo}, {gravedad}) quedó registrado."
                     + ("" if confirmado else " Se verá en el mapa cuando el municipio lo confirme.")),
        )
        return incidente

    def cambiar_estado(self, id_incidente: int, nuevo_estado: str) -> Incidente:
        """
        Cambia el estado de un reporte (por su ID, no por su posición).

        Raises:
            ValueError: si el reporte no existe o el estado no es válido.
        """
        incidente = self.buscar(id_incidente)
        if incidente is None:
            raise ValueError(f"No existe el reporte #{id_incidente}.")
        if not incidente.confirmado:
            raise ValueError("Primero confirma el reporte: todavía no es público.")

        estado_anterior = incidente.estado
        incidente.cambiar_estado(nuevo_estado)
        self._guardar()
        self._avisar_cambio("modificado", incidente, ["estado"])

        self.eventos.registrar("estado_cambiado", {
            "id_incidente": id_incidente,
            "anterior": estado_anterior,
            "nuevo": nuevo_estado,
        })

        self.notificador.notificar(
            titulo="Actualización de tu reporte",
            mensaje=f"El reporte #{id_incidente} ({incidente.tipo_incidente}) ahora está: {nuevo_estado}.",
        )
        return incidente

    def avanzar_estado(self, id_incidente: int) -> Incidente:
        """Pasa el reporte al siguiente estado: Pendiente → En revisión → Reparado."""
        incidente = self.buscar(id_incidente)
        if incidente is None:
            raise ValueError(f"No existe el reporte #{id_incidente}.")
        siguiente = incidente.siguiente_estado()
        if siguiente is None:
            raise ValueError("Este reporte ya está reparado.")
        return self.cambiar_estado(id_incidente, siguiente)

    # ------------------------------------------------------------------
    # Eliminación de reportes: el vecino PIDE, el funcionario DECIDE
    # ------------------------------------------------------------------
    # Los permisos se revisan aquí (no solo en la pantalla): aunque la
    # interfaz fallara, un vecino nunca puede aprobar una eliminación.
    def _reporte(self, id_incidente: int) -> Incidente:
        incidente = self.buscar(id_incidente)
        if incidente is None:
            raise ValueError(f"No existe el reporte #{id_incidente}.")
        return incidente

    @staticmethod
    def _exigir_municipal(usuario) -> None:
        if usuario is None or not usuario.es_municipal:
            raise PermissionError("Solo un funcionario municipal puede decidir sobre una eliminación.")

    def solicitar_eliminacion(self, id_incidente: int, usuario, motivo: str) -> Incidente:
        """El dueño del reporte pide eliminarlo. El reporte NO se borra todavía."""
        incidente = self._reporte(id_incidente)
        if usuario is None or incidente.usuario_id != usuario.uid:
            raise PermissionError("Solo quien creó el reporte puede pedir eliminarlo.")
        if incidente.eliminacion_pendiente:
            raise ValueError("Ya pediste eliminar este reporte. Espera la respuesta del municipio.")
        if motivo not in MOTIVOS_ELIMINACION:
            raise ValueError("Elige el motivo de la eliminación.")

        incidente.solicitud_eliminacion = {"motivo": motivo,
                                           "fecha": datetime.now().strftime(FORMATO_FECHA)}
        self._guardar()
        self._avisar_cambio("modificado", incidente, ["solicitud_eliminacion"])
        self.eventos.registrar("eliminacion_solicitada", {"id_incidente": id_incidente, "motivo": motivo})
        log.info("Eliminación solicitada para el reporte #%s (%s).", id_incidente, motivo)
        return incidente

    def cancelar_solicitud_eliminacion(self, id_incidente: int, usuario) -> Incidente:
        incidente = self._reporte(id_incidente)
        if usuario is None or incidente.usuario_id != usuario.uid:
            raise PermissionError("Solo quien pidió la eliminación puede cancelarla.")
        if not incidente.eliminacion_pendiente:
            raise ValueError("Este reporte no tiene una solicitud de eliminación.")
        incidente.solicitud_eliminacion = None
        self._guardar()
        self._avisar_cambio("modificado", incidente, ["solicitud_eliminacion"])
        self.eventos.registrar("eliminacion_cancelada", {"id_incidente": id_incidente})
        return incidente

    def aprobar_eliminacion(self, id_incidente: int, usuario) -> Incidente:
        """El funcionario aprueba: el reporte y su foto se borran."""
        self._exigir_municipal(usuario)
        incidente = self._reporte(id_incidente)
        if not incidente.eliminacion_pendiente:
            raise ValueError("Este reporte no tiene una solicitud de eliminación.")

        motivo = incidente.solicitud_eliminacion.get("motivo", "")
        self._borrar(incidente)

        self.eventos.registrar("eliminacion_aprobada", {"id_incidente": id_incidente, "motivo": motivo})
        self.notificador.notificar(
            titulo="Solicitud aprobada",
            mensaje=f"El municipio eliminó tu reporte #{id_incidente} ({incidente.tipo_incidente}).",
        )
        log.info("Reporte #%s eliminado por el funcionario id=%s.", id_incidente, usuario.id_usuario)
        return incidente

    def eliminar_reporte(self, id_incidente: int, usuario, motivo: str) -> Incidente:
        """El funcionario borra CUALQUIER reporte, sin esperar una solicitud
        (él es quien autoriza). Siempre con motivo; si el reporte era de un
        vecino, se le avisa. El vecino, en cambio, solo puede PEDIRLO."""
        self._exigir_municipal(usuario)
        incidente = self._reporte(id_incidente)
        if motivo not in MOTIVOS_ELIMINACION_MUNICIPIO:
            raise ValueError("Elige por qué se elimina el reporte.")
        propio = incidente.usuario_id == usuario.uid
        self._borrar(incidente)
        self.eventos.registrar("reporte_eliminado",
                               {"id_incidente": id_incidente, "motivo": motivo, "propio": propio})
        if not propio:
            self.notificador.notificar(
                titulo="Reporte eliminado",
                mensaje=f"El municipio eliminó el reporte #{id_incidente} ({incidente.tipo_incidente}): {motivo}.",
            )
        log.info("Reporte #%s eliminado por el funcionario id=%s (%s).", id_incidente, usuario.id_usuario, motivo)
        return incidente

    def _borrar(self, incidente: Incidente) -> None:
        """Quita el reporte del archivo y borra su foto."""
        self.incidentes = [i for i in self.incidentes if i.id_incidente != incidente.id_incidente]
        self._guardar()
        fotos.borrar_foto(self.almacenamiento.ruta.parent, incidente.imagen)
        self._avisar_cambio("borrado", incidente)

    def rechazar_eliminacion(self, id_incidente: int, usuario) -> Incidente:
        """El funcionario rechaza: el reporte se mantiene y vuelve a la normalidad."""
        self._exigir_municipal(usuario)
        incidente = self._reporte(id_incidente)
        if not incidente.eliminacion_pendiente:
            raise ValueError("Este reporte no tiene una solicitud de eliminación.")
        incidente.solicitud_eliminacion = None
        self._guardar()
        self._avisar_cambio("modificado", incidente, ["solicitud_eliminacion"])
        self.eventos.registrar("eliminacion_rechazada", {"id_incidente": id_incidente})
        self.notificador.notificar(
            titulo="Solicitud rechazada",
            mensaje=f"El municipio mantendrá tu reporte #{id_incidente}: el daño se revisará igual.",
        )
        return incidente

    # ------------------------------------------------------------------
    # Confirmación: un reporte nuevo es público solo cuando el municipio
    # lo revisa (evita bromas, repetidos o lugares equivocados en el mapa)
    # ------------------------------------------------------------------
    def _sin_confirmar(self, id_incidente: int, usuario) -> Incidente:
        if usuario is None or not usuario.es_municipal:
            raise PermissionError("Solo un funcionario municipal puede revisar reportes nuevos.")
        incidente = self._reporte(id_incidente)
        if incidente.confirmado:
            raise ValueError("Este reporte ya fue confirmado.")
        return incidente

    def confirmar_reporte(self, id_incidente: int, usuario) -> Incidente:
        """El funcionario revisó el reporte: pasa a ser visible para todos."""
        incidente = self._sin_confirmar(id_incidente, usuario)
        incidente.confirmado = True
        self._guardar()
        self._avisar_cambio("modificado", incidente, ["confirmado"])
        self.eventos.registrar("reporte_confirmado", {"id_incidente": id_incidente})
        self.notificador.notificar(
            titulo="Reporte confirmado",
            mensaje=f"El reporte #{id_incidente} ({incidente.tipo_incidente}) ya aparece en el mapa de todos.",
        )
        return incidente

    def no_aprobar_reporte(self, id_incidente: int, usuario, motivo: str) -> Incidente:
        """El funcionario no aprueba el reporte: se borra con su foto."""
        incidente = self._sin_confirmar(id_incidente, usuario)
        if motivo not in MOTIVOS_NO_APROBAR:
            raise ValueError("Elige por qué no se aprueba el reporte.")
        self._borrar(incidente)
        self.eventos.registrar("reporte_no_aprobado", {"id_incidente": id_incidente, "motivo": motivo})
        self.notificador.notificar(
            titulo="Reporte no aprobado",
            mensaje=f"El municipio no aprobó el reporte #{id_incidente}: {motivo}.",
        )
        return incidente

    def por_confirmar(self) -> list[Incidente]:
        return sorted((i for i in self.incidentes if not i.confirmado),
                      key=lambda i: i.fecha_creacion)

    def visibles_para(self, usuario) -> list[Incidente]:
        """Lo que muestra el mapa: los confirmados, más los propios por
        confirmar. El funcionario ve todo."""
        if usuario is not None and usuario.es_municipal:
            return self.obtener_historial()
        uid = usuario.uid if usuario is not None else None
        return [i for i in self.obtener_historial() if i.confirmado or (uid and i.usuario_id == uid)]

    def solicitudes_pendientes(self) -> list[Incidente]:
        return [i for i in self.incidentes if i.eliminacion_pendiente]

    # ------------------------------------------------------------------
    # Consultas (no modifican nada)
    # ------------------------------------------------------------------
    def desvincular_usuario(self, uid: str) -> int:
        """Al eliminar una cuenta, sus reportes se conservan (el bache sigue
        ahí y la municipalidad debe repararlo), pero quedan sin dueño."""
        cambiados = [i for i in self.incidentes if i.usuario_id == uid]
        for incidente in cambiados:
            incidente.usuario_id = None
        if cambiados:
            self._guardar()
            for incidente in cambiados:
                self._avisar_cambio("modificado", incidente, ["usuario_id"])
        return len(cambiados)

    # ------------------------------------------------------------------
    # Nube: la usa controllers/nube.py (los reportes de todos los teléfonos)
    # ------------------------------------------------------------------
    def migrar_autores(self, uid_por_id: dict) -> None:
        """Reportes de versiones anteriores guardaban el NÚMERO de la cuenta
        (1, 2...), que se repite entre teléfonos. Se cambia por su uid."""
        cambiados = False
        for incidente in self.incidentes:
            if isinstance(incidente.usuario_id, int) and incidente.usuario_id in uid_por_id:
                incidente.usuario_id = uid_por_id[incidente.usuario_id]
                cambiados = True
        if cambiados:
            self._guardar()

    def cambiar_id(self, id_viejo: int, id_nuevo: int) -> None:
        """Otro teléfono ya usó ese número: el reporte pasa a id_nuevo."""
        incidente = self.buscar(id_viejo)
        if incidente is not None:
            incidente.id_incidente = id_nuevo
            self._guardar()

    def aplicar_desde_nube(self, registros: dict, conservar: set) -> list[tuple]:
        """Reemplaza la copia local por la lista de la nube.

        Args:
            registros: {id: datos} tal como están en la nube.
            conservar: ids con cambios propios que aún no se suben (no se pisan).
        Returns:
            Lista de cambios (tipo, antes, despues) para avisar a la persona:
            "nuevo", "estado", "solicitud" o "borrado".
        """
        antes = {i.id_incidente: i for i in self.incidentes}
        nuevos = {}
        for datos in registros.values():
            try:
                incidente = Incidente.from_dict(datos)
            except (KeyError, ValueError, TypeError) as error:
                log.warning("Reporte inválido en la nube, se omite: %s", error)
                continue
            nuevos[incidente.id_incidente] = incidente
        for id_local in conservar:
            if id_local in antes:
                nuevos[id_local] = antes[id_local]

        cambios = []
        for id_inc, incidente in nuevos.items():
            anterior = antes.get(id_inc)
            if anterior is None:
                cambios.append(("nuevo", None, incidente))
            elif anterior.confirmado != incidente.confirmado:
                cambios.append(("confirmado", anterior, incidente))
            elif anterior.estado != incidente.estado:
                cambios.append(("estado", anterior, incidente))
            elif anterior.solicitud_eliminacion != incidente.solicitud_eliminacion:
                cambios.append(("solicitud", anterior, incidente))
        for id_inc, anterior in antes.items():
            if id_inc not in nuevos:
                cambios.append(("borrado", anterior, None))
                fotos.borrar_foto(self.almacenamiento.ruta.parent, anterior.imagen)

        self.incidentes = list(nuevos.values())
        if cambios:
            self._guardar()
        return cambios

    def buscar(self, id_incidente: int) -> Incidente | None:
        return next((i for i in self.incidentes if i.id_incidente == id_incidente), None)

    def obtener_historial(self, usuario_id: str | None = None) -> list[Incidente]:
        """Copia de los reportes, del más nuevo al más antiguo.
        Si se indica usuario_id, solo los de ese usuario."""
        reportes = [
            i for i in self.incidentes if usuario_id is None or i.usuario_id == usuario_id
        ]
        return sorted(reportes, key=lambda i: i.fecha_creacion, reverse=True)

    def obtener_por_estado(self, estado: str) -> list[Incidente]:
        return [i for i in self.incidentes if i.estado == estado]

    def resumen(self, usuario_id: str | None = None) -> dict:
        """Contadores para las tarjetas del historial y del perfil."""
        reportes = self.obtener_historial(usuario_id)
        return {
            "total": len(reportes),
            "pendientes": sum(i.estado == "Pendiente" for i in reportes),
            "en_revision": sum(i.estado == "En revisión" for i in reportes),
            "reparados": sum(i.estado == "Reparado" for i in reportes),
        }
