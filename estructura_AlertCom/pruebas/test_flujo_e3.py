# =============================================================================
# AlertCom - Pruebas automáticas del flujo principal (Checklist E3)
# =============================================================================
# Ejecutar desde la carpeta estructura_AlertCom:
#
#     python -m unittest discover -s pruebas -v
#
# No abren la app ni necesitan internet: prueban modelos, persistencia JSON,
# login, notificaciones y el filtro de la configuración remota.
# Usan una carpeta temporal, así que NO tocan tus datos reales.
# =============================================================================

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

CARPETA_APP = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CARPETA_APP))

from controllers import (  # noqa: E402
    AlmacenamientoJSON,
    AuthController,
    IncidenteController,
    filtrar_config,
)
from models import Incidente, Usuario  # noqa: E402


class NotificadorFalso:
    """Reemplaza a Plyer en las pruebas y recuerda lo que se notificó."""

    def __init__(self):
        self.enviadas = []

    def notificar(self, titulo, mensaje, timeout=5):
        self.enviadas.append((titulo, mensaje))
        return True


class BaseTemporal(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.carpeta = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()


# ---------------------------------------------------------------------------
# 1. Arquitectura: los modelos no dependen de Kivy
# ---------------------------------------------------------------------------
class TestArquitectura(unittest.TestCase):
    def test_modelos_no_importan_kivy(self):
        codigo = (
            "import sys; sys.path.insert(0, r'%s'); import models; "
            "print(any(m.startswith('kivy') for m in sys.modules))" % CARPETA_APP
        )
        salida = subprocess.run([sys.executable, "-c", codigo], capture_output=True, text=True)
        self.assertEqual(salida.stdout.strip(), "False", salida.stderr)

    def test_ningun_modelo_menciona_kivy_en_sus_imports(self):
        for archivo in (CARPETA_APP / "models").glob("*.py"):
            for linea in archivo.read_text(encoding="utf-8").splitlines():
                if linea.strip().startswith(("import", "from")):
                    self.assertNotIn("kivy", linea.lower(), f"{archivo.name}: {linea}")

    def test_controladores_no_importan_vistas(self):
        for archivo in (CARPETA_APP / "controllers").glob("*.py"):
            for linea in archivo.read_text(encoding="utf-8").splitlines():
                if linea.strip().startswith(("import", "from")):
                    self.assertNotIn("views", linea, f"{archivo.name}: {linea}")

    def test_main_es_minimalista(self):
        lineas = (CARPETA_APP / "main.py").read_text(encoding="utf-8").splitlines()
        self.assertLess(len(lineas), 30)

    def test_cada_carpeta_es_un_paquete(self):
        for carpeta in ("models", "controllers", "views", "views/pantallas",
                        "views/componentes", "pruebas"):
            self.assertTrue((CARPETA_APP / carpeta / "__init__.py").exists(), carpeta)

    def test_cada_pantalla_tiene_su_kv(self):
        for vista in (CARPETA_APP / "views" / "pantallas").glob("*_view.py"):
            nombre = vista.stem.removesuffix("_view")
            self.assertTrue((CARPETA_APP / "views" / "kv" / f"{nombre}.kv").exists(), nombre)


# ---------------------------------------------------------------------------
# 2. Modelos
# ---------------------------------------------------------------------------
class TestModelos(unittest.TestCase):
    def test_usuario_no_guarda_contrasena_en_texto_plano(self):
        usuario = Usuario.crear(1, "Ana", "Ana@Correo.cl", "secreta1")
        self.assertNotIn("secreta1", json.dumps(usuario.to_dict()))
        self.assertEqual(usuario.email, "ana@correo.cl")
        self.assertTrue(usuario.verificar_contrasena("secreta1"))
        self.assertFalse(usuario.verificar_contrasena("otra"))

    def test_incidente_ida_y_vuelta_dict(self):
        original = Incidente(7, "Bache", "frente al 450", "Grave", ubicacion="-38.7, -72.5")
        copia = Incidente.from_dict(original.to_dict())
        self.assertEqual(copia.to_dict(), original.to_dict())
        self.assertEqual(copia.coordenadas(), (-38.7, -72.5))

    def test_ciclo_de_estados(self):
        inc = Incidente(1, "Bache")
        self.assertEqual(inc.siguiente_estado(), "En revisión")
        inc.cambiar_estado("Reparado")
        self.assertIsNone(inc.siguiente_estado())
        with self.assertRaises(ValueError):
            inc.cambiar_estado("Inventado")


# ---------------------------------------------------------------------------
# 3. Persistencia JSON
# ---------------------------------------------------------------------------
class TestPersistencia(BaseTemporal):
    def test_archivo_inexistente_no_cae(self):
        almacen = AlmacenamientoJSON(self.carpeta / "no_existe.json")
        self.assertEqual(almacen.cargar(), [])

    def test_guardar_y_cargar(self):
        almacen = AlmacenamientoJSON(self.carpeta / "datos.json")
        almacen.guardar([{"a": 1, "texto": "Ñuñoa"}])
        self.assertEqual(almacen.cargar(), [{"a": 1, "texto": "Ñuñoa"}])

    def test_json_danado_se_respalda(self):
        ruta = self.carpeta / "datos.json"
        ruta.write_text("{esto no es json", encoding="utf-8")
        self.assertEqual(AlmacenamientoJSON(ruta).cargar(), [])
        self.assertTrue((self.carpeta / "datos.corrupto.json").exists())

    def test_reportes_sobreviven_al_reinicio(self):
        ruta = self.carpeta / "incidentes.json"
        IncidenteController(AlmacenamientoJSON(ruta)).crear_incidente("Bache", "Leve", "uno")
        # "Reiniciar la app" = crear un controlador nuevo que lee el mismo archivo
        reabierto = IncidenteController(AlmacenamientoJSON(ruta))
        self.assertEqual(len(reabierto.obtener_historial()), 1)
        self.assertEqual(reabierto.crear_incidente("Hoyo", "Grave").id_incidente, 2)


# ---------------------------------------------------------------------------
# 4. Autenticación con usuarios.json
# ---------------------------------------------------------------------------
class TestAutenticacion(BaseTemporal):
    def setUp(self):
        super().setUp()
        self.ruta = self.carpeta / "usuarios.json"
        self.auth = AuthController(AlmacenamientoJSON(self.ruta))

    def test_instalacion_nueva_crea_usuarios_demo(self):
        self.assertTrue(self.ruta.exists())
        self.assertNotIn("123456", self.ruta.read_text(encoding="utf-8"))

    def test_login_correcto_e_incorrecto(self):
        self.assertEqual(self.auth.iniciar_sesion("admin@gmail.com", "malo")[0], False)
        self.assertFalse(self.auth.esta_autenticado())
        self.assertEqual(self.auth.iniciar_sesion("ADMIN@gmail.com ", "123456"), (True, None))
        self.assertTrue(self.auth.usuario_actual.es_municipal)
        self.auth.cerrar_sesion()
        self.assertFalse(self.auth.esta_autenticado())

    def test_registro_persiste_y_valida(self):
        self.assertFalse(self.auth.registrar("Ana", "correo-malo", "abcdef", "abcdef")[0])
        self.assertFalse(self.auth.registrar("Ana", "ana@c.cl", "abc", "abc")[0])
        self.assertFalse(self.auth.registrar("Ana", "ana@c.cl", "abcdef", "xxxxxx")[0])
        self.assertTrue(self.auth.registrar("Ana", "ana@c.cl", "abcdef", "abcdef")[0])
        self.assertFalse(self.auth.registrar("Ana", "ana@c.cl", "abcdef", "abcdef")[0])  # duplicado

        reabierto = AuthController(AlmacenamientoJSON(self.ruta))
        self.assertTrue(reabierto.iniciar_sesion("ana@c.cl", "abcdef")[0])


# ---------------------------------------------------------------------------
# 5. Notificaciones dentro de la lógica de negocio
# ---------------------------------------------------------------------------
class TestNotificaciones(BaseTemporal):
    def test_crear_y_avanzar_estado_notifican(self):
        falso = NotificadorFalso()
        ctrl = IncidenteController(AlmacenamientoJSON(self.carpeta / "i.json"), notificador=falso)
        inc = ctrl.crear_incidente("Grieta", "Moderado")
        ctrl.avanzar_estado(inc.id_incidente)
        self.assertEqual(len(falso.enviadas), 2)
        self.assertIn("En revisión", falso.enviadas[1][1])

    def test_datos_invalidos_no_notifican_ni_guardan(self):
        falso = NotificadorFalso()
        ctrl = IncidenteController(AlmacenamientoJSON(self.carpeta / "i.json"), notificador=falso)
        with self.assertRaises(ValueError):
            ctrl.crear_incidente("", "Grave")
        self.assertEqual(falso.enviadas, [])
        self.assertEqual(ctrl.obtener_historial(), [])


# ---------------------------------------------------------------------------
# 6. Configuración remota: solo se aceptan datos seguros
# ---------------------------------------------------------------------------
class TestConfigRemota(unittest.TestCase):
    CLAVES = ("mensaje_banner", "texto_boton_reporte")

    def test_acepta_textos_validos(self):
        datos = {"mensaje_banner": " Hola ", "otra_clave": "x"}
        self.assertEqual(filtrar_config(datos, self.CLAVES, 50), {"mensaje_banner": "Hola"})

    def test_rechaza_tipos_vacios_y_textos_largos(self):
        datos = {"mensaje_banner": 123, "texto_boton_reporte": "x" * 500}
        self.assertEqual(filtrar_config(datos, self.CLAVES, 50), {})
        self.assertEqual(filtrar_config(["no", "es", "dict"], self.CLAVES, 50), {})
        self.assertEqual(filtrar_config({"mensaje_banner": "   "}, self.CLAVES, 50), {})


if __name__ == "__main__":
    unittest.main(verbosity=2)
