# =============================================================================
# AlertCom - Análisis de eventos en el computador (RA3 · método MJV App)
# =============================================================================
# Lee el registro de eventos (eventos.jsonl) que genera la app, filtra el
# PERIODO DE RECOLECCIÓN declarado y calcula los 3 KPIs y las métricas.
# Además genera, en analitica/resultados/:
#   • resumen.md      → tablas listas para pegar en el Informe Final
#   • eventos.csv     → los eventos en una planilla (para Excel)
#   • 01…05_*.png     → gráficos para la presentación y el informe
#
# El análisis se hace AQUÍ, en el PC, y no dentro del APK: matplotlib es
# pesado y el teléfono no lo necesita. Los cálculos son los MISMOS que ve el
# funcionario en la pantalla Métricas (controllers/analitica.py).
#
# Uso (desde la carpeta AlertCom, con el entorno activado):
#   pip install -r requirements-analisis.txt
#   python analitica/analitica_proyecto.py --desde 2026-11-12 --hasta 2026-11-15
#
# Opciones:
#   --datos  archivo .jsonl o carpeta con eventos*.jsonl
#            (por defecto: estructura_AlertCom/datos)
#   --desde / --hasta   periodo de recolección (AAAA-MM-DD, ambos incluidos)
#   --salida carpeta de resultados (por defecto: analitica/resultados)
# =============================================================================

import argparse
import csv
import json
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "estructura_AlertCom"))

from controllers import analitica  # noqa: E402  (mismo código que usa la app)

# Paleta de referencia (modo claro): un color por serie, texto en tinta neutra
FONDO = "#fcfcfb"
TINTA = "#0b0b0b"
TINTA_SUAVE = "#52514e"
GRILLA = "#e4e3df"
AZUL = "#2a78d6"


# -----------------------------------------------------------------------------
# Entrada
# -----------------------------------------------------------------------------
def rutas_de_eventos(datos: Path) -> list[Path]:
    if datos.is_file():
        return [datos]
    return sorted(datos.glob("eventos_*.jsonl")) + [datos / "eventos.jsonl"]


def leer_fecha(texto: str | None) -> date | None:
    return date.fromisoformat(texto) if texto else None


# -----------------------------------------------------------------------------
# Salidas de texto
# -----------------------------------------------------------------------------
def numero(valor) -> str:
    if valor is None:
        return "sin datos"
    texto = f"{valor:.1f}".replace(".", ",")
    return texto[:-2] if texto.endswith(",0") else texto


def estado(kpi: dict) -> str:
    return {True: "Cumple la meta", False: "No cumple la meta", None: "Sin datos suficientes"}[kpi["cumple"]]


def imprimir_consola(res: dict, invalidas: int) -> None:
    m = res["metricas"]
    print("=" * 64)
    print("AlertCom · Resultados de la medición (método MJV App)")
    print("=" * 64)
    if res["periodo"]:
        print(f"Periodo con datos: {res['periodo']['desde']} a {res['periodo']['hasta']}")
    print(f"Eventos analizados: {m['total_eventos']}  ·  líneas inválidas omitidas: {invalidas}")
    print(f"Sesiones: {m['sesiones']}  ·  usuarios activos: {m['usuarios_activos']}"
          f"  ·  volvieron otro día: {m['usuarios_recurrentes']}")
    print("-" * 64)
    for kpi in res["kpis"]:
        comparador = "≤" if kpi["unidad"] == "s" else "≥"
        print(f"KPI · {kpi['nombre']}: {numero(kpi['valor'])} {kpi['unidad']}"
              f"  (meta {comparador} {numero(kpi['meta'])} {kpi['unidad']}) → {estado(kpi)}")
        print(f"      {kpi['detalle']}")
    print("-" * 64)
    print(f"Reportes enviados: {m['reportes_enviados']}  ·  rechazados: {m['reportes_rechazados']}"
          f"  ·  logins fallidos: {m['logins_fallidos']}")
    print(f"Eventos por día: {m['eventos_por_dia']}")


