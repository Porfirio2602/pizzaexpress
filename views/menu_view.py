import asyncio
import flet as ft
from components.pizzas_combinadas import (
    abrir_modal_combinar_pizza,
    obtener_mapa_disponibilidad,
    pizza_disponible_en_todas_versiones,
)


def _crear_toppings_pizza(nombre):
    nombre_lower = (nombre or "").casefold()
    toppings = []

    if "comb." in nombre_lower or "+" in nombre_lower:
        toppings = [
            ft.Container(left=24, top=22, width=16, height=16, border_radius=8, bgcolor="#A91D1D"),
            ft.Container(left=64, top=24, width=14, height=14, border_radius=3, bgcolor="#F4B400"),
            ft.Container(left=70, top=60, width=15, height=15, border_radius=8, bgcolor="#2E7D32", border=ft.Border.all(3, "#1B5E20")),
            ft.Container(left=28, top=64, width=15, height=15, border_radius=4, bgcolor="#E57373"),
            ft.Container(left=48, top=46, width=16, height=16, border_radius=8, bgcolor="#A91D1D"),
            ft.Container(left=46, top=76, width=13, height=13, border_radius=3, bgcolor="#F4B400"),
            ft.Container(left=20, top=44, width=12, height=12, border_radius=6, bgcolor="#6D2B1B"),
        ]
    elif "hawaiana" in nombre_lower:
        posiciones_pina = [(24, 28), (64, 24), (48, 52), (26, 68), (68, 66)]
        posiciones_jamon = [(44, 22), (72, 44), (22, 48), (52, 74), (36, 40)]
        for x, y in posiciones_pina:
            toppings.append(
                ft.Container(
                    left=x,
                    top=y,
                    width=14,
                    height=12,
                    border_radius=3,
                    bgcolor="#F4B400",
                    border=ft.Border.all(1, "#D49400"),
                )
            )
        for x, y in posiciones_jamon:
            toppings.append(
                ft.Container(
                    left=x,
                    top=y,
                    width=14,
                    height=13,
                    border_radius=3,
                    bgcolor="#E57373",
                    border=ft.Border.all(1, "#C95555"),
                )
            )
    elif "carnívora" in nombre_lower or "carnivora" in nombre_lower:
        for x, y in [(24, 26), (62, 26), (44, 48), (26, 66), (64, 64)]:
            toppings.append(
                ft.Container(
                    left=x,
                    top=y,
                    width=16,
                    height=16,
                    border_radius=8,
                    bgcolor="#A91D1D",
                    border=ft.Border.all(1, "#7F1212"),
                )
            )
        for x, y in [(46, 22), (74, 48), (22, 48), (48, 74)]:
            toppings.append(
                ft.Container(
                    left=x,
                    top=y,
                    width=12,
                    height=12,
                    border_radius=6,
                    bgcolor="#5D291C",
                )
            )
        for x, y in [(36, 36), (60, 44), (38, 64)]:
            toppings.append(
                ft.Container(
                    left=x,
                    top=y,
                    width=15,
                    height=6,
                    border_radius=3,
                    bgcolor="#B85038",
                )
            )
    elif "mexicana" in nombre_lower:
        for x, y in [(26, 28), (64, 28), (46, 54), (28, 66), (66, 66)]:
            toppings.append(
                ft.Container(
                    left=x,
                    top=y,
                    width=14,
                    height=14,
                    border_radius=7,
                    bgcolor="#F9D976",
                    border=ft.Border.all(3, "#2E7D32"),
                )
            )
        for x, y in [(46, 24), (24, 48), (72, 48), (48, 76)]:
            toppings.append(
                ft.Container(
                    left=x,
                    top=y,
                    width=12,
                    height=12,
                    border_radius=6,
                    bgcolor="#8D2B1A",
                )
            )
        for x, y in [(36, 38), (60, 44), (40, 66)]:
            toppings.append(
                ft.Container(
                    left=x,
                    top=y,
                    width=13,
                    height=13,
                    border_radius=7,
                    bgcolor=ft.Colors.TRANSPARENT,
                    border=ft.Border.all(2, "#FFF8F2"),
                )
            )
    else:
        for x, y in [(26, 24), (62, 24), (44, 44), (22, 52), (68, 52), (34, 70), (58, 70)]:
            toppings.append(
                ft.Container(
                    left=x,
                    top=y,
                    width=17,
                    height=17,
                    border_radius=9,
                    bgcolor="#B22222",
                    border=ft.Border.all(1.5, "#871414"),
                )
            )
        for x, y in [(48, 28), (38, 58), (60, 40)]:
            toppings.append(
                ft.Container(
                    left=x,
                    top=y,
                    width=7,
                    height=7,
                    border_radius=4,
                    bgcolor="#388E3C",
                )
            )

    return toppings


