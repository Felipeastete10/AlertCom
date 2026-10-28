# =============================================================================
# AlertCom - Configuración remota y resiliencia de red (Sesión 22)
# =============================================================================
# Descarga un JSON público (GitHub / Gist) con textos de la app para poder
# cambiarlos sin recompilar ni publicar una versión nueva.
#
# Flujo seguro (fallback):
#   1. La app ARRANCA con los valores locales de config.VALORES_POR_DEFECTO.
#   2. En segundo plano se pide el JSON remoto con UrlRequest (asíncrono:
#      la interfaz no se congela mientras espera).
#   3. Si llega bien → se aplican SOLO las claves conocidas y de tipo texto.
#      Si falla la red, el servidor o el JSON → se registra en el log y la
#      app sigue con los valores locales. Nunca queda una variable en None.
# =============================================================================

import json
import logging

log = logging.getLogger("alertcom.config_remota")


def filtrar_config(datos, claves_permitidas, largo_maximo: int) -> dict:
    """
    Deja pasar solo claves conocidas con texto no vacío y de largo razonable.
    Función pura (sin red ni Kivy) para poder probarla fácilmente.
    """
    if not isinstance(datos, dict):
        return {}
    limpio = {}
    for clave in claves_permitidas:
        valor = datos.get(clave)
        if isinstance(valor, str) and valor.strip() and len(valor) <= largo_maximo:
            limpio[clave] = valor.strip()
        elif valor is not None:
            log.warning("Valor remoto ignorado para '%s' (tipo o largo no válido).", clave)
    return limpio


class ConfiguracionRemota:
    """Pide la configuración remota y avisa cuando llega algo válido."""

    def __init__(
        self,
        url: str,
        claves_permitidas,
        al_actualizar,
        timeout: int = 5,
        largo_maximo: int = 160,
    ) -> None:
        self.url = url
        self.claves_permitidas = tuple(claves_permitidas)
        self.al_actualizar = al_actualizar
        self.timeout = timeout
        self.largo_maximo = largo_maximo
        self._peticion = None

    def cargar(self) -> None:
        """Lanza la petición asíncrona. Vuelve de inmediato."""
        if not self.url:
            log.info("Sin URL de configuración remota: se usan valores locales.")
            return

        # Import aquí para que el resto del paquete se pueda probar sin Kivy.
        from kivy.network.urlrequest import UrlRequest

        try:
            import certifi
            certificados = certifi.where()
        except ImportError:
            certificados = None

        log.info("Solicitando configuración remota…")
        self._peticion = UrlRequest(
            self.url,
            on_success=self._al_recibir,
            on_failure=self._al_fallar,
            on_error=self._al_error,
            timeout=self.timeout,
            ca_file=certificados,
            verify=True,
        )

    # --- Callbacks de UrlRequest (Kivy los ejecuta en el hilo principal) ---
    def _al_recibir(self, peticion, resultado) -> None:
        # GitHub "raw" responde como text/plain, así que puede llegar como texto.
        if isinstance(resultado, (bytes, str)):
            try:
                resultado = json.loads(resultado)
            except (ValueError, TypeError):
                log.warning("La configuración remota no es un JSON válido.")
                return

        datos = filtrar_config(resultado, self.claves_permitidas, self.largo_maximo)
        if datos:
            log.info("Configuración remota aplicada: %s", list(datos))
            self.al_actualizar(datos)
        else:
            log.info("La configuración remota no trajo cambios válidos.")

    def _al_fallar(self, peticion, resultado) -> None:
        log.warning("Servidor respondió con error HTTP %s. Se mantienen valores locales.",
                    peticion.resp_status)

    def _al_error(self, peticion, error) -> None:
        log.warning("Sin conexión para la configuración remota (%s). Se mantienen valores locales.",
                    error)
