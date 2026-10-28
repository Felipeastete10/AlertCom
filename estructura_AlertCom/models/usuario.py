# =============================================================================
# AlertCom - Modelo de Dominio: Usuario
# =============================================================================
# Representa a un vecino o funcionario municipal.
# Clase pura de dominio: NO importa Kivy ni nada de la interfaz.
#
# Seguridad: el modelo nunca guarda la contraseña en texto plano.
# Solo guarda una "sal" aleatoria y el hash PBKDF2 de la contraseña.
# =============================================================================

import hashlib
import hmac
import secrets

ITERACIONES_HASH = 120_000
ROLES_VALIDOS = ("vecino", "municipal")


class Usuario:
    """
    Usuario registrado en AlertCom.

    Attributes:
        id_usuario: Identificador único.
        nombre: Nombre para mostrar.
        email: Correo (se guarda en minúsculas).
        rol: "vecino" (reporta) o "municipal" (actualiza estados).
        comuna: Comuna de residencia.
        sal: Texto hexadecimal aleatorio usado para el hash.
        hash_contrasena: Hash PBKDF2-SHA256 de la contraseña.
    """

    def __init__(
        self,
        id_usuario: int,
        nombre: str,
        email: str,
        sal: str,
        hash_contrasena: str,
        rol: str = "vecino",
        comuna: str = "Temuco",
    ) -> None:
        if rol not in ROLES_VALIDOS:
            raise ValueError(f"Rol inválido: '{rol}'")
        self.id_usuario = id_usuario
        self.nombre = nombre
        self.email = email.strip().lower()
        self.sal = sal
        self.hash_contrasena = hash_contrasena
        self.rol = rol
        self.comuna = comuna

    # ------------------------------------------------------------------
    # Contraseñas
    # ------------------------------------------------------------------
    @staticmethod
    def generar_hash(contrasena: str, sal: str) -> str:
        """Calcula el hash PBKDF2 de una contraseña con la sal indicada."""
        return hashlib.pbkdf2_hmac(
            "sha256",
            contrasena.encode("utf-8"),
            bytes.fromhex(sal),
            ITERACIONES_HASH,
        ).hex()

    @classmethod
    def crear(
        cls,
        id_usuario: int,
        nombre: str,
        email: str,
        contrasena: str,
        rol: str = "vecino",
        comuna: str = "Temuco",
    ) -> "Usuario":
        """Crea un usuario nuevo generando su sal y su hash."""
        sal = secrets.token_hex(16)
        return cls(
            id_usuario=id_usuario,
            nombre=nombre.strip(),
            email=email,
            sal=sal,
            hash_contrasena=cls.generar_hash(contrasena, sal),
            rol=rol,
            comuna=comuna,
        )

    def verificar_contrasena(self, contrasena: str) -> bool:
        """Compara en tiempo constante (evita ataques por tiempo de respuesta)."""
        calculado = self.generar_hash(contrasena, self.sal)
        return hmac.compare_digest(calculado, self.hash_contrasena)

    # ------------------------------------------------------------------
    # Reglas de negocio
    # ------------------------------------------------------------------
    @property
    def es_municipal(self) -> bool:
        return self.rol == "municipal"

    @property
    def rol_legible(self) -> str:
        return "Funcionario municipal" if self.es_municipal else "Vecino"

    def actualizar_perfil(self, nombre: str | None = None, comuna: str | None = None) -> None:
        """Permite actualizar el nombre o la comuna del usuario."""
        if nombre:
            self.nombre = nombre.strip()
        if comuna:
            self.comuna = comuna.strip()

    # ------------------------------------------------------------------
    # Serialización (para JSON)
    # ------------------------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "id_usuario": self.id_usuario,
            "nombre": self.nombre,
            "email": self.email,
            "rol": self.rol,
            "comuna": self.comuna,
            "sal": self.sal,
            "hash_contrasena": self.hash_contrasena,
        }

    @classmethod
    def from_dict(cls, datos: dict) -> "Usuario":
        return cls(
            id_usuario=int(datos["id_usuario"]),
            nombre=datos["nombre"],
            email=datos["email"],
            sal=datos["sal"],
            hash_contrasena=datos["hash_contrasena"],
            rol=datos.get("rol", "vecino"),
            comuna=datos.get("comuna", "Temuco"),
        )

    def __str__(self) -> str:
        return f"Usuario({self.nombre}, {self.email}, {self.rol})"
