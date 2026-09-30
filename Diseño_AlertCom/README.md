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
* **Qué mostrar:** Campos con soporte Material Design 3 (`MDTextField` con soporte para correo y contraseña).
* **Qué decir:** *"Reducimos la barrera de entrada al mínimo para combatir el desconocimiento."*
* **Acción:** Presionar **"Iniciar Sesión"** para avanzar al mapa principal.

### Paso 3: Home & Call-To-Action (`HomeScreen`)
* **Qué mostrar:** Simulación del mapa geográfico de Temuco con marcadores de estado (Rojo = Pendiente, Amarillo = En revisión, Verde = Reparado) y el gran botón naranja de reporte.
* **Qué decir:** *"La interfaz guía visualmente al ciudadano. No hay menús ocultos ni confusión: el botón '+ Reportar bache' resuelve directamente el dolor de 'no saber dónde reportar'."*
* **Acción:** Presionar **"+ Reportar bache"**.

### Paso 4: Formulario de Reporte (`ReportScreen`)
* **Qué mostrar:** 
  1. Card de fotografía interactiva (al presionarla simula captura fotográfica y asignación de coordenadas GPS automáticas: `-38.7352, -72.5904`).
  2. Selectores desplegables dinámicos (`MDDropdownMenu`) para **Tipo de daño** y **Gravedad**.
  3. Campo de texto para descripción adicional con contador de caracteres (máx. 250).
  4. Todo el contenido está embebido en un `ScrollView` con layout de altura adaptativa (`adaptive_height: True`), garantizando fluidez en cualquier resolución sin solapamiento.
* **Qué decir:** *"Optimizamos el formulario a solo 4 datos esenciales (Foto, Tipo, Gravedad y Descripción) para que el reporte tome menos de 30 segundos y la información llegue georreferenciada a Obras Públicas."*
* **Acción:** Seleccionar Tipo, Gravedad y presionar **"Enviar Reporte"**.

### Paso 5: Historial y Trazabilidad (`HistoryScreen`)
* **Qué mostrar:** Tarjetas de balance superior (Total: 4, En revisión: 2, Reparados: 1) y lista con tarjetas de detalle de baches reportados en Temuco.
* **Qué decir:** *"Cerramos el ciclo de confianza pública. El usuario puede volver en cualquier momento a 'Mis Reportes' para comprobar si la cuadrilla municipal reparó el bache reportado."*
* **Acción:** Presionar **"Volver al Inicio"** o usar la barra inferior para ir a **"Perfil"**.

### Paso 6: Perfil del Usuario (`ProfileScreen` - NUEVA)
* **Qué mostrar:** Avatar de usuario, datos personales (Juan Pérez González, Temuco), métricas cívicas personales (3 reportes enviados, 1 reparado), información comunitaria y el botón rojo de **"Cerrar Sesión"**.
* **Qué decir:** *"El perfil otorga trazabilidad y sentido de pertenencia: el vecino puede verificar cuántos reportes ha aportado a su comunidad. Además, permite un cierre de sesión seguro para alternar cuentas."*
* **Acción:** Presionar el botón rojo **"Cerrar Sesión"** para regresar a la pantalla de Login, demostrando el ciclo completo.

---

## 3. Especificaciones Técnicas de la Implementación
* **Lenguaje:** Python 3.11.1
* **Framework:** Kivy 2.3.1
* **Librería de Componentes:** KivyMD 2.0.1.dev0 (Material Design 3)
* **Gestión de Pantallas:** `ScreenManager` con `SlideTransition` direccional.
* **Arquitectura de Interfaz:** Separación estricta de lógica (`main.py`) y vista declarativa (`alertcom.kv`), asegurando escalabilidad hacia el backend definitivo en Flask + MySQL.
