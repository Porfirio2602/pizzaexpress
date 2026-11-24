import asyncio
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
        self.es_movil = es_movil

        self.expand = True
        self.alignment = ft.Alignment.CENTER

        alto_campo = 56 if es_movil else 62
        self.txt_correo = ft.TextField(
            label="Correo electrónico",
            height=alto_campo,
            expand=True,
            prefix_icon=ft.Icons.EMAIL_OUTLINED,
            keyboard_type=ft.KeyboardType.EMAIL,
            on_submit=self.intentar_login,
        )
        self.txt_contrasena = ft.TextField(
            label="Contraseña",
            password=True,
            can_reveal_password=True,
            height=alto_campo,
            expand=True,
            prefix_icon=ft.Icons.LOCK_OUTLINE,
            on_submit=self.intentar_login,
        )

        for campo in (self.txt_correo, self.txt_contrasena):
            campo.filled = True
            campo.fill_color = "#FFFCFA"
            campo.border = {
                ft.ControlState.DEFAULT: ft.OutlineInputBorder(
                    border_radius=14,
                    side=ft.BorderSide(1, "#E7C8B8"),
                ),
                ft.ControlState.FOCUSED: ft.OutlineInputBorder(
                    border_radius=14,
                    side=ft.BorderSide(2, "#6A0404"),
                ),
            }
            campo.content_padding = ft.Padding(
                left=14,
                top=14,
                right=10,
                bottom=14,
            )

        self.txt_error = ft.Text("", color=ft.Colors.RED_700, size=12)

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
                                    ft.Row(
                                        alignment=ft.MainAxisAlignment.CENTER,
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
                                        ],
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

    def abrir_dialogo_seguro(self, dialogo):
        if not self.page:
            return
        try:
            self.page.show_dialog(dialogo)
        except RuntimeError as error:
            if "Dialog is already opened" in str(error):
                self.page.pop_dialog()
                self.page.show_dialog(dialogo)
            else:
                raise

    def cerrar_dialogo_seguro(self):
        if not self.page:
            return
        try:
            self.page.pop_dialog()
        except RuntimeError:
            pass

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
        ancho_modal = 290 if self.es_movil else 380

        def crear_campo_modal(
            label,
            icono,
            hint="",
            valor="",
            password=False,
            max_length=None,
            teclado=None,
            capitalizacion=None,
            autofocus=False,
            on_submit=None,
        ):
            return ft.TextField(
                label=label,
                hint_text=hint,
                value=valor,
                password=password,
                can_reveal_password=password,
                max_length=max_length,
                keyboard_type=teclado,
                capitalization=capitalizacion,
                autofocus=autofocus,
                prefix_icon=icono,
                filled=True,
                fill_color="#FFFCFA",
                border={
                    ft.ControlState.DEFAULT: ft.OutlineInputBorder(
                        border_radius=14,
                        side=ft.BorderSide(1, "#E7C8B8"),
                    ),
                    ft.ControlState.FOCUSED: ft.OutlineInputBorder(
                        border_radius=14,
                        side=ft.BorderSide(2, "#6A0404"),
                    ),
                },
                content_padding=ft.Padding(left=14, top=14, right=10, bottom=14),
                on_submit=on_submit,
            )

        def crear_titulo_modal(icono, titulo):
            return ft.Column(
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                tight=True,
                controls=[
                    ft.Container(
                        width=60,
                        height=60,
                        alignment=ft.Alignment.CENTER,
                        bgcolor="#FCE8E6",
                        border_radius=30,
                        content=ft.Icon(icono, size=30, color="#6A0404"),
                    ),
                    ft.Text(
                        titulo,
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color="#6A0404",
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
            )

        texto_error = ft.Text(
            "",
            color=ft.Colors.RED_700,
            size=13,
            text_align=ft.TextAlign.CENTER,
            visible=False,
        )

        def mostrar_error(mensaje):
            texto_error.value = mensaje
            texto_error.visible = bool(mensaje)

        dialogo = ft.AlertDialog(
            modal=True,
            bgcolor=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=24),
            title_padding=ft.Padding(left=24, top=24, right=24, bottom=8),
            content_padding=ft.Padding(left=24, top=8, right=24, bottom=12),
            actions_padding=ft.Padding(left=24, top=4, right=24, bottom=20),
        )

        def cerrar_dialogo(_=None):
            self.cerrar_dialogo_seguro()

        def abrir_paso_nueva_contrasena(token):
            mostrar_error("")
            campo_nueva = crear_campo_modal(
                label="Nueva contraseña",
                icono=ft.Icons.LOCK_OUTLINE,
                hint="Mínimo 8 caracteres",
                password=True,
                autofocus=True,
            )
            campo_confirmar = crear_campo_modal(
                label="Confirmar contraseña",
                icono=ft.Icons.LOCK_RESET,
                hint="Repite la contraseña",
                password=True,
            )
            btn_guardar = ft.FilledButton(
                "Guardar contraseña",
                icon=ft.Icons.CHECK,
                bgcolor="#6A0404",
                color=ft.Colors.WHITE,
                height=46,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=14),
                ),
            )

            async def ejecutar_guardado(_=None):
                valor = campo_nueva.value or ""
                pendientes = requisitos_contrasena_pendientes(valor)
                if pendientes:
                    mostrar_error(
                        "La contraseña debe incluir "
                        + ", ".join(pendientes)
                        + "."
                    )
                    if self.page:
                        self.page.update()
                    return
                if valor != (campo_confirmar.value or ""):
                    mostrar_error("Las contraseñas no coinciden.")
                    if self.page:
                        self.page.update()
                    return

                mostrar_error("")
                btn_guardar.disabled = True
                btn_guardar.text = "Guardando..."
                if self.page:
                    self.page.update()

                try:
                    respuesta = await asyncio.to_thread(
                        requests.post,
                        f"{BASE_URL}/api/password-reset/confirm",
                        json={
                            "token": token,
                            "nueva_contrasena": valor,
                        },
                        timeout=45,
                    )
                except requests.RequestException:
                    btn_guardar.disabled = False
                    btn_guardar.text = "Guardar contraseña"
                    mostrar_error("No se pudo conectar con el servidor.")
                    if self.page:
                        self.page.update()
                    return

                if respuesta.ok:
                    self.txt_contrasena.value = ""
                    dialogo.title = crear_titulo_modal(
                        ft.Icons.CHECK_CIRCLE_OUTLINE,
                        "Contraseña actualizada",
                    )
                    dialogo.content = ft.Container(
                        width=ancho_modal,
                        content=ft.Text(
                            "Tu contraseña se cambió correctamente. Ya puedes iniciar sesión.",
                            size=14,
                            color="#54423B",
                            text_align=ft.TextAlign.CENTER,
                        ),
                    )
                    dialogo.actions = [
                        ft.FilledButton(
                            "Iniciar sesión",
                            bgcolor="#6A0404",
                            color=ft.Colors.WHITE,
                            height=44,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=14),
                            ),
                            on_click=cerrar_dialogo,
                        )
                    ]
                    dialogo.actions_alignment = ft.MainAxisAlignment.CENTER
                else:
                    btn_guardar.disabled = False
                    btn_guardar.text = "Guardar contraseña"
                    mostrar_error(
                        self.mensaje_error_restablecimiento(
                            respuesta,
                            "No se pudo cambiar la contraseña.",
                        )
                    )
                if self.page:
                    self.page.update()

            def on_guardar(ev):
                if self.page:
                    self.page.run_task(ejecutar_guardado, ev)

            campo_confirmar.on_submit = on_guardar
            btn_guardar.on_click = on_guardar

            dialogo.title = crear_titulo_modal(
                ft.Icons.PASSWORD,
                "Crear nueva contraseña",
            )
            dialogo.content = ft.Container(
                width=ancho_modal,
                content=ft.Column(
                    tight=True,
                    spacing=12,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                    controls=[
                        ft.Text(
                            "Incluye mayúscula, minúscula, número y símbolo.",
                            size=13,
                            color="#806B63",
                            text_align=ft.TextAlign.CENTER,
                        ),
                        campo_nueva,
                        campo_confirmar,
                        texto_error,
                    ],
                ),
            )
            dialogo.actions = [
                ft.TextButton(
                    "Cancelar",
                    style=ft.ButtonStyle(color="#806B63"),
                    on_click=cerrar_dialogo,
                ),
                btn_guardar,
            ]
            dialogo.actions_alignment = ft.MainAxisAlignment.END
            if self.page:
                self.page.update()

        def abrir_paso_codigo(correo_destino):
            mostrar_error("")
            campo_codigo = crear_campo_modal(
                label="Código de 6 letras",
                icono=ft.Icons.PIN_OUTLINED,
                hint="ABCDEF",
                max_length=6,
                capitalizacion=ft.TextCapitalization.CHARACTERS,
                autofocus=True,
            )
            btn_verificar = ft.FilledButton(
                "Verificar código",
                icon=ft.Icons.VERIFIED_OUTLINED,
                bgcolor="#6A0404",
                color=ft.Colors.WHITE,
                height=46,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=14),
                ),
            )

            async def ejecutar_verificacion(_=None):
                codigo = (campo_codigo.value or "").strip().upper()
                if len(codigo) != 6 or not codigo.isalpha() or not codigo.isascii():
                    mostrar_error("Ingresa las 6 letras del código recibido.")
                    if self.page:
                        self.page.update()
                    return

                mostrar_error("")
                btn_verificar.disabled = True
                btn_verificar.text = "Verificando..."
                if self.page:
                    self.page.update()

                try:
                    respuesta = await asyncio.to_thread(
                        requests.post,
                        f"{BASE_URL}/api/password-reset/verify",
                        json={
                            "correo": correo_destino,
                            "codigo": codigo,
                        },
                        timeout=45,
                    )
                except requests.RequestException:
                    btn_verificar.disabled = False
                    btn_verificar.text = "Verificar código"
                    mostrar_error("No se pudo conectar con el servidor.")
                    if self.page:
                        self.page.update()
                    return

                if respuesta.ok:
                    token = respuesta.json().get("token")
                    if not token:
                        btn_verificar.disabled = False
                        btn_verificar.text = "Verificar código"
                        mostrar_error(
                            "El servidor no pudo completar la verificación."
                        )
                        if self.page:
                            self.page.update()
                        return
                    abrir_paso_nueva_contrasena(token)
                else:
                    btn_verificar.disabled = False
                    btn_verificar.text = "Verificar código"
                    mostrar_error(
                        self.mensaje_error_restablecimiento(
                            respuesta,
                            "El código no es válido o expiró.",
                        )
                    )
                    if self.page:
                        self.page.update()

            def on_verificar(ev):
                if self.page:
                    self.page.run_task(ejecutar_verificacion, ev)

            campo_codigo.on_submit = on_verificar
            btn_verificar.on_click = on_verificar

            dialogo.title = crear_titulo_modal(
                ft.Icons.MARK_EMAIL_READ_OUTLINED,
                "Ingresa el código",
            )
            dialogo.content = ft.Container(
                width=ancho_modal,
                content=ft.Column(
                    tight=True,
                    spacing=12,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                    controls=[
                        ft.Text(
                            f"Enviamos un código de 6 letras a {correo_destino}. "
                            "Revisa tu bandeja o carpeta de Spam.",
                            size=13,
                            color="#806B63",
                            text_align=ft.TextAlign.CENTER,
                        ),
                        campo_codigo,
                        texto_error,
                    ],
                ),
            )
            dialogo.actions = [
                ft.TextButton(
                    "Cancelar",
                    style=ft.ButtonStyle(color="#806B63"),
                    on_click=cerrar_dialogo,
                ),
                btn_verificar,
            ]
            dialogo.actions_alignment = ft.MainAxisAlignment.END
            if self.page:
                self.page.update()

        campo_correo = crear_campo_modal(
            label="Correo electrónico",
            icono=ft.Icons.EMAIL_OUTLINED,
            hint="nombre@correo.com",
            valor=(self.txt_correo.value or "").strip(),
            teclado=ft.KeyboardType.EMAIL,
            autofocus=True,
        )
        btn_enviar = ft.FilledButton(
            "Enviar código",
            icon=ft.Icons.SEND_ROUNDED,
            bgcolor="#6A0404",
            color=ft.Colors.WHITE,
            height=46,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=14),
            ),
        )

        async def ejecutar_envio(_=None):
            correo = (campo_correo.value or "").strip().lower()
            if not correo_valido(correo):
                mostrar_error("Ingresa un correo electrónico válido.")
                if self.page:
                    self.page.update()
                return

            mostrar_error("")
            btn_enviar.disabled = True
            btn_enviar.text = "Enviando..."
            if self.page:
                self.page.update()

            try:
                respuesta = await asyncio.to_thread(
                    requests.post,
                    f"{BASE_URL}/api/password-reset/request",
                    json={"correo": correo},
                    timeout=45,
                )
            except requests.RequestException:
                btn_enviar.disabled = False
                btn_enviar.text = "Enviar código"
                mostrar_error("No se pudo conectar con el servidor.")
                if self.page:
                    self.page.update()
                return

            if respuesta.ok:
                abrir_paso_codigo(correo)
            else:
                btn_enviar.disabled = False
                btn_enviar.text = "Enviar código"
                mostrar_error(
                    self.mensaje_error_restablecimiento(
                        respuesta,
                        "No se pudo solicitar el restablecimiento.",
                    )
                )
                if self.page:
                    self.page.update()

        def on_enviar(ev):
            if self.page:
                self.page.run_task(ejecutar_envio, ev)

        campo_correo.on_submit = on_enviar
        btn_enviar.on_click = on_enviar

        dialogo.title = crear_titulo_modal(
            ft.Icons.LOCK_RESET,
            "Restablecer contraseña",
        )
        dialogo.content = ft.Container(
            width=ancho_modal,
            content=ft.Column(
                tight=True,
                spacing=12,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                controls=[
                    ft.Text(
                        "Te enviaremos un código de confirmación si existe una cuenta "
                        "con este correo. El código vence en 3 minutos.",
                        size=13,
                        color="#806B63",
                        text_align=ft.TextAlign.CENTER,
                    ),
                    campo_correo,
                    texto_error,
                ],
            ),
        )
        dialogo.actions = [
            ft.TextButton(
                "Cancelar",
                style=ft.ButtonStyle(color="#806B63"),
                on_click=cerrar_dialogo,
            ),
            btn_enviar,
        ]
        dialogo.actions_alignment = ft.MainAxisAlignment.END
        self.abrir_dialogo_seguro(dialogo)

    def intentar_login(self, e):
        try:
            self.txt_error.value = ""
            url = f"{BASE_URL}/api/login"

            correo = (
                self.txt_correo.value.strip().lower()
                if self.txt_correo.value
                else ""
            )
            contrasena = (
                self.txt_contrasena.value.strip()
                if self.txt_contrasena.value
                else ""
            )

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
        except Exception:
            self.txt_error.value = "No se pudo conectar con el servidor"
            if self.page:
                self.page.update()

    def mostrar_alerta_validacion(self, mensaje):
        self.txt_error.value = mensaje
        alerta = ft.AlertDialog(
            modal=True,
            bgcolor=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=20),
            title=ft.Text("Revisa los datos", color="#6A0404", weight=ft.FontWeight.BOLD),
            content=ft.Text(mensaje),
            actions=[
                ft.TextButton(
                    "Entendido",
                    style=ft.ButtonStyle(color="#6A0404"),
                    on_click=lambda e: self.cerrar_dialogo_seguro(),
                )
            ],
        )
        self.abrir_dialogo_seguro(alerta)