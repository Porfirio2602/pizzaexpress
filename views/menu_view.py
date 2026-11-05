import flet as ft

class MenuView(ft.Container):
    def __init__(self, on_cart_change, categoria_inicial="Pizzas", es_movil=False):
        super().__init__()
        self.on_cart_change = on_cart_change
        self.expand = True
        self.padding = 15
        self.bgcolor = "#F9F9F9"  # Fondo gris suave para resaltar las tarjetas

        # Catálogo ampliado organizado por categorías (Pizzas, Bebidas, Extras)
        self.productos = [
            # Pizzas
            {"id": 1, "categoria": "Pizzas", "nombre": "Pizza Pepperoni", "descripcion": "Mozzarella dorada, pepperoni abundante y salsa de tomate de la casa.", "precio": 180.00, "imagen": "https://images.unsplash.com/photo-1628840042765-356cda07504e?w=300"},
            {"id": 2, "categoria": "Pizzas", "nombre": "Pizza Hawaiana", "descripcion": "Jamón jugoso, piña dulce y una generosa capa de queso fundido.", "precio": 170.00, "imagen": "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=300"},
            {"id": 3, "categoria": "Pizzas", "nombre": "Pizza Carnívora", "descripcion": "Pepperoni, tocino crujiente, jamón y salchicha italiana en cada bocado.", "precio": 210.00, "imagen": "https://images.unsplash.com/photo-1534308983496-4fabb1a015ee?w=300"},
            {"id": 4, "categoria": "Pizzas", "nombre": "Pizza Mexicana", "descripcion": "Chorizo doradito, jalapeño, cebolla morada y frijoles refritos.", "precio": 195.00, "imagen": "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=300"},
            
            # Bebidas
            {"id": 5, "categoria": "Bebidas", "nombre": "Coca-Cola 2L", "descripcion": "Bien fría y burbujeante, ideal para compartir en la mesa.", "precio": 45.00, "imagen": "https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=300"},
            {"id": 6, "categoria": "Bebidas", "nombre": "Agua Fresa Natural 1L", "descripcion": "Agua fresca de fresa, natural y preparada el mismo día.", "precio": 35.00, "imagen": "https://images.unsplash.com/photo-1556679343-c7306c1976bc?w=300"},
            {"id": 7, "categoria": "Bebidas", "nombre": "Te Manzanita 600ml", "descripcion": "Refrescante sabor a manzana en presentación individual.", "precio": 28.00, "imagen": "https://images.unsplash.com/photo-1600271886742-f049cd451bba?w=300"},

            # Extras
            {"id": 8, "categoria": "Extras", "nombre": "Papas a la Francesa", "descripcion": "Papas doradas y crujientes, con aderezo especial de la casa.", "precio": 65.00, "imagen": "https://images.unsplash.com/photo-1573080496219-bb080dd4f877?w=300"},
            {"id": 9, "categoria": "Extras", "nombre": "Alitas BBQ (6 pzas)", "descripcion": "Alitas jugosas cubiertas con BBQ ahumada y un toque picante.", "precio": 95.00, "imagen": "https://images.unsplash.com/photo-1527477396000-e27163b481c2?w=300"},
            {"id": 10, "categoria": "Extras", "nombre": "Pan de Ajo con Queso", "descripcion": "Baguette tostado con mantequilla de ajo y queso gratinado.", "precio": 55.00, "imagen": "https://images.unsplash.com/photo-1573140247632-f8fd74997d5c?w=300"},
        ]

        # Estructura de cantidades para el carrito
        self.estado_carrito = {p["id"]: {"nombre": p["nombre"], "precio": p["precio"], "cantidad": 0} for p in self.productos}
        self.productos_activos = set()

        if es_movil:
            self.lista_productos_column = ft.Column(
                spacing=15,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            )
        else:
            self.lista_productos_column = ft.ResponsiveRow(
                spacing=15,
                run_spacing=15,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            )

        # Selector visual de categorías dentro del menú
        self.categoria_actual = categoria_inicial
        self.tabs_categoria = ft.Row(
            [
                self.crear_boton_categoria("Pizzas"),
                self.crear_boton_categoria("Bebidas"),
                self.crear_boton_categoria("Extras"),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
            wrap=True,
        )

        self.construir_catalogo()

        self.content = ft.Column([
            ft.Text(
                "CONOCE NUESTRO MENÚ",
                size=24,
                weight=ft.FontWeight.BOLD,
                color="#6A0404",
            ),
            ft.Text("Elige tus favoritas y armemos tu pedido", size=15, color=ft.Colors.GREY_700),
            ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
            self.tabs_categoria,
            ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
            self.lista_productos_column
        ], expand=True)

    def crear_boton_categoria(self, nombre_cat):
        activo = self.categoria_actual == nombre_cat
        return ft.Container(
            content=ft.Text(
                nombre_cat,
                weight=ft.FontWeight.BOLD if activo else ft.FontWeight.W_500,
                color=ft.Colors.WHITE if activo else "#6A0404",
                size=16,
            ),
            padding=ft.Padding(left=18, top=9, right=18, bottom=9),
            bgcolor="#6A0404" if activo else "#FFF1E7",
            border_radius=22,
            border=ft.Border(
                top=ft.BorderSide(1, "#6A0404" if activo else "#F0D8CA"),
                bottom=ft.BorderSide(1, "#6A0404" if activo else "#F0D8CA"),
                left=ft.BorderSide(1, "#6A0404" if activo else "#F0D8CA"),
                right=ft.BorderSide(1, "#6A0404" if activo else "#F0D8CA"),
            ),
            on_click=lambda e: self.cambiar_categoria(nombre_cat)
        )

    def cambiar_categoria(self, nueva_cat):
        self.categoria_actual = nueva_cat
        # Actualizar estilo de pestañas
        self.tabs_categoria.controls = [
            self.crear_boton_categoria("Pizzas"),
            self.crear_boton_categoria("Bebidas"),
            self.crear_boton_categoria("Extras"),
        ]
        self.construir_catalogo()
        self.actualizar_si_montado(self)

    @staticmethod
    def actualizar_si_montado(control):
        try:
            if control.page is not None:
                control.update()
        except RuntimeError:
            return

    def construir_catalogo(self):
        controles = []
        # Filtrar productos según la categoría seleccionada
        productos_filtrados = [p for p in self.productos if p["categoria"] == self.categoria_actual]

        for prod in productos_filtrados:
            prod_id = prod["id"]
            cantidad = self.estado_carrito[prod_id]["cantidad"]

            txt_cantidad = ft.Text(
                value=str(cantidad) if cantidad > 0 else "",
                width=30,
                text_align=ft.TextAlign.CENTER,
                size=15,
                weight=ft.FontWeight.BOLD,
                color="#6A0404",
                visible=prod_id in self.productos_activos,
            )
            badge_cantidad = ft.Container(
                content=txt_cantidad,
                width=34,
                height=30,
                alignment=ft.Alignment.CENTER,
                bgcolor="#FFF1E7",
                border_radius=10,
            )
            controles_cantidad = ft.Row(
                spacing=0,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                visible=prod_id in self.productos_activos,
            )
            boton_agregar = ft.IconButton(
                icon=ft.Icons.ADD,
                icon_color="#6A0404",
                icon_size=20,
                bgcolor="#FEEFE5",
                width=40,
                height=40,
                padding=8,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=12),
                    overlay_color=ft.Colors.with_opacity(0.12, "#6A0404"),
                ),
                visual_density=ft.VisualDensity.COMPACT,
                size_constraints=ft.BoxConstraints(
                    min_width=40,
                    max_width=40,
                    min_height=40,
                    max_height=40,
                ),
                visible=prod_id not in self.productos_activos,
            )
            boton_menos = ft.IconButton(
                icon=ft.Icons.REMOVE_CIRCLE_OUTLINE,
                icon_color=ft.Colors.GREY_600,
                icon_size=19,
                width=36,
                height=36,
                padding=6,
                bgcolor=ft.Colors.GREY_100,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=11),
                ),
                visual_density=ft.VisualDensity.COMPACT,
                size_constraints=ft.BoxConstraints(
                    min_width=36,
                    max_width=36,
                    min_height=36,
                    max_height=36,
                ),
            )
            boton_mas = ft.IconButton(
                icon=ft.Icons.ADD,
                icon_color="#6A0404",
                icon_size=20,
                bgcolor="#FEEFE5",
                width=40,
                height=40,
                padding=8,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=12),
                    overlay_color=ft.Colors.with_opacity(0.12, "#6A0404"),
                ),
                visual_density=ft.VisualDensity.COMPACT,
                size_constraints=ft.BoxConstraints(
                    min_width=40,
                    max_width=40,
                    min_height=40,
                    max_height=40,
                ),
            )
            boton_agregar.on_click = (
                lambda e, pid=prod_id, campo=txt_cantidad, fila=controles_cantidad, add=boton_agregar:
                self.incrementar_cantidad(pid, campo, fila, add)
            )
            boton_menos.on_click = (
                lambda e, pid=prod_id, campo=txt_cantidad, fila=controles_cantidad, add=boton_agregar:
                self.decrementar_cantidad(pid, campo, fila, add)
            )
            boton_mas.on_click = boton_agregar.on_click
            controles_cantidad.controls = [
                boton_menos,
                badge_cantidad,
                boton_mas,
            ]

            tarjeta = ft.Container(
                col={
                    ft.ResponsiveRowBreakpoint.MD: 6,
                    ft.ResponsiveRowBreakpoint.XL: 3,
                },
                content=ft.Row([
                    ft.Container(
                        content=ft.Image(
                            src=prod["imagen"],
                            width=90,
                            height=90,
                            fit="cover"
                        ),
                        border_radius=10,
                        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                        width=90,
                        height=90
                    ),
                    ft.VerticalDivider(width=10, color=ft.Colors.TRANSPARENT),
                    ft.Column([
                        ft.Text(prod["nombre"], weight=ft.FontWeight.BOLD, size=18, color="#1A1A1A"),
                        ft.Text(
                            prod["descripcion"],
                            size=14,
                            color=ft.Colors.GREY_600,
                            max_lines=2,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        ft.Row([
                            ft.Text(
                                f"${prod['precio']:.2f}",
                                weight=ft.FontWeight.W_900,
                                size=17,
                                color="#6A0404",
                            ),
                            ft.Row([
                                boton_agregar,
                                controles_cantidad,
                            ], spacing=2, alignment=ft.MainAxisAlignment.END, tight=True)
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, expand=True)
                    ], expand=True, spacing=4)
                ], alignment=ft.MainAxisAlignment.START, expand=True),
                bgcolor=ft.Colors.WHITE,
                padding=12,
                border_radius=14,
                shadow=ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=6,
                    color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
                    offset=ft.Offset(0, 3)
                )
            )
            controles.append(tarjeta)

        self.lista_productos_column.controls = controles

    def actualizar_controles_cantidad(self, producto_id, campo, controles, boton_agregar):
        activo = (
            producto_id in self.productos_activos
            and self.estado_carrito[producto_id]["cantidad"] > 0
        )
        controles.visible = activo
        campo.visible = activo
        boton_agregar.visible = not activo
        self.actualizar_si_montado(controles)
        self.actualizar_si_montado(boton_agregar)

    def incrementar_cantidad(self, producto_id, campo, controles, boton_agregar):
        self.productos_activos.add(producto_id)
        self.estado_carrito[producto_id]["cantidad"] += 1
        campo.value = str(self.estado_carrito[producto_id]["cantidad"])
        self.actualizar_controles_cantidad(producto_id, campo, controles, boton_agregar)
        self.on_cart_change()

    def decrementar_cantidad(self, producto_id, campo, controles, boton_agregar):
        cantidad = self.estado_carrito[producto_id]["cantidad"]
        if cantidad == 0:
            return
        cantidad -= 1
        self.estado_carrito[producto_id]["cantidad"] = cantidad
        campo.value = str(cantidad) if cantidad > 0 else ""
        if cantidad == 0:
            self.productos_activos.discard(producto_id)
        self.actualizar_controles_cantidad(producto_id, campo, controles, boton_agregar)
        self.on_cart_change()

    def obtener_items_estado(self):
        return [
            {"nombre": datos["nombre"], "precio": datos["precio"], "cantidad": datos["cantidad"]}
            for pid, datos in self.estado_carrito.items() if datos["cantidad"] > 0
        ]

    def limpiar_carrito(self):
        for datos in self.estado_carrito.values():
            datos["cantidad"] = 0
        self.productos_activos.clear()
        self.construir_catalogo()
        self.actualizar_si_montado(self)