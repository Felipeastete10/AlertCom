# =============================================================================
# AlertCom - Pruebas de los reportes compartidos (Firebase) (v1.6)
# =============================================================================
# Ejecutar desde estructura_AlertCom:
#     python -m unittest discover -s pruebas -v
#
# No se usa el Firebase real: se levanta un servidor local que imita su API
# REST (GET/PUT/PATCH/DELETE, la escritura condicional "if-match: null_etag"
# y la regla que rechaza reportes a medias). Dos "teléfonos" (dos carpetas
# de datos) comparten ese servidor, como dos vecinos con la app.
# =============================================================================

import base64
import json
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

CARPETA_APP = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CARPETA_APP))

from controllers.almacenamiento_json import AlmacenamientoJSON  # noqa: E402
from controllers.incidente_controller import IncidenteController  # noqa: E402
from controllers.nube import ClienteFirebase, SincronizadorReportes  # noqa: E402
from models.usuario import Usuario  # noqa: E402

LUGAR = {"ubicacion": "-38.739120, -72.598300", "calle": "Prat 100"}
CAMPOS_OBLIGATORIOS = ("id_incidente", "tipo_incidente", "gravedad", "estado", "ubicacion")


# -----------------------------------------------------------------------------
# Firebase falso
# -----------------------------------------------------------------------------
class FirebaseFalso:
    def __init__(self):
        self.datos = {}
        self.servidor = ThreadingHTTPServer(("127.0.0.1", 0), self._manejador())
        threading.Thread(target=self.servidor.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.servidor.server_port}"

    def cerrar(self):
        self.servidor.shutdown()
        self.servidor.server_close()

    # --- árbol JSON ---
    def leer(self, partes):
        nodo = self.datos
        for parte in partes:
            if not isinstance(nodo, dict) or parte not in nodo:
                return None
            nodo = nodo[parte]
        return nodo

    def escribir(self, partes, valor):
        nodo = self.datos
        for parte in partes[:-1]:
            nodo = nodo.setdefault(parte, {})
        if valor is None:
            nodo.pop(partes[-1], None)
        else:
            nodo[partes[-1]] = valor

    def _manejador(self):
        base = self

        class Manejador(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def _responder(self, codigo, cuerpo=None):
                texto = json.dumps(cuerpo).encode()
                self.send_response(codigo)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(texto)))
                self.end_headers()
                self.wfile.write(texto)

            def _partes(self):
                ruta = self.path.split("?")[0]
                assert ruta.endswith(".json"), ruta
                return [p for p in ruta[:-5].split("/") if p]

            def _cuerpo(self):
                largo = int(self.headers.get("Content-Length", 0))
                return json.loads(self.rfile.read(largo)) if largo else None

            def _valido(self, partes, valor):
                # Regla: alertcom/incidentes/$id debe tener los campos obligatorios
                if len(partes) == 3 and partes[1] == "incidentes" and valor is not None:
                    return isinstance(valor, dict) and all(c in valor for c in CAMPOS_OBLIGATORIOS)
                return True

            def do_GET(self):
                self._responder(200, base.leer(self._partes()))

            def do_PUT(self):
                partes, valor = self._partes(), self._cuerpo()
                if self.headers.get("if-match") == "null_etag" and base.leer(partes) is not None:
                    self._responder(412, base.leer(partes))
                    return
                if not self._valido(partes, valor):
                    self._responder(401, {"error": "Permission denied"})
                    return
                base.escribir(partes, valor)
                self._responder(200, valor)

            def do_PATCH(self):
                partes, cambios = self._partes(), self._cuerpo()
                resultado = dict(base.leer(partes) or {})
                resultado.update(cambios)
                if not self._valido(partes, resultado):
                    self._responder(401, {"error": "Permission denied"})
                    return
                base.escribir(partes, resultado)
                self._responder(200, cambios)

            def do_DELETE(self):
                base.escribir(self._partes(), None)
                self._responder(200, None)

        return Manejador


class NotificadorFalso:
    def __init__(self):
        self.avisos = []

    def notificar(self, titulo, mensaje, timeout=5):
        self.avisos.append((titulo, mensaje))
        return True


def al_tiro(trabajo, al_terminar):
    """Ejecutor de prueba: la petición se hace en el momento (sin hilos)."""
    al_terminar(*trabajo())


