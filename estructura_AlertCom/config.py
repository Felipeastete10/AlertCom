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

# --- Mapa ---------------------------------------------------------------------
CENTRO_TEMUCO = (-38.7359, -72.5904)
ZOOM_INICIAL = 14

# --- Opciones del formulario de reporte --------------------------------------
TIPOS_DANO = ["Bache", "Hoyo", "Grieta", "Hundimiento", "Pavimento roto"]
GRAVEDADES = ["Leve", "Moderado", "Grave", "Crítico"]
MAX_CARACTERES_DESCRIPCION = 250

# --- Archivos de datos locales (JSON) ----------------------------------------
ARCHIVO_USUARIOS = "usuarios.json"
ARCHIVO_INCIDENTES = "incidentes.json"
ARCHIVO_LOG = "alertcom.log"

# --- Configuración remota (Sesión 22) ----------------------------------------
# Archivo JSON público con textos que se pueden cambiar sin recompilar la app.
# Funciona en cuanto config_remota.json exista en la rama main del repositorio
# (o reemplaza la URL por la "Raw" de un GitHub Gist).
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
    },
    {
        "id_usuario": 2,
        "nombre": "Juan Pérez González",
        "email": "vecino@alertcom.cl",
        "rol": "vecino",
        "comuna": "Temuco",
        "sal": "c40a0719f4d7efbb830073ed415f09e4",
        "hash_contrasena": "855441e4703e2da3dddac7dedacf532550fe3513570689e00fab756900c8aaee",
    },
]
