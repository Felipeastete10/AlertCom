# =============================================================================
# AlertCom - Filtro por gravedad (historial y pantalla de confirmación)
# =============================================================================
# Una fila de pastillas: "Todas", "Leve", "Moderado", "Grave", "Crítico".
# Cada una con el color de su gravedad y la cantidad de reportes entre
# paréntesis. Tocar una filtra la lista; tocarla de nuevo vuelve a "Todas".
#
# Uso:
#     filtro = FiltroGravedad(contenedor, al_cambiar=self.cargar_lista)
#     filtro.actualizar(reportes)          # cuenta y redibuja
#     visibles = filtro.aplicar(reportes)  # deja solo la gravedad elegida
# =============================================================================

from config import GRAVEDADES
from views.componentes.estilos import ESTILO_GRAVEDAD
from views.componentes.interaccion import NARANJA, Pastilla

# De la más urgente a la más leve (orden de la pantalla de confirmación)
PRIORIDAD_GRAVEDAD = {gravedad: i for i, gravedad in enumerate(reversed(GRAVEDADES))}


class FiltroGravedad:
    def __init__(self, contenedor, al_cambiar) -> None:
        self.elegida: str | None = None   # None = todas
        self._al_cambiar = al_cambiar
        self._pastillas: dict = {}
        opciones = [(None, "Todas", "filter-variant", NARANJA)]
        opciones += [(g, g, *ESTILO_GRAVEDAD.get(g, ("gauge", NARANJA))) for g in GRAVEDADES]
        for valor, texto, icono, color in opciones:
            pastilla = Pastilla(compacta=True)
            pastilla.texto, pastilla.icono, pastilla.color = texto, icono, color
            pastilla.bind(on_release=lambda _p, v=valor: self.elegir(v))
            contenedor.add_widget(pastilla)
            self._pastillas[valor] = (pastilla, texto)
        self._marcar()

    def elegir(self, gravedad) -> None:
        self.elegida = None if gravedad == self.elegida else gravedad
        self._marcar()
        self._al_cambiar()

    def reiniciar(self) -> None:
        self.elegida = None
        self._marcar()

    def _marcar(self) -> None:
        for valor, (pastilla, _texto) in self._pastillas.items():
            pastilla.seleccionada = valor == self.elegida

    def actualizar(self, reportes) -> None:
        """Pone la cantidad de cada gravedad en su pastilla."""
        for valor, (pastilla, texto) in self._pastillas.items():
            cantidad = len(reportes) if valor is None else sum(r.gravedad == valor for r in reportes)
            pastilla.texto = f"{texto} {cantidad}"

    def aplicar(self, reportes) -> list:
        if self.elegida is None:
            return list(reportes)
        return [r for r in reportes if r.gravedad == self.elegida]