class Telefono:
    """Una instalación de AlertCom: su carpeta de datos, sus reportes y su nube."""

    def __init__(self, url, usuario):
        self._tmp = tempfile.TemporaryDirectory()
        self.carpeta = Path(self._tmp.name)
        self.notificador = NotificadorFalso()
        self.reportes = IncidenteController(AlmacenamientoJSON(self.carpeta / "incidentes.json"),
                                            notificador=self.notificador)
        self.usuario = usuario
        self.cliente = ClienteFirebase(url, ejecutar=al_tiro)
        self.nube = SincronizadorReportes(self.reportes, self.cliente, self.carpeta,
                                          uid_actual=lambda: self.usuario.uid)

    def reportar(self, tipo="Bache", foto=""):
        return self.reportes.crear_incidente(tipo, "Moderado", "", foto=foto,
                                             usuario_id=self.usuario.uid, **LUGAR)

    def ids(self):
        return sorted(i.id_incidente for i in self.reportes.incidentes)

    def cerrar(self):
        self._tmp.cleanup()


class BaseNube(unittest.TestCase):
    def setUp(self):
        self.firebase = FirebaseFalso()
        self.ana = Usuario.crear(2, "Ana", "ana@a.cl", "123456")
        self.municipio = Usuario.crear(1, "Admin", "a@a.cl", "123456", rol="municipal", uid="municipal-temuco")
        self.tel_ana = Telefono(self.firebase.url, self.ana)
        self.tel_muni = Telefono(self.firebase.url, self.municipio)

    def tearDown(self):
        self.tel_ana.cerrar()
        self.tel_muni.cerrar()
        self.firebase.cerrar()

    def en_la_nube(self):
        return self.firebase.datos.get("alertcom", {}).get("incidentes", {})


# -----------------------------------------------------------------------------
# Pruebas
# -----------------------------------------------------------------------------
class PruebaCompartir(BaseNube):
    def test_lo_que_reporta_ana_lo_ve_el_municipio(self):
        self.tel_ana.reportar()                        # sube al instante
        self.assertIn("reporte_1", self.en_la_nube())
        self.tel_muni.nube.sincronizar()
        self.assertEqual(self.tel_muni.ids(), [1])
        self.assertEqual(self.tel_muni.reportes.buscar(1).usuario_id, self.ana.uid)

    def test_la_foto_viaja_reducida_y_se_descarga(self):
        from PIL import Image
        (self.tel_ana.carpeta / "fotos").mkdir()
        Image.new("RGB", (2000, 1500), (200, 80, 40)).save(self.tel_ana.carpeta / "fotos" / "f1.jpg")
        self.tel_ana.reportar(foto="fotos/f1.jpg")
        texto = self.firebase.datos["alertcom"]["fotos"]["reporte_1"]
        self.assertLess(len(texto), 400_000)
        self.tel_muni.nube.sincronizar()
        copia = self.tel_muni.carpeta / "fotos" / "f1.jpg"
        self.assertTrue(copia.is_file())
        with Image.open(copia) as foto:
            self.assertLessEqual(max(foto.size), 800)

    def test_mismo_numero_en_dos_telefonos_no_se_pisa(self):
        self.firebase.cerrar()                          # los dos sin internet
        self.tel_ana.reportar("Bache")
        self.tel_muni.reportar("Grieta")                # los dos crean el #1
        self.firebase = FirebaseFalso()                 # vuelve internet
        for tel in (self.tel_ana, self.tel_muni):
            tel.cliente.url_base = self.firebase.url
        self.tel_ana.nube.sincronizar()
        self.tel_muni.nube.sincronizar()                # el #1 ya existe → pasa a #2
        self.tel_ana.nube.sincronizar()
        self.assertEqual(sorted(self.en_la_nube()), ["reporte_1", "reporte_2"])
        self.assertEqual(self.tel_ana.ids(), [1, 2])
        self.assertEqual(self.tel_muni.ids(), [1, 2])
        tipos = {self.tel_ana.reportes.buscar(n).tipo_incidente for n in (1, 2)}
        self.assertEqual(tipos, {"Bache", "Grieta"})


class PruebaSinInternet(BaseNube):
    def test_sin_internet_queda_en_cola_y_sube_despues(self):
        self.firebase.cerrar()
        self.tel_ana.reportar()
        self.assertEqual(self.tel_ana.nube.pendientes, 1)
        self.assertFalse(self.tel_ana.nube.conectado)
        self.assertEqual(self.tel_ana.ids(), [1])       # el reporte NO se pierde

        # La app se cierra y se vuelve a abrir: la cola sigue en el archivo
        otra_vez = SincronizadorReportes(self.tel_ana.reportes, self.tel_ana.cliente, self.tel_ana.carpeta)
        self.assertEqual(otra_vez.pendientes, 1)

        self.firebase = FirebaseFalso()
        self.tel_ana.cliente.url_base = self.firebase.url
        otra_vez.sincronizar()
        self.assertEqual(otra_vez.pendientes, 0)
        self.assertTrue(otra_vez.conectado)
        self.assertIn("reporte_1", self.en_la_nube())

    def test_borrar_algo_que_nunca_subio_no_va_a_la_nube(self):
        self.firebase.cerrar()
        reporte = self.tel_muni.reportar()
        self.tel_muni.reportes.eliminar_reporte(reporte.id_incidente, self.municipio, "Está repetido")
        self.assertEqual(self.tel_muni.nube.pendientes, 0)


