import flet as ft

class ItemPizzaCard(ft.Container):
    def __init__(self, imagen_src, precio_unitario, nombre, on_change_callback):
        super().__init__()
        self.imagen_src = imagen_src
        self.precio_unitario = precio_unitario
        self.nombre = nombre
        self.cantidad = 0
        self.on_change_callback = on_change_callback

        self.txt_total = ft.Text("$0.00", size=15, weight="bold", color="#6A0404")
        self.txt_cantidad = ft.TextField(
            value="0", width=30, height=28, text_align=ft.TextAlign.CENTER,
            content_padding=0, border_color=ft.Colors.GREY_300, border_radius=6, text_size=14,
            on_change=self.cambiar_manual
        )

        self.controles_cantidad = ft.Row(
            controls=[
                ft.IconButton(icon=ft.Icons.REMOVE_ROUNDED, icon_size=18, width=24, height=24, padding=0, icon_color=ft.Colors.GREY_700, on_click=self.decrementar),
                self.txt_cantidad,
                ft.IconButton(icon=ft.Icons.ADD_ROUNDED, icon_size=18, width=24, height=24, padding=0, icon_color="#6A0404", on_click=self.incrementar),
                ft.VerticalDivider(width=4, color=ft.Colors.TRANSPARENT),
                self.txt_total,
            ],
            spacing=2, vertical_alignment=ft.CrossAxisAlignment.CENTER, visible=False
        )

        self.btn_agregar_inicial = ft.Container(
            content=ft.IconButton(icon=ft.Icons.ADD_ROUNDED, icon_size=19, width=28, height=28, padding=0, icon_color=ft.Colors.WHITE, on_click=self.incrementar),
            bgcolor="#6A0404",
            border_radius=8,
            visible=True,
            alignment=ft.Alignment.CENTER
        )

        self.padding = 10
        self.margin = 8
        self.border_radius = 12
        self.bgcolor = ft.Colors.WHITE
        self.shadow = ft.BoxShadow(
            spread_radius=0,
            blur_radius=8,
            color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK),
            offset=ft.Offset(0, 3)
        )
        
        self.content = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Image(src=self.imagen_src, width=45, height=45, fit="contain"),
                            bgcolor=ft.Colors.GREY_50,
                            padding=4,
                            border_radius=8
                        ),
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Text(self.nombre, size=15, weight="bold", color=ft.Colors.BLACK_87, overflow=ft.TextOverflow.ELLIPSIS),
                                    ft.Text(f"${self.precio_unitario:.2f} c/u", size=14, color=ft.Colors.GREY_600, weight="w500"),
                                ], spacing=1, alignment=ft.MainAxisAlignment.CENTER
                            ), width=95
                        ),
                    ], spacing=6
                ),
                ft.Row(controls=[self.btn_agregar_inicial, self.controles_cantidad], alignment=ft.MainAxisAlignment.END, spacing=2)
            ]
        )

    def actualizar_calculo(self):
        nuevo_total = self.precio_unitario * self.cantidad
        self.txt_total.value = f"${nuevo_total:.2f}"
        self.txt_cantidad.value = str(self.cantidad)
        
        self.controles_cantidad.visible = self.cantidad > 0
        self.btn_agregar_inicial.visible = self.cantidad == 0
        self.update()
        if self.on_change_callback:
            self.on_change_callback()

    def incrementar(self, e):
        self.cantidad += 1
        self.actualizar_calculo()

    def decrementar(self, e):
        if self.cantidad > 0:
            self.cantidad -= 1
            self.actualizar_calculo()

    def cambiar_manual(self, e):
        val_str = self.txt_cantidad.value
        # Si el usuario borra el texto para escribir, no ocultamos los controles de inmediato
        if val_str == "":
            return
        try:
            val = int(val_str)
            if val >= 0:
                self.cantidad = val
                self.actualizar_calculo()
        except ValueError:
            return