def crear_ilustracion_producto(prod, disponible=True):
    categoria = prod.get("categoria", "")
    nombre = prod.get("nombre", "")

    if categoria == "Pizzas":
        pizza_dibujo = ft.Container(
            width=112,
            height=112,
            border_radius=56,
            shadow=ft.BoxShadow(
                blur_radius=12,
                color=ft.Colors.with_opacity(0.18, ft.Colors.BLACK),
                offset=ft.Offset(0, 5),
            ),
            content=ft.Stack(
                controls=[
                    ft.Container(
                        width=112,
                        height=112,
                        border_radius=56,
                        bgcolor="#D98B3A" if disponible else "#B8B0A8",
                        border=ft.Border.all(3, "#B86A22" if disponible else "#9B938C"),
                    ),
                    ft.Container(
                        left=9,
                        top=9,
                        width=94,
                        height=94,
                        border_radius=47,
                        bgcolor="#C0392B" if disponible else "#A69E96",
                    ),
                    ft.Container(
                        left=13,
                        top=13,
                        width=86,
                        height=86,
                        border_radius=43,
                        bgcolor="#F9D976" if disponible else "#CFC8C0",
                    ),
                    *(_crear_toppings_pizza(nombre) if disponible else []),
                ]
            ),
        )
        return ft.Container(
            expand=True,
            alignment=ft.Alignment.CENTER,
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_LEFT,
                end=ft.Alignment.BOTTOM_RIGHT,
                colors=["#FFF2E2", "#FBE0C8"] if disponible else ["#EFECE9", "#E2DDD8"],
            ),
            content=pizza_dibujo,
        )

    if categoria == "Bebidas":
        colores = ["#EBF5FF", "#D6E9FF"]
        icono = ft.Icons.LOCAL_DRINK
        color_icono = "#1565C0"
    else:
        colores = ["#FFF4E5", "#FFE2BD"]
        icono = ft.Icons.FASTFOOD
        color_icono = "#B85C00"

    return ft.Container(
        expand=True,
        alignment=ft.Alignment.CENTER,
        gradient=ft.LinearGradient(
            begin=ft.Alignment.TOP_LEFT,
            end=ft.Alignment.BOTTOM_RIGHT,
            colors=colores if disponible else ["#EFECE9", "#E2DDD8"],
        ),
        content=ft.Container(
            width=74,
            height=74,
            border_radius=37,
            bgcolor=ft.Colors.WHITE,
            alignment=ft.Alignment.CENTER,
            shadow=ft.BoxShadow(
                blur_radius=10,
                color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
                offset=ft.Offset(0, 3),
            ),
            content=ft.Icon(
                icono,
                size=38,
                color=color_icono if disponible else "#9E9E9E",
            ),
        ),
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
        self.mapa_disponibilidad = {}

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
            "Combinar pizza",
            icon=ft.Icons.LOCAL_PIZZA,
            bgcolor="#6A0404",
            color=ft.Colors.WHITE,
            height=40,
            visible=self.mostrar_combinador
            and self.categoria_seleccionada in ("Todas", "Pizzas"),
            on_click=self.abrir_combinador_usuario,
        )
        self.grid_productos = ft.ResponsiveRow(
            spacing=14,
            run_spacing=14,
        )
        self.lista_productos_column = ft.Column(
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            controls=[self.grid_productos],
        )

        self.construir_barra_categorias()
        self.construir_catalogo()

        if self.es_movil:
            barra_superior_menu = ft.Column(
                spacing=8,
                controls=[
                    self.row_categorias,
                    self.btn_combinar,
                ],
            )
        else:
            barra_superior_menu = ft.Row(
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(content=self.row_categorias, expand=True),
                    self.btn_combinar,
                ],
            )

        self.controls = [
            ft.Container(
                expand=True,
                bgcolor="#FFF8F2",
                padding=ft.Padding(left=14, top=12, right=14, bottom=12),
                content=ft.Column(
                    expand=True,
                    spacing=14,
                    controls=[
                        barra_superior_menu,
                        self.lista_productos_column,
                    ],
                ),
            )
        ]

    def did_mount(self):
        try:
            pagina = self.page
        except RuntimeError:
            pagina = None
        if pagina is not None:
            pagina.run_task(self._refrescar_disponibilidad_async)

    async def _refrescar_disponibilidad_async(self):
        self.mapa_disponibilidad = await asyncio.to_thread(
            obtener_mapa_disponibilidad
        )
        self.construir_catalogo()
        self.actualizar_si_montado(self.lista_productos_column)

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
                    padding=ft.Padding(left=16, top=8, right=16, bottom=8),
                    bgcolor="#6A0404" if activa else ft.Colors.WHITE,
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
                    "descripcion": "Combinación personalizada.",
                    "imagen": "pizza_combinada.png",
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

    def _crear_imagen_tarjeta(self, prod, disponible):
        ilustracion = crear_ilustracion_producto(prod, disponible=disponible)
        imagen_nombre = prod.get("imagen")
        if imagen_nombre:
            contenido_visual = ft.Image(
                src=f"imagenes/{imagen_nombre}",
                width=float("inf"),
                height=145,
                fit=ft.BoxFit.COVER,
                error_content=ilustracion,
            )
        else:
            contenido_visual = ilustracion

        capas = [
            ft.Container(
                height=145,
                expand=True,
                content=contenido_visual,
            )
        ]
        if not disponible:
            capas.append(
                ft.Container(
                    left=10,
                    top=10,
                    padding=ft.Padding(left=10, top=4, right=10, bottom=4),
                    bgcolor="#6A0404",
                    border_radius=12,
                    content=ft.Text(
                        "No disponible",
                        size=11,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.WHITE,
                    ),
                )
            )
        return ft.Container(
            height=145,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            border_radius=ft.BorderRadius.only(top_left=18, top_right=18),
            content=ft.Stack(controls=capas),
        )

    def construir_catalogo(self):
        self.grid_productos.controls.clear()
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
                control_accion = ft.Text(
                    "Agotada",
                    size=12,
                    weight=ft.FontWeight.BOLD,
                    color="#9E9E9E",
                )
            elif cant == 0:
                control_accion = ft.FilledButton(
                    "Agregar",
                    icon=ft.Icons.ADD,
                    bgcolor="#6A0404",
                    color=ft.Colors.WHITE,
                    height=36,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=12),
                        padding=ft.Padding(left=12, top=0, right=14, bottom=0),
                    ),
                    on_click=lambda e, i=pid: self.modificar_cantidad(i, 1),
                )
            else:
                control_accion = ft.Container(
                    padding=ft.Padding(left=4, top=2, right=4, bottom=2),
                    bgcolor="#FFF1E7",
                    border_radius=12,
                    border=ft.Border.all(1, "#E7C8B8"),
                    content=ft.Row(
                        spacing=2,
                        tight=True,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.IconButton(
                                icon=ft.Icons.REMOVE,
                                icon_color="#6A0404",
                                icon_size=18,
                                width=30,
                                height=30,
                                padding=0,
                                on_click=lambda e, i=pid: self.modificar_cantidad(
                                    i, -1
                                ),
                            ),
                            ft.Text(
                                str(cant),
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                color="#3F302B",
                            ),
                            ft.IconButton(
                                icon=ft.Icons.ADD,
                                icon_color="#6A0404",
                                icon_size=18,
                                width=30,
                                height=30,
                                padding=0,
                                on_click=lambda e, i=pid: self.modificar_cantidad(
                                    i, 1
                                ),
                            ),
                        ],
                    ),
                )

            tarjeta = ft.Container(
                col={"xs": 12, "sm": 6, "md": 4, "lg": 3},
                bgcolor=ft.Colors.WHITE if disponible else "#F7F4F2",
                border_radius=18,
                border=ft.Border.all(
                    2 if cant > 0 else 1,
                    "#6A0404" if cant > 0 else "#F0D8CA",
                ),
                shadow=ft.BoxShadow(
                    blur_radius=12,
                    color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK),
                    offset=ft.Offset(0, 4),
                ),
                content=ft.Column(
                    spacing=0,
                    controls=[
                        self._crear_imagen_tarjeta(prod, disponible),
                        ft.Container(
                            padding=ft.Padding(
                                left=14, top=12, right=14, bottom=14
                            ),
                            content=ft.Column(
                                spacing=6,
                                controls=[
                                    ft.Text(
                                        prod["nombre"],
                                        size=15,
                                        weight=ft.FontWeight.BOLD,
                                        color="#2B2B2B"
                                        if disponible
                                        else "#806B63",
                                        max_lines=2,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                    ft.Text(
                                        prod.get("descripcion", ""),
                                        size=12,
                                        color="#806B63",
                                        max_lines=2,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                    ft.Container(height=4),
                                    ft.Row(
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                        controls=[
                                            ft.Text(
                                                f"${prod['precio']:.2f}",
                                                size=16,
                                                weight=ft.FontWeight.BOLD,
                                                color="#6A0404"
                                                if disponible
                                                else "#9E9E9E",
                                            ),
                                            control_accion,
                                        ],
                                    ),
                                ],
                            ),
                        ),
                    ],
                ),
            )
            self.grid_productos.controls.append(tarjeta)