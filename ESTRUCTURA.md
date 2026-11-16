# 🗂️ AlertCom – Estructura del proyecto (arquitectura en 3 capas)

> *"Reporta. Ubica. Mejora."* · Python 3.11 · Kivy 2.3.1 · KivyMD 2.0

## Árbol de directorios

```text
AlertCom/
├── estructura_AlertCom/                 ← CÓDIGO DE LA APP (ejecutar desde aquí)
│   ├── main.py                          Punto de entrada (28 líneas): crea la app y el ScreenManager
│   ├── librerias/                       materialyoucolor 3.0.4 incluido (Buildozer trae una versión vieja)
│   ├── config.py                        Constantes, versión, textos por defecto y rutas de carpetas
│   ├── buildozer.spec                   Configuración para generar el APK de Android
│   │
│   ├── models/                          ── CAPA 1 · MODELOS (Python puro, SIN Kivy)
│   │   ├── __init__.py                  Convierte la carpeta en paquete
│   │   ├── usuario.py                   Usuario: datos, rol y contraseña protegida con hash
│   │   ├── incidente.py                 Incidente (la "Tarea"): Pendiente → En revisión → Reparado
│   │   └── evento.py                    Evento de analítica: nombre, timestamp, datos + catálogo
│   │
│   ├── controllers/                     ── CAPA 2 · CONTROLADORES (lógica y flujo, sin widgets)
│   │   ├── __init__.py                  Reúne los controladores (no carga Kivy)
│   │   ├── app_controller.py            Arma todo: datos, log, errores, controladores, config remota
│   │   ├── auth_controller.py           Inicio de sesión y registro contra usuarios.json
│   │   ├── incidente_controller.py      Crear, consultar y cambiar estado de reportes (+ notificaciones)
│   │   ├── almacenamiento_json.py       Lectura/escritura segura: with open + json.dump/load + try/except
│   │   ├── notificador.py               Notificaciones nativas con Plyer
│   │   ├── config_remota.py             Textos desde GitHub con UrlRequest + fallback local
│   │   ├── registro_eventos.py          Guarda eventos en eventos.jsonl (modo "a", rotación, privacidad)
│   │   ├── analitica.py                 Calcula métricas y los 3 KPIs desde los eventos
│   │   ├── preferencias.py              Preferencias de la persona en preferencias.json (letra, fondo, analítica)
│   │   ├── fotos.py                     Copia reducida y sin metadatos de cada foto (datos/fotos/)
│   │   ├── direcciones.py               Calle ↔ coordenadas (Nominatim de OpenStreetMap), solo en Temuco
│   │   ├── ubicacion.py                 GPS del teléfono: permiso, precisión y tiempo máximo
│   │   └── camara.py                    Cámara y galería de Android (sin plyer.camera)
│   │
│   ├── views/                           ── CAPA 3 · VISTAS (única capa con interfaz gráfica)
│   │   ├── __init__.py                  Expone crear_gestor_pantallas
│   │   ├── gestor_pantallas.py          Tema, carga los .kv y crea las 8 pantallas
│   │   ├── apariencia.py                Aplica el tamaño de letra y el fondo elegidos a toda la app
│   │   ├── navegador.py                 Cambio de pantalla, rutas protegidas y solo-municipal
│   │   ├── kv/                          Diseño declarativo (un archivo por pantalla)
│   │   │   ├── _comunes.kv              Plantillas compartidas (se carga primero)
│   │   │   ├── safety.kv                Aviso de seguridad: camino nocturno y deslizador para continuar
│   │   │   ├── login.kv                 Inicio de sesión
│   │   │   ├── register.kv              Crear cuenta
│   │   │   ├── home.kv                  Mapa, banner remoto, leyenda, Mi ubicación y botón de reporte
│   │   │   ├── report.kv                Formulario: mapa con pin, GPS, calle, foto, tipo y gravedad
│   │   │   ├── history.kv               Contadores y lista de reportes
│   │   │   ├── profile.kv               Perfil, estadísticas e interruptor de privacidad
│   │   │   ├── ajustes.kv               Apariencia (letra y fondo) y gestor de cuenta
│   │   │   └── metricas.kv              KPIs y métricas (solo funcionario municipal)
│   │   ├── pantallas/                   Clases de pantalla (qué pasa al tocar algo)
│   │   │   ├── __init__.py
│   │   │   ├── safety_view.py
│   │   │   ├── login_view.py
│   │   │   ├── register_view.py
│   │   │   ├── home_view.py
│   │   │   ├── report_view.py
│   │   │   ├── history_view.py
│   │   │   ├── profile_view.py
│   │   │   ├── metricas_view.py
│   │   │   └── ajustes_view.py
│   │   └── componentes/                 Piezas visuales reutilizables
│   │       ├── __init__.py
│   │       ├── dialogos.py              MDDialog (errores, con foto opcional) y MDSnackbar (avisos)
│   │       ├── detalle_reporte.py       Detalle de un reporte con calle y foto (mapa e historial)
│   │       ├── estilos.py               Colores e íconos de estados, gravedad y tipos (un solo lugar)
│   │       ├── formulario.py            Ventana con campos para el gestor de cuenta
│   │       ├── interaccion.py           Pastillas, barra de avance, animación de éxito, sacudir, contar, vibrar
│   │       ├── mapa.py                  Crea el MapView con la configuración correcta (https, User-Agent)
│   │       ├── seguridad.py             Camino animado, baliza y deslizador "estoy detenido"
│   │       └── pantalla_base.py         Pantalla base: registra "pantalla_vista" en on_enter
│   │
│   ├── recursos/                        ── ARCHIVOS ESTÁTICOS (sí se suben a Git)
│   │   ├── imagenes/                    Marcadores del mapa, punto "mi ubicación", ícono y pantalla de carga
│   │   └── fuentes/                     Tipografías .ttf (vacía por ahora)
│   │
│   ├── datos/                           ── PERSISTENCIA LOCAL (se crea sola, NO va a Git)
│   │   ├── usuarios.json                Cuentas con sal + hash (sin contraseñas)
│   │   ├── incidentes.json              Reportes con estado y fecha
│   │   ├── eventos.jsonl                Eventos de uso, uno por línea (analítica)
│   │   ├── preferencias.json            Si el usuario permite registrar su uso
│   │   ├── alertcom.log                 Registro técnico y errores
│   │   ├── fotos/                       Fotos reducidas de los reportes
│   │   ├── temporal/                    Copia momentánea de la foto mientras se procesa
│   │   └── cache_mapa/                  Imágenes del mapa descargadas (se regeneran solas)
│   │
│   └── pruebas/                         ── PRUEBAS AUTOMÁTICAS
│       ├── __init__.py
│       ├── test_flujo_e3.py             20 pruebas: arquitectura, JSON, login, notificaciones, config remota
│       ├── test_analitica_e4.py         18 pruebas: eventos, KPIs y privacidad
│       ├── test_reporte_completo.py     25 pruebas: ubicación, calle, fotos y decisiones del GPS
│       ├── test_cuenta_y_ajustes.py     14 pruebas: gestor de cuenta, preferencias y tarjetas de reporte
│       └── test_eliminacion.py          12 pruebas: el vecino pide eliminar, el funcionario aprueba/rechaza o borra lo suyo
│
├── analitica/                           ── ANÁLISIS EN EL COMPUTADOR (no va en el APK)
│   ├── analitica_proyecto.py            Lee eventos, filtra el periodo, calcula KPIs y dibuja gráficos
│   └── resultados/                      (se crea al ejecutarlo) resumen.md, eventos.csv y gráficos .png
│
├── docs/
│   ├── Presentación AlertCom.pdf        Material de presentación (fuera del código)
│   └── guion_presentacion_E2.md         Guion de la evaluación E2
├── herramientas_vscode/
│   └── launch.json                      Depurador de VS Code (copiar a .vscode/)
├── config_remota.json                   Textos que la app descarga desde GitHub
├── requirements.txt                     Librerías de la app con versiones fijas
├── requirements-analisis.txt            Librerías para el análisis en el PC (matplotlib)
├── README.md                            Presentación profesional del proyecto
├── DOCUMENTATION.md                     Medición: eventos, KPIs, método MJV App y ética
├── GUIA_APK_BUILDOZER.md                Cómo generar e instalar el APK (WSL2)
├── GUIA_DEPURACION_E3.md                Tracebacks, pdb, breakpoints y checklist
├── uso_de_IA.md                         Declaración de uso de inteligencia artificial
├── ESTRUCTURA.md                        Este archivo
└── .gitignore                           Excluye entorno virtual, datos/, *.jsonl, APK y __pycache__/
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
