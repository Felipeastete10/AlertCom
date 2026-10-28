# 📱 AlertCom - Guion de Presentación Técnica y Metodológica (Evaluación E2)
> *"Reporta. Ubica. Mejora."*

---

## 1. Fundamentación y Evidencia de Campo (Metodología A+S)

El diseño visual, la arquitectura de navegación y los componentes de este Mockup móvil interactivo responden directamente a los hallazgos cuantitativos y cualitativos obtenidos en la investigación de campo realizada en la comuna de **Temuco (26 encuestas ciudadanas)**:

1. **Alta Exposición y Riesgo Vial (70% de los encuestados):**
   * El **70%** de los participantes se moviliza a diario en automóvil particular o transporte público colectivo.
   * *Impacto en el diseño:* La interacción con la app no puede convertirse en un factor de distracción al volante. Por ello, se diseñó la **Pantalla de Aviso de Seguridad (`SafetyScreen`)** con un bloqueo preventivo obligatorio.

2. **Frecuencia Crítica del Problema (57.6%):**
   * El **57.6%** de los encuestados reporta toparse con baches, hoyos o grietas de forma **"Frecuente" o "Muy frecuente"**.
   * *Impacto en el diseño:* Se requiere una herramienta inmediata y de acceso instantáneo sin fricciones burocráticas.

3. **La Barrera Raíz: El Desconocimiento Ciudadano:**
   * La principal dificultad detectada no es la falta de interés, sino el desconocimiento: los ciudadanos afirman *"No sé dónde reportarlo"* y *"No sabía que la municipalidad podía recibir estos reportes"*.
   * *Impacto en el diseño:* 
     * **Login simplificado (`LoginScreen`):** Mínimos campos para eliminar la deserción inicial.
     * **Home / Mapa (`HomeScreen`):** Botón central **`+ Reportar bache`** sobredimensionado, llamativo y ubicado en el centro de atención para que el usuario sepa de forma inequívoca qué acción tomar.

4. **Exigencia de Cierre y Trazabilidad:**
   * Los ciudadanos manifestaron frustración ante canales tradicionales que "no dan respuesta". Consideran **fundamental** saber si su reporte fue recibido y cuándo será reparado.
   * *Impacto en el diseño:* **Pantalla de Historial (`HistoryScreen`)** con contadores de estado (*Total*, *En revisión*, *Reparados*) y lista cronológica con códigos de color de semáforo.

5. **Identidad Ciudadana y Compromiso Comunitario:**
   * Los encuestados valoran el reconocimiento cívico de su aporte barrial y la seguridad de sus datos de contacto en caso de que la cuadrilla municipal necesite validar el reporte.
   * *Impacto en el diseño:* **Pantalla de Perfil (`ProfileScreen`)** con indicadores de aporte cívico personal (*Reportes enviados*, *Baches reparados*) y opción segura de cierre de sesión.

---

## 2. Recorrido Técnico del Mockup (Paso a Paso para la Presentación)

Durante la evaluación, puedes guiar la demostración siguiendo este flujo interactivo entre las 6 pantallas:

```
[1. SafetyScreen] ➔ [2. LoginScreen] ➔ [3. HomeScreen] ➔ [4. ReportScreen] ➔ [5. HistoryScreen] ➔ [6. ProfileScreen] ➔ [Logout -> Login]
```

### Paso 1: Aviso de Seguridad (`SafetyScreen`)
* **Qué mostrar:** Icono de advertencia y mensaje preventivo claro: *"No utilices AlertCom mientras conduces"*.
* **Qué decir:** *"Iniciamos con una medida de Aprendizaje + Servicio y responsabilidad social vial: protegemos al 70% de usuarios que conducen obligándolos a detenerse antes de interactuar."*
* **Acción:** Presionar el botón **"Entendido"**.

### Paso 2: Acceso Directo (`LoginScreen`)
* **Qué mostrar:** Campos Material Design 3 (`MDTextField`). Primero, una contraseña incorrecta: aparece un **`MDDialog`** de error y el campo se vacía. Después, el ingreso con `vecino@alertcom.cl` / `123456`.
* **Qué decir:** *"Reducimos la barrera de entrada al mínimo para combatir el desconocimiento. Las credenciales se validan contra `usuarios.json`, donde las contraseñas se guardan cifradas con hash y nunca en texto plano. Si el vecino no tiene cuenta, la crea en segundos con 'Crear Cuenta'."*
* **Acción:** Presionar **"Iniciar Sesión"** para avanzar al mapa principal.

