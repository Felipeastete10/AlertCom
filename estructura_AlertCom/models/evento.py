# =============================================================================
# AlertCom - Modelo de Dominio: Evento (analítica, RA3)
# =============================================================================
# Un evento es una acción del usuario que decidimos REGISTRAR porque sirve
# para medir algo. Tiene tres partes mínimas:
#   • nombre     → QUÉ pasó          (ej. "reporte_enviado")
#   • timestamp  → CUÁNDO pasó       (fecha y hora ISO 8601 con zona horaria)
#   • datos      → CONTEXTO          (diccionario: pantalla, tipo, motivo…)
# Y dos campos extra que justificamos en DOCUMENTATION.md:
#   • usuario_id → QUIÉN (un número, nunca el correo): permite contar usuarios
#   • sesion_id  → EN QUÉ VISITA: permite medir el tiempo de un flujo
#
# Python puro: no importa Kivy.
# =============================================================================

from datetime import datetime

# Catálogo cerrado de eventos: un nombre fuera de esta lista se rechaza.
# Convención: objeto_accion, en minúsculas y con guion bajo.
CATALOGO_EVENTOS = {
    "app_abierta": "Se abrió la aplicación (inicio de una sesión)",
    "pantalla_vista": "El usuario entró a una pantalla",
    "login_exitoso": "Inicio de sesión correcto",
    "login_fallido": "Inicio de sesión rechazado",
    "registro_exitoso": "Se creó una cuenta nueva",
    "registro_fallido": "El registro de cuenta fue rechazado",
    "cuenta_actualizada": "La persona cambió su nombre, correo o contraseña (solo el campo)",
    "cuenta_eliminada": "La persona eliminó su cuenta",
    "sesion_cerrada": "El usuario cerró sesión",
    "reporte_iniciado": "Se abrió el formulario de reporte",
    "reporte_enviado": "Se guardó un reporte nuevo",
    "reporte_rechazado": "El formulario se envió incompleto o inválido",
    "foto_adjuntada": "Se adjuntó una foto al reporte (cámara, galería o archivo)",
    "ubicacion_solicitada": "Se pidió la ubicación GPS (resultado, sin coordenadas)",
    "eliminacion_solicitada": "El vecino pidió eliminar su reporte (con motivo)",
    "eliminacion_cancelada": "El vecino retiró su solicitud de eliminación",
    "eliminacion_aprobada": "El funcionario aprobó y el reporte se eliminó",
    "reporte_eliminado": "Un funcionario eliminó directamente un reporte propio",
    "eliminacion_rechazada": "El funcionario rechazó la solicitud: el reporte se mantiene",
    "estado_cambiado": "Un funcionario cambió el estado de un reporte",
    "config_remota_aplicada": "Llegaron textos desde la configuración remota",
}

# Solo estos tipos se pueden guardar en JSON sin convertir.
TIPOS_SIMPLES = (str, int, float, bool, type(None))


def ahora_iso() -> str:
    """Fecha y hora actual en ISO 8601 con zona horaria.
    Ej: '2026-11-11T19:30:05-03:00'. Se ordena como texto y se compara."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


def limpiar_datos(datos) -> dict:
    """Deja el diccionario listo para JSON: claves como texto y valores
    simples. Un objeto que JSON no entiende (ej. un widget de Kivy) se
    guarda como texto en vez de hacer fallar el registro."""
    if not isinstance(datos, dict):
        return {}
    limpio = {}
    for clave, valor in datos.items():
        limpio[str(clave)] = valor if isinstance(valor, TIPOS_SIMPLES) else str(valor)
    return limpio


class Evento:
    """Un registro de analítica."""

    def __init__(
        self,
        nombre: str,
        datos: dict | None = None,
        usuario_id: int | None = None,
        sesion_id: str | None = None,
        timestamp: str | None = None,
    ) -> None:
        if nombre not in CATALOGO_EVENTOS:
            raise ValueError(f"Evento no declarado en el catálogo: '{nombre}'")
        self.nombre = nombre
        self.timestamp = timestamp or ahora_iso()
        self.datos = limpiar_datos(datos)
        self.usuario_id = usuario_id
        self.sesion_id = sesion_id

    def momento(self) -> datetime:
        """El timestamp convertido a datetime (para restar fechas)."""
        return datetime.fromisoformat(self.timestamp)

    def to_dict(self) -> dict:
        return {
            "evento": self.nombre,
            "timestamp": self.timestamp,
            "usuario_id": self.usuario_id,
            "sesion_id": self.sesion_id,
            "datos": self.datos,
        }

    @classmethod
    def from_dict(cls, registro: dict) -> "Evento":
        return cls(
            nombre=registro["evento"],
            datos=registro.get("datos"),
            usuario_id=registro.get("usuario_id"),
            sesion_id=registro.get("sesion_id"),
            timestamp=registro["timestamp"],
        )

    def __str__(self) -> str:
        return f"Evento({self.nombre} @ {self.timestamp})"
