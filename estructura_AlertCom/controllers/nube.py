# =============================================================================
# AlertCom - Reportes compartidos en la nube (Firebase Realtime Database)
# =============================================================================
# Antes cada teléfono tenía SUS reportes. Ahora todos se guardan también en
# Firebase, así cada vecino ve en el mapa los baches que reportaron los demás
# y el municipio los gestiona desde su propio teléfono.
#
# Cómo funciona (sin librerías extra: Firebase se usa por su API REST):
#   • El teléfono SIEMPRE guarda primero en incidentes.json: la app funciona
#     igual sin internet.
#   • Cada cambio (reporte nuevo, cambio de estado, solicitud, eliminación)
#     entra a una COLA (datos/nube_pendientes.json) y se sube apenas hay
#     conexión. Si no hay internet, queda en la cola para el próximo intento.
#   • Después de subir, se DESCARGA la lista completa y reemplaza la copia
#     local (menos lo que todavía está en la cola, para no perderlo).
#   • Si dos teléfonos usan el mismo número de reporte al mismo tiempo, el
#     segundo recibe el siguiente número libre (la subida usa una condición:
#     "crear solo si ese número no existe").
#   • Las fotos se suben reducidas (máx. 800 px) como texto base64, en una
#     sección aparte, y se descargan solo cuando faltan en el teléfono.
#   • Las cuentas y contraseñas NO se suben: siguen solo en el teléfono.
#
# Estructura en Firebase:
#   alertcom/incidentes/reporte_5 → {datos del reporte #5}
#   alertcom/fotos/reporte_5      → "foto en base64"
# (Claves "reporte_N" y no "5": con números Firebase devuelve una lista.)
# =============================================================================

import base64
import io
import json
import logging
import ssl
import threading
import urllib.error
import urllib.request
from pathlib import Path

log = logging.getLogger("alertcom.nube")

RAIZ = "alertcom"
ARCHIVO_COLA = "nube_pendientes.json"
LADO_FOTO_NUBE = 800
CALIDAD_FOTO_NUBE = 70
MAX_TEXTO_FOTO = 390_000          # las reglas de Firebase aceptan hasta 400.000
TIEMPO_MAXIMO = 15                # segundos por petición


def clave(id_incidente: int) -> str:
    return f"reporte_{id_incidente}"


# -----------------------------------------------------------------------------
# Cliente HTTP mínimo para Firebase
# -----------------------------------------------------------------------------
def _contexto_ssl():
    try:
        import certifi  # en Android trae los certificados que el sistema no da
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def _en_segundo_plano(trabajo, al_terminar) -> None:
    """La petición corre en otro hilo (la pantalla no se congela) y el
    resultado vuelve al hilo de Kivy."""
    from kivy.clock import Clock

    def correr():
        resultado = trabajo()
        Clock.schedule_once(lambda _dt: al_terminar(*resultado), 0)

    threading.Thread(target=correr, daemon=True).start()


class ClienteFirebase:
    """GET / PUT / PATCH / DELETE sobre la base de datos.

    al_terminar(estado, datos) recibe estado = código HTTP (200, 412...) o
    0 si no hubo conexión.
    """

    def __init__(self, url_base: str, ejecutar=None) -> None:
        self.url_base = url_base.rstrip("/")
        self._ejecutar = ejecutar or _en_segundo_plano
        self._ssl = _contexto_ssl() if self.url_base.startswith("https") else None

    def pedir(self, metodo: str, ruta: str, datos=None, al_terminar=None, solo_si_no_existe=False) -> None:
        url = f"{self.url_base}/{ruta}.json"
        cuerpo = None if datos is None else json.dumps(datos, ensure_ascii=False).encode("utf-8")
        encabezados = {"Content-Type": "application/json"}
        if solo_si_no_existe:
            # Escritura condicional de Firebase: falla con 412 si ya hay algo
            encabezados["if-match"] = "null_etag"

        def trabajo():
            peticion = urllib.request.Request(url, data=cuerpo, method=metodo, headers=encabezados)
            try:
                with urllib.request.urlopen(peticion, timeout=TIEMPO_MAXIMO, context=self._ssl) as respuesta:
                    texto = respuesta.read().decode("utf-8")
                    return respuesta.status, (json.loads(texto) if texto else None)
            except urllib.error.HTTPError as error:
                return error.code, None
            except (urllib.error.URLError, OSError, ValueError) as error:
                log.info("Sin conexión con la nube: %s", error)
                return 0, None

        self._ejecutar(trabajo, al_terminar or (lambda *_: None))


