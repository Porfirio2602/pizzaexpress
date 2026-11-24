import asyncio
import requests
import flet as ft
from config import BASE_URL

INGREDIENTES_POR_PIZZA = {
    "Pizza Pepperoni": ["Masa", "Salsa de tomate", "Queso mozzarella", "Pepperoni"],
    "Pizza Hawaiana": ["Masa", "Salsa de tomate", "Queso mozzarella", "Jamón", "Piña"],
    "Pizza Carnívora": [
        "Masa",
        "Salsa de tomate",
        "Queso mozzarella",
        "Pepperoni",
        "Chorizo",
        "Carne molida",
        "Tocino",
    ],
    "Pizza Mexicana": [
        "Masa",
        "Salsa de tomate",
        "Queso mozzarella",
        "Chorizo",
        "Jalapeño",
        "Cebolla",
        "Pimiento",
    ],
}


class CocineroView(ft.Column):
    def __init__(self, personal, on_cerrar_sesion, es_movil=False):
        super().__init__()
        self.personal = personal
        self.on_cerrar_sesion = on_cerrar_sesion
        self.es_movil = es_movil
        self._actualizacion_activa = False
        self._generacion_actualizacion = 0
        self._sesion_cerrada = False
        self.expand = True
        self.spacing = 12
        self.token_headers = {
            "Authorization": f"Bearer {personal.get('token', '')}",
        }

        self.lbl_estado = ft.Text("", color="#6A0404", size=14)
        self.lbl_contador = ft.Text(
            "0 pedidos pendientes",
            size=14,
            weight=ft.FontWeight.BOLD,
            color="#6A0404",
        )
        self.lista_pedidos = ft.Column(spacing=12)

        self.encabezado = ft.Container(
            padding=ft.Padding(left=8, top=8, right=8, bottom=8),
            content=ft.Row(
                [
                    ft.Container(
                        width=48,
                        height=48,
                        alignment=ft.Alignment.CENTER,
                        bgcolor="#FFF1E7",
                        border_radius=16,
                        content=ft.Icon(
                            ft.Icons.SOUP_KITCHEN,
                            color="#6A0404",
                            size=28,
                        ),
                    ),
                    ft.Column(
                        [
                            ft.Text(
                                "Estación de Cocina",
                                size=22 if not es_movil else 19,
                                weight=ft.FontWeight.BOLD,
                                color="#6A0404",
                            ),
                            ft.Text(
                                f"Cocinero: {personal.get('nombre', '')}",
                                size=14,
                                color="#806B63",
                            ),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.WARNING_AMBER_ROUNDED,
                        icon_color="#9A541D",
                        tooltip="Reportar ingrediente faltante",
                        on_click=self.abrir_dialogo_falta_ingrediente,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.REFRESH,
                        icon_color="#6A0404",
                        tooltip="Actualizar comandas",
                        on_click=self.cargar_pedidos,
                    ),
                    ft.TextButton(
                        "Cerrar sesión",
                        style=ft.ButtonStyle(color="#6A0404"),
                        on_click=lambda e: self.on_cerrar_sesion(),
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        self.controls = [
            self.encabezado,
            ft.Container(
                padding=ft.Padding(left=14, top=8, right=14, bottom=8),
                bgcolor="#FFF8F2",
                border_radius=12,
                content=ft.Row(
                    [
                        ft.Icon(
                            ft.Icons.ASSIGNMENT_TURNED_IN,
                            color="#6A0404",
                            size=20,
                        ),
                        self.lbl_contador,
                        ft.Text(
                            "· Actualización automática cada 15s",
                            size=12,
                            color="#806B63",
                        ),
                    ],
                    wrap=True,
                    spacing=8,
                ),
            ),
            self.lbl_estado,
            ft.Container(
                expand=True,
                padding=10,
                bgcolor="#FFF8F2",
                border_radius=16,
                content=ft.Column(
                    scroll=ft.ScrollMode.AUTO,
                    expand=True,
                    controls=[self.lista_pedidos],
                ),
            ),
        ]

    def _obtener_pagina(self):
        try:
            return self.page
        except RuntimeError:
            return None

    def _manejar_sesion_expirada(self, respuesta):
        if respuesta.status_code in (401, 403):
            if not self._sesion_cerrada:
                self._sesion_cerrada = True
                self._actualizacion_activa = False
                self._generacion_actualizacion += 1
                pagina = self._obtener_pagina()
                if pagina is not None:
                    try:
                        pagina.pop_dialog()
                    except RuntimeError:
                        pass
                self.on_cerrar_sesion()
            return True
        return False

    def did_mount(self):
        self._actualizacion_activa = True
        self._generacion_actualizacion += 1
        pagina = self._obtener_pagina()
        if pagina is not None:
            pagina.run_task(self._cargar_pedidos_async)
            pagina.run_task(
                self.actualizar_automaticamente,
                self._generacion_actualizacion,
            )

    def will_unmount(self):
        self._actualizacion_activa = False
        self._generacion_actualizacion += 1

    async def actualizar_automaticamente(self, generacion):
        while (
            self._actualizacion_activa
            and generacion == self._generacion_actualizacion
        ):
            await asyncio.sleep(15)
            if (
                not self._actualizacion_activa
                or generacion != self._generacion_actualizacion
            ):
                return
            try:
                respuesta = await asyncio.to_thread(self.solicitar_pedidos)
            except requests.RequestException:
                continue
            if (
                self._actualizacion_activa
                and generacion == self._generacion_actualizacion
            ):
                self.renderizar_respuesta(respuesta)

    def solicitar_pedidos(self):
        return requests.get(
            f"{BASE_URL}/api/cocina/pedidos",
            headers=self.token_headers,
            timeout=15,
        )

    def cargar_pedidos(self, e):
        pagina = self._obtener_pagina()
        if pagina is not None:
            pagina.run_task(self._cargar_pedidos_async)
            return
        try:
            respuesta = self.solicitar_pedidos()
            self.renderizar_respuesta(respuesta)
        except requests.RequestException:
            self.lbl_estado.value = "No se pudo conectar con el servidor."

    async def _cargar_pedidos_async(self):
        try:
            respuesta = await asyncio.to_thread(self.solicitar_pedidos)
        except requests.RequestException:
            self.lbl_estado.value = "No se pudo conectar con el servidor."
            self.actualizar_ui()
            return
        self.lbl_estado.value = ""
        self.renderizar_respuesta(respuesta)

    def renderizar_respuesta(self, respuesta):
        if self._manejar_sesion_expirada(respuesta):
            return

        if respuesta.status_code != 200:
            try:
                detalle = respuesta.json().get("detail")
            except ValueError:
                detalle = None
            self.lbl_estado.value = (
                detalle
                if isinstance(detalle, str)
                else "Error al cargar pedidos de cocina."
            )
            self.actualizar_ui()
            return

        pedidos = respuesta.json().get("pedidos", [])
        en_proceso = [p for p in pedidos if p["estado"] == "En Proceso"]
        self.lbl_contador.value = (
            f"{len(en_proceso)} pedido(s) en preparación · {len(pedidos)} en cola"
        )
        self.lista_pedidos.controls = [
            self.crear_tarjeta_comanda(p) for p in pedidos
        ] or [
            ft.Container(
                padding=32,
                alignment=ft.Alignment.CENTER,
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                    controls=[
                        ft.Icon(
                            ft.Icons.CHECK_CIRCLE_OUTLINE,
                            size=48,
                            color="#397A5B",
                        ),
                        ft.Text(
                            "Sin comandas pendientes por preparar",
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            color="#3F302B",
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            "Los nuevos pedidos asignados aparecerán aquí automáticamente.",
                            size=13,
                            color="#806B63",
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                ),
            )
        ]
        self.actualizar_ui()

    def crear_tarjeta_comanda(self, pedido):
        en_proceso = pedido["estado"] == "En Proceso"
        items_ui = [
            ft.Row(
                [
                    ft.Container(
                        padding=ft.Padding(left=8, top=3, right=8, bottom=3),
                        bgcolor="#FCE8E6",
                        border_radius=8,
                        content=ft.Text(
                            f"{item['cantidad']}x",
                            weight=ft.FontWeight.BOLD,
                            color="#6A0404",
                            size=14,
                        ),
                    ),
                    ft.Text(
                        item["nombre_pizza"],
                        size=15,
                        weight=ft.FontWeight.W_600,
                        color="#2B2B2B",
                        expand=True,
                    ),
                ],
                spacing=10,
            )
            for item in pedido.get("detalles", [])
        ]

        btn_detalles = ft.OutlinedButton(
            "Detalles del pedido",
            icon=ft.Icons.LIST_ALT,
            height=46,
            style=ft.ButtonStyle(
                color="#6A0404",
                side=ft.BorderSide(1, "#6A0404"),
            ),
            on_click=lambda e, ped=pedido: self.mostrar_detalles_pedido(ped),
        )

        btn_listo = ft.FilledButton(
            "Marcar pedido listo",
            icon=ft.Icons.DONE_ALL,
            bgcolor="#6A0404",
            color=ft.Colors.WHITE,
            height=46,
            visible=en_proceso,
        )
        btn_listo.on_click = lambda e, pid=pedido[
            "id_pedido"
        ], btn=btn_listo: self.marcar_listo(pid, btn)

        return ft.Container(
            padding=16,
            bgcolor=ft.Colors.WHITE,
            border_radius=16,
            border=ft.Border.all(
                2 if en_proceso else 1,
                "#6A0404" if en_proceso else "#D5E6DC",
            ),
            shadow=ft.BoxShadow(
                blur_radius=10,
                color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK),
                offset=ft.Offset(0, 3),
            ),
            content=ft.Column(
                spacing=10,
                controls=[
                    ft.Row(
                        [
                            ft.Text(
                                pedido["codigo"],
                                size=19,
                                weight=ft.FontWeight.BOLD,
                                color="#6A0404",
                                expand=True,
                            ),
                            ft.Container(
                                padding=ft.Padding(
                                    left=10, top=4, right=10, bottom=4
                                ),
                                bgcolor="#FFF1E7"
                                if en_proceso
                                else "#E8F4EC",
                                border_radius=16,
                                content=ft.Text(
                                    pedido["estado"],
                                    size=12,
                                    weight=ft.FontWeight.BOLD,
                                    color="#9A541D"
                                    if en_proceso
                                    else "#28734D",
                                ),
                            ),
                        ]
                    ),
                    ft.Text(
                        f"Cliente: {pedido['nombre_contacto']} · {pedido['tipo_servicio']} ({pedido['origen']})",
                        size=13,
                        color="#54423B",
                    ),
                    ft.Text(
                        f"Hora ingreso: {pedido['fecha']}",
                        size=12,
                        color="#806B63",
                    ),
                    ft.Divider(height=1, color="#F1E5DE"),
                    *items_ui,
                    ft.Row(
                        [btn_detalles, btn_listo],
                        wrap=True,
                        spacing=10,
                    ),
                ],
            ),
        )

    def mostrar_detalles_pedido(self, pedido):
        pagina = self._obtener_pagina()
        if pagina is None:
            return
        tarjetas_items = []
        ingredientes_totales = []
        detalles = pedido.get("detalles", [])

        for item in detalles:
            nombre = item["nombre_pizza"]
            ings = list(
                item.get("ingredientes")
                or INGREDIENTES_POR_PIZZA.get(nombre, [])
            )
            if not ings:
                for clave, lista_ing in INGREDIENTES_POR_PIZZA.items():
                    if clave.casefold() in nombre.casefold():
                        for ing in lista_ing:
                            if ing not in ings:
                                ings.append(ing)
            for ing in ings:
                if ing not in ingredientes_totales:
                    ingredientes_totales.append(ing)

            chips_item = [
                ft.Container(
                    padding=ft.Padding(left=8, top=4, right=8, bottom=4),
                    bgcolor=ft.Colors.WHITE,
                    border=ft.Border.all(1, "#E7C8B8"),
                    border_radius=10,
                    content=ft.Text(
                        ing,
                        size=12,
                        weight=ft.FontWeight.W_500,
                        color="#3F302B",
                    ),
                )
                for ing in ings
            ]

            tarjetas_items.append(
                ft.Container(
                    padding=12,
                    bgcolor="#FFF8F2",
                    border=ft.Border.all(1, "#F0D8CA"),
                    border_radius=14,
                    content=ft.Column(
                        tight=True,
                        spacing=8,
                        controls=[
                            ft.Row(
                                [
                                    ft.Container(
                                        padding=ft.Padding(
                                            left=8, top=3, right=8, bottom=3
                                        ),
                                        bgcolor="#6A0404",
                                        border_radius=8,
                                        content=ft.Text(
                                            f"{item['cantidad']}×",
                                            size=12,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.WHITE,
                                        ),
                                    ),
                                    ft.Text(
                                        nombre,
                                        size=15,
                                        weight=ft.FontWeight.BOLD,
                                        color="#3F302B",
                                        expand=True,
                                    ),
                                ],
                                spacing=8,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Row(chips_item, wrap=True, spacing=6, run_spacing=6)
                            if chips_item
                            else ft.Text(
                                "Consultar receta base",
                                size=12,
                                color="#806B63",
                            ),
                        ],
                    ),
                )
            )

        controles_contenido = list(tarjetas_items)
        if len(detalles) > 1 and ingredientes_totales:
            chips_totales = [
                ft.Container(
                    padding=ft.Padding(left=9, top=4, right=9, bottom=4),
                    bgcolor="#FCE8E6",
                    border_radius=12,
                    content=ft.Text(
                        ing,
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color="#6A0404",
                    ),
                )
                for ing in ingredientes_totales
            ]
            controles_contenido.append(
                ft.Container(
                    padding=12,
                    bgcolor="#FFFDFB",
                    border=ft.Border.all(1, "#E7C8B8"),
                    border_radius=14,
                    content=ft.Column(
                        tight=True,
                        spacing=8,
                        controls=[
                            ft.Row(
                                [
                                    ft.Icon(
                                        ft.Icons.INVENTORY_2_OUTLINED,
                                        size=16,
                                        color="#6A0404",
                                    ),
                                    ft.Text(
                                        "Total de insumos del pedido",
                                        size=13,
                                        weight=ft.FontWeight.BOLD,
                                        color="#3F302B",
                                    ),
                                ],
                                spacing=6,
                            ),
                            ft.Row(
                                chips_totales,
                                wrap=True,
                                spacing=6,
                                run_spacing=6,
                            ),
                        ],
                    ),
                )
            )

        def cerrar_dialogo(_=None):
            try:
                pagina.pop_dialog()
            except RuntimeError:
                pass

        dialogo = ft.AlertDialog(
            modal=True,
            bgcolor=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=22),
            title=ft.Row(
                [
                    ft.Container(
                        width=38,
                        height=38,
                        alignment=ft.Alignment.CENTER,
                        bgcolor="#FCE8E6",
                        border_radius=12,
                        content=ft.Icon(
                            ft.Icons.RESTAURANT_MENU,
                            color="#6A0404",
                            size=20,
                        ),
                    ),
                    ft.Column(
                        [
                            ft.Text(
                                f"Detalles · {pedido['codigo']}",
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                color="#6A0404",
                            ),
                            ft.Text(
                                f"{pedido['nombre_contacto']} · {pedido['tipo_servicio']}",
                                size=12,
                                color="#806B63",
                            ),
                        ],
                        spacing=1,
                        expand=True,
                    ),
                ],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            content=ft.Container(
                width=320 if self.es_movil else 430,
                content=ft.Column(
                    tight=True,
                    scroll=ft.ScrollMode.AUTO,
                    spacing=10,
                    controls=controles_contenido,
                ),
            ),
            actions=[
                ft.OutlinedButton(
                    "Reportar faltante",
                    icon=ft.Icons.WARNING_AMBER_ROUNDED,
                    style=ft.ButtonStyle(
                        color="#9A541D",
                        side=ft.BorderSide(1, "#9A541D"),
                    ),
                    on_click=lambda e: (
                        cerrar_dialogo(),
                        self.abrir_dialogo_falta_ingrediente(e),
                    ),
                ),
                ft.FilledButton(
                    "Cerrar",
                    bgcolor="#6A0404",
                    color=ft.Colors.WHITE,
                    on_click=cerrar_dialogo,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        try:
            pagina.show_dialog(dialogo)
        except RuntimeError as error:
            if "Dialog is already opened" in str(error):
                pagina.pop_dialog()
                pagina.show_dialog(dialogo)

    def abrir_dialogo_falta_ingrediente(self, e=None):
        pagina = self._obtener_pagina()
        if pagina is None:
            return
        txt_ing = ft.TextField(
            label="Ingrediente agotado",
            hint_text="Ej. Queso mozzarella, Piña",
        )
        txt_nota = ft.TextField(
            label="Nota para vendedor/gerencia",
            hint_text="Ej. Queda para 2 pizzas más",
        )

        def cerrar_dialogo(_=None):
            try:
                pagina.pop_dialog()
            except RuntimeError:
                pass

        async def enviar_reporte(_):
            ing = (txt_ing.value or "").strip()
            if not ing:
                return
            try:
                respuesta = await asyncio.to_thread(
                    requests.post,
                    f"{BASE_URL}/api/cocina/ingredientes/faltantes",
                    json={
                        "ingrediente": ing,
                        "nota": (txt_nota.value or "").strip(),
                    },
                    headers=self.token_headers,
                    timeout=15,
                )
            except requests.RequestException:
                return
            if self._manejar_sesion_expirada(respuesta):
                return
            cerrar_dialogo()
            self.lbl_estado.value = (
                f"Falta de '{ing}' reportada a vendedor y gerencia."
            )
            self.actualizar_ui()

        dialogo = ft.AlertDialog(
            modal=True,
            bgcolor=ft.Colors.WHITE,
            title=ft.Text("Reportar ingrediente faltante", color="#6A0404"),
            content=ft.Column(
                tight=True, spacing=10, controls=[txt_ing, txt_nota]
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=cerrar_dialogo),
                ft.FilledButton(
                    "Avisar",
                    bgcolor="#6A0404",
                    color=ft.Colors.WHITE,
                    on_click=lambda e: pagina.run_task(enviar_reporte, e),
                ),
            ],
        )
        try:
            pagina.show_dialog(dialogo)
        except RuntimeError as error:
            if "Dialog is already opened" in str(error):
                pagina.pop_dialog()
                pagina.show_dialog(dialogo)

    def marcar_listo(self, id_pedido, boton):
        pagina = self._obtener_pagina()
        if pagina is not None:
            pagina.run_task(self._marcar_listo_async, id_pedido, boton)

    async def _marcar_listo_async(self, id_pedido, boton):
        boton.disabled = True
        boton.text = "Actualizando..."
        self.actualizar_ui()
        try:
            respuesta = await asyncio.to_thread(
                requests.patch,
                f"{BASE_URL}/api/cocina/pedidos/{id_pedido}/listo",
                headers=self.token_headers,
                timeout=15,
            )
        except requests.RequestException:
            boton.disabled = False
            boton.text = "Marcar pedido listo"
            self.lbl_estado.value = "No se pudo conectar con el servidor."
            self.actualizar_ui()
            return

        if self._manejar_sesion_expirada(respuesta):
            return

        if respuesta.status_code != 200:
            boton.disabled = False
            boton.text = "Marcar pedido listo"
            try:
                detalle = respuesta.json().get("detail")
            except ValueError:
                detalle = None
            self.lbl_estado.value = (
                detalle
                if isinstance(detalle, str)
                else "No se pudo actualizar la comanda."
            )
            self.actualizar_ui()
            return

        self.lbl_estado.value = "Pedido marcado como listo."
        await self._cargar_pedidos_async()

    def actualizar_ui(self):
        pagina = self._obtener_pagina()
        try:
            if pagina is not None:
                self.update()
        except RuntimeError:
            return