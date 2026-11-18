# =============================================================================
# AlertCom - Pruebas: eliminar un reporte con autorización del funcionario
# =============================================================================
# El vecino PIDE eliminar su reporte (con un motivo); solo un funcionario
# municipal puede APROBAR o RECHAZAR. Ejecutar desde estructura_AlertCom:
#     python -m unittest discover -s pruebas -v
# =============================================================================

import json
import sys
import tempfile
import unittest
from pathlib import Path

CARPETA_APP = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CARPETA_APP))

from PIL import Image  # noqa: E402

from controllers import AlmacenamientoJSON, IncidenteController, RegistroEventos  # noqa: E402
from controllers import fotos  # noqa: E402
from models.usuario import Usuario  # noqa: E402

LUGAR = {"ubicacion": "-38.7359, -72.5904", "calle": "Prat 100"}
MOTIVO = "Está repetido"


class BaseEliminacion(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.carpeta = Path(self._tmp.name)
        self.ruta = self.carpeta / "incidentes.json"
        self.ctrl = IncidenteController(AlmacenamientoJSON(self.ruta), eventos=RegistroEventos(self.carpeta))
        self.vecino = Usuario.crear(2, "Vecina", "v@a.cl", "123456")
        self.otro_vecino = Usuario.crear(3, "Otro", "o@a.cl", "123456")
        self.funcionario = Usuario.crear(1, "Admin", "a@a.cl", "123456", rol="municipal")
        self.reporte = self.ctrl.crear_incidente("Bache", "Leve", usuario_id=self.vecino.uid, **LUGAR)

    def tearDown(self):
        self._tmp.cleanup()

    def eventos(self):
        texto = (self.carpeta / "eventos.jsonl").read_text(encoding="utf-8")
        return [json.loads(linea)["evento"] for linea in texto.splitlines()]

    def recargar(self):
        return IncidenteController(AlmacenamientoJSON(self.ruta))


class TestSolicitud(BaseEliminacion):
    def test_el_dueno_pide_y_el_reporte_sigue_existiendo(self):
        self.ctrl.solicitar_eliminacion(self.reporte.id_incidente, self.vecino, MOTIVO)
        guardado = self.recargar().buscar(self.reporte.id_incidente)
        self.assertIsNotNone(guardado)                           # no se borra solo
        self.assertTrue(guardado.eliminacion_pendiente)
        self.assertEqual(guardado.solicitud_eliminacion["motivo"], MOTIVO)
        self.assertIn("eliminacion_solicitada", self.eventos())

    def test_otro_vecino_no_puede_pedirlo(self):
        with self.assertRaises(PermissionError):
            self.ctrl.solicitar_eliminacion(self.reporte.id_incidente, self.otro_vecino, MOTIVO)

    def test_motivo_obligatorio_y_sin_duplicar(self):
        with self.assertRaises(ValueError):
            self.ctrl.solicitar_eliminacion(self.reporte.id_incidente, self.vecino, "")
        self.ctrl.solicitar_eliminacion(self.reporte.id_incidente, self.vecino, MOTIVO)
        with self.assertRaises(ValueError):
            self.ctrl.solicitar_eliminacion(self.reporte.id_incidente, self.vecino, MOTIVO)

    def test_el_vecino_puede_cancelar(self):
        self.ctrl.solicitar_eliminacion(self.reporte.id_incidente, self.vecino, MOTIVO)
        self.ctrl.cancelar_solicitud_eliminacion(self.reporte.id_incidente, self.vecino)
        self.assertFalse(self.recargar().buscar(self.reporte.id_incidente).eliminacion_pendiente)


class TestDecisionDelFuncionario(BaseEliminacion):
    def setUp(self):
        super().setUp()
        self.ctrl.solicitar_eliminacion(self.reporte.id_incidente, self.vecino, MOTIVO)

    def test_un_vecino_no_puede_aprobar_ni_rechazar(self):
        for persona in (self.vecino, None):
            with self.assertRaises(PermissionError):
                self.ctrl.aprobar_eliminacion(self.reporte.id_incidente, persona)
            with self.assertRaises(PermissionError):
                self.ctrl.rechazar_eliminacion(self.reporte.id_incidente, persona)
        self.assertIsNotNone(self.recargar().buscar(self.reporte.id_incidente))

    def test_aprobar_borra_el_reporte_y_su_foto(self):
        original = self.carpeta / "original.jpg"
        Image.new("RGB", (300, 200), (90, 90, 90)).save(original)
        relativa = fotos.guardar_foto_reducida(original, self.carpeta)
        con_foto = self.ctrl.crear_incidente("Hoyo", "Grave", foto=relativa, usuario_id=self.vecino.uid, **LUGAR)
        self.ctrl.solicitar_eliminacion(con_foto.id_incidente, self.vecino, MOTIVO)

        self.ctrl.aprobar_eliminacion(con_foto.id_incidente, self.funcionario)
        self.assertIsNone(self.recargar().buscar(con_foto.id_incidente))
        self.assertIsNone(fotos.ruta_foto(self.carpeta, relativa))   # la foto también
        self.assertIn("eliminacion_aprobada", self.eventos())

    def test_rechazar_mantiene_el_reporte(self):
        self.ctrl.rechazar_eliminacion(self.reporte.id_incidente, self.funcionario)
        guardado = self.recargar().buscar(self.reporte.id_incidente)
        self.assertIsNotNone(guardado)
        self.assertFalse(guardado.eliminacion_pendiente)
        self.assertIn("eliminacion_rechazada", self.eventos())

    def test_no_se_aprueba_lo_que_nadie_pidio(self):
        otro = self.ctrl.crear_incidente("Grieta", "Leve", usuario_id=self.vecino.uid, **LUGAR)
        with self.assertRaises(ValueError):
            self.ctrl.aprobar_eliminacion(otro.id_incidente, self.funcionario)

    def test_lista_de_pendientes_para_el_funcionario(self):
        pendientes = self.ctrl.solicitudes_pendientes()
        self.assertEqual([i.id_incidente for i in pendientes], [self.reporte.id_incidente])


MOTIVO_MUNICIPIO = "El daño ya fue reparado"


class TestFuncionarioEliminaCualquiera(BaseEliminacion):
    """v1.9: el funcionario puede eliminar cualquier reporte, siempre con motivo."""

    def test_borra_su_propio_reporte_sin_solicitud(self):
        propio = self.ctrl.crear_incidente("Grieta", "Leve", usuario_id=self.funcionario.uid, **LUGAR)
        self.ctrl.eliminar_reporte(propio.id_incidente, self.funcionario, MOTIVO_MUNICIPIO)
        self.assertIsNone(self.recargar().buscar(propio.id_incidente))
        self.assertIn("reporte_eliminado", self.eventos())

    def test_borra_directo_el_reporte_de_un_vecino(self):
        self.ctrl.eliminar_reporte(self.reporte.id_incidente, self.funcionario, "Está repetido")
        self.assertIsNone(self.recargar().buscar(self.reporte.id_incidente))

    def test_sin_motivo_no_se_borra(self):
        with self.assertRaises(ValueError):
            self.ctrl.eliminar_reporte(self.reporte.id_incidente, self.funcionario, "")
        self.assertIsNotNone(self.recargar().buscar(self.reporte.id_incidente))

    def test_un_vecino_no_puede_usar_la_eliminacion_directa(self):
        for quien in (self.vecino, self.otro_vecino, None):
            with self.assertRaises(PermissionError):
                self.ctrl.eliminar_reporte(self.reporte.id_incidente, quien, MOTIVO_MUNICIPIO)
        self.assertIsNotNone(self.recargar().buscar(self.reporte.id_incidente))


if __name__ == "__main__":
    unittest.main(verbosity=2)
