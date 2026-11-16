# =============================================================================
# AlertCom - Pruebas del reporte completo: ubicación, calle y foto (v1.5)
# =============================================================================
# Ejecutar desde estructura_AlertCom:
#     python -m unittest discover -s pruebas -v
#
# La cámara y el GPS reales solo existen en el teléfono; aquí se prueba la
# lógica que no depende del hardware: validaciones, foto reducida y sin
# metadatos, lectura de coordenadas y calle desde la respuesta de Nominatim.
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
from controllers.direcciones import (  # noqa: E402
    calle_desde_respuesta,
    lugar_desde_busqueda,
    texto_de_busqueda,
)
from models.incidente import Incidente, leer_coordenadas  # noqa: E402

UBICACION = "-38.739120, -72.598300"


class BaseTemporal(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.carpeta = Path(self._tmp.name)
        self.eventos = RegistroEventos(self.carpeta)
        self.ctrl = IncidenteController(AlmacenamientoJSON(self.carpeta / "i.json"), eventos=self.eventos)

    def tearDown(self):
        self._tmp.cleanup()

    def motivos_rechazo(self):
        ruta = self.carpeta / "eventos.jsonl"
        if not ruta.exists():
            return []
        return [json.loads(l)["datos"]["motivo"] for l in ruta.read_text(encoding="utf-8").splitlines()
                if json.loads(l)["evento"] == "reporte_rechazado"]


# ---------------------------------------------------------------------------
# 1. Ubicación y calle obligatorias
# ---------------------------------------------------------------------------
class TestUbicacionYCalle(BaseTemporal):
    def test_sin_ubicacion_se_rechaza(self):
        # Antes se guardaba el centro de Temuco y los marcadores se apilaban.
        with self.assertRaises(ValueError):
            self.ctrl.crear_incidente("Hoyo", "Grave", ubicacion=None, calle="Prat 100")
        self.assertEqual(self.motivos_rechazo(), ["sin_ubicacion"])

    def test_ubicacion_invalida_se_rechaza(self):
        for mala in ("", "hola", "-38.7", "200, 10"):
            with self.assertRaises(ValueError):
                self.ctrl.crear_incidente("Hoyo", "Grave", ubicacion=mala, calle="Prat 100")

    def test_sin_calle_se_rechaza(self):
        with self.assertRaises(ValueError):
            self.ctrl.crear_incidente("Hoyo", "Grave", ubicacion=UBICACION, calle="   ")
        self.assertEqual(self.motivos_rechazo(), ["sin_calle"])

    def test_calle_muy_larga_se_rechaza(self):
        with self.assertRaises(ValueError):
            self.ctrl.crear_incidente("Hoyo", "Grave", ubicacion=UBICACION, calle="A" * 121)

    def test_reporte_valido_guarda_calle_y_coordenadas(self):
        inc = self.ctrl.crear_incidente("Hoyo", "Grave", ubicacion=UBICACION,
                                        calle="  Avenida   Alemania  450 ")
        self.assertEqual(inc.calle, "Avenida Alemania 450")  # espacios ordenados
        self.assertEqual(inc.coordenadas(), (-38.73912, -72.5983))
        reabierto = IncidenteController(AlmacenamientoJSON(self.carpeta / "i.json"))
        self.assertEqual(reabierto.buscar(inc.id_incidente).calle, "Avenida Alemania 450")

    def test_reportes_antiguos_sin_calle_se_siguen_leyendo(self):
        antiguo = {"id_incidente": 1, "tipo_incidente": "Bache", "estado": "Pendiente",
                   "fecha_creacion": "2026-10-29 09:58:12", "ubicacion": "-38.7359, -72.5904"}
        self.assertEqual(Incidente.from_dict(antiguo).calle, "")

    def test_leer_coordenadas(self):
        self.assertEqual(leer_coordenadas("-38.5, -72.1"), (-38.5, -72.1))
        self.assertIsNone(leer_coordenadas(None))
        self.assertIsNone(leer_coordenadas("91, 0"))


# ---------------------------------------------------------------------------
# 2. Foto reducida, enderezada y sin metadatos
# ---------------------------------------------------------------------------
class TestFotos(BaseTemporal):
    def crear_foto(self, ancho=4000, alto=3000, con_exif=True) -> Path:
        ruta = self.carpeta / "original.jpg"
        imagen = Image.new("RGB", (ancho, alto), (120, 90, 60))
        exif = Image.Exif()
        if con_exif:
            exif[0x0112] = 6        # orientación: teléfono girado
            exif[0x0110] = "Telefono de prueba"  # modelo de la cámara
        imagen.save(ruta, "JPEG", exif=exif)
        return ruta

    def test_reduce_endereza_y_quita_metadatos(self):
        relativa = fotos.guardar_foto_reducida(self.crear_foto(), self.carpeta)
        self.assertTrue(relativa.startswith("fotos/"))  # ruta relativa, no absoluta
        ruta = fotos.ruta_foto(self.carpeta, relativa)
        with Image.open(ruta) as foto:
            self.assertEqual(foto.size, (960, 1280))  # girada y con lado mayor 1280
            self.assertEqual(len(foto.getexif()), 0)  # sin modelo ni GPS
        self.assertLess(ruta.stat().st_size, 400_000)

    def test_png_con_transparencia_se_guarda_como_jpg(self):
        ruta = self.carpeta / "captura.png"
        Image.new("RGBA", (300, 200), (0, 0, 0, 0)).save(ruta)
        relativa = fotos.guardar_foto_reducida(ruta, self.carpeta)
        self.assertTrue(relativa.endswith(".jpg"))

    def test_archivo_que_no_es_imagen_da_error_claro(self):
        falso = self.carpeta / "virus.jpg"
        falso.write_text("no soy una foto", encoding="utf-8")
        with self.assertRaises(ValueError):
            fotos.guardar_foto_reducida(falso, self.carpeta)

    def test_borrar_foto_no_enviada(self):
        relativa = fotos.guardar_foto_reducida(self.crear_foto(800, 600, False), self.carpeta)
        fotos.borrar_foto(self.carpeta, relativa)
        self.assertIsNone(fotos.ruta_foto(self.carpeta, relativa))
        fotos.borrar_foto(self.carpeta, relativa)  # borrar dos veces no falla

    def test_reporte_con_foto_registra_con_foto_true(self):
        relativa = fotos.guardar_foto_reducida(self.crear_foto(800, 600, False), self.carpeta)
        inc = self.ctrl.crear_incidente("Bache", "Leve", foto=relativa, ubicacion=UBICACION, calle="Prat 1")
        self.assertEqual(inc.imagen, relativa)
        texto = (self.carpeta / "eventos.jsonl").read_text(encoding="utf-8")
        self.assertIn('"con_foto": true', texto)
        self.assertNotIn("fotos/", texto)  # el nombre del archivo no va a la analítica


# ---------------------------------------------------------------------------
# 3. Calle desde la respuesta de Nominatim (OpenStreetMap)
# ---------------------------------------------------------------------------
class TestCalleDesdeCoordenadas(unittest.TestCase):
    def test_calle_con_numero(self):
        datos = {"address": {"road": "Avenida Alemania", "house_number": "0450", "city": "Temuco"}}
        self.assertEqual(calle_desde_respuesta(datos), "Avenida Alemania 0450")

    def test_calle_sin_numero(self):
        self.assertEqual(calle_desde_respuesta({"address": {"road": "Manuel Montt"}}), "Manuel Montt")

    def test_paseo_peatonal(self):
        self.assertEqual(calle_desde_respuesta({"address": {"pedestrian": "Paseo Bulnes"}}), "Paseo Bulnes")

    def test_calle_escrita_con_numero_encontrado(self):
        datos = [{"lat": "-38.7391", "lon": "-72.6052",
                  "address": {"road": "Avenida Alemania", "house_number": "450"}}]
        self.assertEqual(lugar_desde_busqueda(datos), (-38.7391, -72.6052, True))

    def test_calle_escrita_sin_numero_pide_ajustar(self):
        datos = [{"lat": "-38.74", "lon": "-72.59", "address": {"road": "Manuel Montt"}}]
        self.assertEqual(lugar_desde_busqueda(datos)[2], False)

    def test_calle_no_encontrada(self):
        self.assertIsNone(lugar_desde_busqueda([]))
        self.assertIsNone(lugar_desde_busqueda({"error": "x"}))
        self.assertIsNone(lugar_desde_busqueda([{"lat": "no", "lon": "-72"}]))

    def test_la_busqueda_se_limita_a_temuco(self):
        self.assertEqual(texto_de_busqueda("  Prat   450 "), "Prat 450, Temuco")
        self.assertEqual(texto_de_busqueda("Prat 450, Temuco"), "Prat 450, Temuco")

    def test_sin_calle_o_respuesta_rara(self):
        self.assertIsNone(calle_desde_respuesta({"address": {"city": "Temuco"}}))
        self.assertIsNone(calle_desde_respuesta({"error": "Unable to geocode"}))
        self.assertIsNone(calle_desde_respuesta(None))
        self.assertIsNone(calle_desde_respuesta("texto"))


# ---------------------------------------------------------------------------
# 4. Decisiones del GPS (sin teléfono: se simulan las lecturas)
# ---------------------------------------------------------------------------
class TestDecisionesGPS(unittest.TestCase):
    def setUp(self):
        from controllers.ubicacion import ServicioUbicacion
        self.servicio = ServicioUbicacion(precision_buena=30, tiempo_maximo=20)
        self.obtenidas, self.fallos = [], []
        self.servicio._al_obtener = lambda *datos: self.obtenidas.append(datos)
        self.servicio._al_fallar = lambda *datos: self.fallos.append(datos)
        self.servicio.buscando = True

    def test_lectura_precisa_termina_y_apaga_el_gps(self):
        self.servicio._procesar(-38.74, -72.60, 12.0)
        self.assertEqual(self.obtenidas, [(-38.74, -72.60, 12.0, True)])
        self.assertFalse(self.servicio.buscando)

    def test_lectura_imprecisa_mueve_el_mapa_pero_sigue_buscando(self):
        self.servicio._procesar(-38.74, -72.60, 150.0)
        self.assertEqual(self.obtenidas, [(-38.74, -72.60, 150.0, False)])
        self.assertTrue(self.servicio.buscando)

    def test_al_vencer_el_tiempo_se_usa_la_mejor_lectura(self):
        self.servicio._procesar(-38.70, -72.50, 300.0)
        self.servicio._procesar(-38.74, -72.60, 80.0)
        self.servicio._al_vencer_tiempo(0)
        self.assertEqual(self.obtenidas[-1], (-38.74, -72.60, 80.0, True))

    def test_sin_ninguna_lectura_avisa_sin_senal(self):
        self.servicio._al_vencer_tiempo(0)
        self.assertEqual(self.fallos[0][0], "sin_senal")

    def test_en_el_computador_avisa_que_no_hay_gps(self):
        self.servicio.buscando = False
        self.servicio.pedir(lambda *a: None, lambda *datos: self.fallos.append(datos))
        self.assertEqual(self.fallos[0][0], "no_disponible")


if __name__ == "__main__":
    unittest.main(verbosity=2)
