# =============================================================================
# AlertCom - Controlador: Autenticación de Usuarios
# =============================================================================
# Valida credenciales contra usuarios.json, registra cuentas nuevas y guarda
# quién tiene la sesión abierta.
#
# Reglas:
#   • NO navega entre pantallas (eso lo hace views/navegador.py).
#   • NO importa Kivy: solo responde (exito, mensaje_de_error).
#   • NO guarda contraseñas en texto plano (ver models/usuario.py).
#   • Registra eventos de analítica (login_exitoso, login_fallido…) sin
#     guardar nunca el correo: solo el id numérico del usuario.
#   • Gestor de cuenta: cambiar nombre, correo o contraseña y eliminar la
#     cuenta. Los cambios sensibles piden la contraseña ACTUAL.
# =============================================================================

import logging
import re

from config import MAX_CARACTERES_NOMBRE, USUARIOS_DEMO
from controllers.almacenamiento_json import AlmacenamientoJSON
from controllers.registro_eventos import RegistroEventos, RegistroNulo
from models.usuario import Usuario

log = logging.getLogger("alertcom.auth")

PATRON_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
LARGO_MIN_CONTRASENA = 6
MENSAJE_CREDENCIALES = "Correo o contraseña incorrectos. Intenta nuevamente."


class AuthController:
    """Inicio de sesión, registro y cierre de sesión."""

    def __init__(
        self,
        almacenamiento: AlmacenamientoJSON,
        eventos: RegistroEventos | None = None,
    ) -> None:
        self.almacenamiento = almacenamiento
        self.eventos = eventos or RegistroNulo()
        self.usuarios: list[Usuario] = self._cargar_usuarios()
        self.usuario_actual: Usuario | None = None

    # ------------------------------------------------------------------
    # Persistencia
    # ------------------------------------------------------------------
    def _cargar_usuarios(self) -> list[Usuario]:
        registros = self.almacenamiento.cargar()

        if not registros:
            # Instalación nueva: se crean las cuentas demo y se guardan.
            log.info("Creando usuarios.json con las cuentas de demostración.")
            registros = [dict(u) for u in USUARIOS_DEMO]
            self.almacenamiento.guardar(registros)

        usuarios = []
        faltaba_uid = False
        for datos in registros:
            try:
                if not datos.get("uid"):
                    # Cuenta de una versión anterior: las demo reciben su uid
                    # fijo (igual en todos los teléfonos); el resto, uno nuevo.
                    demo = next((d for d in USUARIOS_DEMO if d["email"] == datos.get("email")), None)
                    datos = {**datos, "uid": demo["uid"] if demo else None}
                    faltaba_uid = True
                usuarios.append(Usuario.from_dict(datos))
            except (KeyError, ValueError, TypeError) as error:
                log.warning("Usuario inválido en JSON, se omite: %s", error)
        if faltaba_uid:
            self.almacenamiento.guardar([u.to_dict() for u in usuarios])
        return usuarios

    def _guardar_usuarios(self) -> None:
        self.almacenamiento.guardar([u.to_dict() for u in self.usuarios])

    def _buscar_por_email(self, email: str) -> Usuario | None:
        email = email.strip().lower()
        return next((u for u in self.usuarios if u.email == email), None)

    # ------------------------------------------------------------------
    # Casos de uso
    # ------------------------------------------------------------------
    def iniciar_sesion(self, correo: str, contrasena: str) -> tuple[bool, str | None]:
        """
        Returns:
            (True, None) si las credenciales son válidas.
            (False, mensaje) si no lo son. El mensaje es genérico a propósito:
            no revela si el correo existe.
        """
        if not correo.strip() or not contrasena:
            self.eventos.registrar("login_fallido", {"motivo": "campos_vacios"})
            return False, "Ingresa tu correo y tu contraseña."

        usuario = self._buscar_por_email(correo)
        if usuario is None or not usuario.verificar_contrasena(contrasena):
            log.info("Intento de inicio de sesión fallido.")
            self.eventos.registrar("login_fallido", {"motivo": "credenciales"})
            return False, MENSAJE_CREDENCIALES

        self.usuario_actual = usuario
        self.eventos.asignar_usuario(usuario.id_usuario)
        self.eventos.registrar("login_exitoso", {"rol": usuario.rol})
        log.info("Sesión iniciada (usuario id=%s).", usuario.id_usuario)
        return True, None

    def registrar(
        self, nombre: str, correo: str, contrasena: str, confirmacion: str
    ) -> tuple[bool, str | None]:
        """Crea una cuenta de vecino, la guarda en usuarios.json y abre sesión."""
        nombre = nombre.strip()
        correo = correo.strip().lower()

        # (motivo para la analítica, mensaje para la persona)
        error = None
        if not nombre or not correo or not contrasena:
            error = ("campos_vacios", "Completa nombre, correo y contraseña.")
        elif not PATRON_EMAIL.match(correo):
            error = ("correo_invalido", "El correo no tiene un formato válido.")
        elif len(contrasena) < LARGO_MIN_CONTRASENA:
            error = ("clave_corta", f"La contraseña debe tener al menos {LARGO_MIN_CONTRASENA} caracteres.")
        elif contrasena != confirmacion:
            error = ("claves_distintas", "Las contraseñas no coinciden.")
        elif self._buscar_por_email(correo) is not None:
            error = ("correo_duplicado", "Ya existe una cuenta con ese correo.")
        if error:
            self.eventos.registrar("registro_fallido", {"motivo": error[0]})
            return False, error[1]

        nuevo_id = max((u.id_usuario for u in self.usuarios), default=0) + 1
        usuario = Usuario.crear(nuevo_id, nombre, correo, contrasena, rol="vecino")
        self.usuarios.append(usuario)
        self._guardar_usuarios()

        self.usuario_actual = usuario
        self.eventos.asignar_usuario(nuevo_id)
        self.eventos.registrar("registro_exitoso")
        log.info("Cuenta creada (usuario id=%s).", nuevo_id)
        return True, None

    def cerrar_sesion(self) -> None:
        if self.usuario_actual is not None:
            self.eventos.registrar("sesion_cerrada")
        self.eventos.asignar_usuario(None)
        self.usuario_actual = None

    def esta_autenticado(self) -> bool:
        return self.usuario_actual is not None

    # ------------------------------------------------------------------
    # Gestor de cuenta (todas devuelven (exito, mensaje))
    # ------------------------------------------------------------------
    def _verificar_actual(self, contrasena: str) -> str | None:
        """Mensaje de error, o None si hay sesión y la contraseña es correcta."""
        if self.usuario_actual is None:
            return "Primero inicia sesión."
        if not contrasena or not self.usuario_actual.verificar_contrasena(contrasena):
            return "La contraseña actual no es correcta."
        return None

    def _cambio_guardado(self, campo: str, mensaje: str) -> tuple[bool, str]:
        self._guardar_usuarios()
        self.eventos.registrar("cuenta_actualizada", {"campo": campo})  # nunca el valor nuevo
        log.info("Cuenta actualizada: %s (usuario id=%s).", campo, self.usuario_actual.id_usuario)
        return True, mensaje

    def cambiar_nombre(self, nombre: str) -> tuple[bool, str]:
        nombre = " ".join((nombre or "").split())
        if self.usuario_actual is None:
            return False, "Primero inicia sesión."
        if not nombre:
            return False, "Escribe tu nombre."
        if len(nombre) > MAX_CARACTERES_NOMBRE:
            return False, f"El nombre no puede superar {MAX_CARACTERES_NOMBRE} caracteres."
        self.usuario_actual.actualizar_perfil(nombre=nombre)
        return self._cambio_guardado("nombre", "Nombre actualizado.")

    def cambiar_correo(self, correo_nuevo: str, contrasena_actual: str) -> tuple[bool, str]:
        correo_nuevo = (correo_nuevo or "").strip().lower()
        error = self._verificar_actual(contrasena_actual)
        if error is None:
            if not PATRON_EMAIL.match(correo_nuevo):
                error = "El correo no tiene un formato válido."
            elif correo_nuevo == self.usuario_actual.email:
                error = "Ese ya es tu correo."
            elif self._buscar_por_email(correo_nuevo) is not None:
                error = "Ya existe una cuenta con ese correo."
        if error:
            return False, error
        self.usuario_actual.email = correo_nuevo
        return self._cambio_guardado("correo", "Correo actualizado. Úsalo la próxima vez que entres.")

    def cambiar_contrasena(self, actual: str, nueva: str, confirmacion: str) -> tuple[bool, str]:
        error = self._verificar_actual(actual)
        if error is None:
            if len(nueva or "") < LARGO_MIN_CONTRASENA:
                error = f"La nueva contraseña debe tener al menos {LARGO_MIN_CONTRASENA} caracteres."
            elif nueva != confirmacion:
                error = "Las contraseñas nuevas no coinciden."
            elif nueva == actual:
                error = "La nueva contraseña debe ser distinta de la actual."
        if error:
            return False, error
        usuario = self.usuario_actual
        nuevo = Usuario.crear(usuario.id_usuario, usuario.nombre, usuario.email, nueva,
                              rol=usuario.rol, comuna=usuario.comuna, uid=usuario.uid)
        usuario.sal, usuario.hash_contrasena = nuevo.sal, nuevo.hash_contrasena  # sal nueva
        return self._cambio_guardado("contrasena", "Contraseña actualizada.")

    def eliminar_cuenta(self, contrasena_actual: str) -> tuple[bool, str]:
        """Borra la cuenta y cierra la sesión. Los reportes NO se borran aquí:
        la vista le pide al IncidenteController que los desvincule."""
        error = self._verificar_actual(contrasena_actual)
        if error:
            return False, error
        usuario = self.usuario_actual
        self.usuarios = [u for u in self.usuarios if u.id_usuario != usuario.id_usuario]
        self._guardar_usuarios()
        self.eventos.registrar("cuenta_eliminada")
        self.eventos.asignar_usuario(None)
        self.usuario_actual = None
        log.info("Cuenta eliminada (usuario id=%s).", usuario.id_usuario)
        return True, "Tu cuenta fue eliminada."
