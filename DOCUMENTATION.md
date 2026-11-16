# 📊 AlertCom – Documentación de la medición (RA3)

> Cómo medimos si AlertCom resuelve el problema diagnosticado: qué eventos registra la app, cómo se guardan, qué KPIs calculamos, con qué fórmula, en qué periodo y con qué cuidados éticos.

**Versión de la app:** 1.5.0 · **Método:** MJV App (Medir → Jugar → Validar) · **Herramienta:** analítica *in-house* en Python, sin servicios externos.

---

## 1. Del diagnóstico (RA1) a lo que medimos

| Hallazgo de las 26 encuestas (Temuco) | Lo que la app debe lograr | Cómo lo medimos |
|---|---|---|
| “No sé dónde reportarlo” es la principal barrera | Que reportar sea fácil y se pueda terminar | **KPI 1 · Tasa de finalización del reporte** |
| El 70 % se moviliza en auto o transporte público | Que reportar sea rápido (y nunca al conducir) | **KPI 2 · Tiempo mediano para reportar** |
| El seguimiento es muy importante para los usuarios | Que el vecino vuelva a ver qué pasó con su reporte | **KPI 3 · Tasa de seguimiento** |

---

## 2. Anatomía de un evento

Un **evento** es una acción del usuario que decidimos registrar porque sirve para medir algo. No toda acción es un evento: no registramos cada toque en pantalla, solo lo que alimenta un KPI o una métrica útil.

Cada evento es una línea JSON con esta forma:

```json
{"evento": "reporte_enviado", "timestamp": "2026-11-12T10:15:40-03:00", "usuario_id": 2, "sesion_id": "a3f9c1d2", "datos": {"tipo": "Bache", "gravedad": "Grave", "con_foto": true}}
```

| Campo | Qué es | Por qué está |
|---|---|---|
| `evento` | Qué pasó | Sin nombre no hay qué contar. Convención `objeto_accion` en minúsculas, de un **catálogo cerrado** (`models/evento.py`): un nombre mal escrito se rechaza |
| `timestamp` | Cuándo pasó, en **ISO 8601 con zona horaria** | Sin fecha no se puede calcular el tiempo para reportar, el uso por día ni el periodo. ISO 8601 se ordena como texto y se compara sin ambigüedad |
| `datos` | Contexto (pantalla, tipo, motivo…) | Permite agrupar: reportes por tipo, errores por motivo |
| `usuario_id` | Número del usuario (nunca el correo) | Para contar usuarios distintos, la retención y el seguimiento |
| `sesion_id` | Código aleatorio de cada apertura de la app | Para unir el inicio y el fin de un reporte en la misma visita |

### Catálogo de eventos

| Evento | Dónde se registra | Datos | Alimenta |
|---|---|---|---|
| `app_abierta` | `AppController` | plataforma, versión | Sesiones por día |
| `pantalla_vista` | `PantallaBase.on_enter()` (todas las pantallas) | pantalla | KPI 3, pantallas más usadas |
| `login_exitoso` / `login_fallido` | `AuthController` | rol / motivo | Usuarios activos, errores |
| `registro_exitoso` / `registro_fallido` | `AuthController` | — / motivo | Errores de registro |
| `sesion_cerrada` | `AuthController` | — | Sesiones |
| `eliminacion_solicitada` / `_cancelada` / `_aprobada` / `_rechazada` y `reporte_eliminado` (funcionario borra uno propio) | `IncidenteController` | id del reporte y motivo (de una lista cerrada) | ¿Cuántos reportes se piden borrar y por qué? (ej. muchos «repetidos» → mostrar reportes cercanos antes de enviar) |
| `cuenta_actualizada` / `cuenta_eliminada` | `AuthController` | campo cambiado (nombre, correo o contrasena) — **nunca el valor nuevo** | Uso del gestor de cuenta |
| `reporte_iniciado` | `ReportScreen.on_enter()` | — | KPI 1 y KPI 2 |
| `reporte_enviado` | `IncidenteController.crear_incidente()` | id, tipo, gravedad, con_foto | KPI 1, KPI 2, KPI 3 |
| `reporte_rechazado` | `IncidenteController.crear_incidente()` | motivo (sin_tipo, sin_gravedad, sin_ubicacion, sin_calle…) | Errores del formulario |
| `foto_adjuntada` | `ReportScreen` | origen (camara, galeria, archivo) | ¿Usan la cámara real? |
| `ubicacion_solicitada` | `ReportScreen` / `HomeScreen` | pantalla, método (gps o calle), resultado (ok, aproximada, sin_numero, no_encontrada, sin_permiso, sin_senal…) — **sin coordenadas ni calle** | ¿Cómo marcan el lugar los vecinos y cuánto falla? |
| `estado_cambiado` | `IncidenteController.cambiar_estado()` | id, anterior, nuevo | Trazabilidad |
| `config_remota_aplicada` | `AppController` | cantidad de claves | Funcionamiento de Remote Config |