### Paso 3: Home & Call-To-Action (`HomeScreen`)
* **Qué mostrar:** Mapa real de Temuco (`kivy_garden.mapview`) con un marcador de color por cada reporte (Rojo = Pendiente, Amarillo = En revisión, Verde = Reparado), el **banner superior** con el mensaje de la configuración remota y el gran botón de reporte.
* **Qué decir:** *"La interfaz guía visualmente al ciudadano. No hay menús ocultos ni confusión: el botón '+ Reportar bache' resuelve directamente el dolor de 'no saber dónde reportar'."*
* **Acción:** Presionar **"+ Reportar bache"**.

### Paso 4: Formulario de Reporte (`ReportScreen`)
* **Qué mostrar:** 
  1. Card de fotografía interactiva (al presionarla simula captura fotográfica y asignación de coordenadas GPS automáticas: `-38.7359, -72.5904`).
  2. Selectores desplegables dinámicos (`MDDropdownMenu`) para **Tipo de daño** y **Gravedad**.
  3. Campo de texto para descripción adicional con contador de caracteres (máx. 250).
  4. Todo el contenido está embebido en un `ScrollView` con layout de altura adaptativa (`adaptive_height: True`), garantizando fluidez en cualquier resolución sin solapamiento.
* **Qué decir:** *"Optimizamos el formulario a solo 4 datos esenciales (Foto, Tipo, Gravedad y Descripción) para que el reporte tome menos de 30 segundos y la información llegue georreferenciada a Obras Públicas."*
* **Acción:** Presionar **"Enviar Reporte"** vacío (muestra un MDDialog "Falta información"); luego seleccionar Tipo y Gravedad y enviar. Aparece una **notificación del sistema** (Plyer) y el reporte se guarda en `incidentes.json`.

### Paso 5: Historial y Trazabilidad (`HistoryScreen`)
* **Qué mostrar:** Contadores **reales** (Total, En revisión, Reparados) y la lista de reportes guardados. Para demostrar la persistencia, **cierra y vuelve a abrir la app**: el reporte sigue ahí. Con la cuenta municipal (`admin@gmail.com`), al tocar un reporte aparece "Marcar: En revisión", que cambia el estado y dispara una notificación.
* **Qué decir:** *"Cerramos el ciclo de confianza pública. El usuario puede volver en cualquier momento a 'Mis Reportes' para comprobar si la cuadrilla municipal reparó el bache reportado."*
* **Acción:** Presionar **"Volver al Inicio"** o usar la barra inferior para ir a **"Perfil"**.

### Paso 6: Perfil del Usuario (`ProfileScreen` - NUEVA)
* **Qué mostrar:** Avatar de usuario, datos personales (Juan Pérez González, Temuco), métricas cívicas personales calculadas desde `incidentes.json`, información comunitaria y el botón rojo de **"Cerrar Sesión"**.
* **Qué decir:** *"El perfil otorga trazabilidad y sentido de pertenencia: el vecino puede verificar cuántos reportes ha aportado a su comunidad. Además, permite un cierre de sesión seguro para alternar cuentas."*
* **Acción:** Presionar el botón rojo **"Cerrar Sesión"** para regresar a la pantalla de Login, demostrando el ciclo completo.

---

## 3. Especificaciones Técnicas de la Implementación
* **Lenguaje:** Python 3.11
* **Framework:** Kivy 2.3.1 + KivyMD 2.0 (Material Design 3)
* **Mapa:** `kivy_garden.mapview` (con simulación de respaldo si no está instalado)
* **Notificaciones:** Plyer (`notification.notify`)
* **Persistencia:** archivos JSON locales (`usuarios.json`, `incidentes.json`)
* **Configuración remota:** `UrlRequest` asíncrono + `StringProperty` con valores locales por defecto

### 3.1 Arquitectura en capas (Sesiones 17 y 18)

```
AlertCom/
├── estructura_AlertCom/
│   ├── main.py                    → 28 líneas: solo crea la app y el ScreenManager
│   ├── config.py                  → Constantes, textos por defecto y RUTAS de carpetas
│   │
│   ├── models/                    → CAPA 1 · Python puro, SIN Kivy
│   │   ├── usuario.py             → Usuario (hash de contraseña, rol)
│   │   └── incidente.py           → Incidente (equivale a "Tarea": Pendiente → En revisión → Reparado)
│   │
│   ├── controllers/               → CAPA 2 · Lógica de negocio y flujo, sin widgets
│   │   ├── app_controller.py      → Arma todo: datos, log, errores, controladores, config remota
│   │   ├── auth_controller.py     → Login y registro contra usuarios.json
│   │   ├── incidente_controller.py→ Crear, consultar y cambiar estado (+ notificaciones)
│   │   ├── config_remota.py       → UrlRequest + fallback
│   │   ├── almacenamiento_json.py → with open + json.dump/json.load + try/except
│   │   └── notificador.py         → Plyer encapsulado
│   │
│   ├── views/                     → CAPA 3 · Única capa con interfaz gráfica
│   │   ├── gestor_pantallas.py    → Tema, carga los .kv y arma el ScreenManager
│   │   ├── navegador.py           → Cambio de pantalla + rutas protegidas
│   │   ├── kv/                    → Diseño declarativo, un archivo por pantalla
│   │   │   ├── _comunes.kv        → Plantillas compartidas (TarjetaContador)
│   │   │   └── safety · login · register · home · report · history · profile .kv
│   │   ├── pantallas/             → Clases MDScreen (un *_view.py por pantalla)
│   │   └── componentes/
│   │       └── dialogos.py        → MDDialog y MDSnackbar reutilizables
│   │
│   ├── recursos/                  → Archivos estáticos (sí van a Git)
│   │   ├── imagenes/              → Marcadores del mapa por estado
│   │   └── fuentes/               → Tipografías .ttf (vacía por ahora)
│   ├── datos/                     → (se crea solo) JSON, alertcom.log y cache_mapa/ — NO va a Git
│   └── pruebas/test_flujo_e3.py   → 20 pruebas automáticas (incluye reglas de arquitectura)
│
├── docs/                          → Presentación y documentos (fuera del código)
└── herramientas_vscode/launch.json
```

