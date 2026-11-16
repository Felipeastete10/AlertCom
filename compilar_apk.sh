#!/bin/bash
# =============================================================================
# AlertCom - Compilar el APK en un solo paso (ejecutar en Ubuntu / WSL)
# =============================================================================
#   bash "/mnt/c/Users/FELIPE ASTETE/Desktop/AlertCom/compilar_apk.sh"
#
# 1. Copia el código nuevo desde Windows a ~/alertcom (sin borrar lo que
#    Buildozer ya descargó: SDK, NDK, librerías compiladas).
# 2. Borra el entorno interno de pip de Buildozer: se daña entre una
#    compilación y otra ("cannot import name 'capture_logging'").
# 3. Compila y, si todo sale bien, deja el APK en el Escritorio.
#    Si falla, copia compilacion.log a la carpeta AlertCom para revisarlo.
# =============================================================================

ESCRITORIO="/mnt/c/Users/FELIPE ASTETE/Desktop"
ORIGEN="$ESCRITORIO/AlertCom/estructura_AlertCom"
DESTINO="$HOME/alertcom"

source "$HOME/venv-buildozer/bin/activate"

echo ">> 1/3 Copiando el código nuevo..."
mkdir -p "$DESTINO"
cp -r "$ORIGEN/." "$DESTINO/"

echo ">> 2/3 Limpiando el pip interno de Buildozer..."
rm -rf "$DESTINO/.buildozer/android/platform/build-arm64-v8a/build/venv"

echo ">> 3/3 Compilando (unos 5 minutos)..."
cd "$DESTINO" || exit 1
buildozer -v android debug 2>&1 | tee compilacion.log

if grep -q "Android packaging done" compilacion.log; then
    cp bin/*.apk "$ESCRITORIO/"
    echo
    echo "=============================================================="
    echo " LISTO: el APK nuevo está en tu Escritorio"
    ls -l --time-style=+%H:%M bin/
    echo "=============================================================="
else
    cp compilacion.log "$ESCRITORIO/AlertCom/"
    echo
    echo "=============================================================="
    echo " FALLÓ: copié compilacion.log a la carpeta AlertCom"
    echo "=============================================================="
fi
