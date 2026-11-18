# =============================================================================
# AlertCom - Pruebas: el municipio confirma los reportes nuevos (v1.7)
# =============================================================================
# Un reporte de vecino nace "Por confirmar": solo lo ven su autor y el
# funcionario. Cuando el funcionario lo confirma, aparece en el mapa de todos;
# si no lo aprueba (con motivo), se borra y se avisa al vecino.
#
# Ejecutar desde estructura_AlertCom:
#     python -m unittest discover -s pruebas -v
# =============================================================================

import sys
import tempfile
import unittest
from pathlib import Path

CARPETA_APP = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CARPETA_APP))

from controllers import AlmacenamientoJSON, IncidenteController  # noqa: E402
from models.incidente import Incidente  # noqa: E402
from models.usuario import Usuario  # noqa: E402
from test_nube import BaseNube  # noqa: E402

LUGAR = {"ubicacion": "-38.7359, -72.5904", "calle": "Prat 100"}


class NotificadorFalso:
    def __init__(self):
        self.avisos = []

    def notificar(self, titulo, mensaje, timeout=5):
        self.avisos.append((titulo, mensaje))
        return True


class PruebaConfirmacion(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.notificador = NotificadorFalso()
        self.ctrl = IncidenteController(AlmacenamientoJSON(Path(self._tmp.name) / "i.json"),
                                        notificador=self.notificador)
        self.ana = Usuario.crear(2, "Ana", "ana@a.cl", "123456")
        self.beto = Usuario.crear(3, "Beto", "beto@a.cl", "123456")
        self.municipio = Usuario.crear(1, "Admin", "a@a.cl", "123456", rol="municipal")
        self.reporte = self.ctrl.crear_incidente("Bache", "Grave", usuario_id=self.ana.uid, **LUGAR)

    def tearDown(self):
        self._tmp.cleanup()

    def visibles(self, usuario):
        return [i.id_incidente for i in self.ctrl.visibles_para(usuario)]

    def test_el_reporte_nuevo_nace_por_confirmar(self):
        self.assertFalse(self.reporte.confirmado)
        self.assertIn("cuando el municipio lo confirme", self.notificador.avisos[-1][1])

    def test_por_confirmar_solo_lo_ven_su_autor_y_el_municipio(self):
        self.assertEqual(self.visibles(self.ana), [1])
        self.assertEqual(self.visibles(self.municipio), [1])
        self.assertEqual(self.visibles(self.beto), [])     # otro vecino no lo ve
        self.assertEqual(self.visibles(None), [])

    def test_al_confirmar_lo_ven_todos(self):
        self.ctrl.confirmar_reporte(1, self.municipio)
        self.assertEqual(self.visibles(self.beto), [1])
        self.assertEqual(self.ctrl.por_confirmar(), [])
        with self.assertRaises(ValueError):
            self.ctrl.confirmar_reporte(1, self.municipio)  # ya estaba confirmado

    def test_un_vecino_no_puede_confirmar_ni_rechazar(self):
        with self.assertRaises(PermissionError):
            self.ctrl.confirmar_reporte(1, self.ana)
        with self.assertRaises(PermissionError):
            self.ctrl.no_aprobar_reporte(1, self.beto, "Está repetido")
        self.assertFalse(self.ctrl.buscar(1).confirmado)

    def test_no_aprobar_pide_motivo_y_borra(self):
        with self.assertRaises(ValueError):
            self.ctrl.no_aprobar_reporte(1, self.municipio, "")
        self.ctrl.no_aprobar_reporte(1, self.municipio, "Está repetido")
        self.assertIsNone(self.ctrl.buscar(1))
        self.assertEqual(self.notificador.avisos[-1][0], "Reporte no aprobado")

    def test_no_se_cambia_el_estado_sin_confirmar(self):
        with self.assertRaises(ValueError):
            self.ctrl.avanzar_estado(1)
        self.ctrl.confirmar_reporte(1, self.municipio)
        self.assertEqual(self.ctrl.avanzar_estado(1).estado, "En revisión")

    def test_el_funcionario_publica_directo(self):
        propio = self.ctrl.crear_incidente("Grieta", "Leve", usuario_id=self.municipio.uid,
                                           confirmado=True, **LUGAR)
        self.assertIn(propio.id_incidente, self.visibles(self.beto))

    def test_reportes_antiguos_siguen_publicos(self):
        antiguo = Incidente.from_dict({"id_incidente": 9, "tipo_incidente": "Hoyo",
                                       "fecha_creacion": "2026-10-01 10:00:00"})
        self.assertTrue(antiguo.confirmado)


class PruebaConfirmacionEntreTelefonos(BaseNube):
    def setUp(self):
        super().setUp()
        self.tel_ana.reportar()
        self.tel_muni.nube.sincronizar()

    def test_confirmar_en_un_telefono_avisa_en_el_otro(self):
        self.assertEqual(len(self.tel_muni.reportes.por_confirmar()), 1)
        self.tel_muni.reportes.confirmar_reporte(1, self.municipio)
        self.assertTrue(self.en_la_nube()["reporte_1"]["confirmado"])
        self.tel_ana.nube.sincronizar()
        self.assertTrue(self.tel_ana.reportes.buscar(1).confirmado)
        self.assertIn("Reporte confirmado", [t for t, _ in self.tel_ana.notificador.avisos])

    def test_no_aprobar_en_un_telefono_avisa_en_el_otro(self):
        self.tel_muni.reportes.no_aprobar_reporte(1, self.municipio, "La foto no corresponde")
        self.assertNotIn("reporte_1", self.en_la_nube())
        self.tel_ana.nube.sincronizar()
        self.assertEqual(self.tel_ana.ids(), [])
        self.assertIn("Reporte no aprobado", [t for t, _ in self.tel_ana.notificador.avisos])



class PruebaEspacioDelFuncionario(unittest.TestCase):
    def test_la_pantalla_de_confirmar_es_solo_municipal(self):
        from views.navegador import Navegador
        self.assertIn("confirmar", Navegador.PANTALLAS_MUNICIPALES)

    def test_primero_los_mas_graves(self):
        from views.componentes.filtros import PRIORIDAD_GRAVEDAD
        orden = sorted(["Leve", "Crítico", "Moderado", "Grave"], key=PRIORIDAD_GRAVEDAD.get)
        self.assertEqual(orden, ["Crítico", "Grave", "Moderado", "Leve"])


if __name__ == "__main__":
    unittest.main()
