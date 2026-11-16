# =============================================================================
# AlertCom - Analítica: de los eventos a las métricas y KPIs (RA3)
# =============================================================================
# Funciones puras (sin Kivy, sin red): reciben la lista de eventos y
# devuelven números. Las usan dos lugares:
#   • La pantalla "Métricas" de la app (para el funcionario municipal).
#   • El script analitica/analitica_proyecto.py en el computador, que además
#     dibuja los gráficos del informe.
#
# MÉTRICA = dato descriptivo (cuántos eventos, cuántas sesiones…).
# KPI     = métrica elegida porque mide si la app resuelve el problema
#           diagnosticado en el RA1. Elegimos solo 3 (ver DOCUMENTATION.md).
# =============================================================================

import json
import logging
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from statistics import median

log = logging.getLogger("alertcom.analitica")

# Metas de cada KPI (decididas por el equipo a partir del diagnóstico)
META_FINALIZACION = 80.0   # % de formularios abiertos que terminan en reporte
META_TIEMPO = 60.0         # segundos (mediana) para completar un reporte
META_SEGUIMIENTO = 50.0    # % de vecinos que reportan y luego revisan su historial


# -----------------------------------------------------------------------------
# Cargar
# -----------------------------------------------------------------------------
def cargar_eventos(rutas) -> tuple[list[dict], int]:
    """Lee uno o varios archivos JSON Lines.
    Devuelve (eventos ordenados por fecha, cantidad de líneas inválidas).
    Una línea dañada (ej. un corte a mitad de escritura) se salta, no detiene."""
    eventos, invalidas = [], 0
    for ruta in rutas:
        try:
            with open(ruta, "r", encoding="utf-8") as archivo:
                for linea in archivo:
                    if not linea.strip():
                        continue
                    try:
                        registro = json.loads(linea)
                        datetime.fromisoformat(registro["timestamp"])
                        registro["evento"]
                    except (ValueError, KeyError, TypeError):
                        invalidas += 1
                        continue
                    eventos.append(registro)
        except FileNotFoundError:
            log.info("No existe %s todavía.", ruta)
    eventos.sort(key=lambda e: e["timestamp"])
    return eventos, invalidas


def filtrar_periodo(eventos: list[dict], desde: date | None = None, hasta: date | None = None) -> list[dict]:
    """Deja solo los eventos del periodo de recolección declarado (ambos días incluidos)."""
    resultado = []
    for e in eventos:
        dia = _momento(e).date()
        if (desde is None or dia >= desde) and (hasta is None or dia <= hasta):
            resultado.append(e)
    return resultado


def _momento(evento: dict) -> datetime:
    return datetime.fromisoformat(evento["timestamp"])


def _de_tipo(eventos: list[dict], nombre: str) -> list[dict]:
    return [e for e in eventos if e.get("evento") == nombre]


# -----------------------------------------------------------------------------
# KPI 1 · Tasa de finalización del reporte
# -----------------------------------------------------------------------------
def kpi_finalizacion(eventos: list[dict]) -> dict:
    """reporte_enviado / reporte_iniciado × 100.
    Responde al RA1 ("no sé dónde reportar"): si el formulario se abre pero
    no se termina, la app tampoco está resolviendo el problema."""
    iniciados = len(_de_tipo(eventos, "reporte_iniciado"))
    enviados = len(_de_tipo(eventos, "reporte_enviado"))
    valor = round(min(enviados / iniciados, 1) * 100, 1) if iniciados else None
    return {
        "nombre": "Tasa de finalización del reporte",
        "valor": valor,
        "unidad": "%",
        "meta": META_FINALIZACION,
        "cumple": None if valor is None else valor >= META_FINALIZACION,
        "detalle": {"iniciados": iniciados, "enviados": enviados,
                    "abandonados": max(iniciados - enviados, 0)},
    }


# -----------------------------------------------------------------------------
# KPI 2 · Tiempo mediano para reportar
# -----------------------------------------------------------------------------
def duraciones_reporte(eventos: list[dict]) -> list[float]:
    """Segundos entre abrir el formulario y enviarlo, dentro de la misma sesión.
    Se usa el último reporte_iniciado anterior a cada reporte_enviado."""
    inicio_por_sesion: dict[str, datetime] = {}
    duraciones = []
    for e in eventos:  # ya vienen ordenados por timestamp
        sesion = e.get("sesion_id")
        if e.get("evento") == "reporte_iniciado":
            inicio_por_sesion[sesion] = _momento(e)
        elif e.get("evento") == "reporte_enviado" and sesion in inicio_por_sesion:
            segundos = (_momento(e) - inicio_por_sesion.pop(sesion)).total_seconds()
            if segundos >= 0:
                duraciones.append(segundos)
    return duraciones


def kpi_tiempo_reporte(eventos: list[dict]) -> dict:
    """Mediana de segundos para completar un reporte.
    Responde al RA1: el 70 % se moviliza en auto o micro; reportar debe ser
    rápido. Usamos la mediana porque un reporte olvidado abierto 10 minutos
    no debe distorsionar el resultado (el promedio sí se distorsiona)."""
    duraciones = duraciones_reporte(eventos)
    valor = round(median(duraciones), 1) if duraciones else None
    return {
        "nombre": "Tiempo mediano para reportar",
        "valor": valor,
        "unidad": "s",
        "meta": META_TIEMPO,
        "cumple": None if valor is None else valor <= META_TIEMPO,
        "detalle": {"reportes_medidos": len(duraciones)},
    }


