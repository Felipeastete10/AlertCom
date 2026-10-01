# 🤖 Recurso de Uso de IA - Proyecto AlertCom

Este documento detalla el historial y la estructura de los **prompts (instrucciones)** utilizados con herramientas de Inteligencia Artificial (IA) durante el desarrollo del **Mockup interactivo de la aplicación móvil AlertCom**.

El objetivo de este registro es **transparentar el uso de la IA**, demostrando cómo se aplicó la **ingeniería de prompts** para restringir la herramienta al marco tecnológico exigido (**Python + KivyMD**) y a la metodología de **Aprendizaje + Servicio (A+S)**, utilizando datos obtenidos de una investigación real.

---

## 📋 Índice

1. [Prompt Base: Generación de la Estructura y Mockup Inicial](#1-prompt-base-generación-de-la-estructura-y-mockup-inicial)
2. [Prompt de Depuración: Corrección de Navegación](#2-prompt-de-depuración-corrección-de-navegación-login)
3. [Prompt de Diseño UI: Prevención de Colapso de Componentes](#3-prompt-de-diseño-ui-prevención-de-colapso-de-componentes)
4. [Prompt de Iteración y Funcionalidad: Agregando el Perfil](#4-prompt-de-iteración-y-funcionalidad-agregando-el-perfil)
5. [Prompt de Documentación Académica: Guion de Presentación](#5-prompt-de-documentación-académica-guion-de-presentación)
6. [Buenas Prácticas Aplicadas en estos Prompts](#-buenas-prácticas-aplicadas-en-estos-prompts)

---

# 1. Prompt Base: Generación de la Estructura y Mockup Inicial

### 🎯 Propósito

Contextualizar a la IA sobre las **reglas del proyecto**, las versiones exactas de las librerías y los requerimientos de diseño.

Además, se buscó que las decisiones visuales estuvieran justificadas mediante los resultados obtenidos de **26 encuestas reales realizadas en Temuco**.

### 👨‍💻 Rol y Contexto

> Actúa como un ingeniero de software experto en Python, Kivy/KivyMD, APIs REST (Flask) y aplicaciones Android.
>
> Tu objetivo es ayudar a desarrollar el diseño inicial y Mockup del proyecto móvil **"AlertCom"**.
>
> El lema del proyecto es:
>
> **"Reporta. Ubica. Mejora."**

### ⚙️ Reglas Tecnológicas y de Entorno

La aplicación debe cumplir estrictamente con las siguientes condiciones:

* La aplicación móvil debe construirse **única y exclusivamente con Python + Kivy/KivyMD**.
* No utilizar:

  * Flutter
  * React Native
  * Java
  * Kotlin
* Versiones obligatorias:

  * **Python 3.11.1**
  * **Kivy 2.3.1**
  * **KivyMD 2.0.1.dev0**
* Utilizar exclusivamente la sintaxis correspondiente a **KivyMD 2.0.1.dev0**.
* No utilizar sintaxis perteneciente a versiones antiguas de KivyMD 1.x.

### 📊 Metodología A+S y Justificación de Datos

El diseño se encuentra fundamentado en una investigación realizada mediante **26 encuestas en Temuco**.

Los principales resultados utilizados como referencia fueron:

| Dato                                                 |                                                  Resultado |
| ---------------------------------------------------- | ---------------------------------------------------------: |
| Personas que encuentran baches frecuentemente        |                                                 **57,6 %** |
| Usuarios que utilizan Transporte Público o Automóvil |                                              **Casi 70 %** |
| Principal problema identificado                      | **No sé dónde reportarlo / No sabía que podía reportarlo** |
| Importancia del seguimiento                          |                       **Muy importante para los usuarios** |

Estos datos fueron utilizados para orientar las decisiones de diseño y funcionalidad de la aplicación.

### 🛠️ Instrucciones de Desarrollo

La IA debía generar:

* `main.py`
* `alertcom.kv`

Utilizando `ScreenManager` y KivyMD 2.0.

El Mockup inicial debía incluir **5 pantallas principales**:

1. ⚠️ **Aviso de Seguridad**

   * Protección y advertencia para el conductor.

2. 🔐 **Login**

   * Inicio de sesión del usuario.

3. 🗺️ **Home / Mapa**

   * Visualización del mapa.
   * Botón principal **"+ Reportar bache"**.

4. 📝 **Formulario de Reporte**

   * Registro de información del bache.

5. 📋 **Historial / Seguimiento**

   * Visualización del estado de los reportes realizados.

---

# 2. Prompt de Depuración: Corrección de Navegación (Login)

### 🎯 Propósito

Solucionar un problema de navegación en el Mockup.

La aplicación quedaba detenida en la pantalla de Login debido a que el prototipo todavía no contaba con una conexión funcional al backend.

### ⚠️ Contexto del Problema

El proyecto AlertCom estaba siendo desarrollado como un **Mockup visual**, utilizando:

* Python 3.11.1
* KivyMD 2.0

Al tratarse de una maqueta, **no existía una validación real de credenciales mediante Flask/MySQL**.

### ❌ Problema Detectado

El código funcionaba correctamente a nivel visual, pero al presionar:

> **"Iniciar sesión"**

no ocurría ninguna acción y el usuario no podía acceder a la pantalla principal.

### 🔧 Instrucción de Corrección

Se solicitó a la IA aplicar el **cambio mínimo necesario** para simular un inicio de sesión exitoso.

La modificación debía realizarse sobre el evento del botón utilizando:

```kv
on_release
```

El objetivo era que el `ScreenManager` realizara directamente la transición hacia la pantalla principal.

### ✅ Resultado Esperado

El flujo debía quedar de la siguiente manera:

```text
Aviso de Seguridad
        ↓
      Login
        ↓
   Pantalla Principal
        ↓
       Mapa
```

---

# 3. Prompt de Diseño UI: Prevención de Colapso de Componentes

### 🎯 Propósito

Corregir un problema visual producido por la distribución incorrecta de los componentes dentro del formulario.

Este tipo de problema puede ocurrir frecuentemente en Kivy cuando los elementos no cuentan con contenedores adaptables o cuando se visualiza la aplicación en pantallas pequeñas.

### ⚠️ Contexto del Problema Visual

En la pantalla **"Nuevo Reporte"** se detectó un error de diseño.

### ❌ Problemas Detectados

* Widgets colapsados.
* Botones superpuestos.
* Campos de descripción superpuestos.
* Textos duplicados.
* Mala distribución vertical de los componentes.

### 🔧 Instrucción de Corrección

Se solicitó reescribir exclusivamente el código `.kv` correspondiente a la pantalla del formulario.

Se establecieron las siguientes reglas:

#### 1. Utilizar `ScrollView`

El formulario debía estar dentro de un `ScrollView` para permitir que el usuario pudiera desplazarse verticalmente.

#### 2. Utilizar `MDBoxLayout`

Dentro del `ScrollView` se debía utilizar un `MDBoxLayout` vertical.

Además, debía utilizar:

```kv
adaptive_height: True
```

#### 3. Utilizar sintaxis KivyMD 2.0

Los componentes debían utilizar la sintaxis correspondiente a:

* `MDTextField`
* `MDButton`
* Componentes compatibles con KivyMD 2.0.1.dev0.

### 📐 Estructura Esperada

```text
ScrollView
    │
    └── MDBoxLayout
            │
            ├── Tipo de reporte
            ├── Gravedad
            ├── Descripción
            ├── Ubicación
            ├── Evidencia
            └── Botón de enviar
```

---

# 4. Prompt de Iteración y Funcionalidad: Agregando el Perfil

### 🎯 Propósito

Expandir el flujo de usuario del Mockup mediante la incorporación de una **sexta pantalla: Perfil de Usuario**.

La modificación debía realizarse sin romper las funcionalidades existentes.

### 🎯 Objetivo Crítico

La aplicación debía mantener una navegación fluida y funcional.

El Mockup debía contar con **6 pantallas**:

1. Aviso de Seguridad
2. Login
3. Home / Mapa
4. Formulario de Reporte
5. Historial / Seguimiento
6. Perfil de Usuario

### 🛠️ Instrucciones de Desarrollo

Se solicitó modificar:

```text
main.py
alertcom.kv
```

para incorporar las siguientes funcionalidades.

### 🔽 Menús Desplegables

Los componentes `MDDropdownMenu` debían funcionar correctamente dentro del formulario para:

* Tipo de reporte.
* Gravedad del bache.

### 👤 Nueva Pantalla: Perfil

Se agregó una pantalla denominada:

```text
ProfileScreen
```

Esta pantalla debía mostrar información simulada del usuario:

* 👤 Avatar.
* **Nombre:** dato simulado.
* **Correo:** dato simulado.
* 📊 Estadística:

  * `Reportes enviados: 3`
* 🔴 Botón:

  * `Cerrar Sesión`

### 🧭 Barra de Navegación

El perfil debía conectarse a una barra de navegación inferior mediante:

```text
MDNavigationBar
```

Esto permitió mejorar la navegación entre las principales secciones de la aplicación.

### 📱 Flujo Actualizado

```text
                  ┌───────────────┐
                  │     LOGIN     │
                  └───────┬───────┘
                          ↓
                  ┌───────────────┐
                  │ HOME / MAPA   │
                  └───────┬───────┘
                          ↓
             ┌────────────┴────────────┐
             ↓                         ↓
      ┌──────────────┐          ┌──────────────┐
      │   REPORTAR   │          │  HISTORIAL   │
      │     BACHE    │          │ / SEGUIMIENTO│
      └──────────────┘          └──────────────┘
                                     
                          ↓
                  ┌───────────────┐
                  │    PERFIL     │
                  └───────────────┘
```

---

# 5. Prompt de Documentación Académica: Guion de Presentación

### 🎯 Propósito

Generar material de apoyo para la **Evaluación E2**, relacionando directamente el código desarrollado con la rúbrica del curso y la metodología **Aprendizaje + Servicio (A+S)**.

### 📚 Instrucción de Documentación

Se solicitó generar un archivo:

```text
README.md
```

con un **Guion de Presentación A+S** que sirviera como apoyo para la defensa técnica y metodológica del proyecto.

### 📌 Aspectos que debía explicar

El documento debía explicar cómo las decisiones de diseño visual y UX de AlertCom responden directamente a los resultados obtenidos mediante las **26 encuestas**.

Entre los principales aspectos se consideraron:

* 🚧 El problema relacionado con los baches.
* ❓ El desconocimiento sobre dónde realizar un reporte.
* 🚗 La necesidad de considerar a los conductores.
* 📍 La importancia de conocer la ubicación del problema.
* 📋 La necesidad de realizar seguimiento a los reportes.
* 📱 La facilidad de uso de la aplicación.

De esta forma, la documentación debía conectar:

```text
Investigación
     ↓
26 Encuestas
     ↓
Identificación del problema
     ↓
Requerimientos
     ↓
Diseño UX/UI
     ↓
Desarrollo del Mockup
     ↓
Solución propuesta: AlertCom
```

---

# 💡 Buenas Prácticas Aplicadas en estos Prompts

Durante el desarrollo de AlertCom se aplicaron diferentes técnicas de **ingeniería de prompts** para obtener resultados más consistentes y alineados con los requerimientos del proyecto.

## 1. 🎯 Asignación de Rol Restringido

Se limitó a la IA a trabajar como un experto específicamente en:

* Python.
* Kivy.
* KivyMD.
* APIs REST.
* Aplicaciones móviles Android.

Esto permitió evitar recomendaciones de tecnologías que no correspondían al proyecto, como:

* Flutter.
* React Native.
* Java.
* Kotlin.

---

## 2. 📊 Inyección de Datos Reales

En lugar de entregar un contexto genérico y permitir que la IA inventara información, se proporcionaron datos obtenidos de las **26 encuestas realizadas**.

Entre ellos:

* **57,6 %** encuentra baches frecuentemente.
* **Casi 70 %**
