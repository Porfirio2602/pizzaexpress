import asyncio
import flet as ft
import requests
from config import BASE_URL
from components.validaciones import (
    correo_valido,
    nombre_valido,
    requisitos_contrasena_pendientes,
    telefono_valido,
)


class RegistroView(ft.Container):
    def __init__(self, on_volver, on_registro_exitoso, es_movil=False):
        super().__init__()
        self.on_volver = on_volver
        self.on_registro_exitoso = on_registro_exitoso

        self.expand = True
        self.alignment = ft.Alignment.CENTER

        ancho_campo = 280 if es_movil else None
        alto_campo = 45 if es_movil else 52
        expandir_campo = not es_movil
        self.txt_nombre = ft.TextField(
            label="Nombre",
            width=ancho_campo,
            height=alto_campo,
            expand=expandir_campo,
        )
        self.txt_primer_apellido = ft.TextField(
            label="Primer Apellido",
            width=ancho_campo,
            height=alto_campo,
            expand=expandir_campo,
        )
        self.txt_segundo_apellido = ft.TextField(
            label="Segundo Apellido",
            width=ancho_campo,
            height=alto_campo,
            expand=expandir_campo,
        )
        self.txt_telefono = ft.TextField(
            label="Teléfono",
            width=ancho_campo,
            height=alto_campo,
            expand=expandir_campo,
            on_change=self.validar_telefono,
        )
        self.txt_correo = ft.TextField(
            label="Correo electrónico",
            width=ancho_campo,
            height=alto_campo,
            expand=expandir_campo,
            on_change=self.validar_correo_en_tiempo_real,
        )
        self.txt_contrasena = ft.TextField(
            label="Contraseña",
            password=True,
            width=ancho_campo,
            height=alto_campo,
            expand=expandir_campo,
        )
        self.txt_confirmar_contrasena = ft.TextField(
            label="Confirmar contraseña",
            password=True,
            width=ancho_campo,
            height=alto_campo,
            expand=expandir_campo,
        )
        self.txt_contrasena.can_reveal_password = True
        self.txt_confirmar_contrasena.can_reveal_password = True
        self.txt_contrasena.on_change = self.validar_contrasena
        self.txt_confirmar_contrasena.on_change = (
            self.validar_confirmacion_contrasena
        )
        self.txt_error = ft.Text("", color=ft.Colors.RED, size=12)

        borde_campo = {
            ft.ControlState.DEFAULT: ft.OutlineInputBorder(
                border_radius=14,
                side=ft.BorderSide(1, "#E7C8B8"),
            ),
            ft.ControlState.FOCUSED: ft.OutlineInputBorder(
                border_radius=14,
                side=ft.BorderSide(2, "#6A0404"),
            ),
        }

        for campo, ayuda in (
            (self.txt_nombre, "Escribe tu nombre."),
            (self.txt_primer_apellido, "Escribe tu primer apellido."),
            (self.txt_segundo_apellido, "Escribe tu segundo apellido."),
            (self.txt_telefono, "Ingresa un teléfono de 10 dígitos."),
            (self.txt_correo, "Usaremos este correo para iniciar sesión."),
            (
                self.txt_contrasena,
                "Mínimo 8 caracteres con mayúscula, minúscula, número y símbolo.",
            ),
            (
                self.txt_confirmar_contrasena,
                "Vuelve a escribir la misma contraseña.",
            ),
        ):
            campo.width = None
            campo.expand = True
            campo.height = 58 if es_movil else 62
            campo.text_size = 14 if es_movil else 15
            campo.filled = True
            campo.fill_color = "#FFFCFA"
            campo.border = borde_campo
            campo.content_padding = ft.Padding(
                left=14, top=14, right=10, bottom=14
            )
            campo.hint_style = ft.TextStyle(color="#9A8B83")
            campo.helper = None
            campo.suffix_icon = ft.Icon(
                ft.Icons.INFO_OUTLINE,
                size=18,
                color="#9A8B83",
                tooltip=ayuda,
            )

        self.txt_nombre.label = "Nombre"
        self.txt_nombre.hint_text = "Tu nombre"
        self.txt_nombre.prefix_icon = ft.Icons.PERSON_OUTLINE
        self.txt_primer_apellido.label = "Primer apellido"
        self.txt_primer_apellido.hint_text = "Tu primer apellido"
        self.txt_primer_apellido.prefix_icon = ft.Icons.BADGE_OUTLINED
        self.txt_segundo_apellido.label = "Segundo apellido"
        self.txt_segundo_apellido.hint_text = "Tu segundo apellido"
        self.txt_segundo_apellido.prefix_icon = ft.Icons.BADGE_OUTLINED
        self.txt_telefono.hint_text = "10 dígitos"
        self.txt_telefono.prefix_icon = ft.Icons.PHONE_OUTLINED
        self.txt_telefono.keyboard_type = ft.KeyboardType.PHONE
        self.txt_telefono.max_length = 10
        self.txt_correo.hint_text = "nombre@correo.com"
        self.txt_correo.prefix_icon = ft.Icons.MAIL_OUTLINE
        self.txt_correo.keyboard_type = ft.KeyboardType.EMAIL
        self.txt_contrasena.hint_text = (
            "Mínimo 8 caracteres y estructura segura"
        )
        self.txt_contrasena.prefix_icon = ft.Icons.LOCK_OUTLINE
        self.txt_confirmar_contrasena.hint_text = "Repite tu contraseña"
        self.txt_confirmar_contrasena.prefix_icon = ft.Icons.LOCK_OUTLINE

        self.btn_crear_cuenta = ft.FilledButton(
            "Crear cuenta",
            icon=ft.Icons.ARROW_FORWARD,
            bgcolor="#6A0404",
            color=ft.Colors.WHITE,
            height=54,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=16),
                elevation={
                    ft.ControlState.DEFAULT: 3,
                    ft.ControlState.HOVERED: 6,
                    ft.ControlState.PRESSED: 1,
                },
                shadow_color=ft.Colors.with_opacity(
                    0.24,
                    "#6A0404",
                ),
                overlay_color=ft.Colors.with_opacity(
                    0.12,
                    ft.Colors.WHITE,
                ),
            ),
            on_click=self.intentar_registro,
        )

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
                                ft.ResponsiveRowBreakpoint.MD: 10,
                                ft.ResponsiveRowBreakpoint.LG: 8,
                                ft.ResponsiveRowBreakpoint.XL: 7,
                            },
                            padding=20 if es_movil else 32,
                            bgcolor=ft.Colors.WHITE,
                            border_radius=24,
                            shadow=ft.BoxShadow(
                                blur_radius=18,
                                color=ft.Colors.with_opacity(
                                    0.1, ft.Colors.BLACK
                                ),
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
                                                    ft.Icons.PERSON_ADD_ALT_1,
                                                    size=32,
                                                    color="#6A0404",
                                                ),
                                            ),
                                        ],
                                    ),
                                    ft.Text(
                                        "Crear cuenta",
                                        size=28,
                                        weight=ft.FontWeight.BOLD,
                                        color="#6A0404",
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                    ft.Text(
                                        "Completa tus datos para comenzar.",
                                        size=14,
                                        color="#806B63",
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                    ft.ResponsiveRow(
                                        spacing=12,
                                        run_spacing=12,
                                        controls=[
                                            ft.Container(
                                                content=campo,
                                                col={
                                                    ft.ResponsiveRowBreakpoint.XS: (
                                                        12
                                                        if ancho_completo
                                                        else 6
                                                    ),
                                                    ft.ResponsiveRowBreakpoint.MD: (
                                                        12
                                                        if ancho_completo
                                                        else 6
                                                    ),
                                                },
                                            )
                                            for campo, ancho_completo in (
                                                (self.txt_nombre, False),
                                                (
                                                    self.txt_primer_apellido,
                                                    False,
                                                ),
                                                (
                                                    self.txt_segundo_apellido,
                                                    False,
                                                ),
                                                (self.txt_telefono, False),
                                                (self.txt_correo, True),
                                                (self.txt_contrasena, False),
                                                (
                                                    self.txt_confirmar_contrasena,
                                                    False,
                                                ),
                                            )
                                        ],
                                    ),
                                    ft.Text(
                                        "La contraseña debe tener al menos 8 caracteres, "
                                        "una mayúscula, una minúscula, un número y un símbolo.",
                                        size=12,
                                        color="#806B63",
                                    ),
                                    self.txt_error,
                                    self.btn_crear_cuenta,
                                    ft.TextButton(
                                        "Volver al inicio",
                                        icon=ft.Icons.ARROW_BACK,
                                        on_click=self.on_volver,
                                    ),
                                ],
                            ),
                        )
                    ],
                ),
            ],
        )

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

    def intentar_registro(self, e):
        if self.page:
            self.page.run_task(self._intentar_registro_async, e)

    async def _intentar_registro_async(self, e):
        try:
            self.txt_error.value = ""
            url = f"{BASE_URL}/api/registro"

            datos_usuario = {
                "nombre": self.txt_nombre.value.strip()
                if self.txt_nombre.value
                else "",
                "primer_apellido": self.txt_primer_apellido.value.strip()
                if self.txt_primer_apellido.value
                else "",
                "segundo_apellido": self.txt_segundo_apellido.value.strip()
                if self.txt_segundo_apellido.value
                else "",
                "telefono": self.txt_telefono.value.strip()
                if self.txt_telefono.value
                else "",
                "correo": self.txt_correo.value.strip().lower()
                if self.txt_correo.value
                else "",
                "contrasena": self.txt_contrasena.value.strip()
                if self.txt_contrasena.value
                else "",
            }

            confirmar_contrasena = (
                self.txt_confirmar_contrasena.value.strip()
                if self.txt_confirmar_contrasena.value
                else ""
            )
            errores = []
            campos_obligatorios = (
                ("Nombre", datos_usuario["nombre"]),
                ("Primer apellido", datos_usuario["primer_apellido"]),
                ("Segundo apellido", datos_usuario["segundo_apellido"]),
                ("Teléfono", datos_usuario["telefono"]),
                ("Correo electrónico", datos_usuario["correo"]),
                ("Contraseña", datos_usuario["contrasena"]),
                ("Confirmación de contraseña", confirmar_contrasena),
            )
            faltantes = [
                nombre for nombre, valor in campos_obligatorios if not valor
            ]
            if faltantes:
                errores.append(
                    f"Completa los siguientes campos: {', '.join(faltantes)}."
                )
            if datos_usuario["nombre"] and not nombre_valido(
                datos_usuario["nombre"]
            ):
                errores.append(
                    "El nombre solo debe contener letras, espacios, guiones o apóstrofos."
                )
            if datos_usuario["primer_apellido"] and not nombre_valido(
                datos_usuario["primer_apellido"]
            ):
                errores.append(
                    "El primer apellido solo debe contener letras, espacios, guiones o apóstrofos."
                )
            if datos_usuario["segundo_apellido"] and not nombre_valido(
                datos_usuario["segundo_apellido"]
            ):
                errores.append(
                    "El segundo apellido solo debe contener letras, espacios, guiones o apóstrofos."
                )
            if datos_usuario["telefono"] and not telefono_valido(
                datos_usuario["telefono"]
            ):
                errores.append(
                    "El teléfono debe contener exactamente 10 dígitos."
                )
            if datos_usuario["correo"] and not correo_valido(
                datos_usuario["correo"]
            ):
                errores.append("Ingresa un correo electrónico válido.")
            if datos_usuario["contrasena"]:
                requisitos_pendientes = requisitos_contrasena_pendientes(
                    datos_usuario["contrasena"]
                )
                if requisitos_pendientes:
                    errores.append(
                        "La contraseña debe cumplir con: "
                        + ", ".join(requisitos_pendientes)
                        + "."
                    )
            if (
                datos_usuario["contrasena"]
                and confirmar_contrasena
                and datos_usuario["contrasena"] != confirmar_contrasena
            ):
                errores.append("Las contraseñas no coinciden.")

            if errores:
                self.mostrar_alerta_validacion("\n".join(errores))
                return

            self.btn_crear_cuenta.disabled = True
            if self.page:
                self.page.update()

            respuesta = await asyncio.to_thread(
                requests.post,
                url,
                json=datos_usuario,
                timeout=25,
            )
            self.btn_crear_cuenta.disabled = False

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
                self.on_registro_exitoso(
                    datos.get("id"),
                    datos_usuario["nombre"],
                    datos_usuario["primer_apellido"],
                    token,
                )
            else:
                try:
                    detalle = respuesta.json().get("detail", "")
                except ValueError:
                    detalle = ""

                detalle_normalizado = str(detalle).casefold()
                correo_duplicado = (
                    respuesta.status_code == 409
                    or "unique constraint failed" in detalle_normalizado
                    and "correo" in detalle_normalizado
                    or "ya existe una cuenta con ese correo"
                    in detalle_normalizado
                )

                if correo_duplicado:
                    alerta = ft.AlertDialog(
                        modal=True,
                        title=ft.Text("Correo ya registrado"),
                        content=ft.Text(
                            "Ya existe una cuenta con ese correo. Inicia sesión o usa otro correo."
                        ),
                        actions=[
                            ft.TextButton(
                                "Entendido",
                                on_click=lambda e: self.cerrar_dialogo_seguro(),
                            )
                        ],
                    )
                    self.abrir_dialogo_seguro(alerta)
                else:
                    self.txt_error.value = (
                        detalle
                        if respuesta.status_code == 422
                        and isinstance(detalle, str)
                        else "Error al registrar el usuario"
                    )
                    if self.page:
                        self.page.update()
        except Exception:
            self.btn_crear_cuenta.disabled = False
            self.txt_error.value = "No se pudo conectar con el servidor"
            if self.page:
                self.page.update()

    def validar_correo_en_tiempo_real(self, e):
        valor = (e.control.value or "").strip()
        e.control.error_text = (
            "Ingresa un correo electrónico válido."
            if valor and not correo_valido(valor)
            else None
        )
        e.control.update()

    def validar_telefono(self, e):
        valor = (e.control.value or "").strip()
        e.control.error_text = (
            "El teléfono debe contener exactamente 10 dígitos."
            if valor and not telefono_valido(valor)
            else None
        )
        e.control.update()

    def validar_contrasena(self, e):
        valor = e.control.value or ""
        pendientes = requisitos_contrasena_pendientes(valor)
        e.control.error_text = (
            "Falta: " + ", ".join(pendientes).lower()
            if valor and pendientes
            else None
        )
        e.control.update()
        if self.txt_confirmar_contrasena.value:
            self.validar_confirmacion_contrasena(None)

    def validar_confirmacion_contrasena(self, e):
        contrasena = self.txt_contrasena.value or ""
        confirmar = self.txt_confirmar_contrasena.value or ""
        self.txt_confirmar_contrasena.error_text = (
            "Las contraseñas no coinciden."
            if confirmar and contrasena != confirmar
            else None
        )
        self.txt_confirmar_contrasena.update()

    def mostrar_alerta_validacion(self, mensaje):
        self.txt_error.value = mensaje
        alerta = ft.AlertDialog(
            modal=True,
            title=ft.Text("Revisa los datos"),
            content=ft.Text(mensaje),
            actions=[
                ft.TextButton(
                    "Entendido",
                    on_click=lambda e: self.cerrar_dialogo_seguro(),
                )
            ],
        )
        self.abrir_dialogo_seguro(alerta)