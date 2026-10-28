# =============================================================================
# AlertCom - Capa de Vistas (MVC)
# =============================================================================
# Única capa que maneja la interfaz gráfica:
#   • kv/            → diseño declarativo de cada pantalla
#   • pantallas/     → clases MDScreen (qué pasa al tocar algo)
#   • componentes/   → piezas reutilizables (diálogos, avisos)
#   • navegador.py   → cambio de pantalla y rutas protegidas
#   • gestor_pantallas.py → arma el ScreenManager
# Las vistas solo muestran datos y capturan eventos; las reglas de negocio
# viven en controllers/.
# =============================================================================

from views.gestor_pantallas import crear_gestor_pantallas

__all__ = ["crear_gestor_pantallas"]
