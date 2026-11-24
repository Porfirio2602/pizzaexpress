import flet as ft
from components.pizzas_combinadas import (
    abrir_modal_combinar_pizza,
    obtener_mapa_disponibilidad,
    pizza_disponible_en_todas_versiones,
)


class MenuView(ft.Column):
    def __init__(
        self,
        on_cart_change=None,
        es_movil=False,
        mostrar_combinador=True,
        categoria_inicial="Todas",
    ):
        super().__init__()
        self.on_cart_change = on_cart_change
        self.es_movil = es_movil
        self.mostrar_combinador = mostrar_combinador
        self.expand = True
        self.spacing = 10

        self.categoria_seleccionada = categoria_inicial or "Todas"
        self.productos_activos = set()
        self.mapa_disponibilidad = obtener_mapa_disponibilidad()

        self.productos = [
            {
                "id": 1,
                "nombre": "Pizza Pepperoni",
                "precio": 180.00,
                "categoria": "Pizzas",
                "descripcion": "Queso mozzarella fundido y pepperoni dorado.",
                "imagen": "pizza_pepperoni.png",
            },
            {
                "id": 2,
                "nombre": "Pizza Hawaiana",
                "precio": 170.00,
                "categoria": "Pizzas",
                "descripcion": "Jamón ahumado, piña dulce y queso mozzarella.",
                "imagen": "pizza_hawaiana.png",
            },
            {
                "id": 3,
                "nombre": "Pizza Carnívora",
                "precio": 210.00,
                "categoria": "Pizzas",
                "descripcion": "Pepperoni, chorizo, carne molida y tocino.",
                "imagen": "pizza_carnivora.png",
            },
            {
                "id": 4,
                "nombre": "Pizza Mexicana",
                "precio": 195.00,
                "categoria": "Pizzas",
                "descripcion": "Chorizo, jalapeño, cebolla y pimiento morrón.",
                "imagen": "pizza_mexicana.png",
            },
            {
                "id": 5,
                "nombre": "Coca-Cola 2L",
                "precio": 45.00,
                "categoria": "Bebidas",
                "descripcion": "Refresco bien frío de 2 litros.",
                "imagen": "coca_cola.png",
            },
            {
                "id": 6,
                "nombre": "Agua Fresa Natural 1L",
                "precio": 35.00,
                "categoria": "Bebidas",
                "descripcion": "Agua fresca artesanal de fresa.",
                "imagen": "agua_fresa.png",
            },
            {
                "id": 7,
                "nombre": "Te Manzanita 600ml",
                "precio": 28.00,
                "categoria": "Bebidas",
                "descripcion": "Bebida refrescante sabor manzana.",
                "imagen": "manzanita.png",
            },
            {
                "id": 8,
                "nombre": "Papas a la Francesa",
                "precio": 65.00,
                "categoria": "Complementos",
                "descripcion": "Porción crujiente recién hecha.",
                "imagen": "papas.png",
            },
            {
                "id": 9,
                "nombre": "Alitas BBQ (6 pzas)",
                "precio": 95.00,
                "categoria": "Complementos",
                "descripcion": "Bañadas en salsa BBQ artesanal.",
                "imagen": "alitas.png",
            },
            {
                "id": 10,
                "nombre": "Pan de Ajo con Queso",
                "precio": 55.00,
                "categoria": "Complementos",
                "descripcion": "Crujiente pan con mantequilla de ajo y queso.",
                "imagen": "pan_ajo.png",
            },
        ]

        self.estado_carrito = {
            prod["id"]: {"cantidad": 0, "precio": prod["precio"]}
            for prod in self.productos
        }

        self.row_categorias = ft.Row(spacing=8, scroll=ft.ScrollMode.AUTO)
        self.btn_combinar = ft.FilledButton(
            "Combinar pizza (precio fijo)",
            icon=ft.Icons.LOCAL_PIZZA,
            bgcolor="#6A0404",
            color=ft.Colors.WHITE,
            height=40,
            visible=self.mostrar_combinador
            and self.categoria_seleccionada in ("Todas", "Pizzas"),
            on_click=self.abrir_combinador_usuario,
        )
        self.lista_productos_column = ft.Column(spacing=10)

        self.construir_barra_categorias()
        self.construir_catalogo()

        self.controls = [
            ft.Container(
                expand=True,
                bgcolor="#FFF8F2",
                content=ft.Column(
                    expand=True,
                    spacing=10,
                    controls=[
                        ft.Container(
                            padding=ft.Padding(left=6, top=4, right=6, bottom=2),
                            content=ft.Row(
                                [
                                    ft.Container(content=self.row_categorias, expand=True),
                                    self.btn_combinar,
                                ],
                                wrap=True,
                                spacing=8,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                        ),
                        ft.Container(
                            expand=True,
                            padding=ft.Padding(left=6, top=2, right=6, bottom=10),
                            content=ft.Column(
                                scroll=ft.ScrollMode.AUTO,
                                expand=True,
                                controls=[self.lista_productos_column],
                            ),
                        ),
                    ],
                ),
            )
        ]

    def did_mount(self):
        self.refrescar_disponibilidad()

    def refrescar_disponibilidad(self):
        self.mapa_disponibilidad = obtener_mapa_disponibilidad()
        self.construir_catalogo()
        self.actualizar_si_montado(self.lista_productos_column)

    def actualizar_si_montado(self, control):
        try:
            if control.page is not None:
                control.update()
        except RuntimeError:
            pass

    def construir_barra_categorias(self):
        categorias = ["Todas", "Pizzas", "Bebidas", "Complementos"]
        self.row_categorias.controls.clear()
        for cat in categorias:
            activa = self.categoria_seleccionada == cat
            self.row_categorias.controls.append(
                ft.Container(
                    padding=ft.Padding(left=14, top=8, right=14, bottom=8),
                    bgcolor="#6A0404" if activa else "#FFF8F2",
                    border_radius=20,
                    border=ft.Border.all(
                        1, "#6A0404" if activa else "#E7C8B8"
                    ),
                    ink=True,
                    on_click=lambda e, c=cat: self.seleccionar_categoria(c),
                    content=ft.Text(
                        cat,
                        size=13,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.WHITE if activa else "#6A0404",
                    ),
                )
            )

    def seleccionar_categoria(self, categoria):
        self.categoria_seleccionada = categoria
        self.btn_combinar.visible = self.mostrar_combinador and categoria in (
            "Todas",
            "Pizzas",
        )
        self.construir_barra_categorias()
        self.construir_catalogo()
        self.actualizar_si_montado(self.row_categorias)
        self.actualizar_si_montado(self.btn_combinar)
        self.actualizar_si_montado(self.lista_productos_column)

    def cambiar_categoria(self, categoria):
        categorias_validas = {"Todas", "Pizzas", "Bebidas", "Complementos"}
        self.seleccionar_categoria(
            categoria if categoria in categorias_validas else "Todas"
        )

    def abrir_combinador_usuario(self, e=None):
        try:
            pagina = self.page
        except RuntimeError:
            pagina = None
        if pagina is None:
            return
        abrir_modal_combinar_pizza(
            pagina,
            self.es_movil,
            self.agregar_producto_combinado,
        )

    def agregar_producto_combinado(self, combo):
        id_combo = f"combo_{combo['nombre']}"
        existente = next(
            (p for p in self.productos if p["id"] == id_combo),
            None,
        )
        if existente is None:
            self.productos.insert(
                0,
                {
                    "id": id_combo,
                    "nombre": combo["nombre"],
                    "precio": float(combo["precio"]),
                    "categoria": "Pizzas",
                    "descripcion": "Pizza combinada a precio fijo por tamaño.",
                    "imagen": "pizza_pepperoni.png",
                },
            )
        if id_combo not in self.estado_carrito:
            self.estado_carrito[id_combo] = {
                "cantidad": 0,
                "precio": float(combo["precio"]),
            }
        self.estado_carrito[id_combo]["cantidad"] += int(
            combo.get("cantidad", 1)
        )
        self.productos_activos.add(id_combo)
        self.construir_catalogo()
        self.actualizar_si_montado(self.lista_productos_column)
        if self.on_cart_change:
            self.on_cart_change()

    def modificar_cantidad(self, prod_id, delta):
        datos = self.estado_carrito.get(prod_id)
        if not datos:
            return
        nueva = max(0, datos["cantidad"] + delta)
        datos["cantidad"] = nueva
        if nueva > 0:
            self.productos_activos.add(prod_id)
        else:
            self.productos_activos.discard(prod_id)
        self.construir_catalogo()
        self.actualizar_si_montado(self.lista_productos_column)
        if self.on_cart_change:
            self.on_cart_change()

    def obtener_items_estado(self):
        items = []
        for prod in self.productos:
            datos = self.estado_carrito.get(prod["id"])
            if datos and datos["cantidad"] > 0:
                items.append(
                    {
                        "id": prod["id"],
                        "nombre": prod["nombre"],
                        "precio": float(datos["precio"]),
                        "cantidad": int(datos["cantidad"]),
                        "categoria": prod.get("categoria", ""),
                    }
                )
        return items

    def limpiar_carrito(self):
        for datos in self.estado_carrito.values():
            datos["cantidad"] = 0
        self.productos_activos.clear()
        self.construir_catalogo()
        self.actualizar_si_montado(self.lista_productos_column)
        if self.on_cart_change:
            self.on_cart_change()

    def construir_catalogo(self):
        self.lista_productos_column.controls.clear()
        filtrados = [
            p
            for p in self.productos
            if self.categoria_seleccionada == "Todas"
            or p["categoria"] == self.categoria_seleccionada
        ]

        for prod in filtrados:
            pid = prod["id"]
            cant = self.estado_carrito[pid]["cantidad"]
            disponible = (
                pizza_disponible_en_todas_versiones(
                    prod["nombre"], self.mapa_disponibilidad
                )
                if prod["categoria"] == "Pizzas"
                else True
            )

            if not disponible and cant > 0:
                self.estado_carrito[pid]["cantidad"] = 0
                self.productos_activos.discard(pid)
                cant = 0

            if not disponible:
                control_accion = ft.Container(
                    padding=ft.Padding(left=10, top=6, right=10, bottom=6),
                    bgcolor="#FCE8E6",
                    border_radius=12,
                    content=ft.Text(
                        "No disponible",
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color="#6A0404",
                    ),
                )
            elif cant == 0:
                control_accion = ft.FilledButton(
                    "Agregar",
                    icon=ft.Icons.ADD,
                    bgcolor="#6A0404",
                    color=ft.Colors.WHITE,
                    height=38,
                    on_click=lambda e, i=pid: self.modificar_cantidad(i, 1),
                )
            else:
                control_accion = ft.Row(
                    spacing=4,
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.REMOVE_CIRCLE_OUTLINE,
                            icon_color="#6A0404",
                            icon_size=22,
                            on_click=lambda e, i=pid: self.modificar_cantidad(
                                i, -1
                            ),
                        ),
                        ft.Text(
                            str(cant),
                            size=15,
                            weight=ft.FontWeight.BOLD,
                            color="#3F302B",
                        ),
                        ft.IconButton(
                            icon=ft.Icons.ADD_CIRCLE,
                            icon_color="#6A0404",
                            icon_size=22,
                            on_click=lambda e, i=pid: self.modificar_cantidad(
                                i, 1
                            ),
                        ),
                    ],
                )

            self.lista_productos_column.controls.append(
                ft.Container(
                    padding=12,
                    bgcolor=ft.Colors.WHITE if disponible else "#F7F4F2",
                    border_radius=16,
                    border=ft.Border.all(
                        1.5 if cant > 0 else 1,
                        "#6A0404" if cant > 0 else "#F0D8CA",
                    ),
                    shadow=ft.BoxShadow(
                        blur_radius=8,
                        color=ft.Colors.with_opacity(0.05, ft.Colors.BLACK),
                        offset=ft.Offset(0, 2),
                    ),
                    content=ft.Row(
                        spacing=12,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Container(
                                width=54,
                                height=54,
                                bgcolor="#FFF1E7",
                                border_radius=14,
                                alignment=ft.Alignment.CENTER,
                                content=ft.Icon(
                                    ft.Icons.LOCAL_PIZZA
                                    if prod["categoria"] == "Pizzas"
                                    else (
                                        ft.Icons.LOCAL_DRINK
                                        if prod["categoria"] == "Bebidas"
                                        else ft.Icons.FASTFOOD
                                    ),
                                    color="#6A0404" if disponible else "#9E9E9E",
                                    size=28,
                                ),
                            ),
                            ft.Column(
                                spacing=3,
                                expand=True,
                                controls=[
                                    ft.Text(
                                        prod["nombre"],
                                        size=15,
                                        weight=ft.FontWeight.BOLD,
                                        color="#2B2B2B"
                                        if disponible
                                        else "#806B63",
                                    ),
                                    ft.Text(
                                        prod.get("descripcion", ""),
                                        size=12,
                                        color="#806B63",
                                        max_lines=2,
                                    ),
                                    ft.Text(
                                        f"${prod['precio']:.2f}",
                                        size=14,
                                        weight=ft.FontWeight.BOLD,
                                        color="#6A0404"
                                        if disponible
                                        else "#9E9E9E",
                                    ),
                                ],
                            ),
                            control_accion,
                        ],
                    ),
                )
            )