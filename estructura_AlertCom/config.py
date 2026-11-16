# =============================================================================
# AlertCom - Configuración central (constantes compartidas)
# =============================================================================
# Un solo lugar para los valores que antes estaban repetidos en varios
# archivos (coordenadas, listas de opciones, textos por defecto).
# Python puro: no importa Kivy, así que lo pueden usar modelos y pruebas.
# =============================================================================

from pathlib import Path

# --- Carpetas del proyecto ----------------------------------------------------
# Todas las rutas se calculan desde ESTE archivo, así funcionan aunque la app
# se ejecute desde otra carpeta. Si mueves una carpeta, cambias solo esta línea.
BASE_DIR = Path(__file__).resolve().parent
CARPETA_KV = BASE_DIR / "views" / "kv"                  # diseño de cada pantalla
CARPETA_IMAGENES = BASE_DIR / "recursos" / "imagenes"   # íconos y marcadores
CARPETA_FUENTES = BASE_DIR / "recursos" / "fuentes"     # tipografías (.ttf)
CARPETA_DATOS = BASE_DIR / "datos"                      # JSON y log (no va a Git)

# --- Versión (se muestra en el Perfil y se registra en app_abierta) ---------
VERSION_APP = "1.6.0"

# --- Mapa ---------------------------------------------------------------------
CENTRO_TEMUCO = (-38.7359, -72.5904)
# Zona de AlertCom: Temuco y Padre Las Casas (oeste, sur, este, norte).
# El mapa no deja salir de aquí y no se aceptan reportes fuera de esta zona.
LIMITES_TEMUCO = (-72.75, -38.82, -72.47, -38.64)
ZOOM_INICIAL = 14
ZOOM_REPORTE = 15          # zoom del minimapa al abrir el formulario
ZOOM_UBICACION = 18        # zoom al encontrar la ubicación del usuario
URL_MAPA = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"   # https: Android bloquea http

# OpenStreetMap exige que cada app se identifique (política de uso de sus
# servidores). Sin esto, los servidores pueden bloquear las imágenes del mapa.
USER_AGENT = "AlertCom/1.6 (proyecto academico UC Temuco; +https://github.com/Felipeastete10/AlertCom)"

# Dirección a partir de coordenadas (Nominatim, de OpenStreetMap).
# Solo se consulta mientras el vecino marca un reporte (máx. 1 vez por segundo).
URL_DIRECCION = (
    "https://nominatim.openstreetmap.org/reverse?format=jsonv2"
    "&lat={lat:.6f}&lon={lon:.6f}&zoom=18&addressdetails=1&accept-language=es"
)

# Buscar una calle escrita (geocodificación directa), solo dentro de Temuco y
# Padre Las Casas: viewbox = oeste, norte, este, sur.
URL_BUSCAR_CALLE = (
    "https://nominatim.openstreetmap.org/search?format=jsonv2&q={texto}"
    "&countrycodes=cl&viewbox=-72.72,-38.66,-72.50,-38.80&bounded=1"
    "&limit=1&addressdetails=1&accept-language=es"
)
CIUDAD_BUSQUEDA = "Temuco"

# Punta de los marcadores (marcador_*.png mide 40×56 px y la punta está en la
# fila 53): el punto exacto queda 2,5 px sobre el borde inferior.
ANCLA_MARCADOR_Y = 2.5 / 56

# --- Apariencia (Ajustes) ----------------------------------------------------
# (clave, texto, factor): multiplica el tamaño de todos los textos.
TAMANOS_LETRA = [
    ("pequena", "Pequeña", 0.9),
    ("normal", "Normal", 1.0),
    ("grande", "Grande", 1.15),
    ("muy_grande", "Muy grande", 1.3),
]
# Letra grande del TELÉFONO (Ajustes de Android → Tamaño de fuente): se respeta
# hasta este factor. Más allá, los textos no cabían en sus espacios; para letra
# más grande se usa el control propio de la app (Ajustes → Tamaño de letra).
LETRA_SISTEMA_MAXIMA = 1.15
# (clave, texto, color). Todos oscuros para mantener el diseño de la app;
# None = el fondo original del tema.
# Colores de fondo. Antes eran casi negros y en el teléfono no se notaba la
# diferencia: ahora cada uno se distingue, y todos dejan el texto blanco con
# contraste alto (más de 10:1).
FONDOS = [
    ("original", "Original", None),
    ("negro", "Negro", [0, 0, 0, 1]),
    ("azul", "Azul noche", [0.07, 0.14, 0.30, 1]),
    ("grafito", "Grafito", [0.22, 0.22, 0.24, 1]),
    ("bosque", "Bosque", [0.05, 0.23, 0.15, 1]),
    ("vino", "Vino", [0.30, 0.07, 0.12, 1]),
    ("morado", "Morado", [0.20, 0.11, 0.33, 1]),
]
MAX_CARACTERES_NOMBRE = 60

