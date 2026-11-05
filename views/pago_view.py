import re

import flet as ft
import requests
from config import BASE_URL

class PagoView(ft.Column):
    def __init__(
        self,
        usuario_actual,
        datos_pedido,
        items_estado,
        on_cancelar,
        on_compra_finalizada,
        es_movil=False,
    ):
        super().__init__()
        self.expand = not es_movil
        self.spacing = 0
        self.usuario_actual = usuario_actual
        self.datos_pedido = datos_pedido
        self.items_estado = items_estado
        self.on_cancelar = on_cancelar
        self.on_compra_finalizada = on_compra_finalizada

        tamano_texto = 13 if es_movil else 15
        alto_campo = 42 if es_movil else 52
        self.txt_tarjeta = ft.TextField(
            label="Número de Tarjeta",
            hint_text="0000 0000 0000 0000",
            keyboard_type=ft.KeyboardType.NUMBER,
            input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9 ]*"),
            max_length=23,
            text_size=tamano_texto,
            height=alto_campo,
            content_padding=10 if es_movil else 12,
            expand=not es_movil,
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
            content_padding=10 if es_movil else 12,
            expand=True,
            on_change=self.formatear_vencimiento,
        )
        self.txt_cvv = ft.TextField(label="CVV", text_size=13, height=42, content_padding=10, password=True, expand=True)
        self.txt_cvv.keyboard_type = ft.KeyboardType.NUMBER
        self.txt_cvv.input_filter = ft.InputFilter(
            allow=True,
            regex_string=r"[0-9]*",
        )
        self.txt_cvv.max_length = 4
        self.txt_nombre_titular = ft.TextField(label="Nombre del Titular", text_size=tamano_texto, height=alto_campo, content_padding=10 if es_movil else 12, expand=not es_movil)
        self.lbl_error = ft.Text("", color=ft.Colors.RED_700, size=12, weight="bold")
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
                            ft.Icon(
                                ft.Icons.LOCK_OUTLINE,
                                size=18,
                                color="#6A0404",
                            ),
                            ft.Text(
                                "Pago de demostración: no hay pasarela conectada",
                                size=12,
                                color="#54423B",
                                weight=ft.FontWeight.W_500,
                                expand=True,
                            ),
                        ],
                    ),
                    ft.Row(
                        spacing=8,
                        controls=[
                            ft.Text(
                                marca,
                                size=12,
                                weight=ft.FontWeight.BOLD,
                                color=color,
                            )
                            for marca, color in (
                                ("VISA", "#1A1F71"),
                                ("Mastercard", "#EB001B"),
                                ("AMEX", "#2E77BC"),
                            )
                        ],
                    ),
                    ft.Text(
                        "Marcas ilustrativas; aún no se procesan pagos.",
                        size=11,
                        color="#806B63",
                    ),
                ],
            ),
        )
        self.btn_cancelar = ft.OutlinedButton(
            content=ft.Text(
                "Cancelar",
                color=ft.Colors.RED_900,
                weight="bold",
            ),
            height=48,
            style=ft.ButtonStyle(
                side=ft.BorderSide(1, ft.Colors.RED_900)
            ),
            on_click=lambda e: self.on_cancelar(),
        )
        self.btn_finalizar = ft.FilledButton(
            content=ft.Text(
                "Finalizar compra",
                color=ft.Colors.WHITE,
                weight="bold",
            ),
            bgcolor="#6A0404",
            color=ft.Colors.WHITE,
            height=48,
            expand=True,
            on_click=self.finalizar_compra_bd,
        )
        if es_movil:
            self.acciones_pago = ft.Column(
                [self.btn_cancelar, self.btn_finalizar],
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                spacing=10,
            )
        else:
            self.acciones_pago = ft.Row(
                [self.btn_cancelar, self.btn_finalizar],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                spacing=14,
            )

        self.controls = [
            ft.Container(
                content=ft.Row([
                    ft.TextButton(
                        content=ft.Row([ft.Icon(ft.Icons.ARROW_BACK, size=16, color="#6A0404"), ft.Text("Volver", color="#6A0404", weight="bold")], spacing=2),
                        on_click=lambda e: self.on_cancelar(),
                        style=ft.ButtonStyle(padding=5)
                    ),
                    ft.Text("DATOS DE PAGO", size=14, weight="bold", color="#6A0404"),
                    ft.Container(width=50)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=5,
                bgcolor="#FEEFE5D8"
            ),
            ft.Column(
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
                                    ft.ResponsiveRowBreakpoint.MD: 9,
                                    ft.ResponsiveRowBreakpoint.LG: 7,
                                    ft.ResponsiveRowBreakpoint.XL: 6,
                                },
                                padding=28,
                                bgcolor=ft.Colors.WHITE,
                                border_radius=22,
                                shadow=ft.BoxShadow(
                                    blur_radius=18,
                                    color=ft.Colors.with_opacity(
                                        0.1,
                                        ft.Colors.BLACK,
                                    ),
                                    offset=ft.Offset(0, 6),
                                ),
                                content=ft.Column(
                                    spacing=16,
                                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                                    controls=[
                                        ft.Icon(
                                            ft.Icons.PAYMENT,
                                            size=38,
                                            color="#6A0404",
                                        ),
                                        self.info_pago,
                                        ft.Text(
                                            f"Total a pagar: ${self.datos_pedido['total']:.2f}",
                                            size=22,
                                            weight=ft.FontWeight.BOLD,
                                            color="#6A0404",
                                            text_align=ft.TextAlign.CENTER,
                                        ),
                                        ft.Divider(),
                                        self.txt_nombre_titular,
                                        self.txt_tarjeta,
                                        ft.ResponsiveRow(
                                            spacing=10,
                                            controls=[
                                                ft.Container(
                                                    content=self.txt_exp,
                                                    col={
                                                        ft.ResponsiveRowBreakpoint.XS: 6,
                                                    },
                                                ),
                                                ft.Container(
                                                    content=self.txt_cvv,
                                                    col={
                                                        ft.ResponsiveRowBreakpoint.XS: 6,
                                                    },
                                                ),
                                            ],
                                        ),
                                        self.lbl_error,
                                        self.acciones_pago,
                                    ],
                                ),
                            )
                        ],
                    )
                ],
            )
        ]
        if es_movil:
            self.controls[1] = ft.Container(
                padding=20,
                content=ft.Column(
                    [
                        ft.Text(
                            f"Total a Pagar: ${self.datos_pedido['total']:.2f}",
                            size=16,
                            weight="bold",
                            color="#6A0404",
                        ),
                        ft.Divider(height=10),
                        self.info_pago,
                        self.txt_nombre_titular,
                        self.txt_tarjeta,
                        ft.Row([self.txt_exp, self.txt_cvv], spacing=8),
                        ft.Container(height=5),
                        self.lbl_error,
                        ft.Container(height=5),
                        self.acciones_pago,
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=12,
                ),
            )

    def formatear_numero_tarjeta(self, e):
        campo = e.control
        valor = campo.value or ""
        seleccion = campo.selection
        digitos_antes = (
            len(
                re.sub(
                    r"\D",
                    "",
                    valor[: max(0, min(seleccion.base_offset, len(valor)))],
                )
            )
            if seleccion and seleccion.base_offset >= 0
            else len(re.sub(r"\D", "", valor))
        )
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
        digitos_antes = (
            len(
                re.sub(
                    r"\D",
                    "",
                    valor[: max(0, min(seleccion.base_offset, len(valor)))],
                )
            )
            if seleccion and seleccion.base_offset >= 0
            else len(re.sub(r"\D", "", valor))
        )
        digitos = re.sub(r"\D", "", valor)[:4]
        valor_formateado = (
            f"{digitos[:2]}/{digitos[2:]}" if len(digitos) > 2 else digitos
        )
        if valor_formateado != valor:
            campo.value = valor_formateado
            posicion = digitos_antes + (1 if digitos_antes > 2 else 0)
            campo.selection = ft.TextSelection(posicion, posicion)
            campo.update()

    def finalizar_compra_bd(self, e):
        if not self.usuario_actual.get("id") or not self.usuario_actual.get("token"):
            self.lbl_error.value = "¡Debes iniciar sesión para finalizar la compra!"
            self.lbl_error.update()
            return

        items = [
            {
                "nombre_pizza": item["nombre"],
                "cantidad": item["cantidad"],
                "precio_unitario": item["precio"],
            }
            for item in self.items_estado
            if item.get("cantidad", 0) > 0
        ]
        if not items:
            self.lbl_error.value = (
                "Tu carrito está vacío. Regresa al menú y agrega al menos un producto."
            )
            self.lbl_error.update()
            return

        payload = {
            "nombre_contacto": self.datos_pedido["nombre_contacto"],
            "tipo_servicio": self.datos_pedido["tipo_servicio"],
            "direccion": self.datos_pedido["direccion"],
            "referencias": self.datos_pedido["referencias"],
            "hora_recoleccion": self.datos_pedido["hora_recoleccion"],
            "subtotal": self.datos_pedido["subtotal"],
            "costo_envio": self.datos_pedido["envio"],
            "total": self.datos_pedido["total"],
            "items": items,
        }
        try:
            respuesta = requests.post(
                f"{BASE_URL}/api/pedidos",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.usuario_actual['token']}"
                },
                timeout=15,
            )
            if respuesta.status_code == 401:
                self.lbl_error.value = "Tu sesión expiró. Inicia sesión nuevamente."
                self.lbl_error.update()
                return
            if respuesta.status_code == 422:
                try:
                    detalle = respuesta.json().get("detail")
                except ValueError:
                    detalle = None

                if isinstance(detalle, str):
                    mensaje_error = detalle
                elif isinstance(detalle, list) and any(
                    isinstance(error, dict)
                    and "items" in error.get("loc", [])
                    for error in detalle
                ):
                    mensaje_error = (
                        "El pedido no contiene productos válidos. "
                        "Regresa al menú y agrega al menos un producto."
                    )
                else:
                    mensaje_error = (
                        "No se pudieron validar los datos del pedido. "
                        "Revísalos e inténtalo de nuevo."
                    )

                self.lbl_error.value = mensaje_error
                self.lbl_error.update()
                return
            respuesta.raise_for_status()
        except requests.RequestException:
            self.lbl_error.value = (
                "No se pudo guardar el pedido en el servidor. "
                "Revisa tu conexión e inténtalo de nuevo."
            )
            self.lbl_error.update()
            return

        self.on_compra_finalizada()