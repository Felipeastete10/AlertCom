# =============================================================================
# AlertCom - Pruebas: zona de Temuco y colores de fondo (v1.6)
# =============================================================================
# Ejecutar desde estructura_AlertCom:
#     python -m unittest discover -s pruebas -v
# =============================================================================

import sys
import tempfile
import unittest
from pathlib import Path

CARPETA_APP = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CARPETA_APP))

from config import CENTRO_TEMUCO, FONDOS, LIMITES_TEMUCO  # noqa: E402
from controllers.almacenamiento_json import AlmacenamientoJSON  # noqa: E402
from controllers.incidente_controller import IncidenteController  # noqa: E402
from models.incidente import dentro_de_zona  # noqa: E402

PLAZA_TEMUCO = "-38.739120, -72.598300"
PADRE_LAS_CASAS = "-38.766500, -72.596000"
SANTIAGO = "-33.448900, -70.669300"
VILLARRICA = "-39.282000, -72.227000"


class PruebaZonaTemuco(unittest.TestCase):
    def setUp(self):
        self.carpeta = tempfile.TemporaryDirectory()
        self.controlador = IncidenteController(AlmacenamientoJSON(Path(self.carpeta.name) / "inc.json"))

    def tearDown(self):
        self.carpeta.cleanup()

    def crear(self, ubicacion):
        return self.controlador.crear_incidente("Bache", "Moderado", "", ubicacion=ubicacion,
                                                usuario_id=1, calle="Calle de prueba 123")

    def test_el_centro_de_temuco_esta_dentro(self):
        self.assertTrue(dentro_de_zona(*CENTRO_TEMUCO, LIMITES_TEMUCO))

    def test_temuco_y_padre_las_casas_se_aceptan(self):
        self.assertEqual(self.crear(PLAZA_TEMUCO).calle, "Calle de prueba 123")
        self.assertIsNotNone(self.crear(PADRE_LAS_CASAS))

    def test_fuera_de_temuco_se_rechaza(self):
        for lugar in (SANTIAGO, VILLARRICA):
            with self.assertRaises(ValueError) as error:
                self.crear(lugar)
            self.assertIn("Temuco", str(error.exception))
        self.assertEqual(self.controlador.obtener_historial(), [])


class PruebaZoomMinimo(unittest.TestCase):
    def test_pantalla_mas_grande_necesita_mas_zoom(self):
        from views.componentes.mapa import zoom_minimo_para
        chico = zoom_minimo_para(360, 600)
        grande = zoom_minimo_para(1440, 2400)
        self.assertGreaterEqual(grande, chico)

    def test_en_el_zoom_minimo_la_pantalla_cabe_en_temuco(self):
        from views.componentes.mapa import zoom_minimo_para
        oeste, sur, este, norte = LIMITES_TEMUCO
        for ancho, alto in ((360, 600), (720, 1300), (1080, 2000)):
            zoom = zoom_minimo_para(ancho, alto)
            grados_por_pixel = 360 / (256 * 2 ** zoom)
            self.assertLessEqual(ancho * grados_por_pixel, este - oeste)


class PruebaFondos(unittest.TestCase):
    @staticmethod
    def contraste_con_blanco(color):
        def canal(v):
            return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
        luz = 0.2126 * canal(color[0]) + 0.7152 * canal(color[1]) + 0.0722 * canal(color[2])
        return 1.05 / (luz + 0.05)

    def test_el_texto_blanco_se_lee_en_todos_los_fondos(self):
        for _clave, nombre, color in FONDOS:
            if color:
                self.assertGreaterEqual(self.contraste_con_blanco(color), 7, nombre)

    def test_los_fondos_se_distinguen_entre_si(self):
        # Antes eran casi negros y no se notaba el cambio en el teléfono
        colores = [c for _k, _n, c in FONDOS if c]
        for i, a in enumerate(colores):
            for b in colores[i + 1:]:
                diferencia = sum(abs(x - y) for x, y in zip(a[:3], b[:3]))
                self.assertGreater(diferencia, 0.12, (a, b))


if __name__ == "__main__":
    unittest.main()