Los eventos de **negocio** se registran en los controladores, después de que la acción realmente ocurrió. Los de **interfaz** (`pantalla_vista`, `reporte_iniciado`) se registran en las vistas, con el evento nativo `on_enter` de Kivy.

---

## 3. Cómo se guardan (formato y archivo)

- **Formato JSON Lines** (`eventos.jsonl`, un evento por línea), en lugar de una gran lista JSON:
  - Agregar un evento es escribir una línea al final; no hay que leer y reescribir todo el archivo.
  - Si la app se cierra a mitad de una escritura, solo se pierde esa línea. Al leer, las líneas dañadas se saltan y se informan.
- **Modo `"a"` (append)**: agrega al final. Con `"w"` se borraría el historial en cada evento.
- **`encoding="utf-8"`**: guarda bien “En revisión” o “Ñielol”.
- **Dónde se guarda:**
  - **Android:** `App.user_data_dir`, la carpeta privada de la app. La carpeta del código es de solo lectura y se reemplaza al actualizar.
  - **Computador:** `estructura_AlertCom/datos/`, que está excluida de Git y del APK.
- **Crecimiento controlado:** sobre 2 MB (~10.000 eventos), el archivo se archiva como `eventos_AAAAMMDD_HHMMSS.jsonl` y se empieza uno nuevo.
- **Registrar nunca cierra la app:** cualquier error se anota en `alertcom.log` y la app sigue funcionando.

Código: `models/evento.py` (estructura) y `controllers/registro_eventos.py` (escritura).

---

## 4. Métricas y KPIs

- **Métrica:** cualquier dato medible que describe qué está pasando (ej. *total de eventos*, *sesiones por día*).
- **KPI:** una métrica **elegida** porque indica si el proyecto cumple su objetivo. Tiene meta y obliga a una decisión. Elegimos **solo 3**, uno por cada hallazgo del diagnóstico. Con más KPIs ninguno guía la decisión.

### KPI 1 · Tasa de finalización del reporte

```
KPI1 = (reportes enviados ÷ formularios abiertos) × 100
     = count(reporte_enviado) / count(reporte_iniciado) × 100
```

- **Meta:** ≥ 80 %.
- **Por qué:** si el vecino abre el formulario y no lo termina, la app no está resolviendo el “no sé dónde reportar”.
- **Decisión que habilita:** si no se cumple, revisamos `motivos_de_rechazo` para encontrar el campo que traba al usuario.

### KPI 2 · Tiempo mediano para reportar

```
Para cada reporte_enviado: segundos desde el último reporte_iniciado de la MISMA sesión
KPI2 = mediana de esas duraciones
```

- **Meta:** ≤ 60 s.
- **Por qué la mediana y no el promedio:** un formulario olvidado 10 minutos en pantalla distorsiona el promedio, pero no la mediana.
- **Decisión que habilita:** si no se cumple, simplificar el formulario (menos campos, valores por defecto).

### KPI 3 · Tasa de seguimiento

```
KPI3 = (vecinos que entraron a "history" DESPUÉS de su primer reporte
        ÷ vecinos que enviaron al menos un reporte) × 100
```

- **Meta:** ≥ 50 %.
- **Por qué:** las encuestas dijeron que el seguimiento es muy importante. Si nadie revisa su historial, esa función no está aportando.
- **Decisión que habilita:** si no se cumple, hacer más visible el historial (por ejemplo, abrir el reporte al tocar la notificación).

### Métricas descriptivas (no son KPI)

Sesiones · usuarios activos · usuarios que vuelven otro día (retención) · reportes por tipo y gravedad · motivos de rechazo · logins fallidos · eventos por día · pantallas más vistas.

> **Ejemplo de métrica vanidosa:** *total de pantallas vistas*. Siempre crece con el uso, pero no dice si la app resuelve algo, así que no sirve para decidir.

Código: `controllers/analitica.py`. Las mismas funciones calculan los KPIs en la pantalla **Métricas** del teléfono y en el script del computador.

---

## 5. Método MJV App aplicado a AlertCom

El método es un **ciclo**: después de validar se vuelve a medir con la app mejorada.

| Paso | Qué hacemos en AlertCom |
|---|---|
| **Medir** | Definir los 3 KPIs desde el diagnóstico (sección 1) e instrumentar la app con los eventos que los alimentan (sección 2). |
| **Jugar** | Observar a personas reales usando la app instalada en el teléfono, sin ayudarlas, con una tarea concreta: *“Reporta un bache que hayas visto esta semana y luego revisa qué pasó con tu reporte”*. Anotamos dudas y comentarios, que se cruzan con los datos. |
| **Validar** | Comparar cada KPI con su hipótesis y su meta, y decidir: mantener, ajustar el diseño o volver a medir. |

**Hipótesis previas** (se escriben ANTES de mirar los datos, para no forzar los resultados):

