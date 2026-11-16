# 📱 AlertCom – Generar el APK con Buildozer (Windows + WSL2)

Buildozer **no funciona directamente en Windows**: necesita Linux. En Windows se usa **WSL2** (Linux dentro de Windows). La primera compilación tarda entre **30 y 60 minutos**, porque descarga el SDK y el NDK de Android; las siguientes, unos 5 minutos.

> El archivo `estructura_AlertCom/buildozer.spec` ya está configurado: carpetas MVC, `.kv`, `certifi`, permisos de red y notificaciones, API 33 y arm64-v8a.

---

## Paso 1 · Instalar WSL2 con Ubuntu 22.04 (una sola vez)

En **PowerShell como administrador**:

```powershell
wsl --install -d Ubuntu-22.04
```

Reinicia el computador. Al abrir "Ubuntu 22.04" desde el menú Inicio, crea un usuario y una contraseña de Linux.

> Usa la **22.04**: en la 24.04 falta un paquete (`libtinfo5`) que Buildozer necesita.

## Paso 2 · Instalar las herramientas en Ubuntu (una sola vez)

En la terminal de **Ubuntu**:

```bash
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip python3-venv \
  autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev \
  libtinfo5 cmake libffi-dev libssl-dev automake

python3 -m venv ~/venv-buildozer
source ~/venv-buildozer/bin/activate
pip install --upgrade buildozer "Cython==0.29.33" virtualenv setuptools
```

## Paso 3 · Copiar el proyecto al disco de Linux

Compilar directamente en `C:\` (`/mnt/c/...`) es muy lento y falla por permisos. Copia la carpeta de la app al disco de Linux:

```bash
rm -rf ~/alertcom
cp -r "/mnt/c/Users/FELIPE ASTETE/Desktop/AlertCom/estructura_AlertCom" ~/alertcom
cd ~/alertcom
```

> Cada vez que cambies el código en Windows, repite este paso antes de compilar.

## Paso 4 · Compilar

```bash
source ~/venv-buildozer/bin/activate
cd ~/alertcom
buildozer -v android debug
```

Si te pregunta por licencias, acepta. ✅ **Criterio de éxito:** aparece `bin/alertcom-1.5.0-arm64-v8a-debug.apk`.

## Paso 5 · Pasar el APK a Windows y al teléfono

```bash
cp ~/alertcom/bin/*.apk "/mnt/c/Users/FELIPE ASTETE/Desktop/"
```

Para instalarlo en el teléfono, elige una opción:
- **Sin cables:** envíate el APK (Drive o WhatsApp), ábrelo en el teléfono y permite "instalar apps de origen desconocido".
- **Con cable (adb):** activa **Opciones de desarrollador → Depuración USB** y, en PowerShell, ejecuta `adb install -r "$HOME\Desktop\alertcom-1.5.0-arm64-v8a-debug.apk"`.

Al abrir la app por primera vez, **acepta el permiso de notificaciones**. Al abrir **Reportar bache**, acepta la **ubicación precisa** (no “aproximada”).

## Paso 6 · Si la app se cierra en el teléfono

Conecta el teléfono por USB y lee el error de Python (de abajo hacia arriba, como siempre):

```powershell
adb logcat -s python
```

| Mensaje | Causa probable | Solución |
|---|---|---|
| `ModuleNotFoundError: No module named 'X'` | Falta una librería en `requirements` | Agrégala en `buildozer.spec` y recompila |
| `No module named 'materialyoucolor.dynamiccolor.color_spec'` | Buildozer instala materialyoucolor 2.0.10 y KivyMD necesita la 3.x | Ya resuelto: la versión 3.0.4 va en `librerias/` y `main.py` la carga primero |
| `No module named 'materialshapes'` | KivyMD lo carga con sus listas y necesita cairo, que no existe en Android | Ya resuelto: `librerias/sustitutos/` trae un reemplazo liviano que se activa solo si falta cairo |
| Se cierra al tocar un botón; el registro dice `SIGSEGV ... vbo.so ... fbo.so` | El efecto de onda (ripple) de KivyMD falla en algunas GPU de Android | Ya resuelto: `views/compatibilidad.py` lo apaga solo en Android |
| `cannot import name 'capture_logging'` (al compilar) | El entorno interno de Buildozer quedó con un `pip` a medio actualizar | `rm -rf ~/alertcom/.buildozer/android/platform/build-arm64-v8a/build/venv` y volver a compilar |
| `FileNotFoundError ... .kv` | El `.kv` no entró al APK | Revisa `source.include_exts` (debe tener `kv`) |
| `SSLError` / `CERTIFICATE_VERIFY_FAILED` | Falta `certifi` | Ya está en `requirements`; recompila con `buildozer android clean` |
| El mapa sale gris | Sin internet o sin permiso `INTERNET` | Revisa la conexión del teléfono |
| No aparecen notificaciones | Permiso rechazado | Ajustes → Apps → AlertCom → Notificaciones |
| “No se encontró señal GPS” | Interior de un edificio | Sal a un lugar abierto o mueve el mapa a mano |
| “Se necesita la ubicación PRECISA” | Se eligió “Aproximada” | Ajustes → Apps → AlertCom → Permisos → Ubicación → activar “Usar ubicación precisa” |
| La calle no se completa sola | Sin internet | Escríbela a mano: el reporte se guarda igual |
| La cámara no abre | El teléfono no tiene app de cámara por defecto | Usa el botón **Galería** |

Para limpiar y compilar desde cero: `buildozer android clean`.

## Paso 7 · Traer los eventos del teléfono al computador (analítica)

En el teléfono, la app guarda `eventos.jsonl` en su **carpeta privada** (`App.user_data_dir`), no en la carpeta del código, que es de solo lectura. Con el APK *debug* se puede copiar así (PowerShell, con el teléfono conectado):

```powershell
cd "C:\Users\FELIPE ASTETE\Desktop\AlertCom"
adb exec-out run-as org.alertcom.alertcom cat files/eventos.jsonl > analitica\eventos_telefono.jsonl
```

Y se analiza con:

```powershell
python analitica\analitica_proyecto.py --datos analitica\eventos_telefono.jsonl --desde 2026-11-12 --hasta 2026-11-15
```

> Si usan varios teléfonos, copia uno por uno con nombres distintos (`eventos_tel1.jsonl`, `eventos_tel2.jsonl`), ponlos en una carpeta y pasa esa carpeta en `--datos`. Para que los lea, cada nombre debe empezar con `eventos_` y terminar en `.jsonl`.

---

## Checklist antes de la presentación

- [ ] El APK se instaló y abre en el teléfono.
- [ ] Login, reporte, cerrar y reabrir: el reporte sigue ahí.
- [ ] Aparece la notificación al enviar un reporte.
- [ ] El botón GPS lleva el mapa a tu posición y la calle se completa sola.
- [ ] **Tomar foto** abre la cámara y la foto aparece en el formulario y en el detalle del reporte.
- [ ] El reporte aparece en el mapa en el lugar correcto (no en el centro de Temuco).
- [ ] El funcionario ve **Perfil → Ver métricas de uso** con los KPIs.
- [ ] Plan B: un video corto de la app funcionando, por si falla el teléfono.
