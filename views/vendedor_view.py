import asyncio
import re

import requests
import flet as ft
from config import BASE_URL
from views.menu_view import MenuView


class VendedorView(ft.Column):
    def __init__(self, personal, on_cerrar_sesion, es_movil=False):
        super().__init__()
        self.personal = personal
        self.on_cerrar_sesion = on_cerrar_sesion
        self.es_movil = es_movil
        self._actualizacion_activa = False
        self._generacion_actualizacion = 0
        self.spacing = 12
        self.expand = True
        self.lbl_total = ft.Text(
            "$0.00",
            size=24 if es_movil else 28,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.WHITE,
        )
        self.lbl_total_pago = ft.Text(
            "$0.00",
            size=20,
            weight=ft.FontWeight.BOLD,
            color="#6A0404",
        )
        self.lbl_estado = ft.Text("", size=15, color="#6A0404")
        self.lbl_estado_entrega = ft.Text("", size=15, color="#6A0404")
        self.lista_pedidos = ft.Column(spacing=8)
        self.detalle_pedido_entrega = ft.Column(spacing=8)
        self.codigo_pedido_encontrado = None
        self.id_pedido_encontrado = None
        self.txt_codigo_pedido = ft.TextField(
            label="Código del pedido",
            hint_text="Ej. PE-000019",
            text_size=17 if not es_movil else 16,
            prefix_icon=ft.Icons.QR_CODE_SCANNER,
            autofocus=True,
            on_submit=self.buscar_pedido_por_codigo,
            border_radius=12,
            filled=True,
            fill_color=ft.Colors.WHITE,
        )
        self.menu = MenuView(
            on_cart_change=self.actualizar_total,
            categoria_inicial="Pizzas",
            es_movil=es_movil,
        )
        self.txt_nombre = ft.TextField(
            label="Nombre completo del cliente",
            expand=not es_movil,
            text_size=17 if not es_movil else 16,
        )
        self.txt_telefono = ft.TextField(
            label="Teléfono de contacto (10 dígitos)",
            text_size=17 if not es_movil else 16,
            keyboard_type=ft.KeyboardType.PHONE,
            max_length=10,
            visible=False,
            expand=not es_movil,
        )
        self.lbl_aviso_telefono = ft.Text(
            "El teléfono se guarda para contacto; todavía no se envían SMS.",
            size=14,
            color="#806B63",
            visible=False,
        )
        self.selector_servicio = ft.Dropdown(
            label="Tipo de servicio",
            value=None,
            options=[
                ft.DropdownOption(
                    key="Comer en tienda",
                    text="Comer en tienda",
                ),
                ft.DropdownOption(
                    key="Para recoger en tienda",
                    text="Para recoger en tienda",
                ),
            ],
            on_select=self.cambiar_servicio,
            visible=False,
        )
        self.tarjeta_comer = self.crear_tarjeta_servicio(
            "Comer en tienda",
            "Consumo en el establecimiento",
            ft.Icons.RESTAURANT,
        )
        self.tarjeta_recoger = self.crear_tarjeta_servicio(
            "Para llevar",
            "El cliente recogerá su pedido",
            ft.Icons.STORE,
            valor="Para recoger en tienda",
        )
        self.boton_pagar_ahora = ft.Container(
            visible=False,
            alignment=ft.Alignment.CENTER,
            padding=ft.Padding(
                left=14,
                top=10 if not es_movil else 8,
                right=14,
                bottom=10 if not es_movil else 8,
            ),
            content=ft.Container(
                width=None if es_movil else 720,
                padding=16 if not es_movil else 12,
                bgcolor="#6A0404",
                border_radius=18,
                ink=True,
                on_click=self.iniciar_checkout,
                shadow=ft.BoxShadow(
                    blur_radius=18,
                    spread_radius=1,
                    color=ft.Colors.with_opacity(0.24, ft.Colors.BLACK),
                    offset=ft.Offset(0, -3),
                ),
                content=ft.Row(
                    spacing=12,
                    controls=[
                        ft.Container(
                            width=58 if not es_movil else 50,
                            height=58 if not es_movil else 50,
                            alignment=ft.Alignment.CENTER,
                            bgcolor=ft.Colors.WHITE,
                            border_radius=14,
                            content=ft.Icon(
                                ft.Icons.CREDIT_CARD,
                                color="#6A0404",
                                size=31 if not es_movil else 27,
                            ),
                        ),
                        ft.Column(
                            spacing=1,
                            expand=True,
                            controls=[
                                ft.Text(
                                    "Pagar ahora",
                                    size=20 if not es_movil else 18,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.WHITE,
                                ),
                                ft.Text(
                                    "Continúa con tu pedido",
                                    size=16 if not es_movil else 15,
                                    color="#FFF4EE",
                                ),
                            ],
                        ),
                        ft.Column(
                            spacing=1,
                            horizontal_alignment=ft.CrossAxisAlignment.END,
                            controls=[
                                ft.Text(
                                    "TOTAL",
                                    size=16 if not es_movil else 14,
                                    weight=ft.FontWeight.BOLD,
                                    color="#FFF4EE",
                                ),
                                self.lbl_total,
                            ],
                        ),
                    ],
                ),
            ),
        )
        tamano_texto = 15 if es_movil else 17
        alto_campo = 42 if es_movil else 52
        self.txt_nombre_titular = ft.TextField(
            label="Nombre del Titular",
            text_size=tamano_texto,
            height=alto_campo,
        )
        self.txt_tarjeta = ft.TextField(
            label="Número de Tarjeta",
            hint_text="0000 0000 0000 0000",
            keyboard_type=ft.KeyboardType.NUMBER,
            input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9 ]*"),
            max_length=23,
            text_size=tamano_texto,
            height=alto_campo,
            on_change=self.formatear_numero_tarjeta,
        )
        self.txt_exp = ft.TextField(
            label="MM/AA",
            hint_text="MM/AA",
            keyboard_type=ft.KeyboardType.NUMBER,
            input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9]*"),
            max_length=5,
            text_size=tamano_texto,
            height=alto_campo,
            expand=True,
            on_change=self.formatear_vencimiento,
        )
        self.txt_cvv = ft.TextField(
            label="CVV",
            keyboard_type=ft.KeyboardType.NUMBER,
            input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9]*"),
            max_length=4,
            text_size=tamano_texto,
            height=alto_campo,
            expand=True,
        )
        self.info_pago = ft.Container(
            padding=12,
            bgcolor="#FFF8F2",
            border_radius=12,
            border=ft.Border(
                top=ft.BorderSide(1, "#F0D8CA"),
                bottom=ft.BorderSide(1, "#F0D8CA"),
                left=ft.BorderSide(1, "#F0D8CA"),
                right=ft.BorderSide(1, "#F0D8CA"),
            ),
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Row(
                        spacing=8,
                        controls=[
                            ft.Icon(ft.Icons.LOCK_OUTLINE, size=18, color="#6A0404"),
                            ft.Text(
                                "Pago de demostración: no hay pasarela conectada",
                                size=14,
                                color="#54423B",
                                weight=ft.FontWeight.W_500,
                                expand=True,
                            ),
                        ],
                    ),
                    ft.Row(
                        spacing=8,
                        controls=[
                            ft.Text(marca, size=14, weight=ft.FontWeight.BOLD, color=color)
                            for marca, color in (
                                ("VISA", "#1A1F71"),
                                ("Mastercard", "#EB001B"),
                                ("AMEX", "#2E77BC"),
                            )
                        ],
                    ),
                    ft.Text(
                        "Marcas ilustrativas; aún no se procesan pagos.",
                        size=14,
                        color="#806B63",
                    ),
                ],
            ),
        )
        self.lista_resumen_pago = ft.Column(spacing=6)
        self.encabezado = ft.Container(
            padding=ft.Padding(left=8, top=8, right=8, bottom=8),
            bgcolor=ft.Colors.TRANSPARENT,
            content=ft.Row(
                [
                    ft.Container(
                        width=48,
                        height=48,
                        alignment=ft.Alignment.CENTER,
                        bgcolor="#FFF1E7",
                        border_radius=16,
                        content=ft.Icon(
                            ft.Icons.POINT_OF_SALE,
                            color="#6A0404",
                            size=28,
                        ),
                    ),
                    ft.Column(
                        [
                            ft.Text(
                                "Punto de venta",
                                size=23,
                                weight=ft.FontWeight.BOLD,
                                color="#6A0404",
                            ),
                            ft.Text(
                                f"Vendedor: {personal.get('nombre', '')}",
                                size=15,
                                color="#806B63",
                            ),
                        ],
                        spacing=2,
                        expand=True,
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
        self.seccion_menu = ft.Column(
            expand=True,
            spacing=12,
            controls=[self.menu, self.boton_pagar_ahora],
        )
        self.seccion_pedidos = ft.Container(
            padding=14,
            bgcolor=ft.Colors.WHITE,
            border_radius=14,
            content=ft.Column(
                spacing=10,
                controls=[
                    ft.Row(
                        [
                            ft.Text(
                                "Pedidos de mi turno",
                                size=19,
                                weight=ft.FontWeight.BOLD,
                                color="#6A0404",
                                expand=True,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.REFRESH,
                                tooltip="Actualizar pedidos",
                                icon_color="#6A0404",
                                on_click=self.cargar_pedidos,
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Text(
                        "Ordenados del más reciente al más antiguo. "
                        "Actualización automática cada 30 segundos.",
                        size=14,
                        color="#806B63",
                    ),
                    self.lista_pedidos,
                ],
            ),
        )
        self.seccion_entregas = ft.Container(
            padding=16,
            bgcolor="#FFF8F2",
            border_radius=14,
            content=ft.Column(
                spacing=12,
                controls=[
                    ft.Text(
                        "Validar entrega",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color="#6A0404",
                    ),
                    ft.Text(
                        "Escanea el código de barras del pedido o escríbelo "
                        "manualmente para confirmar su entrega.",
                        size=15,
                        color="#806B63",
                    ),
                    ft.Row(
                        [
                            self.txt_codigo_pedido,
                            ft.FilledButton(
                                "Buscar pedido",
                                icon=ft.Icons.SEARCH,
                                bgcolor="#6A0404",
                                color=ft.Colors.WHITE,
                                height=48,
                                on_click=self.buscar_pedido_por_codigo,
                            ),
                        ],
                        wrap=True,
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Text(
                        "Los lectores USB/Bluetooth que escriben el código "
                        "y envían Enter son compatibles.",
                        size=14,
                        color="#806B63",
                    ),
                    self.lbl_estado_entrega,
                    self.detalle_pedido_entrega,
                ],
            ),
        )
        ancho_checkout = 420 if not es_movil else 300
        self.contenido_pago = ft.Column(
            spacing=14,
            scroll=ft.ScrollMode.AUTO,
            height=520 if not es_movil else 460,
            width=ancho_checkout,
        )
        self.paso_checkout = "servicio"
        self.selector_metodo_pago = ft.SegmentedButton(
            selected=["Efectivo"],
            allow_multiple_selection=False,
            segments=[
                ft.Segment(value="Efectivo", label=ft.Text("Efectivo"), icon=ft.Icon(ft.Icons.PAYMENTS)),
                ft.Segment(value="Tarjeta", label=ft.Text("Tarjeta"), icon=ft.Icon(ft.Icons.CREDIT_CARD)),
            ],
            on_change=self.cambiar_metodo_pago,
        )
        self.txt_efectivo_recibido = ft.TextField(
            label="Efectivo recibido",
            keyboard_type=ft.KeyboardType.NUMBER,
            input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9.]*"),
            expand=True,
            on_change=self.calcular_cambio,
        )
        self.lbl_cambio = ft.Text("Cambio: $0.00", size=18, weight=ft.FontWeight.BOLD, color="#28734D")
        self.lbl_error_pago = ft.Text("", size=15, color="#8A3B2E")
        self.boton_finalizar_pago = ft.FilledButton(
            "Registrar pago y pedido",
            icon=ft.Icons.DONE_ALL,
            bgcolor="#6A0404",
            color=ft.Colors.WHITE,
            height=48,
            on_click=self.registrar_pedido,
        )
        self.dialogo_checkout = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirmar pedido", color="#6A0404"),
            content=ft.Container(
                width=ancho_checkout,
                padding=ft.Padding(left=0, top=0, right=0, bottom=4),
                content=self.contenido_pago,
            ),
            actions=[
                ft.TextButton(
                    "Cancelar",
                    on_click=self.cerrar_checkout,
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.secciones = [
            self.seccion_menu,
            self.seccion_pedidos,
            self.seccion_entregas,
        ]
        self.indice_seccion = 0
        self.contenido_seccion = ft.Column(
            controls=[self.seccion_menu],
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )
        self.opciones_navegacion = [
            ("Menú", ft.Icons.LOCAL_PIZZA_OUTLINED, ft.Icons.LOCAL_PIZZA),
            ("Pedidos", ft.Icons.RECEIPT_LONG_OUTLINED, ft.Icons.RECEIPT_LONG),
            ("Entregas", ft.Icons.QR_CODE_SCANNER, ft.Icons.QR_CODE_SCANNER),
        ]
        self.navegacion_secciones = ft.Container(
            height=82,
            bgcolor="#6A0404",
            padding=ft.Padding(left=8, top=4, right=8, bottom=4),
            content=ft.Row(
                controls=[self.crear_opciones_navegacion()],
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )
        self.controls = [
            self.encabezado,
            self.contenido_seccion,
            self.navegacion_secciones,
        ]
        self.actualizar_resumen_pago()
        self.cargar_pedidos(None)

    def crear_boton_accion_pago(self, titulo, subtitulo, accion):
        self.total_accion_pago = ft.Text(
            self.lbl_total.value,
            size=18,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.WHITE,
        )
        return ft.Container(
            padding=12,
            bgcolor="#6A0404",
            border_radius=18,
            ink=True,
            on_click=accion,
            content=ft.Row(
                spacing=12,
                controls=[
                    ft.Container(
                        width=46,
                        height=46,
                        alignment=ft.Alignment.CENTER,
                        bgcolor=ft.Colors.WHITE,
                        border_radius=14,
                        content=ft.Icon(ft.Icons.CREDIT_CARD, color="#6A0404", size=25),
                    ),
                    ft.Column(
                        spacing=1,
                        expand=True,
                        controls=[
                            ft.Text(titulo, size=17, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                            ft.Text(subtitulo, size=14, color="#F8E8E0"),
                        ],
                    ),
                    ft.Column(
                        spacing=1,
                        horizontal_alignment=ft.CrossAxisAlignment.END,
                        controls=[
                            ft.Text("TOTAL", size=14, weight=ft.FontWeight.BOLD, color="#F8E8E0"),
                            self.total_accion_pago,
                        ],
                    ),
                ],
            ),
        )

    def crear_tarjeta_servicio(self, servicio, descripcion, icono, valor=None):
        return ft.Container(
            padding=14,
            height=76,
            bgcolor=ft.Colors.WHITE,
            border=ft.Border.all(1, "#E8D8CF"),
            border_radius=14,
            ink=True,
            on_click=lambda e, valor=valor or servicio: self.seleccionar_servicio(valor),
            content=ft.Row(
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(icono, color="#6A0404", size=24),
                    ft.Column(
                        spacing=2,
                        expand=True,
                        tight=True,
                        controls=[
                            ft.Text(servicio, weight=ft.FontWeight.BOLD, size=15),
                            ft.Text(descripcion, size=15, color="#806B63"),
                        ],
                    ),
                    ft.Icon(ft.Icons.CHECK_CIRCLE, color="#28734D", visible=False),
                ],
            ),
        )

    def crear_resumen_checkout(self):
        return ft.Container(
            padding=14,
            bgcolor=ft.Colors.WHITE,
            border_radius=14,
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Text("Resumen del pedido", size=17, weight=ft.FontWeight.BOLD, color="#3F302B"),
                    self.lista_resumen_pago,
                    ft.Divider(height=1, color="#F1E5DE"),
                    ft.Row(
                        [
                            ft.Text("Total", size=18, weight=ft.FontWeight.BOLD),
                            self.lbl_total_pago,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                ],
            ),
        )

    def iniciar_checkout(self, e=None):
        if not self.menu.obtener_items_estado():
            return
        self.paso_checkout = "servicio"
        self.construir_pantalla_servicio()
        self.page.show_dialog(self.dialogo_checkout)

    def cerrar_checkout(self, e=None):
        if self.page is not None:
            self.page.pop_dialog()

    def construir_pantalla_servicio(self):
        controles = [
            ft.Text("Confirma tu pedido", size=22, weight=ft.FontWeight.BOLD, color="#6A0404"),
            self.crear_resumen_checkout(),
        ]
        if not self.selector_servicio.value:
            controles.extend(
                [
                    ft.Text("Primero, selecciona el tipo de servicio", size=16, weight=ft.FontWeight.BOLD),
                    ft.Column(
                        controls=[self.tarjeta_comer, self.tarjeta_recoger],
                        spacing=10,
                        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                    ),
                    self.lbl_error_pago,
                ]
            )
        else:
            nombre_servicio = (
                "Para llevar"
                if self.selector_servicio.value == "Para recoger en tienda"
                else "Comer en tienda"
            )
            controles.extend(
                [
                    ft.Row(
                        [
                            ft.Text(
                                f"Servicio: {nombre_servicio}",
                                size=16,
                                weight=ft.FontWeight.BOLD,
                                color="#6A0404",
                                expand=True,
                            ),
                            ft.TextButton(
                                "Cambiar",
                                on_click=self.cambiar_seleccion_servicio,
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    self.txt_nombre,
                ]
            )
            if self.selector_servicio.value == "Para recoger en tienda":
                controles.extend([self.txt_telefono, self.lbl_aviso_telefono])
            controles.extend(
                [
                    self.lbl_error_pago,
                    self.crear_boton_accion_pago(
                        "Continuar al pago",
                        "Selecciona un método de pago",
                        self.continuar_a_metodo_pago,
                    ),
                ]
            )
        self.contenido_pago.controls = controles
        self.tarjeta_comer.content.controls[2].visible = self.selector_servicio.value == "Comer en tienda"
        self.tarjeta_recoger.content.controls[2].visible = self.selector_servicio.value == "Para recoger en tienda"
        self.actualizar_contenido_pago()

    def seleccionar_servicio(self, servicio):
        self.selector_servicio.value = servicio
        self.cambiar_servicio(None)
        self.tarjeta_comer.bgcolor = "#FFF1E7" if servicio == "Comer en tienda" else ft.Colors.WHITE
        self.tarjeta_recoger.bgcolor = "#FFF1E7" if servicio == "Para recoger en tienda" else ft.Colors.WHITE
        self.tarjeta_comer.border = ft.Border.all(2 if servicio == "Comer en tienda" else 1, "#6A0404" if servicio == "Comer en tienda" else "#E8D8CF")
        self.tarjeta_recoger.border = ft.Border.all(2 if servicio == "Para recoger en tienda" else 1, "#6A0404" if servicio == "Para recoger en tienda" else "#E8D8CF")
        self.tarjeta_comer.content.controls[2].visible = servicio == "Comer en tienda"
        self.tarjeta_recoger.content.controls[2].visible = servicio == "Para recoger en tienda"
        self.lbl_error_pago.value = ""
        self.construir_pantalla_servicio()

    def cambiar_seleccion_servicio(self, e=None):
        self.selector_servicio.value = None
        self.txt_telefono.value = ""
        self.txt_telefono.visible = False
        self.lbl_aviso_telefono.visible = False
        self.construir_pantalla_servicio()

    def continuar_a_metodo_pago(self, e=None):
        self.lbl_error_pago.value = ""
        if not (self.txt_nombre.value or "").strip():
            self.lbl_error_pago.value = "Escribe el nombre completo del cliente."
        elif not self.selector_servicio.value:
            self.lbl_error_pago.value = "Selecciona el tipo de servicio."
        elif self.selector_servicio.value == "Para recoger en tienda" and (
            len((self.txt_telefono.value or "").strip()) != 10
            or not (self.txt_telefono.value or "").strip().isdigit()
        ):
            self.lbl_error_pago.value = "Para recoger se requiere un teléfono de 10 dígitos."
        else:
            self.paso_checkout = "pago"
            self.construir_pantalla_metodo_pago()
            return
        self.actualizar_contenido_pago()

    def construir_pantalla_metodo_pago(self):
        self.contenido_pago.controls = [
            ft.Text("Selecciona el método de pago", size=22, weight=ft.FontWeight.BOLD, color="#6A0404"),
            self.crear_resumen_checkout(),
            self.selector_metodo_pago,
            ft.Row(
                [
                    ft.Text("$", size=22, weight=ft.FontWeight.BOLD, color="#6A0404"),
                    self.txt_efectivo_recibido,
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            self.lbl_cambio,
            self.info_pago,
            self.txt_nombre_titular,
            self.txt_tarjeta,
            ft.Row([self.txt_exp, self.txt_cvv], spacing=10),
            self.lbl_error_pago,
            self.boton_finalizar_pago,
            ft.TextButton("Volver a datos del pedido", on_click=self.volver_a_datos_pedido),
        ]
        self.actualizar_campos_metodo_pago()
        self.actualizar_contenido_pago()

    def cambiar_metodo_pago(self, e):
        self.actualizar_campos_metodo_pago()
        self.actualizar_contenido_pago()

    def actualizar_campos_metodo_pago(self):
        metodo = self.metodo_pago_seleccionado()
        es_efectivo = metodo == "Efectivo"
        self.txt_efectivo_recibido.visible = es_efectivo
        self.lbl_cambio.visible = es_efectivo
        self.info_pago.visible = not es_efectivo
        self.txt_nombre_titular.visible = not es_efectivo
        self.txt_tarjeta.visible = not es_efectivo
        self.txt_exp.visible = not es_efectivo
        self.txt_cvv.visible = not es_efectivo
        if es_efectivo:
            self.calcular_cambio(None)

    def metodo_pago_seleccionado(self):
        seleccion = self.selector_metodo_pago.selected
        return seleccion[0] if seleccion else "Efectivo"

    def calcular_cambio(self, e):
        try:
            recibido = float((self.txt_efectivo_recibido.value or "0").strip() or 0)
        except ValueError:
            recibido = 0
        total = sum(
            item["cantidad"] * item["precio"]
            for item in self.menu.obtener_items_estado()
        )
        cambio = max(0, recibido - total)
        self.lbl_cambio.value = f"Cambio: ${cambio:.2f}"
        self.lbl_cambio.color = "#28734D" if recibido >= total else "#8A3B2E"
        try:
            if self.lbl_cambio.page is not None:
                self.lbl_cambio.update()
        except RuntimeError:
            return

    def volver_a_datos_pedido(self, e=None):
        self.paso_checkout = "servicio"
        self.construir_pantalla_servicio()

    def actualizar_contenido_pago(self):
        try:
            if self.contenido_pago.page is not None:
                self.contenido_pago.update()
        except RuntimeError:
            return

    def crear_opciones_navegacion(self):
        opciones = []
        for indice, (etiqueta, icono, icono_seleccionado) in enumerate(
            self.opciones_navegacion
        ):
            seleccionado = indice == self.indice_seccion
            opciones.append(
                ft.Container(
                    expand=True,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Container(
                        padding=ft.Padding(left=18, top=8, right=18, bottom=8),
                        border_radius=24,
                        bgcolor=ft.Colors.WHITE if seleccionado else ft.Colors.TRANSPARENT,
                        content=ft.Column(
                            controls=[
                                ft.Icon(
                                    icono_seleccionado if seleccionado else icono,
                                    size=28 if seleccionado else 26,
                                    color="#6A0404" if seleccionado else "#FFE9DF",
                                ),
                                ft.Text(
                                    etiqueta,
                                    size=15 if seleccionado else 14,
                                    color="#6A0404" if seleccionado else "#FFE9DF",
                                    weight=(
                                        ft.FontWeight.BOLD
                                        if seleccionado
                                        else ft.FontWeight.W_500
                                    ),
                                ),
                            ],
                            spacing=2,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            tight=True,
                        ),
                    ),
                    on_click=lambda e, indice=indice: self.cambiar_seccion(indice),
                )
            )
        return ft.Container(
            width=None if self.es_movil else 640,
            expand=self.es_movil,
            content=ft.Row(
                controls=opciones,
                alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def cambiar_seccion(self, indice):
        if not 0 <= indice < len(self.secciones):
            return
        self.indice_seccion = indice
        self.contenido_seccion.controls = [self.secciones[indice]]
        try:
            if self.contenido_seccion.page is not None:
                self.contenido_seccion.update()
        except RuntimeError:
            pass
        self.navegacion_secciones.content.controls = [
            self.crear_opciones_navegacion()
        ]
        try:
            if self.navegacion_secciones.page is not None:
                self.navegacion_secciones.update()
        except RuntimeError:
            return

    def buscar_pedido_por_codigo(self, e):
        codigo = (self.txt_codigo_pedido.value or "").strip().upper()
        self.lbl_estado_entrega.value = ""
        self.codigo_pedido_encontrado = None
        self.id_pedido_encontrado = None
        if not codigo:
            self.lbl_estado_entrega.value = "Escanea o escribe el código del pedido."
            self.detalle_pedido_entrega.controls = []
            self.actualizar_estado_entrega()
            return

        try:
            respuesta = requests.get(
                f"{BASE_URL}/api/personal/pedidos/codigo/{codigo}",
                headers={
                    "Authorization": f"Bearer {self.personal['token']}",
                    "ngrok-skip-browser-warning": "true",
                },
                timeout=15,
            )
        except requests.RequestException:
            self.lbl_estado_entrega.value = "No se pudo conectar con el servidor."
            self.actualizar_estado_entrega()
            return

        if respuesta.status_code == 404:
            pedido = self.buscar_pedido_en_historial_vendedor(codigo)
            if pedido is not None:
                self.codigo_pedido_encontrado = pedido["codigo"]
                self.id_pedido_encontrado = pedido["id_pedido"]
                self.mostrar_detalle_pedido_entrega(pedido)
                return
            self.lbl_estado_entrega.value = (
                "No se encontró el pedido. El servidor puede no tener activa "
                "la búsqueda global; reinicia server.py y verifica la base de datos."
            )
            self.detalle_pedido_entrega.controls = []
            self.actualizar_estado_entrega()
            return
        if respuesta.status_code != 200:
            try:
                detalle = respuesta.json().get("detail")
            except ValueError:
                detalle = None
            self.lbl_estado_entrega.value = (
                detalle
                if isinstance(detalle, str)
                else "No se pudo consultar el pedido."
            )
            self.detalle_pedido_entrega.controls = []
            self.actualizar_estado_entrega()
            return

        pedido = respuesta.json()
        self.codigo_pedido_encontrado = pedido["codigo"]
        self.id_pedido_encontrado = pedido.get("id_pedido")
        self.mostrar_detalle_pedido_entrega(pedido)

    def buscar_pedido_en_historial_vendedor(self, codigo):
        digitos = codigo.removeprefix("PE-").lstrip("0") or "0"
        try:
            respuesta = requests.get(
                f"{BASE_URL}/api/personal/pedidos",
                headers={
                    "Authorization": f"Bearer {self.personal['token']}",
                    "ngrok-skip-browser-warning": "true",
                },
                timeout=15,
            )
        except requests.RequestException:
            return None
        if respuesta.status_code != 200:
            return None

        for pedido in respuesta.json().get("pedidos", []):
            id_pedido = str(pedido.get("id_pedido", ""))
            if id_pedido != digitos:
                continue
            pedido["codigo"] = f"PE-{int(id_pedido):06d}"
            return pedido
        return None

    def mostrar_detalle_pedido_entrega(self, pedido):
        estado = pedido["estado"]
        articulo_textos = [
            f"{item['cantidad']} × {item['nombre_pizza']}"
            for item in pedido.get("detalles", [])
        ]
        controles = [
            ft.Row(
                [
                    ft.Icon(ft.Icons.RECEIPT_LONG, color="#6A0404"),
                    ft.Text(
                        pedido["codigo"],
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color="#6A0404",
                        expand=True,
                    ),
                    ft.Container(
                        padding=ft.Padding(left=10, top=5, right=10, bottom=5),
                        bgcolor="#E8F4EC" if estado == "Finalizada" else "#FFF1E7",
                        border_radius=18,
                        content=ft.Text(
                            estado,
                            size=14,
                            weight=ft.FontWeight.BOLD,
                            color="#28734D" if estado == "Finalizada" else "#9A541D",
                        ),
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            ft.Text(
                f"Cliente: {pedido['nombre_contacto']}",
                size=14,
                weight=ft.FontWeight.W_500,
            ),
            ft.Text(
                f"Origen: {pedido.get('origen', 'No especificado')}",
                size=14,
                color="#806B63",
                visible=bool(pedido.get("origen")),
            ),
            ft.Text(f"Servicio: {pedido['tipo_servicio']}", size=15),
            ft.Text(
                f"Productos: {', '.join(articulo_textos)}",
                size=15,
            ),
            ft.Text(
                f"Total: ${pedido['total']:.2f}",
                size=16,
                weight=ft.FontWeight.BOLD,
            ),
        ]
        if pedido.get("telefono_contacto"):
            controles.append(
                ft.Text(
                    f"Teléfono: {pedido['telefono_contacto']}",
                    size=15,
                )
            )

        if estado == "Finalizada":
            controles.append(
                ft.Text(
                    "Este pedido ya fue entregado.",
                    size=15,
                    color="#28734D",
                )
            )
        elif estado == "Cancelada":
            controles.append(
                ft.Text(
                    "Este pedido está cancelado y no se puede entregar.",
                    size=15,
                    color="#8A3B2E",
                )
            )
        else:
            controles.append(
                ft.FilledButton(
                    "Confirmar entrega y finalizar",
                    icon=ft.Icons.DONE_ALL,
                    bgcolor="#6A0404",
                    color=ft.Colors.WHITE,
                    height=46,
                    on_click=self.confirmar_entrega_pedido,
                )
            )

        self.detalle_pedido_entrega.controls = [
            ft.Container(
                padding=16,
                bgcolor=ft.Colors.WHITE,
                border_radius=14,
                shadow=ft.BoxShadow(
                    blur_radius=12,
                    color=ft.Colors.with_opacity(0.07, ft.Colors.BLACK),
                    offset=ft.Offset(0, 3),
                ),
                content=ft.Column(spacing=10, controls=controles),
            )
        ]
        self.actualizar_estado_entrega()

    def confirmar_entrega_pedido(self, e):
        if not self.codigo_pedido_encontrado:
            self.lbl_estado_entrega.value = "Primero busca un pedido válido."
            self.actualizar_estado_entrega()
            return
        try:
            respuesta = requests.patch(
                f"{BASE_URL}/api/personal/pedidos/codigo/"
                f"{self.codigo_pedido_encontrado}/entregar",
                headers={
                    "Authorization": f"Bearer {self.personal['token']}",
                    "ngrok-skip-browser-warning": "true",
                },
                timeout=15,
            )
        except requests.RequestException:
            self.lbl_estado_entrega.value = "No se pudo conectar con el servidor."
            self.actualizar_estado_entrega()
            return

        if respuesta.status_code == 404 and self.id_pedido_encontrado is not None:
            try:
                respuesta = requests.patch(
                    f"{BASE_URL}/api/personal/pedidos/"
                    f"{self.id_pedido_encontrado}/estado",
                    json={"estado": "Finalizada"},
                    headers={
                        "Authorization": f"Bearer {self.personal['token']}",
                        "ngrok-skip-browser-warning": "true",
                    },
                    timeout=15,
                )
            except requests.RequestException:
                self.lbl_estado_entrega.value = "No se pudo conectar con el servidor."
                self.actualizar_estado_entrega()
                return

        if respuesta.status_code != 200:
            try:
                detalle = respuesta.json().get("detail")
            except ValueError:
                detalle = None
            self.lbl_estado_entrega.value = (
                detalle
                if isinstance(detalle, str)
                else "No se pudo confirmar la entrega."
            )
            self.actualizar_estado_entrega()
            return

        self.cargar_pedidos(None)
        self.buscar_pedido_por_codigo(None)
        self.lbl_estado_entrega.value = "Pedido entregado y finalizado."
        self.actualizar_estado_entrega()

    def actualizar_estado_entrega(self):
        try:
            if self.lbl_estado_entrega.page is not None:
                self.lbl_estado_entrega.update()
            if self.detalle_pedido_entrega.page is not None:
                self.detalle_pedido_entrega.update()
        except RuntimeError:
            return

    def did_mount(self):
        self._actualizacion_activa = True
        self._generacion_actualizacion += 1
        self.page.run_task(
            self.actualizar_pedidos_automaticamente,
            self._generacion_actualizacion,
        )

    def will_unmount(self):
        self._actualizacion_activa = False
        self._generacion_actualizacion += 1

    def actualizar_total(self):
        total = sum(
            item["cantidad"] * item["precio"]
            for item in self.menu.obtener_items_estado()
        )
        self.lbl_total.value = f"${total:.2f}"
        self.lbl_total_pago.value = f"${total:.2f}"
        if hasattr(self, "total_accion_pago"):
            self.total_accion_pago.value = f"${total:.2f}"
        self.boton_pagar_ahora.visible = total > 0
        self.actualizar_resumen_pago()
        controles = [self.lbl_total, self.lbl_total_pago, self.boton_pagar_ahora]
        if hasattr(self, "total_accion_pago"):
            controles.append(self.total_accion_pago)
        for control in controles:
            try:
                if control.page is not None:
                    control.update()
            except RuntimeError:
                continue

    def actualizar_resumen_pago(self):
        if not hasattr(self, "lista_resumen_pago"):
            return
        articulos = self.menu.obtener_items_estado()
        self.lista_resumen_pago.controls = [
            ft.Row(
                [
                    ft.Text(
                        f"{articulo['cantidad']} × {articulo['nombre']}",
                        size=15,
                        expand=True,
                    ),
                    ft.Text(
                        f"${articulo['cantidad'] * articulo['precio']:.2f}",
                        size=15,
                        weight=ft.FontWeight.W_500,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
            for articulo in articulos
        ] or [ft.Text("Agrega productos desde la pestaña Menú.", size=14, color="#806B63")]
        try:
            if self.lista_resumen_pago.page is not None:
                self.lista_resumen_pago.update()
        except RuntimeError:
            return

    def formatear_numero_tarjeta(self, e):
        campo = e.control
        valor = campo.value or ""
        seleccion = campo.selection
        digitos_antes = len(
            re.sub(r"\D", "", valor[: max(0, min(seleccion.base_offset, len(valor)))])
        ) if seleccion and seleccion.base_offset >= 0 else len(re.sub(r"\D", "", valor))
        digitos = re.sub(r"\D", "", valor)[:19]
        valor_formateado = " ".join(
            digitos[indice : indice + 4]
            for indice in range(0, len(digitos), 4)
        )
        if valor_formateado != valor:
            campo.value = valor_formateado
            posicion = digitos_antes + max(0, (digitos_antes - 1) // 4)
            campo.selection = ft.TextSelection(posicion, posicion)
            campo.update()

    def formatear_vencimiento(self, e):
        campo = e.control
        valor = campo.value or ""
        seleccion = campo.selection
        digitos_antes = len(
            re.sub(r"\D", "", valor[: max(0, min(seleccion.base_offset, len(valor)))])
        ) if seleccion and seleccion.base_offset >= 0 else len(re.sub(r"\D", "", valor))
        digitos = re.sub(r"\D", "", valor)[:4]
        valor_formateado = (
            f"{digitos[:2]}/{digitos[2:]}" if len(digitos) > 2 else digitos
        )
        if valor_formateado != valor:
            campo.value = valor_formateado
            posicion = digitos_antes + (1 if digitos_antes > 2 else 0)
            campo.selection = ft.TextSelection(posicion, posicion)
            campo.update()

    def cambiar_servicio(self, e):
        es_recoger = self.selector_servicio.value == "Para recoger en tienda"
        self.txt_telefono.visible = es_recoger
        self.lbl_aviso_telefono.visible = es_recoger
        if not es_recoger:
            self.txt_telefono.value = ""
        try:
            if self.txt_telefono.page is not None:
                self.txt_telefono.update()
                self.lbl_aviso_telefono.update()
        except RuntimeError:
            return

    def mostrar_alerta_pago(self, codigo, cambio, metodo_pago):
        detalle_pago = (
            f"Pedido {codigo} registrado. Cambio a entregar: ${cambio:.2f}."
            if metodo_pago == "Efectivo"
            else f"Pedido {codigo} registrado. Pago de tarjeta de demostración."
        )
        self.page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("¡Pago efectuado!", color="#6A0404"),
                content=ft.Text(detalle_pago),
                actions=[
                    ft.FilledButton(
                        "Aceptar",
                        bgcolor="#6A0404",
                        color=ft.Colors.WHITE,
                        on_click=lambda e: self.page.pop_dialog(),
                    )
                ],
                actions_alignment=ft.MainAxisAlignment.CENTER,
            )
        )

    def registrar_pedido(self, e):
        self.lbl_error_pago.value = ""
        nombre = (self.txt_nombre.value or "").strip()
        items = self.menu.obtener_items_estado()
        servicio = self.selector_servicio.value
        telefono = (self.txt_telefono.value or "").strip()
        if not nombre:
            self.lbl_error_pago.value = "Escribe el nombre completo del cliente."
            self.actualizar_contenido_pago()
            return
        if not items:
            self.lbl_error_pago.value = "Agrega al menos un producto al pedido."
            self.actualizar_contenido_pago()
            return
        if not servicio:
            self.lbl_error_pago.value = "Selecciona el tipo de servicio."
            self.actualizar_contenido_pago()
            return
        if servicio == "Para recoger en tienda" and (
            len(telefono) != 10 or not telefono.isdigit()
        ):
            self.lbl_error_pago.value = "Para recoger se requiere un teléfono de 10 dígitos."
            self.actualizar_contenido_pago()
            return
        metodo_pago = self.metodo_pago_seleccionado()
        total = sum(item["cantidad"] * item["precio"] for item in items)
        recibido = 0.0
        if metodo_pago == "Efectivo":
            try:
                recibido = float((self.txt_efectivo_recibido.value or "").strip())
            except ValueError:
                recibido = 0
            if recibido < total:
                self.lbl_error_pago.value = "El efectivo recibido debe cubrir el total del pedido."
                self.actualizar_contenido_pago()
                return
        ids_por_nombre = {
            producto["nombre"]: producto["id"]
            for producto in self.menu.productos
        }
        payload = {
            "nombre_contacto": nombre,
            "telefono_contacto": telefono if servicio == "Para recoger en tienda" else "",
            "tipo_servicio": servicio,
            "metodo_pago": metodo_pago,
            "items": [
                {
                    "producto_id": ids_por_nombre[item["nombre"]],
                    "cantidad": item["cantidad"],
                }
                for item in items
            ],
        }
        try:
            respuesta = requests.post(
                f"{BASE_URL}/api/personal/pedidos",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.personal['token']}",
                },
                timeout=15,
            )
        except requests.RequestException:
            self.lbl_error_pago.value = "No se pudo conectar con el servidor."
            self.actualizar_contenido_pago()
            return

        if respuesta.status_code != 201:
            try:
                detalle = respuesta.json().get("detail")
            except ValueError:
                detalle = None
            self.lbl_error_pago.value = (
                detalle
                if isinstance(detalle, str)
                else "No se pudo guardar el pedido."
            )
            self.actualizar_contenido_pago()
            return

        codigo = respuesta.json().get("codigo", "")
        self.menu.limpiar_carrito()
        self.txt_nombre.value = ""
        self.txt_telefono.value = ""
        self.txt_nombre_titular.value = ""
        self.txt_tarjeta.value = ""
        self.txt_exp.value = ""
        self.txt_cvv.value = ""
        self.txt_efectivo_recibido.value = ""
        self.selector_servicio.value = None
        self.selector_metodo_pago.selected = ["Efectivo"]
        self.lbl_error_pago.value = ""
        self.paso_checkout = "carrito"
        self.actualizar_total()
        self.cargar_pedidos(None)
        cambio = max(0, recibido - total) if metodo_pago == "Efectivo" else None
        self.cerrar_checkout()
        self.mostrar_alerta_pago(codigo, cambio, metodo_pago)

    def cargar_pedidos(self, e):
        try:
            respuesta = self.solicitar_pedidos()
        except requests.RequestException:
            self.lista_pedidos.controls = [
                ft.Text(
                    "No se pudo actualizar el historial. Inténtalo de nuevo.",
                    color="#8A3B2E",
                )
            ]
            self.actualizar_lista_pedidos()
            return

        self.mostrar_pedidos(respuesta)

    def solicitar_pedidos(self):
        return requests.get(
            f"{BASE_URL}/api/personal/pedidos",
            headers={
                "Authorization": f"Bearer {self.personal['token']}",
            },
            timeout=15,
        )

    def mostrar_pedidos(self, respuesta):
        if respuesta.status_code != 200:
            try:
                detalle = respuesta.json().get("detail")
            except ValueError:
                detalle = None
            self.lista_pedidos.controls = [
                ft.Text(
                    detalle
                    if isinstance(detalle, str)
                    else "No se pudo cargar el historial de pedidos.",
                    color="#8A3B2E",
                )
            ]
            self.actualizar_lista_pedidos()
            return

        pedidos = respuesta.json().get("pedidos", [])
        id_vendedor_actual = self.personal.get("id")

        def es_pedido_propio(pedido):
            id_vendedor = pedido.get("id_vendedor")
            if id_vendedor is not None:
                return str(id_vendedor) == str(id_vendedor_actual)
            return str(pedido.get("origen") or "").strip().casefold() != "app"

        pedidos = [pedido for pedido in pedidos if es_pedido_propio(pedido)]
        self.lista_pedidos.controls = [
            self.crear_tarjeta_pedido(pedido) for pedido in pedidos
        ] or [ft.Text("Todavía no hay pedidos registrados.", color="#806B63")]
        self.actualizar_lista_pedidos()

    async def actualizar_pedidos_automaticamente(self, generacion):
        while (
            self._actualizacion_activa
            and generacion == self._generacion_actualizacion
        ):
            await asyncio.sleep(30)
            if (
                not self._actualizacion_activa
                or generacion != self._generacion_actualizacion
            ):
                return
            try:
                respuesta = await asyncio.to_thread(self.solicitar_pedidos)
            except requests.RequestException:
                self.lbl_estado.value = "No se pudo actualizar el historial."
                self.actualizar_estado()
                continue
            if (
                self._actualizacion_activa
                and generacion == self._generacion_actualizacion
            ):
                self.mostrar_pedidos(respuesta)

    def crear_tarjeta_pedido(self, pedido):
        estado = pedido["estado"]
        servicio = pedido["tipo_servicio"]
        acciones = []
        if estado == "En Proceso" and servicio == "Para recoger en tienda":
            acciones.append(
                ft.OutlinedButton(
                    "Marcar listo para recoger",
                    on_click=lambda e, pedido_id=pedido["id_pedido"]: self.cambiar_estado_pedido(
                        pedido_id,
                        "Lista",
                    ),
                )
            )
        if estado in ("En Proceso", "Lista") and not (
            estado == "En Proceso" and servicio == "Para recoger en tienda"
        ):
            acciones.append(
                ft.OutlinedButton(
                    "Finalizar pedido",
                    on_click=lambda e, pedido_id=pedido["id_pedido"]: self.cambiar_estado_pedido(
                        pedido_id,
                        "Finalizada",
                    ),
                )
            )

        return ft.Container(
            padding=12,
            bgcolor="#FFF8F2",
            border_radius=12,
            content=ft.Column(
                spacing=5,
                controls=[
                    ft.Row(
                        [
                            ft.Text(
                                f"PE-{pedido['id_pedido']:06d}",
                                weight=ft.FontWeight.BOLD,
                                color="#6A0404",
                            ),
                            ft.Text(
                                f"${pedido['total']:.2f}",
                                weight=ft.FontWeight.BOLD,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Text(
                        f"{pedido['fecha']} · {estado}",
                        size=14,
                    ),
                    ft.Text(
                        f"{pedido['nombre_contacto']} · {servicio}",
                        size=15,
                    ),
                    ft.Text(
                        f"Origen: {pedido.get('origen', 'No especificado')}",
                        size=14,
                        color="#806B63",
                        visible=bool(pedido.get("origen")),
                    ),
                    ft.Text(
                        f"Pago: {pedido.get('metodo_pago') or 'No especificado'}",
                        size=14,
                        color="#806B63",
                    ),
                    ft.Text(
                        " · ".join(
                            f"{item['cantidad']}× {item['nombre_pizza']}"
                            for item in pedido.get("detalles", [])
                        ),
                        size=14,
                    ),
                    ft.Text(
                        f"Teléfono: {pedido['telefono_contacto']}"
                        if pedido.get("telefono_contacto")
                        else "",
                        size=14,
                        visible=bool(pedido.get("telefono_contacto")),
                    ),
                    ft.Row(acciones, wrap=True, spacing=8) if acciones else ft.Container(),
                ],
            ),
        )

    def cambiar_estado_pedido(self, id_pedido, estado):
        try:
            respuesta = requests.patch(
                f"{BASE_URL}/api/personal/pedidos/{id_pedido}/estado",
                json={"estado": estado},
                headers={
                    "Authorization": f"Bearer {self.personal['token']}",
                },
                timeout=15,
            )
        except requests.RequestException:
            self.lbl_estado.value = "No se pudo conectar con el servidor."
            self.actualizar_estado()
            return

        if respuesta.status_code != 200:
            try:
                detalle = respuesta.json().get("detail")
            except ValueError:
                detalle = None
            self.lbl_estado.value = (
                detalle
                if isinstance(detalle, str)
                else "No se pudo actualizar el estado del pedido."
            )
            self.actualizar_estado()
            return

        self.lbl_estado.value = "Estado del pedido actualizado."
        self.cargar_pedidos(None)
        self.actualizar_estado()

    def actualizar_lista_pedidos(self):
        try:
            if self.lista_pedidos.page is not None:
                self.lista_pedidos.update()
        except RuntimeError:
            return

    def actualizar_estado(self):
        try:
            if self.lbl_estado.page is not None:
                self.lbl_estado.update()
        except RuntimeError:
            return