def escribir_resumen_md(res: dict, ruta: Path, desde, hasta, invalidas: int) -> None:
    m = res["metricas"]
    lineas = [
        "# AlertCom · Resultados de la medición",
        "",
        f"- **Periodo de recolección declarado:** {desde or 'inicio de los datos'} a {hasta or 'fin de los datos'}",
        f"- **Periodo con datos:** "
        + (f"{res['periodo']['desde']} a {res['periodo']['hasta']}" if res["periodo"] else "sin eventos"),
        f"- **Instrumento:** registro de eventos `eventos.jsonl` generado por la app (JSON Lines)",
        f"- **Eventos analizados:** {m['total_eventos']} (líneas inválidas omitidas: {invalidas})",
        f"- **Sesiones:** {m['sesiones']} · **Usuarios activos:** {m['usuarios_activos']}",
        "",
        "## KPIs",
        "",
        "| KPI | Resultado | Meta | Estado | Detalle |",
        "|---|---|---|---|---|",
    ]
    for kpi in res["kpis"]:
        comparador = "≤" if kpi["unidad"] == "s" else "≥"
        detalle = ", ".join(f"{k.replace('_', ' ')}: {v}" for k, v in kpi["detalle"].items())
        lineas.append(f"| {kpi['nombre']} | {numero(kpi['valor'])} {kpi['unidad']} | "
                      f"{comparador} {numero(kpi['meta'])} {kpi['unidad']} | {estado(kpi)} | {detalle} |")
    lineas += ["", "## Métricas descriptivas", "", "| Métrica | Valor |", "|---|---|"]
    for clave in ("usuarios_recurrentes", "reportes_enviados", "reportes_rechazados", "logins_fallidos"):
        lineas.append(f"| {clave.replace('_', ' ').capitalize()} | {m[clave]} |")
    for titulo, clave in (("Eventos por tipo", "eventos_por_tipo"),
                          ("Pantallas vistas", "pantallas_vistas"),
                          ("Reportes por tipo de daño", "reportes_por_tipo"),
                          ("Reportes por gravedad", "reportes_por_gravedad"),
                          ("Motivos de rechazo del formulario", "motivos_de_rechazo"),
                          ("Eventos por día", "eventos_por_dia")):
        lineas += ["", f"### {titulo}", "", "| Categoría | Cantidad |", "|---|---|"]
        lineas += [f"| {k} | {v} |" for k, v in m[clave].items()] or ["| (sin datos) | 0 |"]
    ruta.write_text("\n".join(lineas) + "\n", encoding="utf-8")


def escribir_csv(eventos: list[dict], ruta: Path) -> None:
    """CSV plano: los 'datos' (diccionario) quedan como texto JSON en una
    columna, porque un CSV no puede guardar estructuras anidadas."""
    with open(ruta, "w", encoding="utf-8-sig", newline="") as archivo:
        escritor = csv.writer(archivo, delimiter=";")
        escritor.writerow(["timestamp", "evento", "usuario_id", "sesion_id", "datos"])
        for e in eventos:
            escritor.writerow([e["timestamp"], e["evento"], e.get("usuario_id"), e.get("sesion_id"),
                               json.dumps(e.get("datos", {}), ensure_ascii=False)])


# -----------------------------------------------------------------------------
# Gráficos
# -----------------------------------------------------------------------------
def preparar_estilo(plt) -> None:
    plt.rcParams.update({
        "figure.facecolor": FONDO, "axes.facecolor": FONDO, "savefig.facecolor": FONDO,
        "axes.edgecolor": GRILLA, "axes.labelcolor": TINTA_SUAVE, "text.color": TINTA,
        "xtick.color": TINTA_SUAVE, "ytick.color": TINTA_SUAVE, "font.size": 11,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": GRILLA, "grid.linewidth": 0.8,
        "axes.titleweight": "bold", "axes.titlesize": 13, "axes.titlelocation": "left",
        "axes.axisbelow": True,  # la grilla queda detrás de las barras
    })


def barras_horizontales(plt, datos: dict, titulo: str, subtitulo: str, ruta: Path, etiqueta_x: str) -> None:
    fig, ax = plt.subplots(figsize=(8, 0.6 * max(len(datos), 2) + 1.6))
    if not datos:
        ax.text(0.5, 0.5, "Sin datos en el periodo", ha="center", va="center", color=TINTA_SUAVE)
        ax.set_axis_off()
    else:
        nombres = list(datos)[::-1]
        valores = [datos[n] for n in nombres]
        barras = ax.barh(nombres, valores, color=AZUL, height=0.55)
        ax.bar_label(barras, padding=4, color=TINTA, fontsize=10)
        ax.grid(axis="y", visible=False)
        ax.set_xlabel(etiqueta_x)
        ax.set_xlim(0, max(valores) * 1.18 or 1)
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))  # conteos: sin decimales
    ax.set_title(titulo)
    fig.text(0.01, 0.01, subtitulo, color=TINTA_SUAVE, fontsize=9)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(ruta, dpi=160)
    plt.close(fig)