1. Si el botón “Reportar bache” está siempre visible y el formulario pide solo 4 datos, **al menos el 80 %** de quienes lo abren lo termina.
2. Un reporte se completa en **60 segundos o menos** (mediana).
3. **Al menos la mitad** de quienes reportan vuelve a revisar su historial.

### Periodo de recolección

| Dato | Valor |
|---|---|
| Periodo declarado | **[del ___ al ___ de noviembre de 2026]** |
| Participantes | **[N]** personas: **[vecinos de ___ / compañeros / familiares]** |
| Dispositivos | **[N]** teléfonos Android con el APK 1.5.0 |
| Instrumento | `eventos.jsonl` de cada teléfono + notas de observación |
| Análisis | `python analitica/analitica_proyecto.py --desde AAAA-MM-DD --hasta AAAA-MM-DD` |

> Completar con los datos reales. El script solo analiza los eventos dentro de ese periodo, así que lo declarado coincide con lo calculado.

---

## 6. Herramientas: industria vs. solución propia

| | Firebase / Google Analytics | Registro propio (AlertCom) |
|---|---|---|
| Qué entrega | Paneles automáticos, cohortes, retención y segmentación, en tiempo real | Exactamente los eventos que definimos, y control total del cálculo |
| Requiere | Internet, cuenta de Google, SDK | Nada externo; funciona sin conexión |
| Privacidad | Los datos salen del teléfono hacia un tercero | Los datos quedan en el teléfono |
| Costo | Gratis hasta cierto volumen | Tiempo de desarrollo del equipo |

**Por qué elegimos la solución propia:** es un proyecto A+S sin presupuesto, debe funcionar sin internet, y el curso pide entender cómo se calculan los indicadores.

**Cuándo migraríamos:** si la app se publica en Google Play y se usa en muchos teléfonos, porque juntar archivos a mano deja de ser viable.

---

## 7. Privacidad y ética de los datos

- **Mínimo necesario:** los eventos guardan el **id numérico**, nunca el correo ni el nombre. Del reporte se guardan tipo y gravedad, **no la descripción, la calle, la ubicación ni el nombre de la foto**, que podrían identificar a la persona. Hay pruebas automáticas que lo verifican.
- **Fotos:** se guarda una copia reducida y **sin metadatos EXIF** (la foto original del teléfono puede traer la ubicación exacta y el modelo del teléfono). La copia de la galería se borra.
- **Ubicación:** el GPS se enciende solo mientras se marca un reporte y se apaga apenas hay una ubicación. Se pide el permiso con contexto (al abrir el formulario) y, si se rechaza, la app sigue funcionando moviendo el mapa a mano.
- **Transparencia y control:** en **Perfil → “Registrar mis datos de uso”**, el vecino puede desactivar el registro, y la preferencia se recuerda.
- **Local:** los eventos y las métricas no se envían a internet; las métricas solo las ve el rol municipal.
- **Servicios de terceros (transparencia):** para dibujar el mapa, el teléfono descarga imágenes de **OpenStreetMap**; para completar la calle, envía las coordenadas del pin a **Nominatim** (también de OpenStreetMap), y para ubicar una calle escrita le envía ese texto. Ambos ven la dirección IP del teléfono y la zona consultada. No se envía ningún dato de la cuenta.
- **Fuera de Git y del APK:** `datos/` y `*.jsonl` están en `.gitignore`, y `buildozer.spec` excluye `datos/`.
- **Contraseñas:** solo sal + hash PBKDF2 (ver `models/usuario.py`).

---

## 8. Límites de nuestra medición (lo que NO podemos afirmar)

- Con **[N]** participantes y **[N]** días, los resultados muestran **tendencias, no conclusiones generales** sobre Temuco.
- Los participantes saben que están en una prueba: pueden comportarse distinto que en la vida real.
- No medimos **si el bache se repara de verdad**: el rol municipal lo simula el equipo.
- Desde la versión 1.5 el tiempo para reportar incluye tomar una foto real y marcar la ubicación, así que **no es comparable** con pruebas hechas con la versión 1.4 (foto simulada).
- Un mismo vecino en dos teléfonos cuenta como dos usuarios, porque los ids son locales a cada teléfono.

---

## 9. Cómo reproducir los resultados

```powershell
# 1. Copiar los eventos de cada teléfono (ver GUIA_APK_BUILDOZER.md, paso 7)
# 2. Instalar matplotlib (solo la primera vez)
pip install -r requirements-analisis.txt
# 3. Analizar el periodo declarado
python analitica\analitica_proyecto.py --datos analitica\eventos_telefono.jsonl --desde 2026-11-12 --hasta 2026-11-15
```

Se generan en `analitica/resultados/`: `resumen.md`, `eventos.csv` y 5 gráficos (sesiones por día, embudo del reporte, KPIs frente a su meta, reportes por tipo y errores).

**Resultados:** ver `analitica/resultados/resumen.md` y el Informe Final.
