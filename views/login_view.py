import flet as ft
import requests
from config import BASE_URL
from components.validaciones import (
    correo_valido,
    requisitos_contrasena_pendientes,
)

class LoginView(ft.Container):
    def __init__(
        self,
        on_volver,
        on_login_exitoso,
        es_movil=False,
        on_registro=None,
    ):
        super().__init__()
        self.on_volver = on_volver
        self.on_login_exitoso = on_login_exitoso
        self.on_registro = on_registro
        
        self.expand = True
        self.alignment = ft.Alignment.CENTER
        
        ancho_campo = 280 if es_movil else None
        alto_campo = 56 if es_movil else 62
        self.txt_correo = ft.TextField(
            label="Correo electrónico",
            width=ancho_campo,
            height=alto_campo,
            expand=not es_movil,
        )
        self.txt_contrasena = ft.TextField(
            label="Contraseña",
            password=True,
            width=ancho_campo,
            height=alto_campo,
            expand=not es_movil,
        )
        self.txt_contrasena.can_reveal_password = True
        self.txt_correo.width = None
        self.txt_correo.expand = True
        self.txt_correo.prefix_icon = ft.Icons.EMAIL_OUTLINED
        self.txt_correo.keyboard_type = ft.KeyboardType.EMAIL
        self.txt_contrasena.width = None
        self.txt_contrasena.expand = True
        self.txt_contrasena.prefix_icon = ft.Icons.LOCK_OUTLINE
        for campo in (self.txt_correo, self.txt_contrasena):
            campo.filled = True
            campo.fill_color = "#FFFCFA"
            campo.border_color = "#E7C8B8"
            campo.focused_border_color = "#6A0404"
            campo.focused_border_width = 2
            campo.border_radius = 14
            campo.content_padding = ft.Padding(
                left=14,
                top=14,
                right=10,
                bottom=14,
            )
        self.txt_error = ft.Text("", color=ft.Colors.RED, size=12)

        self.content = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                ft.ResponsiveRow(
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ft.Container(
                            col={
                                ft.ResponsiveRowBreakpoint.XS: 12,
                                ft.ResponsiveRowBreakpoint.MD: 8,
                                ft.ResponsiveRowBreakpoint.LG: 6,
                                ft.ResponsiveRowBreakpoint.XL: 5,
                            },
                            padding=20 if es_movil else 32,
                            bgcolor=ft.Colors.WHITE,
                            border_radius=24,
                            shadow=ft.BoxShadow(
                                blur_radius=18,
                                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                                offset=ft.Offset(0, 6),
                            ),
                            content=ft.Column(
                                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                                spacing=14,
                                controls=[
                                    ft.Container(
                                        width=68,
                                        height=68,
                                        alignment=ft.Alignment.CENTER,
                                        bgcolor=ft.Colors.with_opacity(
                                            0.08,
                                            "#6A0404",
                                        ),
                                        border_radius=34,
                                        content=ft.Icon(
                                            ft.Icons.LOCAL_PIZZA_ROUNDED,
                                            size=34,
                                            color="#6A0404",
                                        ),
                                    ),
                                    ft.Text(
                                        "Iniciar sesión",
                                        size=28,
                                        weight=ft.FontWeight.BOLD,
                                        color="#6A0404",
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                    ft.Text(
                                        "Bienvenido de nuevo a PizzaExpress",
                                        size=14,
                                        color="#806B63",
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                    self.txt_correo,
                                    self.txt_contrasena,
                                    ft.Row(
                                        [
                                            ft.TextButton(
                                                "¿Olvidaste tu contraseña?",
                                                style=ft.ButtonStyle(
                                                    color="#806B63",
                                                ),
                                                on_click=self.solicitar_restablecimiento,
                                            )
                                        ],
                                        alignment=ft.MainAxisAlignment.END,
                                    ),
                                    self.txt_error,
                                    ft.FilledButton(
                                        "Entrar",
                                        icon=ft.Icons.ARROW_FORWARD,
                                        bgcolor="#6A0404",
                                        color=ft.Colors.WHITE,
                                        height=52,
                                        style=ft.ButtonStyle(
                                            shape=ft.RoundedRectangleBorder(
                                                radius=16
                                            ),
                                        ),
                                        on_click=self.intentar_login,
                                    ),
                                    ft.TextButton(
                                        "¿Aún no tienes cuenta? Regístrate aquí",
                                        style=ft.ButtonStyle(color="#6A0404"),
                                        on_click=self.ir_a_registro,
                                    ),
                                    ft.TextButton(
                                        "Volver",
                                        on_click=self.on_volver,
                                    ),
                                ],
                            ),
                        )
                    ],
                ),
            ],
        )
    def ir_a_registro(self, e):
        if self.on_registro:
            self.on_registro()

    @staticmethod
    def mensaje_error_restablecimiento(respuesta, mensaje_predeterminado):
        if respuesta.status_code == 404:
            return (
                "La API todavía no tiene activa la recuperación por código. "
                "Actualiza el servidor e inténtalo de nuevo."
            )
        try:
            detalle = respuesta.json().get("detail")
        except (ValueError, AttributeError):
            detalle = None
        return detalle if isinstance(detalle, str) else mensaje_predeterminado

    def solicitar_restablecimiento(self, e):
        campo_correo = ft.TextField(
            label="Correo electrónico",
            value=self.txt_correo.value or "",
            keyboard_type=ft.KeyboardType.EMAIL,
            autofocus=True,
        )
        texto_error = ft.Text("", color=ft.Colors.RED, size=12)
        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Text("Restablecer contraseña"),
            content=ft.Column(
                tight=True,
                controls=[
                    ft.Text(
                        "Te enviaremos un código de confirmación si existe "
                        "una cuenta con este correo."
                    ),
                    campo_correo,
                    texto_error,
                ],
            ),
        )

        def cambiar_contrasena(token):
            nueva = ft.TextField(
                label="Nueva contraseña",
                password=True,
                can_reveal_password=True,
                autofocus=True,
            )
            confirmar = ft.TextField(
                label="Confirma la contraseña",
                password=True,
                can_reveal_password=True,
            )
            error_contrasena = ft.Text("", color=ft.Colors.RED, size=12)
            dialogo_contrasena = ft.AlertDialog(
                modal=True,
                title=ft.Text("Crear nueva contraseña"),
                content=ft.Column(
                    tight=True,
                    controls=[nueva, confirmar, error_contrasena],
                ),
            )

            def guardar(_):
                valor = nueva.value or ""
                pendientes = requisitos_contrasena_pendientes(valor)
                if pendientes:
                    error_contrasena.value = (
                        "La contraseña debe incluir "
                        + ", ".join(pendientes)
                        + "."
                    )
                    self.page.update()
                    return
                if valor != (confirmar.value or ""):
                    error_contrasena.value = "Las contraseñas no coinciden."
                    self.page.update()
                    return

                try:
                    respuesta = requests.post(
                        f"{BASE_URL}/api/password-reset/confirm",
                        json={
                            "token": token,
                            "nueva_contrasena": valor,
                        },
                        timeout=45,
                    )
                except requests.RequestException:
                    error_contrasena.value = (
                        "No se pudo conectar con el servidor."
                    )
                    self.page.update()
                    return

                if respuesta.ok:
                    dialogo_contrasena.title = ft.Text("Contraseña actualizada")
                    dialogo_contrasena.content = ft.Text(
                        "Ya puedes iniciar sesión con tu nueva contraseña."
                    )
                    dialogo_contrasena.actions = [
                        ft.TextButton(
                            "Cerrar",
                            on_click=lambda _: self.page.pop_dialog(),
                        )
                    ]
                else:
                    error_contrasena.value = (
                        self.mensaje_error_restablecimiento(
                            respuesta,
                            "No se pudo cambiar la contraseña.",
                        )
                    )
                self.page.update()

            dialogo_contrasena.actions = [
                ft.TextButton(
                    "Cancelar",
                    on_click=lambda _: self.page.pop_dialog(),
                ),
                ft.FilledButton(
                    "Guardar contraseña",
                    on_click=guardar,
                ),
            ]
            self.page.show_dialog(dialogo_contrasena)

        def verificar(campo_codigo):
            codigo = (campo_codigo.value or "").strip().upper()
            if len(codigo) != 6 or not codigo.isalpha() or not codigo.isascii():
                texto_error.value = "Ingresa las 6 letras del código recibido."
                self.page.update()
                return

            try:
                respuesta = requests.post(
                    f"{BASE_URL}/api/password-reset/verify",
                    json={
                        "correo": campo_correo.value,
                        "codigo": codigo,
                    },
                    timeout=45,
                )
            except requests.RequestException:
                texto_error.value = (
                    "No se pudo conectar con el servidor."
                )
                self.page.update()
                return

            if respuesta.ok:
                token = respuesta.json().get("token")
                if not token:
                    texto_error.value = (
                        "El servidor no pudo completar la verificación."
                    )
                    self.page.update()
                    return
                self.page.pop_dialog()
                cambiar_contrasena(token)
            else:
                texto_error.value = self.mensaje_error_restablecimiento(
                    respuesta,
                    "El código no es válido o expiró.",
                )
                self.page.update()

        def enviar(_):
            correo = (campo_correo.value or "").strip().lower()
            if not correo_valido(correo):
                texto_error.value = "Ingresa un correo electrónico válido."
                self.page.update()
                return

            try:
                respuesta = requests.post(
                    f"{BASE_URL}/api/password-reset/request",
                    json={"correo": correo},
                    timeout=45,
                )
            except requests.RequestException:
                texto_error.value = (
                    "No se pudo conectar con el servidor."
                )
                self.page.update()
                return

            if respuesta.ok:
                campo_codigo = ft.TextField(
                    label="Código de 6 letras",
                    max_length=6,
                    autofocus=True,
                    capitalization=ft.TextCapitalization.CHARACTERS,
                )
                dialogo.title = ft.Text("Ingresa el código")
                dialogo.content = ft.Column(
                    tight=True,
                    controls=[
                        ft.Text(
                            "Si existe una cuenta con ese correo, recibirás "
                            "un código. Ingresa las 6 letras para continuar."
                        ),
                        campo_codigo,
                        texto_error,
                    ],
                )
                dialogo.actions = [
                    ft.TextButton(
                        "Cancelar",
                        on_click=lambda _: self.page.pop_dialog(),
                    ),
                    ft.FilledButton(
                        "Verificar código",
                        on_click=lambda _: verificar(campo_codigo),
                    ),
                ]
            else:
                texto_error.value = self.mensaje_error_restablecimiento(
                    respuesta,
                    "No se pudo solicitar el restablecimiento.",
                )
            self.page.update()

        dialogo.actions = [
            ft.TextButton("Cancelar", on_click=lambda _: self.page.pop_dialog()),
            ft.FilledButton("Enviar código", on_click=enviar),
        ]
        self.page.show_dialog(dialogo)

    def intentar_login(self, e):
        try:
            self.txt_error.value = ""
            url = f"{BASE_URL}/api/login"
            
            correo = self.txt_correo.value.strip().lower() if self.txt_correo.value else ""
            contrasena = self.txt_contrasena.value.strip() if self.txt_contrasena.value else ""

            errores = []
            if not correo or not contrasena:
                errores.append("Completa todos los campos.")
            if correo and not correo_valido(correo):
                errores.append("Ingresa un correo electrónico válido.")
            if errores:
                self.mostrar_alerta_validacion("\n".join(errores))
                return

            respuesta = requests.post(
                url,
                json={"correo": correo, "contrasena": contrasena},
                timeout=45,
            )

            if respuesta.status_code == 200:
                datos = respuesta.json()
                token = datos.get("token")
                if not token:
                    self.txt_error.value = (
                        "El servidor debe actualizarse para sincronizar pedidos."
                    )
                    if self.page:
                        self.page.update()
                    return
                self.on_login_exitoso(
                    datos.get("id"), 
                    datos.get("nombre"), 
                    datos.get("apellido"),
                    token,
                )
            else:
                self.txt_error.value = "Correo o contraseña incorrectos"
                if self.page:
                    self.page.update()
        except Exception as ex:
            self.txt_error.value = "No se pudo conectar con el servidor"
            if self.page:
                self.page.update()

    def mostrar_alerta_validacion(self, mensaje):
        self.txt_error.value = mensaje
        try:
            page = self.page
        except RuntimeError:
            page = None
        if page:
            alerta = ft.AlertDialog(
                modal=True,
                title=ft.Text("Revisa los datos"),
                content=ft.Text(mensaje),
                actions=[
                    ft.TextButton("Entendido", on_click=lambda e: page.pop_dialog())
                ],
            )
            page.show_dialog(alerta)