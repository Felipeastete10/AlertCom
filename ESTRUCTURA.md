# 🗂️ AlertCom – Estructura del proyecto (arquitectura en 3 capas)

> *"Reporta. Ubica. Mejora."* · Python 3.11 · Kivy 2.3.1 · KivyMD 2.0

## Árbol de directorios

```text
AlertCom/
├── estructura_AlertCom/                 ← CÓDIGO DE LA APP (ejecutar desde aquí)
│   ├── main.py                          Punto de entrada (28 líneas): crea la app y el ScreenManager
│   ├── config.py                        Constantes, textos por defecto y rutas de carpetas
│   │
│   ├── models/                          ── CAPA 1 · MODELOS (Python puro, SIN Kivy)
│   │   ├── __init__.py                  Convierte la carpeta en paquete
│   │   ├── usuario.py                   Usuario: datos, rol y contraseña protegida con hash
│   │   └── incidente.py                 Incidente (la "Tarea"): Pendiente → En revisión → Reparado
│   │
│   ├── controllers/                     ── CAPA 2 · CONTROLADORES (lógica y flujo, sin widgets)
│   │   ├── __init__.py                  Reúne los controladores (no carga Kivy)
│   │   ├── app_controller.py            Arma todo: datos, log, errores, controladores, config remota
│   │   ├── auth_controller.py           Inicio de sesión y registro contra usuarios.json
│   │   ├── incidente_controller.py      Crear, consultar y cambiar estado de reportes (+ notificaciones)
│   │   ├── almacenamiento_json.py       Lectura/escritura segura: with open + json.dump/load + try/except
│   │   ├── notificador.py               Notificaciones nativas con Plyer
│   │   └── config_remota.py             Textos desde GitHub con UrlRequest + fallback local
│   │
│   ├── views/                           ── CAPA 3 · VISTAS (única capa con interfaz gráfica)
│   │   ├── __init__.py                  Expone crear_gestor_pantallas
│   │   ├── gestor_pantallas.py          Tema, carga los .kv y crea las 7 pantallas
│   │   ├── navegador.py                 Cambio de pantalla y rutas protegidas
│   │   ├── kv/                          Diseño declarativo (un archivo por pantalla)
│   │   │   ├── _comunes.kv              Plantillas compartidas (se carga primero)
│   │   │   ├── safety.kv                Aviso "no uses la app mientras conduces"
│   │   │   ├── login.kv                 Inicio de sesión
│   │   │   ├── register.kv              Crear cuenta
│   │   │   ├── home.kv                  Mapa, banner remoto, leyenda y botón de reporte
│   │   │   ├── report.kv                Formulario de reporte
│   │   │   ├── history.kv               Contadores y lista de reportes
│   │   │   └── profile.kv               Perfil y estadísticas
│   │   ├── pantallas/                   Clases MDScreen (qué pasa al tocar algo)
│   │   │   ├── __init__.py
│   │   │   ├── safety_view.py
│   │   │   ├── login_view.py
│   │   │   ├── register_view.py
│   │   │   ├── home_view.py
│   │   │   ├── report_view.py
│   │   │   ├── history_view.py
│   │   │   └── profile_view.py
│   │   └── componentes/                 Piezas visuales reutilizables
│   │       ├── __init__.py
│   │       └── dialogos.py              MDDialog (errores) y MDSnackbar (avisos)
│   │
│   ├── recursos/                        ── ARCHIVOS ESTÁTICOS (sí se suben a Git)
│   │   ├── imagenes/                    Marcadores del mapa: rojo, amarillo, verde
│   │   └── fuentes/                     Tipografías .ttf (vacía por ahora)
│   │
│   ├── datos/                           ── PERSISTENCIA LOCAL (se crea sola, NO va a Git)
│   │   ├── usuarios.json                Cuentas con sal + hash (sin contraseñas)
│   │   ├── incidentes.json              Reportes con estado y fecha
│   │   ├── alertcom.log                 Eventos y errores
│   │   └── cache_mapa/                  Imágenes del mapa descargadas (se regeneran solas)
│   │
│   └── pruebas/                         ── PRUEBAS AUTOMÁTICAS
│       ├── __init__.py
│       └── test_flujo_e3.py             20 pruebas: arquitectura, JSON, login, notificaciones, config remota
│
├── docs/
│   └── Presentación AlertCom.pdf        Material de presentación (fuera del código)
├── herramientas_vscode/
│   └── launch.json                      Depurador de VS Code (copiar a .vscode/)
├── config_remota.json                   Textos que la app descarga desde GitHub
├── requirements.txt                     Librerías con versiones fijas
├── README.md                            Guion de presentación y documentación técnica
├── GUIA_DEPURACION_E3.md                Tracebacks, pdb, breakpoints y checklist E3
├── ESTRUCTURA.md                        Este archivo
└── .gitignore                           Excluye entorno virtual, datos/ y __pycache__/
```

> **Carpetas que se generan solas** (no se escriben a mano y no se suben a Git):
> - `datos/`: la crea la app la primera vez que se abre.
> - `__pycache__/`: Python la crea en cada paquete para cargar más rápido. Es normal verla.
> - `entorno_alertcom/`: el entorno virtual, que cada integrante crea en su computador.

---

## Cómo se conectan las capas

```text
main.py ──► views ──► controllers ──► models
   └──────────┴───────────┴──────────────┴──► config.py (todos pueden usarlo)
```

| Regla | Cómo se cumple | Prueba que la verifica |
|---|---|---|
| `main.py` minimalista | 28 líneas: solo `MDApp` + `ScreenManager` | `test_main_es_minimalista` |
| Modelos sin Kivy | Solo usan `hashlib`, `datetime`, `secrets` | `test_modelos_no_importan_kivy`, `test_ningun_modelo_menciona_kivy_en_sus_imports` |
| Controladores sin vistas | Nunca importan `views/`; avisan con *callbacks* | `test_controladores_no_importan_vistas` |
| Solo `views/` maneja la interfaz | Widgets, `.kv`, `ScreenManager` y transiciones viven ahí | — |
| Paquetes importables | `__init__.py` en cada carpeta de código | `test_cada_carpeta_es_un_paquete` |
| Un diseño por pantalla | `views/kv/<pantalla>.kv` ↔ `views/pantallas/<pantalla>_view.py` | `test_cada_pantalla_tiene_su_kv` |

---

## Cómo ejecutar

```powershell
# 1. Crear y activar el entorno virtual (solo la primera vez)
python -m venv entorno_alertcom
entorno_alertcom\Scripts\activate
pip install -r requirements.txt

# 2. Ejecutar las pruebas y la app (siempre desde estructura_AlertCom)
cd estructura_AlertCom
python -m unittest discover -s pruebas -v
python main.py
```

**Cuentas demo:** `vecino@alertcom.cl` / `123456` (vecino) · `admin@gmail.com` / `123456` (funcionario municipal).

**Importaciones:** siempre desde la raíz de la app, por ejemplo `from models.usuario import Usuario` o `from views.componentes.dialogos import mostrar_dialogo`.
