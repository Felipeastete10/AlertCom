class Usuario:
    """
    Clase que representa a un usuario dentro del sistema AlertCom.
    Maneja la información del perfil y su estado de sesión.
    """
    def __init__(self, id_usuario: int, nombre: str, email: str, contrasena: str, avatar: str = "default.png"):
        self.id_usuario = id_usuario
        self.nombre = nombre
        self.email = email
        self.contrasena = contrasena 
        self.avatar = avatar
        self.sesion_activa = False

    def iniciar_sesion(self, email: str, contrasena: str) -> bool:
        """Verifica las credenciales del usuario e inicia sesión."""
        if self.email == email and self.contrasena == contrasena:
            self.sesion_activa = True
            return True
        return False

    def cerrar_sesion(self) -> None:
        """Cierra la sesión del usuario."""
        self.sesion_activa = False

    def actualizar_perfil(self, nombre: str = None, avatar: str = None) -> None:
        """Permite actualizar el nombre o avatar del usuario."""
        if nombre:
            self.nombre = nombre
        if avatar:
            self.avatar = avatar

    def to_dict(self) -> dict:
        """Retorna una representación en diccionario de los datos del usuario."""
        return {
            "id_usuario": self.id_usuario,
            "nombre": self.nombre,
            "email": self.email,
            "avatar": self.avatar,
            "sesion_activa": self.sesion_activa
        }

    def __str__(self) -> str:
        return f"Usuario({self.nombre}, Email: {self.email})"