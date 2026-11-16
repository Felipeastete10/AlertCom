# =============================================================================
# AlertCom - Pruebas del GPS con un "teléfono simulado" (v1.5.1)
# =============================================================================
# Ejecutar desde estructura_AlertCom:
#     python -m unittest discover -s pruebas -v
#
# En el computador no hay Android. Aquí se reemplazan los módulos "jnius" y
# "android" por versiones falsas que se comportan como el teléfono, para
# probar ServicioUbicacion de punta a punta:
#   - Android 12+ entrega las ubicaciones como LISTA (la causa del cierre).
#   - Android antiguo entrega UNA ubicación.
#   - Permiso negado, ubicación apagada y que ningún error se escape.
# =============================================================================

import sys
import types
import unittest
from pathlib import Path

CARPETA_APP = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CARPETA_APP))


# ---------------------------------------------------------------------------
# Teléfono simulado
# ---------------------------------------------------------------------------
class UbicacionFalsa:
    def __init__(self, lat, lon, precision, edad_s=0):
        import time
        self._datos = (lat, lon, precision)
        self._tiempo = (time.time() - edad_s) * 1000

    def getLatitude(self): return self._datos[0]
    def getLongitude(self): return self._datos[1]
    def getAccuracy(self): return self._datos[2]
    def hasAccuracy(self): return True
    def getTime(self): return self._tiempo


class ListaJava:
    """Imita java.util.List (size/get), que es lo que entrega Android 12+."""
    def __init__(self, elementos): self._e = list(elementos)
    def size(self): return len(self._e)
    def get(self, i): return self._e[i]


class GestorFalso:
    def __init__(self):
        self.encendidos = {"gps": True, "network": True}
        self.ultima = {}
        self.escuchadores = []

    def isProviderEnabled(self, p): return self.encendidos.get(p, False)
    def getLastKnownLocation(self, p): return self.ultima.get(p)

    def requestLocationUpdates(self, proveedor, tiempo, distancia, escuchador, looper):
        assert isinstance(tiempo, int) and isinstance(distancia, float)
        self.escuchadores.append(escuchador)

    def removeUpdates(self, escuchador):
        self.escuchadores = [e for e in self.escuchadores if e is not escuchador]

    def avisar(self, metodo, firma, argumento):
        """Imita a Android llamando al escuchador (como lo hace pyjnius)."""
        unicos = {id(e): e for e in self.escuchadores}.values()  # 1 objeto, 2 proveedores
        for e in list(unicos):
            funcion = e.__javamethods__.get((metodo, firma))
            if funcion is None:
                raise NotImplementedError(metodo + firma)  # así falla Plyer
            funcion(argumento)


def instalar_android_falso(gestor, permiso=True, respuesta=(True, True)):
    def java_method(firma, name=None):
        def marcar(f):
            f.__javasignature__, f.__javaname__ = firma, name
            return f
        return marcar

    class PythonJavaClass:
        def __init__(self):
            # Igual que pyjnius: el método se identifica por (nombre Java, firma)
            self.__javamethods__ = {}
            for nombre in dir(self):
                attr = getattr(self, nombre)
                if callable(attr) and hasattr(attr, "__javasignature__"):
                    self.__javamethods__[(attr.__javaname__ or nombre, attr.__javasignature__)] = attr

    actividad = types.SimpleNamespace(getSystemService=lambda _s: gestor)
    clases = {
        "org.kivy.android.PythonActivity": types.SimpleNamespace(mActivity=actividad),
        "android.content.Context": types.SimpleNamespace(LOCATION_SERVICE="location"),
        "android.os.Looper": types.SimpleNamespace(getMainLooper=lambda: "looper"),
    }
    jnius = types.ModuleType("jnius")
    jnius.autoclass = clases.__getitem__
    jnius.java_method = java_method
    jnius.PythonJavaClass = PythonJavaClass

    permisos = types.ModuleType("android.permissions")
    permisos.Permission = types.SimpleNamespace(ACCESS_FINE_LOCATION="fine", ACCESS_COARSE_LOCATION="coarse")
    permisos.check_permission = lambda _p: permiso
    permisos.request_permissions = lambda lista, cb: cb(lista, list(respuesta))
    android = types.ModuleType("android")
    android.permissions = permisos
    sys.modules.update({"jnius": jnius, "android": android, "android.permissions": permisos})


