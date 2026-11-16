# 📍 AlertCom

> **Reporta. Ubica. Mejora.** App móvil para que los vecinos de Temuco reporten baches desde su celular y sigan su reparación.

Proyecto Integrado Final · **TINF1119 Desarrollo Móvil (A+S)** · Instituto Tecnológico UC Temuco · 2026
**Equipo:** [Integrantes del grupo] · **Versión:** 1.5.0

---

## El problema

En una investigación con **26 encuestas** en Temuco encontramos que:

- El **57,6 %** se topa con baches de forma frecuente o muy frecuente.
- El **70 %** se moviliza a diario en auto o transporte público.
- La barrera principal no es el desinterés, sino el **desconocimiento**: *“no sé dónde reportarlo”*.
- Para los vecinos, **saber qué pasó con su reporte** es muy importante.

AlertCom responde con un canal simple: un botón visible para reportar, un formulario corto y un historial para seguir cada caso.

## Funcionalidades

| Funcionalidad | Detalle |
|---|---|
| Aviso de seguridad | Pide no usar la app mientras se conduce |
| Inicio de sesión y registro | Cuentas en `usuarios.json` con contraseña protegida por hash PBKDF2 |
| Mapa de Temuco | Un marcador de color por reporte (Pendiente, En revisión, Reparado) y botón **Mi ubicación** |
| Reporte de baches | **Ubicación** (GPS, moviendo el mapa bajo un pin o **escribiendo la calle**), **calle** (se completa sola), **foto real** (cámara o galería del teléfono), tipo, gravedad y descripción, con validación |
| Historial y seguimiento | Cada vecino ve sus reportes; el funcionario municipal avanza su estado |
| Notificaciones | Aviso nativo al enviar un reporte y al cambiar su estado (Plyer) |
| Configuración remota | Textos que cambian desde GitHub, con valores locales si no hay internet |
| **Eliminar reportes (nuevo)** | El vecino pide eliminar su reporte eligiendo un motivo; solo un funcionario municipal puede aprobar (se borra con su foto) o rechazar (se mantiene). El funcionario puede eliminar directamente sus propios reportes |
| **Ajustes (nuevo)** | Tamaño de letra (4 niveles) y color de fondo, guardados en el teléfono |
| **Mi cuenta (nuevo)** | Cambiar nombre, correo o contraseña (pide la actual) y eliminar la cuenta; los reportes se conservan sin nombre |
| Interacción | Filtros del mapa por estado, tipo y gravedad con opciones que se tocan, barra de avance del formulario, animación al enviar, contadores-filtro en el historial, mostrar/ocultar contraseña y vibración en el teléfono |
| **Analítica (nuevo)** | Registro de eventos de uso y pantalla **Métricas** con 3 KPIs, solo para el rol municipal |
| **Privacidad (nuevo)** | El vecino puede desactivar el registro de su uso desde el Perfil |

## Tecnologías

Python 3.11 · Kivy 2.3.1 · KivyMD 2.0 · kivy_garden.mapview · Plyer · JSON / JSON Lines · Buildozer (APK) · matplotlib (solo para el análisis en el PC) · Git + GitHub.

## Arquitectura

La app sigue una arquitectura en **3 capas (MVC)**. Las dependencias van en una sola dirección:

```text
main.py ──► views ──► controllers ──► models        (todos pueden usar config.py)
```

- **`models/`** · Python puro, sin Kivy: `Usuario`, `Incidente` y `Evento`.
- **`controllers/`** · Lógica de negocio: autenticación, reportes, persistencia JSON, notificaciones, configuración remota, registro de eventos y cálculo de KPIs.
- **`views/`** · La única capa con interfaz: 8 pantallas, un archivo `.kv` por pantalla, el navegador con rutas protegidas y los diálogos.

El árbol completo de carpetas está en [ESTRUCTURA.md](ESTRUCTURA.md).

## Cómo ejecutar (Windows)

```powershell
# 1. Entorno virtual (solo la primera vez)
python -m venv entorno_alertcom
entorno_alertcom\Scripts\activate
pip install -r requirements.txt

# 2. Ejecutar la app
cd estructura_AlertCom
python main.py

# 3. Ejecutar las pruebas automáticas
python -m unittest discover -s pruebas -v
```

### Cuentas de demostración

| Rol | Correo | Contraseña |
|---|---|---|
| Vecino | `vecino@alertcom.cl` | `123456` |
| Funcionario municipal (cambia estados y ve Métricas) | `admin@gmail.com` | `123456` |

> Se crean solas en `datos/usuarios.json` la primera vez que se abre la app. Para empezar de cero, borra `estructura_AlertCom/datos/`.

## APK para Android

`estructura_AlertCom/buildozer.spec` ya está configurado. Se compila en Linux o WSL2 con `buildozer -v android debug`.
Paso a paso: [GUIA_APK_BUILDOZER.md](GUIA_APK_BUILDOZER.md).

## Medición (RA3)

- La app registra eventos (`reporte_iniciado`, `reporte_enviado`, `pantalla_vista`…) en `eventos.jsonl`, dentro de la carpeta privada de la app.
- Tres KPIs: **tasa de finalización del reporte**, **tiempo mediano para reportar** y **tasa de seguimiento**.
- Análisis en el PC, con gráficos:

```powershell
pip install -r requirements-analisis.txt
python analitica\analitica_proyecto.py --desde 2026-11-12 --hasta 2026-11-15
```

Eventos, fórmulas, método MJV App, periodo de recolección y privacidad: [DOCUMENTATION.md](DOCUMENTATION.md).

## Calidad

- **89 pruebas automáticas:** arquitectura, persistencia, login, notificaciones, configuración remota, registro de eventos, KPIs, privacidad, ubicación, calle, fotos, decisiones del GPS, gestor de cuenta, preferencias y eliminación autorizada de reportes.
- Errores no controlados guardados en `datos/alertcom.log`.
- Guía de depuración y checklist: [GUIA_DEPURACION_E3.md](GUIA_DEPURACION_E3.md).

## Documentos del repositorio

| Archivo | Contenido |
|---|---|
| [DOCUMENTATION.md](DOCUMENTATION.md) | Medición: eventos, KPIs, MJV App, ética |
| [ESTRUCTURA.md](ESTRUCTURA.md) | Árbol de carpetas y reglas de arquitectura |
| [GUIA_APK_BUILDOZER.md](GUIA_APK_BUILDOZER.md) | Generar e instalar el APK |
| [GUIA_DEPURACION_E3.md](GUIA_DEPURACION_E3.md) | Tracebacks, pdb y checklist |
| [uso_de_IA.md](uso_de_IA.md) | Declaración de uso de inteligencia artificial |
| `docs/` | Presentación y guion de la evaluación E2 |
| Informe Final | [Agregar enlace o archivo] |

## Uso de inteligencia artificial

El equipo usó herramientas de IA como apoyo en el diseño, el código y la documentación. El detalle de los usos y la revisión que hizo el equipo está en [uso_de_IA.md](uso_de_IA.md).