# -----------------------------------------------------------------------------
# KPI 3 · Tasa de seguimiento
# -----------------------------------------------------------------------------
def kpi_seguimiento(eventos: list[dict]) -> dict:
    """Vecinos que, después de enviar un reporte, entran a su historial ÷
    vecinos que enviaron al menos un reporte × 100.
    Responde al RA1: las encuestas mostraron que el seguimiento es muy
    importante; si nadie revisa el historial, esa parte no está sirviendo."""
    primer_envio: dict[int, datetime] = {}
    for e in _de_tipo(eventos, "reporte_enviado"):
        usuario = e.get("usuario_id")
        if usuario is not None and usuario not in primer_envio:
            primer_envio[usuario] = _momento(e)

    con_seguimiento = set()
    for e in _de_tipo(eventos, "pantalla_vista"):
        usuario = e.get("usuario_id")
        if (e.get("datos", {}).get("pantalla") == "history"
                and usuario in primer_envio and _momento(e) >= primer_envio[usuario]):
            con_seguimiento.add(usuario)

    reportantes = len(primer_envio)
    valor = round(len(con_seguimiento) / reportantes * 100, 1) if reportantes else None
    return {
        "nombre": "Tasa de seguimiento",
        "valor": valor,
        "unidad": "%",
        "meta": META_SEGUIMIENTO,
        "cumple": None if valor is None else valor >= META_SEGUIMIENTO,
        "detalle": {"vecinos_que_reportaron": reportantes,
                    "vecinos_que_revisaron": len(con_seguimiento)},
    }


# -----------------------------------------------------------------------------
# Métricas descriptivas
# -----------------------------------------------------------------------------
def metricas(eventos: list[dict]) -> dict:
    enviados = _de_tipo(eventos, "reporte_enviado")
    rechazados = _de_tipo(eventos, "reporte_rechazado")
    return {
        "total_eventos": len(eventos),
        "sesiones": len({e.get("sesion_id") for e in _de_tipo(eventos, "app_abierta")}),
        "usuarios_activos": len({e.get("usuario_id") for e in eventos if e.get("usuario_id") is not None}),
        "usuarios_recurrentes": usuarios_recurrentes(eventos),
        "reportes_enviados": len(enviados),
        "reportes_rechazados": len(rechazados),
        "logins_fallidos": len(_de_tipo(eventos, "login_fallido")),
        "eventos_por_tipo": dict(Counter(e.get("evento") for e in eventos).most_common()),
        "pantallas_vistas": dict(Counter(
            e.get("datos", {}).get("pantalla") for e in _de_tipo(eventos, "pantalla_vista")
        ).most_common()),
        "reportes_por_tipo": dict(Counter(e.get("datos", {}).get("tipo") for e in enviados).most_common()),
        "reportes_por_gravedad": dict(Counter(e.get("datos", {}).get("gravedad") for e in enviados).most_common()),
        "motivos_de_rechazo": dict(Counter(e.get("datos", {}).get("motivo") for e in rechazados).most_common()),
        "eventos_por_dia": uso_diario(eventos),
    }


def usuarios_recurrentes(eventos: list[dict]) -> int:
    """Retención simple: usuarios con actividad en 2 o más días distintos."""
    dias_por_usuario: dict[int, set] = {}
    for e in eventos:
        usuario = e.get("usuario_id")
        if usuario is not None:
            dias_por_usuario.setdefault(usuario, set()).add(_momento(e).date())
    return sum(1 for dias in dias_por_usuario.values() if len(dias) >= 2)


def uso_diario(eventos: list[dict]) -> dict:
    """{'2026-11-12': 34, ...}: cuántos eventos hubo cada día."""
    por_dia: dict[str, int] = {}
    for e in eventos:
        dia = _momento(e).date().isoformat()
        por_dia[dia] = por_dia.get(dia, 0) + 1
    return por_dia


def resumen(eventos: list[dict]) -> dict:
    """Todo junto: periodo, los 3 KPIs y las métricas."""
    periodo = None
    if eventos:
        periodo = {"desde": _momento(eventos[0]).date().isoformat(),
                   "hasta": _momento(eventos[-1]).date().isoformat()}
    return {
        "periodo": periodo,
        "kpis": [kpi_finalizacion(eventos), kpi_tiempo_reporte(eventos), kpi_seguimiento(eventos)],
        "metricas": metricas(eventos),
    }


def resumen_desde_carpeta(carpeta: Path | str) -> dict:
    """Atajo para la app: lee todos los eventos*.jsonl de la carpeta de datos."""
    carpeta = Path(carpeta)
    rutas = sorted(carpeta.glob("eventos_*.jsonl")) + [carpeta / "eventos.jsonl"]
    eventos, invalidas = cargar_eventos(rutas)
    datos = resumen(eventos)
    datos["lineas_invalidas"] = invalidas
    return datos