class PruebaMunicipio(BaseNube):
    def setUp(self):
        super().setUp()
        self.tel_ana.reportar()
        self.tel_muni.nube.sincronizar()
        self.tel_muni.reportes.confirmar_reporte(1, self.municipio)   # ya es público
        self.tel_ana.nube.sincronizar()
        self.tel_ana.notificador.avisos.clear()

    def test_cambio_de_estado_llega_al_vecino_con_aviso(self):
        self.tel_muni.reportes.avanzar_estado(1)        # el municipio, en SU teléfono
        self.assertEqual(self.en_la_nube()["reporte_1"]["estado"], "En revisión")
        self.tel_ana.nube.sincronizar()
        self.assertEqual(self.tel_ana.reportes.buscar(1).estado, "En revisión")
        titulos = [t for t, _ in self.tel_ana.notificador.avisos]
        self.assertIn("Actualización de tu reporte", titulos)

    def test_solicitud_y_aprobacion_entre_telefonos(self):
        self.tel_ana.reportes.solicitar_eliminacion(1, self.ana, "Está repetido")
        self.tel_muni.nube.sincronizar()
        self.assertEqual(len(self.tel_muni.reportes.solicitudes_pendientes()), 1)

        self.tel_muni.reportes.aprobar_eliminacion(1, self.municipio)
        self.assertNotIn("reporte_1", self.en_la_nube())
        self.tel_ana.nube.sincronizar()
        self.assertEqual(self.tel_ana.ids(), [])
        self.assertIn("Solicitud aprobada", [t for t, _ in self.tel_ana.notificador.avisos])

    def test_rechazo_avisa_al_vecino(self):
        self.tel_ana.reportes.solicitar_eliminacion(1, self.ana, "Está repetido")
        self.tel_muni.nube.sincronizar()
        self.tel_muni.reportes.rechazar_eliminacion(1, self.municipio)
        self.tel_ana.nube.sincronizar()
        self.assertFalse(self.tel_ana.reportes.buscar(1).eliminacion_pendiente)
        self.assertIn("Solicitud rechazada", [t for t, _ in self.tel_ana.notificador.avisos])

    def test_el_municipio_elimina_y_el_vecino_recibe_aviso(self):
        self.tel_muni.reportes.eliminar_reporte(1, self.municipio, "El daño ya fue reparado")
        self.assertNotIn("reporte_1", self.en_la_nube())
        self.tel_ana.nube.sincronizar()
        self.assertEqual(self.tel_ana.ids(), [])
        self.assertIn("Reporte eliminado", [t for t, _ in self.tel_ana.notificador.avisos])

    def test_modificar_algo_ya_borrado_no_lo_revive(self):
        self.firebase.datos["alertcom"]["incidentes"].pop("reporte_1")  # otro teléfono lo borró
        self.tel_muni.reportes.avanzar_estado(1)
        self.assertNotIn("reporte_1", self.en_la_nube())   # la regla rechazó el reporte a medias
        self.assertEqual(self.tel_muni.nube.pendientes, 0)
        self.assertEqual(self.tel_muni.ids(), [])           # y la copia local se pone al día


class PruebaSeguridad(BaseNube):
    def test_foto_con_ruta_tramposa_se_ignora(self):
        self.firebase.datos = {"alertcom": {
            "incidentes": {"reporte_7": {
                "id_incidente": 7, "tipo_incidente": "Bache", "gravedad": "Leve", "estado": "Pendiente",
                "ubicacion": LUGAR["ubicacion"], "imagen": "../../fuera.jpg",
                "fecha_creacion": "2026-11-16 10:00:00"}},
            "fotos": {"reporte_7": base64.b64encode(b"x").decode()}}}
        self.tel_ana.nube.sincronizar()
        self.assertEqual(self.tel_ana.ids(), [7])
        self.assertFalse((self.tel_ana.carpeta.parent / "fuera.jpg").exists())

    def test_reportes_antiguos_pasan_de_numero_a_uid(self):
        reportes = self.tel_ana.reportes
        legado = self.tel_ana.reportar()
        legado.usuario_id = 2                       # como lo guardaba la versión 1.5
        reportes.migrar_autores({2: self.ana.uid})
        self.assertEqual(reportes.buscar(legado.id_incidente).usuario_id, self.ana.uid)


if __name__ == "__main__":
    unittest.main()