Cada carpeta de código tiene su `__init__.py`, así Python la reconoce como **paquete** y se importa desde la raíz de la app: `from models.usuario import Usuario`, `from views.componentes.dialogos import mostrar_dialogo`.

**Regla de dependencias:** `main.py → views → controllers → models` (todos pueden usar `config.py`). Los modelos no conocen a nadie, los controladores no importan `views/` y solo `views/` crea widgets o cambia de pantalla. Las pruebas de arquitectura verifican estas reglas automáticamente.

### 3.2 Persistencia local con JSON (Sesiones 19 y 20)
* `to_dict()` / `from_dict()` en cada modelo convierten los objetos en diccionarios y viceversa.
* `AlmacenamientoJSON.guardar()` usa `with open(...)` + `json.dump`. Escribe primero en un archivo temporal y luego lo reemplaza, para no corromper datos si la app se cierra a mitad del guardado.
* `AlmacenamientoJSON.cargar()` usa `json.load` dentro de `try/except FileNotFoundError` (instalación nueva → lista vacía, sin cierre forzado). Si el JSON está dañado, lo respalda como `.corrupto.json` y sigue funcionando.
* En el computador los datos quedan en `estructura_AlertCom/datos/`; en Android, en la carpeta privada de la app.

### 3.3 Notificaciones locales con Plyer (Sesión 21)
* `Notificador.notificar()` envuelve `notification.notify(title=..., message=..., timeout=...)`.
* Solo se llama desde la lógica de negocio (`IncidenteController.crear_incidente` y `cambiar_estado`), cuando cambia el estado de un reporte.
* Si la plataforma no soporta notificaciones, se registra en el log y la app sigue funcionando.

### 3.4 Configuración remota (Sesión 22)
* `config_remota.json` (en la raíz del repositorio) define `mensaje_banner`, `mensaje_seguridad` y `texto_boton_reporte`.
* La app parte con los valores de `config.VALORES_POR_DEFECTO` en propiedades `StringProperty`. Al iniciar, pide el JSON con `UrlRequest` (asíncrono, con 5 s de espera máxima).
* Solo se aceptan claves conocidas con texto válido. Ante error de red, HTTP o JSON, se mantienen los valores locales.
* El KV usa binding (`text: app.mensaje_banner`), así que el cambio se ve al instante.
* URL configurada en `config.py` → `URL_CONFIG_REMOTA`. Para que funcione, sube `config_remota.json` a la rama **main** (el repositorio debe ser público) o pega ahí la URL "Raw" de un GitHub Gist.

### 3.5 Depuración (Sesión 23)
Ver **`GUIA_DEPURACION_E3.md`**: lectura de tracebacks, `pdb`, breakpoints de VS Code (`herramientas_vscode/launch.json`, copiar a `.vscode/`), log de errores y checklist E3.

---

## 4. Cómo ejecutar

```bash
# 1. Activar el entorno virtual (Windows)
entorno_alertcom\Scripts\activate

# 2. Instalar dependencias (solo la primera vez)
pip install -r requirements.txt

# 3. Ejecutar la app
cd estructura_AlertCom
python main.py

# 4. Ejecutar las pruebas
python -m unittest discover -s pruebas -v
```

### Cuentas de demostración
| Rol | Correo | Contraseña |
|---|---|---|
| Vecino | `vecino@alertcom.cl` | `123456` |
| Funcionario municipal (puede cambiar estados) | `admin@gmail.com` | `123456` |

> Se crean automáticamente en `datos/usuarios.json` la primera vez que se abre la app. Para volver a empezar desde cero, borra la carpeta `estructura_AlertCom/datos/`.