# -----------------------------------------------------------------------------
# Sincronización de reportes
# -----------------------------------------------------------------------------
class SincronizadorReportes:
    def __init__(self, incidentes, cliente: ClienteFirebase, carpeta_datos,
                 uid_actual=lambda: None, al_actualizar=None) -> None:
        """
        Args:
            incidentes: IncidenteController (la copia local).
            cliente: ClienteFirebase.
            uid_actual: función que devuelve el uid de quien usa la app (para
                avisarle solo de SUS reportes).
            al_actualizar: función sin argumentos; se llama cuando llegan
                datos nuevos (la pantalla se refresca).
        """
        self.incidentes = incidentes
        self.cliente = cliente
        self.carpeta_datos = Path(carpeta_datos)
        self.uid_actual = uid_actual
        self.al_actualizar = al_actualizar
        self.ruta_cola = self.carpeta_datos / ARCHIVO_COLA
        self.cola: list[dict] = self._leer_cola()
        self.ocupado = False
        self._repetir = False
        self.conectado: bool | None = None   # None = todavía no se intenta
        self._despues: list = []
        incidentes.al_cambiar = self._anotar_cambio

    # ------------------------------------------------------------------
    # Cola de cambios por subir (se guarda en un archivo)
    # ------------------------------------------------------------------
    def _leer_cola(self) -> list[dict]:
        try:
            datos = json.loads(self.ruta_cola.read_text(encoding="utf-8"))
            return datos if isinstance(datos, list) else []
        except (OSError, ValueError):
            return []

    def _guardar_cola(self) -> None:
        try:
            self.ruta_cola.parent.mkdir(parents=True, exist_ok=True)
            self.ruta_cola.write_text(json.dumps(self.cola, ensure_ascii=False, indent=1), encoding="utf-8")
        except OSError as error:
            log.warning("No se pudo guardar la cola de la nube: %s", error)

    @property
    def pendientes(self) -> int:
        return len(self.cola)

    def subir_todo_lo_local(self) -> None:
        """Primera vez con nube: los reportes que ya estaban en el teléfono
        se suben (si su número está ocupado, reciben otro)."""
        ya = {t["id"] for t in self.cola if t["op"] == "nuevo"}
        for incidente in self.incidentes.incidentes:
            if incidente.id_incidente not in ya:
                self.cola.append({"op": "nuevo", "id": incidente.id_incidente})
        self._guardar_cola()

    def _anotar_cambio(self, tipo: str, incidente, campos) -> None:
        id_inc = incidente.id_incidente
        nuevo_pendiente = any(t["op"] == "nuevo" and t["id"] == id_inc for t in self.cola)
        if tipo == "borrado":
            # Si nunca alcanzó a subirse, basta con olvidarlo
            self.cola = [t for t in self.cola if t["id"] != id_inc]
            if not nuevo_pendiente:
                self.cola.append({"op": "borrado", "id": id_inc})
        elif tipo == "modificado":
            if not nuevo_pendiente:  # si el "nuevo" aún no sube, sube completo después
                existente = next((t for t in self.cola if t["op"] == "modificado" and t["id"] == id_inc), None)
                if existente:
                    existente["campos"] = sorted(set(existente["campos"]) | set(campos or []))
                else:
                    self.cola.append({"op": "modificado", "id": id_inc, "campos": list(campos or [])})
        else:
            self.cola.append({"op": "nuevo", "id": id_inc})
        self._guardar_cola()
        self.sincronizar()

    # ------------------------------------------------------------------
    # Ciclo: subir la cola → descargar todo → bajar fotos que falten
    # ------------------------------------------------------------------
    def sincronizar(self, al_terminar=None) -> None:
        if al_terminar:
            self._despues.append(al_terminar)
        if self.ocupado:
            self._repetir = True  # hubo otro cambio mientras se subía
            return
        self.ocupado = True
        self._subir_siguiente()

    def _terminar(self, conectado: bool) -> None:
        self.conectado = conectado
        self.ocupado = False
        if self._repetir and conectado:
            self._repetir = False
            self.sincronizar()
            return
        self._repetir = False
        despues, self._despues = self._despues, []
        for funcion in despues:
            funcion(conectado)

    def _quitar_tarea(self) -> None:
        self.cola.pop(0)
        self._guardar_cola()
        self._subir_siguiente()

    def _subir_siguiente(self) -> None:
        if not self.cola:
            self._descargar()
            return
        tarea = self.cola[0]
        id_inc = tarea["id"]
        if tarea["op"] == "borrado":
            self.cliente.pedir("DELETE", f"{RAIZ}/incidentes/{clave(id_inc)}",
                               al_terminar=lambda estado, _d: self._tras_borrar(id_inc, estado))
            return

        incidente = self.incidentes.buscar(id_inc)
        if incidente is None:  # se borró antes de subir
            self._quitar_tarea()
            return
        if tarea["op"] == "nuevo":
            self.cliente.pedir("PUT", f"{RAIZ}/incidentes/{clave(id_inc)}", incidente.to_dict(),
                               al_terminar=lambda estado, _d: self._tras_crear(id_inc, estado),
                               solo_si_no_existe=True)
        else:
            datos = incidente.to_dict()
            cambios = {campo: datos.get(campo) for campo in tarea.get("campos", [])}
            self.cliente.pedir("PATCH", f"{RAIZ}/incidentes/{clave(id_inc)}", cambios,
                               al_terminar=lambda estado, _d: self._tras_modificar(estado))

    def _tras_crear(self, id_inc: int, estado: int) -> None:
        if estado == 0:
            self._terminar(False)
        elif estado == 412:
            # Ese número ya lo usó otro teléfono: se prueba con el siguiente
            nuevo = max(id_inc, max((i.id_incidente for i in self.incidentes.incidentes), default=0)) + 1
            log.info("El reporte #%s pasa a ser #%s (número ocupado en la nube).", id_inc, nuevo)
            self.incidentes.cambiar_id(id_inc, nuevo)
            for tarea in self.cola:
                if tarea["id"] == id_inc:
                    tarea["id"] = nuevo
            self._guardar_cola()
            self._subir_siguiente()
        elif 200 <= estado < 300:
            self._subir_foto(id_inc)
        else:
            log.warning("La nube rechazó el reporte #%s (HTTP %s); se descarta.", id_inc, estado)
            self._quitar_tarea()

    def _subir_foto(self, id_inc: int) -> None:
        incidente = self.incidentes.buscar(id_inc)
        texto = _foto_en_base64(self.carpeta_datos, incidente.imagen if incidente else "")
        if not texto:
            self._quitar_tarea()
            return
        self.cliente.pedir("PUT", f"{RAIZ}/fotos/{clave(id_inc)}", texto,
                           al_terminar=lambda estado, _d: self._terminar(False) if estado == 0
                           else self._quitar_tarea())

    def _tras_modificar(self, estado: int) -> None:
        if estado == 0:
            self._terminar(False)
        else:
            # 2xx = listo. 4xx = el reporte ya no existe en la nube (las reglas
            # rechazan un reporte a medias): no hay nada que modificar.
            self._quitar_tarea()

    def _tras_borrar(self, id_inc: int, estado: int) -> None:
        if estado == 0:
            self._terminar(False)
            return
        self.cliente.pedir("DELETE", f"{RAIZ}/fotos/{clave(id_inc)}",
                           al_terminar=lambda _e, _d: self._quitar_tarea())

    def _descargar(self) -> None:
        self.cliente.pedir("GET", f"{RAIZ}/incidentes", al_terminar=self._al_descargar)

    def _al_descargar(self, estado: int, datos) -> None:
        if estado == 0:
            self._terminar(False)
            return
        if not 200 <= estado < 300:
            log.warning("La nube no deja leer los reportes (HTTP %s): revisa las reglas de "
                        "Firebase (GUIA_FIREBASE.md).", estado)
            self._terminar(False)
            return
        registros = datos if isinstance(datos, dict) else {}
        conservar = {t["id"] for t in self.cola if t["op"] in ("nuevo", "modificado")}
        cambios = self.incidentes.aplicar_desde_nube(registros, conservar)
        self._avisar(cambios)
        if cambios and self.al_actualizar:
            self.al_actualizar()
        self._bajar_fotos_faltantes([i for i in self.incidentes.incidentes if i.imagen])

    def _bajar_fotos_faltantes(self, por_revisar: list) -> None:
        from controllers.fotos import ruta_foto
        while por_revisar and ruta_foto(self.carpeta_datos, por_revisar[0].imagen) is not None:
            por_revisar.pop(0)
        if not por_revisar:
            self._terminar(True)
            return
        incidente = por_revisar.pop(0)

        def guardar(estado, texto):
            if estado == 0:
                self._terminar(False)
                return
            if isinstance(texto, str) and _guardar_foto(self.carpeta_datos, incidente.imagen, texto):
                if self.al_actualizar:
                    self.al_actualizar()
            self._bajar_fotos_faltantes(por_revisar)

        self.cliente.pedir("GET", f"{RAIZ}/fotos/{clave(incidente.id_incidente)}", al_terminar=guardar)

    # ------------------------------------------------------------------
    # Avisos: el municipio cambió algo de MIS reportes desde otro teléfono
    # ------------------------------------------------------------------
    def _avisar(self, cambios: list) -> None:
        uid = self.uid_actual()
        notificador = self.incidentes.notificador
        if not uid:
            return
        for tipo, antes, despues in cambios:
            propio = (despues or antes).usuario_id == uid
            if not propio or antes is None:
                continue
            numero = antes.id_incidente
            if tipo == "estado":
                notificador.notificar(titulo="Actualización de tu reporte",
                                      mensaje=f"El reporte #{numero} ({antes.tipo_incidente}) ahora está: "
                                              f"{despues.estado}.")
            elif tipo == "borrado" and antes.eliminacion_pendiente:
                notificador.notificar(titulo="Solicitud aprobada",
                                      mensaje=f"El municipio eliminó tu reporte #{numero} ({antes.tipo_incidente}).")
            elif tipo == "solicitud" and antes.eliminacion_pendiente and not despues.eliminacion_pendiente:
                notificador.notificar(titulo="Solicitud rechazada",
                                      mensaje=f"El municipio mantendrá tu reporte #{numero}: "
                                              "el daño se revisará igual.")


