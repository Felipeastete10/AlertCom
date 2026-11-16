# AlertCom – Reportes compartidos con Firebase (v1.6)

Desde la versión 1.6 los reportes se guardan también en **Firebase Realtime
Database**. Así cada vecino ve en el mapa los baches que reportaron los demás
y el funcionario municipal los gestiona desde su propio teléfono.

## Qué se comparte y qué no

| Se sube a Firebase | Se queda SOLO en el teléfono |
|---|---|
| Reportes (tipo, gravedad, estado, calle, coordenadas, fecha) | Cuentas, correos y contraseñas |
| Foto del daño, reducida (máx. 800 px) | Preferencias (letra, fondo) |
| Solicitudes de eliminación | Analítica de uso (eventos.jsonl) |

El autor de cada reporte se guarda con un identificador aleatorio (`uid`), nunca
con su correo.

## 1. Crear la base de datos

1. Entra a https://console.firebase.google.com con una cuenta de Google.
2. **Crear un proyecto** → nombre `alertcom` → desactiva Google Analytics → Crear.
3. Menú izquierdo: **Compilación → Realtime Database → Crear base de datos**.
   - Ubicación: Estados Unidos (us-central1).
   - Modo: **bloqueado** → Habilitar.
4. Pestaña **Reglas** → pega las reglas de abajo → **Publicar**.
5. Pestaña **Datos** → copia el enlace (`https://alertcom-xxxxx-default-rtdb.firebaseio.com/`).

## 2. Reglas de seguridad

```json
{
  "rules": {
    ".read": false,
    ".write": false,
    "alertcom": {
      ".read": true,
      "incidentes": {
        "$id": {
          ".write": true,
          ".validate": "!newData.exists() || newData.hasChildren(['id_incidente', 'tipo_incidente', 'gravedad', 'estado', 'ubicacion'])"
        }
      },
      "fotos": {
        "$id": {
          ".write": true,
          ".validate": "!newData.exists() || (newData.isString() && newData.val().length < 400000)"
        }
      }
    }
  }
}
```

- Todo lo que no sea `alertcom/incidentes` o `alertcom/fotos` queda bloqueado.
- Un reporte debe tener sus campos obligatorios: si alguien intenta modificar
  uno que ya fue borrado, Firebase lo rechaza (no se "revive" a medias).
- Una foto no puede pasar de ~300 KB.

> **Límite conocido (proyecto académico):** no hay inicio de sesión en
> Firebase, así que cualquiera con el enlace podría escribir en esas dos
> secciones. Para producción se agregaría Firebase Authentication y reglas
> por usuario (`auth.uid`).

## 3. Conectar la app

En `estructura_AlertCom/config.py`:

```python
URL_FIREBASE = "https://alertcom-xxxxx-default-rtdb.firebaseio.com"
```

Con `URL_FIREBASE = ""` la app funciona como antes (solo en el teléfono).

## 4. Cómo se sincroniza (controllers/nube.py)

1. El teléfono **siempre guarda primero** en `incidentes.json`: sin internet
   la app funciona igual.
2. Cada cambio entra a una **cola** (`datos/nube_pendientes.json`) y se sube
   apenas hay conexión.
3. Luego se **descarga** la lista completa (al abrir la app, al entrar al mapa
   o al historial, y cada 45 segundos).
4. Si dos teléfonos crean el mismo número de reporte sin internet, el segundo
   en subir recibe el siguiente número libre (escritura condicional
   `if-match: null_etag`).
5. Si el municipio cambia el estado de un reporte, aprueba o rechaza una
   solicitud desde su teléfono, el vecino recibe la notificación en el suyo.

La primera vez que la app se conecta, sube los reportes que ya había en el
teléfono.

## 5. Pruebas

`pruebas/test_nube.py` levanta un Firebase **falso** en el computador (mismas
reglas) y simula dos teléfonos: compartir reportes y fotos, números repetidos,
sin internet, cambio de estado, solicitud/aprobación/rechazo y rutas de foto
tramposas.

```
python -m unittest pruebas.test_nube -v
```
