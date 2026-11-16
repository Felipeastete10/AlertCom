# =============================================================================
# AlertCom - Pruebas del gestor de cuenta, las preferencias y las tarjetas
# =============================================================================
# Ejecutar desde estructura_AlertCom:
#     python -m unittest discover -s pruebas -v
# Usan carpetas temporales: no tocan tus datos.
# =============================================================================

import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

CARPETA_APP = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CARPETA_APP))

from controllers import AlmacenamientoJSON, AuthController, IncidenteController, RegistroEventos  # noqa: E402
from controllers.preferencias import Preferencias  # noqa: E402
from models.incidente import Incidente  # noqa: E402

CORREO, CLAVE = "vecino@alertcom.cl", "123456"
LUGAR = {"ubicacion": "-38.7359, -72.5904", "calle": "Prat 100"}


class BaseCuenta(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.carpeta = Path(self._tmp.name)
        self.eventos = RegistroEventos(self.carpeta)
        self.auth = self._nuevo_auth()
        self.assertTrue(self.auth.iniciar_sesion(CORREO, CLAVE)[0])

    def tearDown(self):
        self._tmp.cleanup()

    def _nuevo_auth(self):
        return AuthController(AlmacenamientoJSON(self.carpeta / "usuarios.json"), eventos=self.eventos)

    def texto_eventos(self):
        return (self.carpeta / "eventos.jsonl").read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 1. Gestor de cuenta
# ---------------------------------------------------------------------------
class TestCambiarNombre(BaseCuenta):
    def test_cambia_y_se_guarda(self):
        ok, _ = self.auth.cambiar_nombre("  Felipe   Astete ")
        self.assertTrue(ok)
        reabierto = self._nuevo_auth()
        self.assertEqual(reabierto._buscar_por_email(CORREO).nombre, "Felipe Astete")

    def test_nombre_vacio_o_muy_largo(self):
        self.assertFalse(self.auth.cambiar_nombre("   ")[0])
        self.assertFalse(self.auth.cambiar_nombre("A" * 61)[0])


class TestCambiarCorreo(BaseCuenta):
    def test_pide_la_contrasena_actual(self):
        ok, mensaje = self.auth.cambiar_correo("nuevo@correo.cl", "mala")
        self.assertFalse(ok)
        self.assertIn("contraseña actual", mensaje)

    def test_rechaza_formato_invalido_y_duplicado(self):
        self.assertFalse(self.auth.cambiar_correo("sin-arroba", CLAVE)[0])
        self.assertFalse(self.auth.cambiar_correo("admin@gmail.com", CLAVE)[0])  # ya existe
        self.assertFalse(self.auth.cambiar_correo(CORREO, CLAVE)[0])            # es el mismo

    def test_cambio_correcto_permite_entrar_con_el_nuevo(self):
        self.assertTrue(self.auth.cambiar_correo("Felipe@Correo.CL", CLAVE)[0])
        reabierto = self._nuevo_auth()
        self.assertTrue(reabierto.iniciar_sesion("felipe@correo.cl", CLAVE)[0])
        self.assertFalse(reabierto.iniciar_sesion(CORREO, CLAVE)[0])

    def test_el_evento_no_guarda_el_correo(self):
        self.auth.cambiar_correo("felipe@correo.cl", CLAVE)
        texto = self.texto_eventos()
        self.assertIn('"campo": "correo"', texto)
        self.assertNotIn("felipe@correo.cl", texto)


class TestCambiarContrasena(BaseCuenta):
    def test_validaciones(self):
        self.assertFalse(self.auth.cambiar_contrasena("mala", "nueva123", "nueva123")[0])
        self.assertFalse(self.auth.cambiar_contrasena(CLAVE, "123", "123")[0])
        self.assertFalse(self.auth.cambiar_contrasena(CLAVE, "nueva123", "otra123")[0])
        self.assertFalse(self.auth.cambiar_contrasena(CLAVE, CLAVE, CLAVE)[0])

    def test_cambio_correcto(self):
        hash_antes = self.auth.usuario_actual.hash_contrasena
        self.assertTrue(self.auth.cambiar_contrasena(CLAVE, "nueva123", "nueva123")[0])
        self.assertNotEqual(self.auth.usuario_actual.hash_contrasena, hash_antes)
        reabierto = self._nuevo_auth()
        self.assertTrue(reabierto.iniciar_sesion(CORREO, "nueva123")[0])
        self.assertFalse(reabierto.iniciar_sesion(CORREO, CLAVE)[0])
        self.assertNotIn("nueva123", (self.carpeta / "usuarios.json").read_text(encoding="utf-8"))


class TestEliminarCuenta(BaseCuenta):
    def test_con_contrasena_incorrecta_no_borra(self):
        self.assertFalse(self.auth.eliminar_cuenta("mala")[0])
        self.assertIsNotNone(self.auth.usuario_actual)

    def test_elimina_cierra_sesion_y_conserva_los_reportes(self):
        incidentes = IncidenteController(AlmacenamientoJSON(self.carpeta / "i.json"))
        id_usuario = self.auth.usuario_actual.id_usuario
        incidentes.crear_incidente("Bache", "Leve", usuario_id=id_usuario, **LUGAR)

        self.assertTrue(self.auth.eliminar_cuenta(CLAVE)[0])
        self.assertEqual(incidentes.desvincular_usuario(id_usuario), 1)

        self.assertIsNone(self.auth.usuario_actual)
        self.assertFalse(self._nuevo_auth().iniciar_sesion(CORREO, CLAVE)[0])
        reportes = IncidenteController(AlmacenamientoJSON(self.carpeta / "i.json")).obtener_historial()
        self.assertEqual(len(reportes), 1)              # el bache sigue registrado
        self.assertIsNone(reportes[0].usuario_id)       # pero sin dueño
        self.assertIn("cuenta_eliminada", self.texto_eventos())


# ---------------------------------------------------------------------------
# 2. Preferencias (tamaño de letra, fondo, analítica)
# ---------------------------------------------------------------------------
class TestPreferencias(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.carpeta = Path(self._tmp.name)
        self.ruta = self.carpeta / "preferencias.json"

    def tearDown(self):
        self._tmp.cleanup()

    def test_se_mezclan_y_no_se_borran(self):
        prefs = Preferencias(self.ruta)
        prefs.guardar("tamano_letra", "grande")
        prefs.guardar("fondo", "azul")
        RegistroEventos(self.carpeta).cambiar_activo(False)   # antes borraba lo demás
        datos = json.loads(self.ruta.read_text(encoding="utf-8"))
        self.assertEqual(datos, {"tamano_letra": "grande", "fondo": "azul", "analitica_activa": False})

    def test_archivo_danado_usa_valores_por_defecto(self):
        self.ruta.write_text("{roto", encoding="utf-8")
        self.assertEqual(Preferencias(self.ruta).obtener("fondo", "original"), "original")
        self.assertTrue(RegistroEventos(self.carpeta).activo)


# ---------------------------------------------------------------------------
# 3. Datos de las tarjetas de reporte
# ---------------------------------------------------------------------------
class TestTarjetaReporte(unittest.TestCase):
    def test_antiguedad_legible(self):
        base = datetime(2026, 11, 12, 12, 0)
        inc = Incidente(1, "Bache", "Leve", fecha_creacion=base)
        casos = [(timedelta(seconds=20), "hace un momento"), (timedelta(minutes=5), "hace 5 min"),
                 (timedelta(hours=2), "hace 2 h"), (timedelta(days=1, hours=3), "ayer"),
                 (timedelta(days=3), "hace 3 días"), (timedelta(days=20), "12/11/2026")]
        for paso, esperado in casos:
            self.assertEqual(inc.antiguedad_legible(base + paso), esperado)

    def test_paso_del_estado(self):
        inc = Incidente(1, "Bache", "Leve")
        self.assertEqual(inc.paso_estado(), 0)
        inc.estado = "En revisión"
        self.assertEqual(inc.paso_estado(), 1)
        inc.estado = "Reparado"
        self.assertEqual(inc.paso_estado(), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
