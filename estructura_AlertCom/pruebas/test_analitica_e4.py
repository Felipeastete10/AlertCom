# =============================================================================
# AlertCom - Pruebas de la analítica (Evaluación E4 · RA3)
# =============================================================================
# Ejecutar desde estructura_AlertCom:
#     python -m unittest discover -s pruebas -v
#
# Prueban el registro de eventos, el cálculo de los KPIs y que la analítica
# respete la privacidad. Usan carpetas temporales: no tocan tus datos.
# =============================================================================

import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

CARPETA_APP = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CARPETA_APP))

import controllers.registro_eventos as modulo_registro  # noqa: E402
from controllers import (  # noqa: E402
    AlmacenamientoJSON,
    AuthController,
    IncidenteController,
    RegistroEventos,
    analitica,
)
from models import Evento  # noqa: E402


def evento(nombre, hora, usuario=2, sesion="s1", **datos):
    """Evento de prueba en formato dict, a una hora del 12-11-2026."""
    return {"evento": nombre, "timestamp": f"2026-11-12T{hora}-03:00",
            "usuario_id": usuario, "sesion_id": sesion, "datos": datos}


class BaseTemporal(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.carpeta = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def lineas(self):
        return (self.carpeta / "eventos.jsonl").read_text(encoding="utf-8").splitlines()


# ---------------------------------------------------------------------------
# 1. Anatomía del evento
# ---------------------------------------------------------------------------
class TestEvento(unittest.TestCase):
    def test_tiene_nombre_timestamp_y_datos(self):
        e = Evento("reporte_enviado", {"tipo": "Bache"}).to_dict()
        self.assertEqual(e["evento"], "reporte_enviado")
        self.assertIsNotNone(datetime.fromisoformat(e["timestamp"]).tzinfo)  # con zona horaria
        self.assertEqual(e["datos"], {"tipo": "Bache"})

    def test_rechaza_nombres_fuera_del_catalogo(self):
        with self.assertRaises(ValueError):
            Evento("clic_en_cualquier_cosa")

    def test_datos_no_serializables_se_convierten_a_texto(self):
        e = Evento("pantalla_vista", {"widget": object(), "n": 3})
        json.dumps(e.to_dict())  # no debe fallar
        self.assertIsInstance(e.datos["widget"], str)
        self.assertEqual(e.datos["n"], 3)


# ---------------------------------------------------------------------------
# 2. Registro en archivo (JSON Lines, modo "a")
# ---------------------------------------------------------------------------
class TestRegistroEventos(BaseTemporal):
    def test_agrega_sin_borrar_lo_anterior(self):
        RegistroEventos(self.carpeta).registrar("app_abierta")
        RegistroEventos(self.carpeta).registrar("app_abierta")  # otra "apertura"
        self.assertEqual(len(self.lineas()), 2)

    def test_guarda_tildes_en_utf8(self):
        RegistroEventos(self.carpeta).registrar("estado_cambiado", {"nuevo": "En revisión"})
        self.assertIn("En revisión", self.lineas()[0])

    def test_nombre_invalido_no_cae_ni_escribe(self):
        self.assertIsNone(RegistroEventos(self.carpeta).registrar("no_existe"))
        self.assertFalse((self.carpeta / "eventos.jsonl").exists())

    def test_desactivar_detiene_el_registro_y_se_recuerda(self):
        registro = RegistroEventos(self.carpeta)
        registro.cambiar_activo(False)
        registro.registrar("app_abierta")
        self.assertFalse((self.carpeta / "eventos.jsonl").exists())
        self.assertFalse(RegistroEventos(self.carpeta).activo)  # la preferencia persiste

    def test_rota_el_archivo_cuando_crece(self):
        original = modulo_registro.TAMANO_MAXIMO_BYTES
        modulo_registro.TAMANO_MAXIMO_BYTES = 200
        try:
            registro = RegistroEventos(self.carpeta)
            for _ in range(5):
                registro.registrar("pantalla_vista", {"pantalla": "home"})
        finally:
            modulo_registro.TAMANO_MAXIMO_BYTES = original
        self.assertTrue(list(self.carpeta.glob("eventos_*.jsonl")))
        eventos, _ = analitica.cargar_eventos(registro.archivos())
        self.assertEqual(len(eventos), 5)  # no se pierde ninguno

    def test_linea_danada_se_salta_al_leer(self):
        registro = RegistroEventos(self.carpeta)
        registro.registrar("app_abierta")
        with open(registro.ruta, "a", encoding="utf-8") as archivo:
            archivo.write('{"evento": "reporte_env')  # corte a mitad de escritura
        eventos, invalidas = analitica.cargar_eventos([registro.ruta])
        self.assertEqual((len(eventos), invalidas), (1, 1))


# ---------------------------------------------------------------------------
# 3. KPIs
# ---------------------------------------------------------------------------
class TestKPIs(unittest.TestCase):
    EVENTOS = [
        evento("reporte_iniciado", "10:00:00"),
        evento("reporte_enviado", "10:00:40", tipo="Bache"),
        evento("pantalla_vista", "10:00:41", pantalla="history"),
        evento("reporte_iniciado", "11:00:00", usuario=3, sesion="s2"),
        evento("reporte_enviado", "11:01:20", usuario=3, sesion="s2", tipo="Hoyo"),
        evento("reporte_iniciado", "12:00:00", usuario=4, sesion="s3"),  # abandonado
    ]

    def test_tasa_de_finalizacion(self):
        kpi = analitica.kpi_finalizacion(self.EVENTOS)
        self.assertEqual(kpi["valor"], 66.7)  # 2 enviados / 3 iniciados
        self.assertEqual(kpi["detalle"]["abandonados"], 1)
        self.assertFalse(kpi["cumple"])

    def test_tiempo_mediano(self):
        self.assertEqual(analitica.duraciones_reporte(self.EVENTOS), [40.0, 80.0])
        self.assertEqual(analitica.kpi_tiempo_reporte(self.EVENTOS)["valor"], 60.0)

    def test_tasa_de_seguimiento(self):
        kpi = analitica.kpi_seguimiento(self.EVENTOS)
        self.assertEqual(kpi["valor"], 50.0)  # 1 de 2 vecinos revisó su historial
        self.assertTrue(kpi["cumple"])

    def test_retencion_cuenta_usuarios_de_dos_dias(self):
        otro_dia = dict(evento("app_abierta", "09:00:00"), timestamp="2026-11-13T09:00:00-03:00")
        self.assertEqual(analitica.usuarios_recurrentes(self.EVENTOS + [otro_dia]), 1)

    def test_sin_datos_no_divide_por_cero(self):
        for kpi in analitica.resumen([])["kpis"]:
            self.assertIsNone(kpi["valor"])
            self.assertIsNone(kpi["cumple"])

    def test_filtro_por_periodo(self):
        from datetime import date
        otro_dia = dict(evento("app_abierta", "09:00:00"), timestamp="2026-11-20T09:00:00-03:00")
        filtrados = analitica.filtrar_periodo(self.EVENTOS + [otro_dia], date(2026, 11, 12), date(2026, 11, 15))
        self.assertEqual(len(filtrados), len(self.EVENTOS))


# ---------------------------------------------------------------------------
# 4. Eventos desde la lógica de negocio + privacidad
# ---------------------------------------------------------------------------
class TestInstrumentacion(BaseTemporal):
    def test_login_registra_id_y_nunca_el_correo(self):
        eventos = RegistroEventos(self.carpeta)
        auth = AuthController(AlmacenamientoJSON(self.carpeta / "usuarios.json"), eventos=eventos)
        auth.iniciar_sesion("vecino@alertcom.cl", "malo")
        auth.iniciar_sesion("vecino@alertcom.cl", "123456")
        auth.cerrar_sesion()
        texto = (self.carpeta / "eventos.jsonl").read_text(encoding="utf-8")
        nombres = [json.loads(linea)["evento"] for linea in texto.splitlines()]
        self.assertEqual(nombres, ["login_fallido", "login_exitoso", "sesion_cerrada"])
        self.assertNotIn("vecino@alertcom.cl", texto)
        self.assertIn('"usuario_id": 2', texto)

    def test_reporte_registra_tipo_pero_no_descripcion_ni_ubicacion(self):
        eventos = RegistroEventos(self.carpeta)
        ctrl = IncidenteController(AlmacenamientoJSON(self.carpeta / "i.json"), eventos=eventos)
        with self.assertRaises(ValueError):
            ctrl.crear_incidente("", "Grave")
        ctrl.crear_incidente("Bache", "Grave", descripcion="frente a mi casa en Lautaro 123",
                             ubicacion="-38.7, -72.6", calle="Pasaje Los Aromos 77")
        texto = (self.carpeta / "eventos.jsonl").read_text(encoding="utf-8")
        self.assertIn("reporte_rechazado", texto)
        self.assertIn('"tipo": "Bache"', texto)
        self.assertNotIn("Lautaro", texto)
        self.assertNotIn("Aromos", texto)  # la calle tampoco va a la analítica
        self.assertNotIn("-38.7", texto)

    def test_analitica_se_importa_sin_kivy(self):
        codigo = ("import sys; sys.path.insert(0, r'%s'); import controllers.analitica; "
                  "print(any(m.startswith('kivy') for m in sys.modules))" % CARPETA_APP)
        salida = subprocess.run([sys.executable, "-c", codigo], capture_output=True, text=True)
        self.assertEqual(salida.stdout.strip(), "False", salida.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