# --- GPS ----------------------------------------------------------------------
PRECISION_GPS_BUENA = 30   # metros: con esto ya se acepta la ubicación
TIEMPO_MAXIMO_GPS = 20     # segundos esperando señal antes de rendirse

# --- Fotos --------------------------------------------------------------------
CARPETA_FOTOS = "fotos"    # dentro de la carpeta de datos (no va a Git ni al APK)
LADO_MAXIMO_FOTO = 1280    # px: se reduce para no llenar el teléfono
CALIDAD_FOTO = 80          # calidad JPEG (0-100)

# --- Opciones del formulario de reporte --------------------------------------
TIPOS_DANO = ["Bache", "Hoyo", "Grieta", "Hundimiento", "Pavimento roto"]
GRAVEDADES = ["Leve", "Moderado", "Grave", "Crítico"]
MAX_CARACTERES_DESCRIPCION = 250
MAX_CARACTERES_CALLE = 120

# Motivos para pedir que se elimine un reporte (lo aprueba un funcionario)
MOTIVOS_ELIMINACION = [
    "Lo reporté por error",
    "Está repetido",
    "La ubicación está mal",
    "El daño ya no existe",
]

# --- Archivos de datos locales (JSON) ----------------------------------------
ARCHIVO_USUARIOS = "usuarios.json"
ARCHIVO_INCIDENTES = "incidentes.json"
ARCHIVO_LOG = "alertcom.log"

# --- Configuración remota (Sesión 22) ----------------------------------------
# Archivo JSON público con textos que se pueden cambiar sin recompilar la app.
# Funciona en cuanto config_remota.json exista en la rama main del repositorio
# (o reemplaza la URL por la "Raw" de un GitHub Gist).
# --- Reportes compartidos (Firebase Realtime Database) -------------------------
# Enlace de la base de datos (Firebase → Realtime Database → pestaña Datos).
# Vacío = cada teléfono guarda solo sus reportes (como antes).
URL_FIREBASE = "https://alertcom-6f983-default-rtdb.firebaseio.com"
SEGUNDOS_ENTRE_SINCRONIZACIONES = 45

URL_CONFIG_REMOTA = (
    "https://raw.githubusercontent.com/Felipeastete10/AlertCom/main/config_remota.json"
)
TIEMPO_ESPERA_RED = 5          # segundos antes de rendirse
LARGO_MAX_TEXTO_REMOTO = 160   # evita que un texto remoto rompa el diseño

# Valores locales por defecto: la app SIEMPRE parte con estos.
# Si la red falla, se quedan tal cual y nada se rompe.
VALORES_POR_DEFECTO = {
    "mensaje_banner": "Reporta baches en Temuco y sigue su reparación.",
    "mensaje_seguridad": (
        "Estaciona en un lugar seguro antes de reportar un bache. "
        "Tu vida y la de otros es más importante."
    ),
    "texto_boton_reporte": "Reportar bache",
}

# --- Usuarios de demostración -------------------------------------------------
# Se escriben en usuarios.json SOLO la primera vez (instalación nueva).
# No hay contraseñas en texto plano: solo sal + hash PBKDF2.
# Contraseña de ambas cuentas demo: 123456 (documentada en el README).
USUARIOS_DEMO = [
    {
        "id_usuario": 1,
        "nombre": "Administrador Municipal",
        "email": "admin@gmail.com",
        "rol": "municipal",
        "comuna": "Temuco",
        "sal": "c99e3bbbe671c9d6e74fe1b43c128ac8",
        "hash_contrasena": "a1ef50f38a6952ef6d34f46fb6c91c311e9d8d4e3e48fd0017fff3ccc3e15500",
        "uid": "municipal-temuco",   # el mismo en todos los teléfonos
    },
    {
        "id_usuario": 2,
        "nombre": "Juan Pérez González",
        "email": "vecino@alertcom.cl",
        "rol": "vecino",
        "comuna": "Temuco",
        "sal": "c40a0719f4d7efbb830073ed415f09e4",
        "hash_contrasena": "855441e4703e2da3dddac7dedacf532550fe3513570689e00fab756900c8aaee",
        "uid": "vecino-demo",
    },
]
