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
# =============================================================================

import logging
import re

from config import USUARIOS_DEMO
from controllers.almacenamiento_json import AlmacenamientoJSON
from models.usuario import Usuario

log = logging.getLogger("alertcom.auth")

PATRON_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
LARGO_MIN_CONTRASENA = 6
MENSAJE_CREDENCIALES = "Correo o contraseña incorrectos. Intenta nuevamente."


class AuthController:
    """Inicio de sesión, registro y cierre de sesión."""

    def __init__(self, almacenamiento: AlmacenamientoJSON) -> None:
        self.almacenamiento = almacenamiento
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
        for datos in registros:
            try:
                usuarios.append(Usuario.from_dict(datos))
            except (KeyError, ValueError, TypeError) as error:
                log.warning("Usuario inválido en JSON, se omite: %s", error)
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
            return False, "Ingresa tu correo y tu contraseña."

        usuario = self._buscar_por_email(correo)
        if usuario is None or not usuario.verificar_contrasena(contrasena):
            log.info("Intento de inicio de sesión fallido.")
            return False, MENSAJE_CREDENCIALES

        self.usuario_actual = usuario
        log.info("Sesión iniciada (usuario id=%s).", usuario.id_usuario)
        return True, None

    def registrar(
        self, nombre: str, correo: str, contrasena: str, confirmacion: str
    ) -> tuple[bool, str | None]:
        """Crea una cuenta de vecino, la guarda en usuarios.json y abre sesión."""
        nombre = nombre.strip()
        correo = correo.strip().lower()

        if not nombre or not correo or not contrasena:
            return False, "Completa nombre, correo y contraseña."
        if not PATRON_EMAIL.match(correo):
            return False, "El correo no tiene un formato válido."
        if len(contrasena) < LARGO_MIN_CONTRASENA:
            return False, f"La contraseña debe tener al menos {LARGO_MIN_CONTRASENA} caracteres."
        if contrasena != confirmacion:
            return False, "Las contraseñas no coinciden."
        if self._buscar_por_email(correo) is not None:
            return False, "Ya existe una cuenta con ese correo."

        nuevo_id = max((u.id_usuario for u in self.usuarios), default=0) + 1
        usuario = Usuario.crear(nuevo_id, nombre, correo, contrasena, rol="vecino")
        self.usuarios.append(usuario)
        self._guardar_usuarios()

        self.usuario_actual = usuario
        log.info("Cuenta creada (usuario id=%s).", nuevo_id)
        return True, None

    def cerrar_sesion(self) -> None:
        self.usuario_actual = None

    def esta_autenticado(self) -> bool:
        return self.usuario_actual is not None