def graficar(res: dict, eventos: list[dict], carpeta: Path, periodo_txt: str) -> list[Path]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    global MaxNLocator
    from matplotlib.ticker import MaxNLocator

    preparar_estilo(plt)
    m = res["metricas"]
    rutas = []

    # 1 · Sesiones por día (uso a lo largo del periodo)
    sesiones_por_dia: dict[str, int] = {}
    for e in eventos:
        if e["evento"] == "app_abierta":
            dia = e["timestamp"][:10]
            sesiones_por_dia[dia] = sesiones_por_dia.get(dia, 0) + 1
    fig, ax = plt.subplots(figsize=(8, 3.6))
    if sesiones_por_dia:
        dias = sorted(sesiones_por_dia)
        barras = ax.bar([d[5:] for d in dias], [sesiones_por_dia[d] for d in dias], color=AZUL, width=0.6)
        ax.bar_label(barras, padding=3, fontsize=10)
        ax.grid(axis="x", visible=False)
        ax.set_ylabel("Sesiones")
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    else:
        ax.text(0.5, 0.5, "Sin sesiones en el periodo", ha="center", va="center", color=TINTA_SUAVE)
        ax.set_axis_off()
    ax.set_title("Sesiones por día (aperturas de la app)")
    fig.text(0.01, 0.01, periodo_txt, color=TINTA_SUAVE, fontsize=9)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    rutas.append(carpeta / "01_sesiones_por_dia.png")
    fig.savefig(rutas[-1], dpi=160)
    plt.close(fig)

    # 2 · Embudo del flujo principal
    k1 = res["kpis"][0]["detalle"]
    embudo = {"Abrieron el formulario": k1["iniciados"], "Enviaron el reporte": k1["enviados"]}
    rutas.append(carpeta / "02_embudo_reporte.png")
    barras_horizontales(plt, embudo if k1["iniciados"] else {},
                        "Embudo del reporte: de abrir el formulario a enviarlo",
                        f"{periodo_txt} · abandonos: {k1['abandonados']}", rutas[-1], "Cantidad de veces")

    # 3 · KPIs frente a su meta (un panel por KPI: unidades distintas, sin doble eje)
    fig, ejes = plt.subplots(1, 3, figsize=(10, 3.6))
    for ax, kpi in zip(ejes, res["kpis"]):
        valor = kpi["valor"] or 0
        tope = max(valor, kpi["meta"]) * 1.25
        ax.bar([0], [valor], color=AZUL, width=0.5)
        ax.axhline(kpi["meta"], color=TINTA_SUAVE, linestyle="--", linewidth=1.2)
        ax.text(1.0, kpi["meta"], f"meta {numero(kpi['meta'])} {kpi['unidad']}",
                va="bottom", ha="right", fontsize=9, color=TINTA_SUAVE)
        ax.text(0, valor + tope * 0.02, f"{numero(kpi['valor'])} {kpi['unidad']}",
                ha="center", va="bottom", fontsize=12, fontweight="bold")
        ax.set_xlim(-0.5, 1.05)
        ax.set_ylim(0, tope)
        ax.set_xticks([])
        ax.grid(axis="x", visible=False)
        ax.set_title(kpi["nombre"], fontsize=10)
        ax.set_xlabel(estado(kpi), fontsize=10, color=TINTA)
    fig.suptitle("KPIs frente a su meta", x=0.01, ha="left", fontweight="bold")
    fig.text(0.01, 0.01, periodo_txt, color=TINTA_SUAVE, fontsize=9)
    fig.tight_layout(rect=(0, 0.05, 1, 0.94))
    rutas.append(carpeta / "03_kpis_vs_meta.png")
    fig.savefig(rutas[-1], dpi=160)
    plt.close(fig)

    # 4 · Reportes por tipo de daño
    rutas.append(carpeta / "04_reportes_por_tipo.png")
    barras_horizontales(plt, m["reportes_por_tipo"], "Reportes enviados por tipo de daño",
                        periodo_txt, rutas[-1], "Reportes")

    # 5 · Errores: dónde se traba el usuario
    errores = {f"Formulario: {k.replace('_', ' ')}": v for k, v in m["motivos_de_rechazo"].items()}
    if m["logins_fallidos"]:
        errores["Inicio de sesión fallido"] = m["logins_fallidos"]
    errores = dict(sorted(errores.items(), key=lambda par: par[1], reverse=True))
    rutas.append(carpeta / "05_errores.png")
    barras_horizontales(plt, errores, "Errores del usuario por motivo", periodo_txt, rutas[-1], "Veces")
    return rutas


# -----------------------------------------------------------------------------
# Programa
# -----------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description="Analiza eventos.jsonl de AlertCom")
    parser.add_argument("--datos", default=str(RAIZ / "estructura_AlertCom" / "datos"))
    parser.add_argument("--desde")
    parser.add_argument("--hasta")
    parser.add_argument("--salida", default=str(RAIZ / "analitica" / "resultados"))
    parser.add_argument("--sin-graficos", action="store_true", help="solo consola, resumen y CSV")
    args = parser.parse_args()

    desde, hasta = leer_fecha(args.desde), leer_fecha(args.hasta)
    eventos, invalidas = analitica.cargar_eventos(rutas_de_eventos(Path(args.datos)))
    eventos = analitica.filtrar_periodo(eventos, desde, hasta)
    if not eventos:
        print("No hay eventos en ese periodo. Revisa --datos, --desde y --hasta.")
        return 1

    res = analitica.resumen(eventos)
    salida = Path(args.salida)
    salida.mkdir(parents=True, exist_ok=True)
    periodo_txt = f"Periodo: {res['periodo']['desde']} a {res['periodo']['hasta']} · {len(eventos)} eventos"

    imprimir_consola(res, invalidas)
    escribir_resumen_md(res, salida / "resumen.md", desde, hasta, invalidas)
    escribir_csv(eventos, salida / "eventos.csv")
    archivos = ["resumen.md", "eventos.csv"]
    if not args.sin_graficos:
        archivos += [r.name for r in graficar(res, eventos, salida, periodo_txt)]
    print("-" * 64)
    print(f"Archivos generados en {salida}: {', '.join(archivos)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