from kivy.clock import Clock  # noqa: E402

import controllers.ubicacion as modulo  # noqa: E402


class PruebaGPS(unittest.TestCase):
    def setUp(self):
        self.gestor = GestorFalso()
        self.obtenidas, self.fallas = [], []
        self._plataforma = modulo.platform
        modulo.platform = "android"

    def tearDown(self):
        modulo.platform = self._plataforma
        for nombre in ("jnius", "android", "android.permissions"):
            sys.modules.pop(nombre, None)

    def pedir(self, **opciones):
        instalar_android_falso(self.gestor, **opciones)
        servicio = modulo.ServicioUbicacion()
        servicio.pedir(lambda *d: self.obtenidas.append(d), lambda m, _t: self.fallas.append(m))
        Clock.tick()  # ejecuta lo enviado con @mainthread
        return servicio

    def test_android_12_entrega_lista_y_funciona(self):
        servicio = self.pedir()
        self.assertEqual(len(self.gestor.escuchadores), 2)  # gps y network
        lista = ListaJava([UbicacionFalsa(-38.70, -72.50, 80), UbicacionFalsa(-38.7391, -72.5983, 8)])
        self.gestor.avisar("onLocationChanged", "(Ljava/util/List;)V", lista)
        Clock.tick()
        self.assertEqual(self.obtenidas, [(-38.7391, -72.5983, 8.0, True)])  # usa la más nueva
        self.assertFalse(servicio.buscando)
        self.assertEqual(self.gestor.escuchadores, [])  # GPS apagado al terminar

    def test_android_antiguo_entrega_una_ubicacion(self):
        self.pedir()
        self.gestor.avisar("onLocationChanged", "(Landroid/location/Location;)V",
                           UbicacionFalsa(-38.74, -72.59, 12))
        Clock.tick()
        self.assertEqual(self.obtenidas[-1][3], True)
        self.assertEqual(self.fallas, [])

    def test_aproximada_mueve_el_mapa_y_sigue_buscando(self):
        servicio = self.pedir()
        self.gestor.avisar("onLocationChanged", "(Landroid/location/Location;)V",
                           UbicacionFalsa(-38.74, -72.59, 150))
        Clock.tick()
        self.assertEqual(self.obtenidas, [(-38.74, -72.59, 150.0, False)])
        self.assertTrue(servicio.buscando)
        servicio.detener()

    def test_otros_avisos_de_android_no_fallan(self):
        servicio = self.pedir()
        self.gestor.avisar("onProviderDisabled", "(Ljava/lang/String;)V", "gps")
        self.gestor.avisar("onFlushComplete", "(I)V", 0)
        servicio.detener()

    def test_ubicacion_rota_no_escapa_el_error(self):
        servicio = self.pedir()
        self.gestor.avisar("onLocationChanged", "(Landroid/location/Location;)V", object())
        self.gestor.avisar("onLocationChanged", "(Ljava/util/List;)V", ListaJava([]))
        Clock.tick()
        self.assertEqual(self.obtenidas, [])
        servicio.detener()

    def test_ultima_conocida_reciente_se_usa_al_tiro(self):
        self.gestor.ultima["gps"] = UbicacionFalsa(-38.73, -72.60, 10, edad_s=30)
        self.pedir()
        self.assertEqual(self.obtenidas, [(-38.73, -72.60, 10.0, True)])
        self.assertEqual(self.gestor.escuchadores, [])  # ni siquiera encendió el GPS

    def test_permiso_negado(self):
        self.pedir(permiso=False, respuesta=(False, False))
        self.assertEqual(self.fallas, ["sin_permiso"])

    def test_solo_ubicacion_aproximada(self):
        self.pedir(permiso=False, respuesta=(False, True))
        self.assertEqual(self.fallas, ["sin_precision"])

    def test_ubicacion_del_telefono_apagada(self):
        self.gestor.encendidos = {"gps": False, "network": False}
        self.pedir()
        self.assertEqual(self.fallas, ["ubicacion_apagada"])


if __name__ == "__main__":
    unittest.main()