# -----------------------------------------------------------------------------
# Fotos ↔ texto base64
# -----------------------------------------------------------------------------
def _foto_en_base64(carpeta_datos, imagen: str) -> str | None:
    from controllers.fotos import ruta_foto
    ruta = ruta_foto(carpeta_datos, imagen) if imagen else None
    if ruta is None:
        return None
    try:
        from PIL import Image
        with Image.open(ruta) as foto:
            foto = foto.convert("RGB")
            foto.thumbnail((LADO_FOTO_NUBE, LADO_FOTO_NUBE))
            for calidad in (CALIDAD_FOTO_NUBE, 55, 40):
                memoria = io.BytesIO()
                foto.save(memoria, "JPEG", quality=calidad, optimize=True)
                texto = base64.b64encode(memoria.getvalue()).decode("ascii")
                if len(texto) <= MAX_TEXTO_FOTO:
                    return texto
    except (OSError, ValueError) as error:
        log.warning("No se pudo preparar la foto para la nube: %s", error)
    return None


def _guardar_foto(carpeta_datos, imagen: str, texto: str) -> bool:
    """Guarda la foto descargada en la misma ruta relativa del reporte."""
    destino = (Path(carpeta_datos) / imagen).resolve()
    if Path(carpeta_datos).resolve() not in destino.parents or destino.suffix.lower() != ".jpg":
        log.warning("Ruta de foto sospechosa en la nube, se ignora: %s", imagen)
        return False
    try:
        contenido = base64.b64decode(texto, validate=True)
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(contenido)
        return True
    except (ValueError, OSError) as error:
        log.warning("Foto de la nube dañada: %s", error)
        return False
