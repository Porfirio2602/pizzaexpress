import asyncio
import requests
import flet as ft
from config import BASE_URL


class PersonalLoginView(ft.Container):
    def __init__(
        self,
        rol,
        on_login_exitoso,
        on_volver,
        es_movil=False,
    ):
        super().__init__()
        self.rol = rol
        self.on_login_exitoso = on_login_exitoso
        self.on_volver = on_volver
        self.expand = True
        self.alignment = ft.Alignment.CENTER

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

        self.txt_correo = ft.TextField(
            label="Correo del personal",
            value="sajusa1@gmail.com" if rol == "gerente" else "",
            keyboard_type=ft.KeyboardType.EMAIL,
            width=300 if es_movil else None,
            expand=not es_movil,
            prefix_icon=ft.Icons.BADGE_OUTLINED,
            on_submit=self.iniciar_sesion,
        )
        self.txt_contrasena = ft.TextField(
            label="Contraseña",
            password=True,
            can_reveal_password=True,
            width=300 if es_movil else None,
            expand=not es_movil,
            prefix_icon=ft.Icons.KEY_OUTLINED,
            on_submit=self.iniciar_sesion,
        )
        self.txt_error = ft.Text("", color=ft.Colors.RED_700, size=13)

        for campo in (self.txt_correo, self.txt_contrasena):
            campo.height = 58 if es_movil else 62
            campo.filled = True
            campo.fill_color = "#FFFCFA"
            campo.border = borde_campo
            campo.content_padding = ft.Padding(
                left=14,
                top=14,
                right=10,
                bottom=14,
            )

        if rol == "gerente":
            titulo = "Administración general"
            subtitulo = "Accede a la administración general del negocio."
            icono_cabecera = ft.Icons.ADMIN_PANEL_SETTINGS
            icono_boton = ft.Icons.SHIELD
        elif rol == "cocinero":
            titulo = "Estación de Cocina"
            subtitulo = "Accede a las comandas asignadas en tiempo real."
            icono_cabecera = ft.Icons.SOUP_KITCHEN
            icono_boton = ft.Icons.SOUP_KITCHEN
        else:
            titulo = "Comanda y caja de venta"
            subtitulo = "Accede a la comanda y caja de venta diaria."
            icono_cabecera = ft.Icons.STOREFRONT
            icono_boton = ft.Icons.STOREFRONT

        self.btn_iniciar = ft.FilledButton(
            content=ft.Row(
                [
                    ft.Icon(
                        icono_boton,
                        size=19,
                    ),
                    ft.Text("Iniciar sesión"),
                    ft.Icon(
                        ft.Icons.ARROW_FORWARD,
                        size=19,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10,
                tight=True,
            ),
            bgcolor="#6A0404",
            color=ft.Colors.WHITE,
            height=52,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=16),
            ),
            on_click=self.iniciar_sesion,
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
                                ft.ResponsiveRowBreakpoint.MD: 8,
                                ft.ResponsiveRowBreakpoint.LG: 5,
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
                                spacing=14,
                                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
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
                                                    icono_cabecera,
                                                    size=34,
                                                    color="#6A0404",
                                                ),
                                            ),
                                        ],
                                    ),
                                    ft.Text(
                                        titulo,
                                        size=24,
                                        weight=ft.FontWeight.BOLD,
                                        color="#6A0404",
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                    ft.Text(
                                        subtitulo,
                                        size=14,
                                        color="#806B63",
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                    self.txt_correo,
                                    self.txt_contrasena,
                                    self.txt_error,
                                    self.btn_iniciar,
                                    ft.Text(
                                        "Sesión protegida para terminal del local.",
                                        size=12,
                                        color="#806B63",
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                    ft.TextButton(
                                        "Volver",
                                        style=ft.ButtonStyle(color="#6A0404"),
                                        on_click=lambda e: self.on_volver(),
                                    ),
                                ],
                            ),
                        )
                    ],
                )
            ],
        )

    def iniciar_sesion(self, e):
        if self.page is not None:
            self.page.run_task(self._iniciar_sesion_async, e)

    async def _iniciar_sesion_async(self, e):
        correo = (self.txt_correo.value or "").strip().lower()
        contrasena = self.txt_contrasena.value or ""
        if not correo or not contrasena:
            self.txt_error.value = "Escribe tu correo y contraseña."
            self.actualizar_error()
            return

        self.txt_error.value = ""
        self.btn_iniciar.disabled = True
        if self.page is not None:
            self.page.update()

        try:
            respuesta = await asyncio.to_thread(
                requests.post,
                f"{BASE_URL}/api/personal/login",
                json={
                    "correo": correo,
                    "contrasena": contrasena,
                    "rol": self.rol,
                },
                timeout=45,
            )
        except requests.RequestException:
            self.btn_iniciar.disabled = False
            self.txt_error.value = (
                "No se pudo conectar con el servidor. Inténtalo de nuevo."
            )
            self.actualizar_error()
            return

        self.btn_iniciar.disabled = False
        if respuesta.status_code != 200:
            try:
                detalle = respuesta.json().get("detail")
            except ValueError:
                detalle = None
            self.txt_error.value = (
                detalle
                if isinstance(detalle, str)
                else "No se pudo iniciar sesión. Revisa tus datos."
            )
            self.actualizar_error()
            return

        personal = respuesta.json()
        if personal.get("rol") != self.rol or not personal.get("token"):
            self.txt_error.value = "La cuenta no tiene acceso a esta sección."
            self.actualizar_error()
            return
        self.on_login_exitoso(personal)

    def actualizar_error(self):
        try:
            if self.page is not None:
                self.update()
        except RuntimeError:
            return