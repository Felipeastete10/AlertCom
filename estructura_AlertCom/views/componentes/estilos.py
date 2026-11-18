# =============================================================================
# AlertCom - Colores e íconos compartidos (un solo lugar, siempre los mismos)
# =============================================================================

COLOR_ESTADO = {
    "Pendiente": [0.9, 0.28, 0.28, 1],
    "En revisión": [0.96, 0.62, 0.04, 1],
    "Reparado": [0.2, 0.66, 0.33, 1],
}
ICONO_ESTADO = {
    "Pendiente": "alert-circle",
    "En revisión": "clock-outline",
    "Reparado": "check-circle",
}
# Íconos de cada tipo de daño (si se agrega un tipo en config.py, usa uno genérico)
ICONO_TIPO = {
    "Bache": "road-variant",
    "Hoyo": "circle-slice-8",
    "Grieta": "lightning-bolt-outline",
    "Hundimiento": "arrow-collapse-down",
    "Pavimento roto": "texture-box",
}
# Cada gravedad con su color: de verde (leve) a rojo (crítico)
ESTILO_GRAVEDAD = {
    "Leve": ("gauge-low", [0.2, 0.66, 0.33, 1]),
    "Moderado": ("gauge", [0.96, 0.62, 0.04, 1]),
    "Grave": ("gauge-full", [1, 0.45, 0.1, 1]),
    "Crítico": ("alert-octagon", [0.9, 0.28, 0.28, 1]),
}
GRIS = [0.6, 0.6, 0.6, 1]
# Reporte nuevo que espera la revisión del municipio (aún no es público)
COLOR_POR_CONFIRMAR = [0.62, 0.66, 1, 1]
ICONO_POR_CONFIRMAR = "shield-search"
