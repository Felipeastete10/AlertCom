# =============================================================================
# AlertCom - Configuración de empaquetado Android (Buildozer)
# =============================================================================
# Este archivo es el "plano" del APK. Se ejecuta desde esta misma carpeta
# (estructura_AlertCom), en Linux o WSL2:
#     buildozer -v android debug
# El APK queda en bin/. Guía completa: GUIA_APK_BUILDOZER.md
# =============================================================================

[app]

# --- Identidad de la app -----------------------------------------------------
title = AlertCom
package.name = alertcom
package.domain = org.alertcom
# Nombre del paquete final: org.alertcom.alertcom
version = 1.6.0

# --- Qué archivos entran al APK ----------------------------------------------
# main.py está en esta carpeta: la fuente es "."
source.dir = .
# .py (código), .kv (diseño de views/kv), .png (íconos y marcadores),
# .json (no hay JSON de datos aquí: datos/ se excluye abajo)
source.include_exts = py,kv,png,jpg,json,ttf

# Carpetas que NO van al APK:
#   pruebas  → solo se usan en el computador
#   datos    → usuarios, reportes y eventos del PC: nunca deben viajar en el APK
#   bin, .buildozer, __pycache__, cache → archivos generados
source.exclude_dirs = pruebas, datos, cache, bin, .buildozer, __pycache__
source.exclude_patterns = *.log, *.jsonl, *.spec

# --- Pantalla ----------------------------------------------------------------
orientation = portrait
fullscreen = 0
icon.filename = %(source.dir)s/recursos/imagenes/icono.png
presplash.filename = %(source.dir)s/recursos/imagenes/presplash.png
android.presplash_color = #1E1E28

# --- Librerías ---------------------------------------------------------------
# python-for-android instala cada librería SIN sus dependencias, por eso se
# listan todas:
#   kivymd (commit fijo, igual al del computador) + lo que necesita:
#       materialyoucolor, asynckivy, asyncgui, exceptiongroup, pillow
#   plyer                 → notificaciones
#   kivy_garden.mapview   → mapa (usa requests para bajar las imágenes)
#   requests + urllib3 + idna + charset-normalizer → descargas del mapa
#   certifi               → certificados HTTPS (sin esto fallan GitHub y el mapa)
# No se incluye "materialshapes": solo lo usan dos widgets de KivyMD que
# AlertCom no ocupa, y requiere cairo (difícil de compilar para Android).
# Nota: materialyoucolor aparece aquí, pero Buildozer trae la versión 2.0.10 y
# KivyMD 2.0 necesita la 3.x. La versión correcta va incluida en librerias/ y
# main.py la carga primero (ver librerias/__init__.py).
requirements = python3,kivy==2.3.1,https://github.com/kivymd/KivyMD/archive/a00c10c385064afb3a46b3a10d1d2c0c6505dc48.zip,materialyoucolor,asynckivy,asyncgui,exceptiongroup,pillow,plyer,kivy_garden.mapview,requests,urllib3,idna,charset-normalizer,certifi

# --- Android -----------------------------------------------------------------
# Permisos:
#   INTERNET / ACCESS_NETWORK_STATE → mapa y configuración remota
#   POST_NOTIFICATIONS              → notificaciones en Android 13+
#   VIBRATE                         → requerido por las notificaciones de Plyer
#   ACCESS_FINE/COARSE_LOCATION     → GPS para marcar dónde está el bache
#   WRITE_EXTERNAL_STORAGE          → foto con la cámara en Android 9 o anterior
#                                     (en Android 10+ no se usa ni se pide)
#   No se pide CAMERA: la foto la toma la app de cámara del teléfono.
android.permissions = INTERNET, ACCESS_NETWORK_STATE, POST_NOTIFICATIONS, VIBRATE, ACCESS_FINE_LOCATION, ACCESS_COARSE_LOCATION, WRITE_EXTERNAL_STORAGE

# API 33 = Android 13 (exigencia actual de Google Play); mínimo Android 5.0
android.api = 33
android.minapi = 21

# Teléfonos actuales de 64 bits. Si el teléfono de prueba es antiguo
# (32 bits), agrega: , armeabi-v7a   (la compilación tarda el doble)
android.archs = arm64-v8a

android.accept_sdk_license = True
android.allow_backup = True


[buildozer]

# 2 = muestra los comandos y errores completos (útil para depurar)
log_level = 2
warn_on_root = 1
