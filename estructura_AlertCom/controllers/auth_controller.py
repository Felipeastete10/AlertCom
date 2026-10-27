# =============================================================================
# AlertCom - Controlador: Autenticación de Usuarios
# =============================================================================
# Gestiona el inicio y cierre de sesión.
# Compatible con KivyMD 2.0.1.dev0: no importa KivyMD; solo usa
# kivy.app.App para acceder al ScreenManager y cambiar de pantalla.
# =============================================================================

from kivy.app import App


class AuthController:
    """
    Controlador de autenticación.

    Responsabilidades:
      • Validar credenciales (mock MVP contra el administrador).
      • Cambiar la pantalla activa al iniciar sesión exitosamente.
      • Retornar un error a la vista para que ésta lo notifique al usuario.
    """

    # Credenciales temporales para pruebas sin backend (MVP)
    ADMIN_EMAIL = "admin@gmail.com"
    ADMIN_PASSWORD = "123456"

    def __init__(self) -> None:
        self.usuario_autenticado: bool = False
        self.usuario_nombre: str | None = None
        self.usuario_email: str | None = None
        # Cuentas creadas en la app (MVP en memoria): correo -> (contraseña, nombre)
        self.cuentas: dict[str, tuple[str, str]] = {}

    def registrar(self, correo: str, contrasena: str, nombre: str | None = None) -> tuple[bool, str | None]:
        """
        Crea una cuenta nueva en memoria.

        Returns:
            Tupla (exito, mensaje). Si exito=False, mensaje explica el motivo.
        """
        correo = correo.strip().lower()
        if correo == self.ADMIN_EMAIL or correo in self.cuentas:
            return False, "Ya existe una cuenta con ese correo."
        nombre = nombre or correo.split("@")[0].replace(".", " ").title()
        self.cuentas[correo] = (contrasena, nombre)
        return True, None

    def iniciar_sesion(self, correo: str, contrasena: str) -> tuple[bool, str | None]:
        """
        Valida las credenciales y, si son correctas, navega a la pantalla "safety".

        Args:
            correo: Correo electrónico del usuario.
            contrasena: Contraseña en texto plano.

        Returns:
            Tupla (exito, mensaje).
            - exito=True: login válido, la app ya navegó a 'safety', mensaje=None.
            - exito=False: credenciales inválidas, mensaje contiene el error que
              la vista debe mostrar al usuario.
        """
        # Validación mock: administrador o cuenta creada con registrar()
        nombre = None
        if correo == self.ADMIN_EMAIL and contrasena == self.ADMIN_PASSWORD:
            nombre = "Administrador"
        else:
            cuenta = self.cuentas.get(correo.strip().lower())
            if cuenta is not None and cuenta[0] == contrasena:
                nombre = cuenta[1]

        if nombre is not None:
            self.usuario_autenticado = True
            self.usuario_nombre = nombre
            self.usuario_email = correo

            # Navegar al aviso de seguridad mediante el ScreenManager de la app
            app = App.get_running_app()
            if app is not None and app.root is not None:
                app.root.current = "safety"

            print("Login exitoso: navegando a pantalla 'safety'.")
            return True, None

        # Credenciales incorrectas → retornar error a la vista
        mensaje = "Correo o contraseña incorrectos. Intente nuevamente."
        print(f"Error de login: {mensaje}")
        return False, mensaje

    def cerrar_sesion(self) -> None:
        self.usuario_autenticado = False
        self.usuario_nombre = None
        self.usuario_email = None

    def esta_autenticado(self) -> bool:
        return self.usuario_autenticado
