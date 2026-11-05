import flet as ft

class InicioView(ft.Container):
    def __init__(self, on_ir_a_menu, es_movil=False):
        super().__init__()
        self.on_ir_a_menu = on_ir_a_menu
        self.expand = True
        self.padding = 15
        self.bgcolor = "#F9F9F9"

        contenido_inicio = ft.Column(
                        [
                # Banner principal (Hero Section)
                # Banner principal (Hero Section) con color corporativo y esquinas redondeadas
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("¡Bienvenido a PizzaExpress! 🍕", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                            ft.Text("Las mejores pizzas artesanales, listas y calientes hasta la puerta de tu hogar.", size=13, color=ft.Colors.WHITE_70),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=5,
                    ),
                    bgcolor="#6A0404",
                    padding=20,
                    border_radius=16,
                    shadow=ft.BoxShadow(
                        spread_radius=1,
                        blur_radius=8,
                        color=ft.Colors.with_opacity(0.15, ft.Colors.BLACK),
                        offset=ft.Offset(0, 4)
                    )
                ),
                
                ft.Divider(height=15, color=ft.Colors.TRANSPARENT),

                # Sección de Promociones / Especiales
                ft.Text("🔥 Especiales del Día", size=18, weight=ft.FontWeight.BOLD, color="#2B2B2B"),
                
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Container(
                                content=ft.Image(
                                    src="https://images.unsplash.com/photo-1513104890138-7c749659a591?w=300",
                                    width=80,
                                    height=80,
                                    fit="cover"
                                ),
                                border_radius=10,
                                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                                width=80,
                                height=80
                            ),
                            ft.VerticalDivider(width=10, color=ft.Colors.TRANSPARENT),
                            ft.Column(
                                [
                                    ft.Text("Combo Familiar 2x1", weight=ft.FontWeight.BOLD, size=15, color="#1A1A1A"),
                                    ft.Text("Lleva dos pizzas grandes de especialidad por el precio de una.", size=11, color=ft.Colors.GREY_700, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                                    ft.Text("¡Por tiempo limitado!", size=11, weight=ft.FontWeight.BOLD, color="#6A0404"),
                                ],
                                expand=True,
                                spacing=3
                            )
                        ],
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    bgcolor=ft.Colors.WHITE,
                    padding=12,
                    border_radius=14,
                    shadow=ft.BoxShadow(
                        spread_radius=1,
                        blur_radius=6,
                        color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
                        offset=ft.Offset(0, 3)
                    )
                ),

                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),

                # Sección de Categorías Rápidas interactivas
                ft.Text("¿Qué se te antoja hoy?", size=18, weight=ft.FontWeight.BOLD, color="#2B2B2B"),
                
                ft.Row(
                    [
                        self.crear_chip_categoria("🍕 Pizzas", "#6A0404", "Pizzas"),
                        self.crear_chip_categoria("🥤 Bebidas", "#333333", "Bebidas"),
                        self.crear_chip_categoria("🍟 Extras", "#333333", "Extras"),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),

                ft.Divider(height=15, color=ft.Colors.TRANSPARENT),

                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(ft.Icons.LOCAL_PIZZA, color="#6A0404", size=32),
                            ft.Text("Calidad y sabor garantizado en cada rebanada", size=12, italic=True, color=ft.Colors.GREY_600, text_align=ft.TextAlign.CENTER),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=5,
                    ),
                    alignment=ft.Alignment.CENTER,
                    padding=10,
                )
                        ],
                        scroll=ft.ScrollMode.AUTO,
                        expand=True,
                    )
        if es_movil:
            self.content = contenido_inicio
        else:
            self.content = ft.ResponsiveRow(
                expand=True,
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        col={
                            ft.ResponsiveRowBreakpoint.XS: 12,
                            ft.ResponsiveRowBreakpoint.XL: 10,
                        },
                        content=contenido_inicio,
                    )
                ],
            )

    def crear_chip_categoria(self, texto, color_bg, categoria_destino):
        return ft.GestureDetector(
            on_tap=lambda e: self.on_ir_a_menu(categoria_destino),
            content=ft.Container(
                content=ft.Text(texto, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, size=13),
                bgcolor=color_bg,
                padding=ft.Padding(left=16, top=10, right=16, bottom=10),
                border_radius=20,
                alignment=ft.Alignment.CENTER,
            )
        )