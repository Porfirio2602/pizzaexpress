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
        self.txt_correo = ft.TextField(
            label="Correo",
            value="sajusa1@gmail.com" if rol == "gerente" else "",
            keyboard_type=ft.KeyboardType.EMAIL,
            width=300 if es_movil else None,
            expand=not es_movil,
        )
        self.txt_contrasena = ft.TextField(
            label="Contraseña",
            password=True,
            can_reveal_password=True,
            width=300 if es_movil else None,
            expand=not es_movil,
        )
        self.txt_error = ft.Text("", color=ft.Colors.RED_700, size=13)

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
                            padding=28,
                            bgcolor=ft.Colors.WHITE,
                            border_radius=20,
                            shadow=ft.BoxShadow(
                                blur_radius=16,
                                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                                offset=ft.Offset(0, 5),
                            ),
                            content=ft.Column(
                                spacing=14,
                                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                                controls=[
                                    ft.Icon(
                                        ft.Icons.ADMIN_PANEL_SETTINGS
                                        if rol == "gerente"
                                        else ft.Icons.BADGE,
                                        size=40,
                                        color="#6A0404",
                                    ),
                                    ft.Text(
                                        "Acceso de Gerencia"
                                        if rol == "gerente"
                                        else "Acceso de Vendedor",
                                        size=24,
                                        weight=ft.FontWeight.BOLD,
                                        color="#6A0404",
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                    self.txt_correo,
                                    self.txt_contrasena,
                                    self.txt_error,
                                    ft.FilledButton(
                                        "Iniciar sesión",
                                        bgcolor="#6A0404",
                                        color=ft.Colors.WHITE,
                                        height=48,
                                        on_click=self.iniciar_sesion,
                                    ),
                                    ft.TextButton(
                                        "Volver",
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
        correo = (self.txt_correo.value or "").strip().lower()
        contrasena = self.txt_contrasena.value or ""
        if not correo or not contrasena:
            self.txt_error.value = "Escribe tu correo y contraseña."
            self.actualizar_error()
            return

        try:
            respuesta = requests.post(
                f"{BASE_URL}/api/personal/login",
                json={
                    "correo": correo,
                    "contrasena": contrasena,
                    "rol": self.rol,
                },
                headers={"ngrok-skip-browser-warning": "true"},
                timeout=45,
            )
        except requests.RequestException:
            self.txt_error.value = (
                "No se pudo conectar con el servidor. Inténtalo de nuevo."
            )
            self.actualizar_error()
            return

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
                self.txt_error.update()
        except RuntimeError:
            return
