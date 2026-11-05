import flet as ft

class MenuLateral(ft.Container):
    def __init__(
        self,
        usuario_actual,
        on_login_click,
        on_registro_click,
        on_logout_click,
        on_close_click,
        personal_actual=None,
        on_vendedor_click=None,
        on_gerencia_click=None,
        on_personal_logout_click=None,
    ):
        super().__init__()
        self.usuario_actual = usuario_actual
        self.personal_actual = personal_actual or {}
        self.on_login_click = on_login_click
        self.on_registro_click = on_registro_click
        self.on_logout_click = on_logout_click
        self.on_close_click = on_close_click
        self.on_vendedor_click = on_vendedor_click
        self.on_gerencia_click = on_gerencia_click
        self.on_personal_logout_click = on_personal_logout_click

        self.columna_contenido_menu = ft.Column([], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5)
        
        # Poblamos los controles iniciales sin llamar a update() todavía
        self._poblar_menu_controls()

        self.bgcolor = "#6A0404"
        self.width = 220
        self.height = 760
        self.visible = False
        self.padding = 10
        self.content = ft.Column([
            ft.Container(height=10),
            ft.Row([
                ft.IconButton(
                    icon=ft.Icons.CLOSE,
                    icon_color=ft.Colors.WHITE,
                    on_click=self.on_close_click
                )
            ], alignment=ft.MainAxisAlignment.END),
            ft.Container(height=10),
            self.columna_contenido_menu
        ])

    def _poblar_menu_controls(self):
        self.columna_contenido_menu.controls.clear()
        if self.usuario_actual["nombre"]:
            self.columna_contenido_menu.controls.extend([
                ft.Icon(ft.Icons.ACCOUNT_CIRCLE, size=70, color=ft.Colors.WHITE),
                ft.Container(height=5),
                ft.Text(f"{self.usuario_actual['nombre']} {self.usuario_actual['apellido']}", color=ft.Colors.WHITE, size=15, weight="bold", text_align=ft.TextAlign.CENTER),
                ft.Container(height=10),
                ft.TextButton(
                    content=ft.Text("Cerrar Sesión", color=ft.Colors.WHITE, size=15),
                    on_click=self.on_logout_click,
                ),
            ])
        else:
            self.columna_contenido_menu.controls.extend([
                ft.Icon(ft.Icons.ACCOUNT_CIRCLE, size=70, color=ft.Colors.WHITE),
                ft.Container(height=10),
                ft.TextButton(
                    content=ft.Text("Iniciar Sesión", color=ft.Colors.WHITE, size=15),
                    on_click=self.on_login_click,
                ),
                ft.Container(height=5),
                ft.TextButton(
                    content=ft.Text("Registrarse", color=ft.Colors.WHITE, size=15),
                    on_click=self.on_registro_click,
                ),
            ])
        self.columna_contenido_menu.controls.extend(
            [
                ft.Divider(color="#8E3B3B", height=16),
                ft.TextButton(
                    content=ft.Text(
                        "Vendedor",
                        color=ft.Colors.WHITE,
                        size=15,
                    ),
                    on_click=self.on_vendedor_click,
                ),
                ft.TextButton(
                    content=ft.Text(
                        "Gerencia",
                        color=ft.Colors.WHITE,
                        size=15,
                    ),
                    on_click=self.on_gerencia_click,
                ),
            ]
        )
        if self.personal_actual.get("token"):
            self.columna_contenido_menu.controls.extend(
                [
                    ft.Container(height=5),
                    ft.Text(
                        f"{self.personal_actual.get('nombre', '')} "
                        f"({self.personal_actual.get('rol', '').title()})",
                        color="#F8E8E0",
                        size=12,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.TextButton(
                        content=ft.Text(
                            "Cerrar sesión de personal",
                            color=ft.Colors.WHITE,
                            size=13,
                        ),
                        on_click=self.on_personal_logout_click,
                    ),
                ]
            )

    def actualizar_menu(self):
        self._poblar_menu_controls()
        # Verificamos que el control ya esté agregado a la página antes de actualizarlo
        if self.page is not None:
            self.update()

    def actualizar_personal(self, personal_actual):
        self.personal_actual = personal_actual
        self.actualizar_menu()