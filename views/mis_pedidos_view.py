import asyncio
from datetime import datetime, timedelta

import flet as ft
import requests
from config import BASE_URL


_PATRONES_CODE128 = """
11011001100 11001101100 11001100110 10010011000 10010001100
10001001100 10011001000 10011000100 10001100100 11001001000
11001000100 11000100100 10110011100 10011011100 10011001110
10111001100 10011101100 10011100110 11001110010 11001011100
11001001110 11011100100 11001110100 11101101110 11101001100
11100101100 11100100110 11101100100 11100110100 11100110010
11011011000 11011000110 11000110110 10100011000 10001011000
10001000110 10110001000 10001101000 10001100010 11010001000
11000101000 11000100010 10110111000 10110001110 10001101110
10111011000 10111000110 10001110110 11101110110 11010001110
11000101110 11011101000 11011100010 11011101110 11101011000
11101000110 11100010110 11101101000 11101100010 11100011010
11101111010 11001000010 11110001010 10100110000 10100001100
10010110000 10010000110 10000101100 10000100110 10110010000
10110000100 10011010000 10011000010 10000110100 10000110010
11000010010 11001010000 11110111010 11000010100 10001111010
10100111100 10010111100 10010011110 10111100100 10011110100
10011110010 11110100100 11110010100 11110010010 11011011110
11011110110 11110110110 10101111000 10100011110 10001011110
10111101000 10111100010 11110101000 11110100010 10111011110
10111101110 11101011110 11110101110 11010000100 11010010000
""".split()
_PATRON_PARADA_CODE128 = "1100011101011"


def _codificar_code128(codigo_pedido):
    if not codigo_pedido or any(
        not 32 <= ord(caracter) <= 126 for caracter in codigo_pedido
    ):
        raise ValueError("Code 128 solo admite caracteres ASCII imprimibles.")

    palabras_codigo = [104, *(ord(caracter) - 32 for caracter in codigo_pedido)]
    checksum = sum(
        indice * palabra for indice, palabra in enumerate(palabras_codigo)
    ) % 103
    return (
        "".join(_PATRONES_CODE128[palabra] for palabra in palabras_codigo)
        + _PATRONES_CODE128[checksum]
        + _PATRON_PARADA_CODE128
    )


def crear_codigo_barras(codigo_pedido, ancho=300):
    bits = _codificar_code128(codigo_pedido)
    modulo = ancho / (len(bits) + 20)
    controles = [ft.Container(width=modulo * 10, height=60, bgcolor=ft.Colors.WHITE)]
    posicion = 0
    while posicion < len(bits):
        fin = posicion + 1
        while fin < len(bits) and bits[fin] == bits[posicion]:
            fin += 1
        controles.append(
            ft.Container(
                width=modulo * (fin - posicion),
                height=60,
                bgcolor=ft.Colors.BLACK if bits[posicion] == "1" else ft.Colors.WHITE,
            )
        )
        posicion = fin
    controles.append(
        ft.Container(width=modulo * 10, height=60, bgcolor=ft.Colors.WHITE)
    )

    return ft.Container(
        width=ancho,
        height=90,
        alignment=ft.Alignment.CENTER,
        content=ft.Row(
            controls=controles,
            width=ancho,
            height=60,
            spacing=0,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
    )


class MisPedidosView(ft.Column):
    def __init__(
        self,
        usuario_actual,
        vista_inicio=False,
        es_movil=False,
        pedido_activo=None,
        historial=None,
        error_consulta=None,
        cargando=False,
    ):
        super().__init__()
        self.expand = True
        self.spacing = 0
        self.usuario_actual = usuario_actual
        self.vista_inicio = vista_inicio
        self.es_movil = es_movil
        self.detalles_activo_visible = True
        self.pedido_activo = pedido_activo
        self.error_consulta = error_consulta

        if self.usuario_actual.get("id") and not self.usuario_actual.get("token"):
            self.error_consulta = (
                "Inicia sesión nuevamente para consultar tus pedidos."
            )

        if cargando:
            self.controls = [
                ft.Container(
                    content=ft.Text(
                        "MIS PEDIDOS",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color="#6A0404",
                    ),
                    padding=10,
                    alignment=ft.Alignment.CENTER,
                    bgcolor="#FEEFE5D8",
                ),
                ft.Container(
                    expand=True,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Column(
                        controls=[
                            ft.ProgressRing(color="#6A0404"),
                            ft.Text(
                                "Cargando tus pedidos...",
                                size=14,
                                color=ft.Colors.GREY_700,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=12,
                    ),
                ),
            ]
            return

        controles_pedidos = [ft.Container(height=10)]
        if self.usuario_actual["id"]:
            historial = historial or []

            if vista_inicio and self.pedido_activo:
                codigo_pedido = f"PE-{self.pedido_activo['id_pedido']:06d}"
                self.controls = [
                    ft.Container(
                        expand=True,
                        alignment=ft.Alignment.CENTER,
                        padding=20,
                        content=ft.Container(
                            width=320 if es_movil else 520,
                            padding=20,
                            bgcolor="#FFF8F2",
                            border_radius=24,
                            shadow=ft.BoxShadow(
                                spread_radius=1,
                                blur_radius=12,
                                color=ft.Colors.with_opacity(0.12, ft.Colors.BLACK),
                                offset=ft.Offset(0, 5),
                            ),
                            content=ft.Column(
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=12,
                                controls=[
                                    ft.Image(
                                        src="imagenes/detalle_pedido.gif",
                                        width=220 if es_movil else 300,
                                        height=125,
                                        fit=ft.BoxFit.CONTAIN,
                                    ),
                                    ft.Text(
                                        "¡Estamos preparando tu pedido!",
                                        size=19,
                                        weight=ft.FontWeight.BOLD,
                                        color="#6A0404",
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                    ft.Text(
                                        "Tu pedido activo está en proceso.",
                                        size=14,
                                        color=ft.Colors.GREY_700,
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                    ft.Container(
                                        padding=ft.Padding(
                                            left=14, top=7, right=14, bottom=7
                                        ),
                                        bgcolor="#FCE8E6",
                                        border_radius=18,
                                        content=ft.Text(
                                            codigo_pedido,
                                            size=15,
                                            weight=ft.FontWeight.BOLD,
                                            color="#6A0404",
                                        ),
                                    ),
                                    ft.Text(
                                        "Presenta este código al vendedor",
                                        size=13,
                                        color=ft.Colors.GREY_700,
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                    crear_codigo_barras(
                                        codigo_pedido,
                                        ancho=300 if es_movil else 420,
                                    ),
                                ],
                            ),
                        ),
                    )
                ]
                return

            if self.pedido_activo:
                self.gif_pedido = ft.Image(
                    src="imagenes/detalle_pedido.gif",
                    width=240,
                    height=135,
                    fit=ft.BoxFit.CONTAIN,
                )
                self.panel_pedido_activo = self.crear_panel_pedido_activo(
                    self.pedido_activo
                )
                self.seccion_pedido_activo = ft.Column(
                    controls=[
                        self.gif_pedido,
                        self.panel_pedido_activo,
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                )
                self.btn_ver_pedido_activo = ft.OutlinedButton(
                    "Ver pedido activo",
                    icon=ft.Icons.RECEIPT_LONG,
                    on_click=self.mostrar_detalles_pedido,
                    visible=False,
                )
                controles_pedidos.append(
                    ft.Container(
                        content=ft.Column(
                            controls=[self.seccion_pedido_activo],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        visible=True,
                        alignment=ft.Alignment.CENTER,
                    )
                )
                controles_pedidos.append(
                    ft.Container(
                        content=self.btn_ver_pedido_activo,
                        width=320,
                        alignment=ft.Alignment.CENTER,
                    )
                )

            encabezado_historial = ft.Text(
                "HISTORIAL DE PEDIDOS",
                size=18,
                weight=ft.FontWeight.BOLD,
                color="#6A0404",
                text_align=ft.TextAlign.CENTER,
            )
            if es_movil:
                self.seccion_historial = ft.Column(
                    visible=not bool(self.pedido_activo),
                    spacing=8,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[encabezado_historial],
                )
            else:
                self.seccion_historial = ft.ResponsiveRow(
                    expand=True,
                    visible=not bool(self.pedido_activo),
                    spacing=8,
                    run_spacing=8,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ft.Container(
                            col=12,
                            alignment=ft.Alignment.CENTER,
                            content=encabezado_historial,
                        )
                    ],
                )

            if self.error_consulta:
                self.seccion_historial.controls.append(
                    ft.Container(
                        content=ft.Text(
                            self.error_consulta,
                            size=14,
                            color=ft.Colors.GREY_700,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        alignment=ft.Alignment.CENTER,
                        padding=30,
                    )
                )
            elif historial:
                self.seccion_historial.controls.extend(
                    self.tarjeta_pedido(
                        registro["id_pedido"],
                        registro["fecha"],
                        registro["total"],
                        registro["estado"],
                    )
                    for registro in historial
                )
            elif not self.pedido_activo:
                self.seccion_historial.controls.append(
                    ft.Container(
                        content=ft.Text(
                            "No tienes pedidos registrados aún.",
                            size=14,
                            color=ft.Colors.GREY_700,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        alignment=ft.Alignment.CENTER,
                        padding=30,
                    )
                )
            controles_pedidos.append(self.seccion_historial)
        else:
            controles_pedidos.append(
                ft.Container(
                    content=ft.Text(
                        "Inicia sesión para ver tus pedidos.",
                        size=14,
                        color=ft.Colors.GREY_700,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    alignment=ft.Alignment.CENTER,
                    padding=30,
                )
            )

        controles_pedidos.append(ft.Container(height=20))
        self.controls = [
            ft.Container(
                content=ft.Text(
                    "MIS PEDIDOS",
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color="#6A0404",
                    text_align=ft.TextAlign.CENTER,
                ),
                padding=10,
                alignment=ft.Alignment.CENTER,
                bgcolor="#FEEFE5D8",
            ),
            ft.Container(
                expand=True,
                content=ft.Column(
                    scroll=ft.ScrollMode.AUTO,
                    spacing=8,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=controles_pedidos,
                ),
            ),
        ]

    async def cargar_pedidos(self):
        pedido_activo = None
        historial = []
        error_consulta = None

        if not self.usuario_actual.get("token"):
            error_consulta = "Inicia sesión nuevamente para consultar tus pedidos."
        else:
            try:
                pedido_activo, historial = await asyncio.to_thread(
                    self.consultar_pedidos
                )
            except requests.HTTPError as error:
                if error.response is not None and error.response.status_code == 401:
                    error_consulta = "Tu sesión expiró. Inicia sesión nuevamente."
                else:
                    error_consulta = (
                        "No se pudieron cargar tus pedidos. Inténtalo de nuevo."
                    )
            except (requests.RequestException, KeyError, ValueError):
                error_consulta = (
                    "No se pudieron cargar tus pedidos. Revisa tu conexión "
                    "e inténtalo de nuevo."
                )

        return MisPedidosView(
            usuario_actual=self.usuario_actual,
            vista_inicio=self.vista_inicio,
            es_movil=self.es_movil,
            pedido_activo=pedido_activo,
            historial=historial,
            error_consulta=error_consulta,
        )

    def consultar_pedidos(self):
        respuesta = requests.get(
            f"{BASE_URL}/api/pedidos",
            headers={"Authorization": f"Bearer {self.usuario_actual['token']}"},
            timeout=15,
        )
        respuesta.raise_for_status()
        datos = respuesta.json()
        return datos["pedido_activo"], datos["historial"]

    def crear_panel_pedido_activo(self, pedido):
        try:
            if pedido["tipo_servicio"] == "En Tienda" and pedido.get(
                "hora_recoleccion"
            ):
                fecha_estimada = datetime.fromisoformat(
                    pedido["hora_recoleccion"]
                ).astimezone()
            else:
                fecha_pedido = datetime.strptime(
                    pedido["fecha"], "%d/%m/%Y - %H:%M"
                )
                minutos_estimados = (
                    45 if pedido["tipo_servicio"] == "A Domicilio" else 30
                )
                fecha_estimada = fecha_pedido + timedelta(
                    minutes=minutos_estimados
                )
            estimacion = fecha_estimada.strftime("%d/%m/%Y - %H:%M")
        except ValueError:
            estimacion = "No disponible"

        codigo_pedido = f"PE-{pedido['id_pedido']:06d}"
        filas_detalle = [
            ft.Row(
                controls=[
                    ft.Text(
                        f"{articulo['cantidad']} x {articulo['nombre_pizza']}",
                        size=14,
                        expand=True,
                    ),
                    ft.Text(
                        f"${articulo['cantidad'] * articulo['precio_unitario']:.2f}",
                        size=14,
                        weight=ft.FontWeight.BOLD,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
            for articulo in pedido["detalles"]
        ]
        return ft.Container(
            width=320,
            padding=18,
            margin=ft.Margin(left=10, top=8, right=10, bottom=8),
            bgcolor="#E7E7E7",
            border_radius=18,
            content=ft.Column(
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(
                                "Detalles del pedido",
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                color="#6A0404",
                                expand=True,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.CLOSE,
                                tooltip="Cerrar detalles",
                                icon_color=ft.Colors.GREY_700,
                                icon_size=20,
                                on_click=self.cerrar_detalles_pedido,
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Text(
                        f"Código de pedido: {codigo_pedido}",
                        size=15,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text(
                        "El código identifica el pedido; sus datos aparecen abajo.",
                        size=13,
                        color=ft.Colors.GREY_700,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    crear_codigo_barras(codigo_pedido),
                    ft.Text(f"A nombre de: {pedido['nombre_contacto']}", size=15),
                    ft.Text(f"Fecha y hora del pedido: {pedido['fecha']}", size=14),
                    ft.Text(f"Hora estimada: {estimacion}", size=14),
                    ft.Text(
                        f"Servicio: {pedido['tipo_servicio']}",
                        size=14,
                        color=ft.Colors.GREY_700,
                    ),
                    ft.Divider(height=1),
                    ft.Text(
                        "Detalle del pedido",
                        size=15,
                        weight=ft.FontWeight.BOLD,
                        color="#6A0404",
                    ),
                    *filas_detalle,
                    ft.Text(
                        f"Total del pedido: ${pedido['total']:.2f}",
                        size=15,
                        weight=ft.FontWeight.BOLD,
                        color="#6A0404",
                    ),
                ],
            ),
        )

    def cerrar_detalles_pedido(self, e):
        self.detalles_activo_visible = False
        self.seccion_pedido_activo.visible = False
        self.btn_ver_pedido_activo.visible = True
        self.seccion_historial.visible = True
        self.seccion_pedido_activo.update()
        self.btn_ver_pedido_activo.update()
        self.seccion_historial.update()

    def mostrar_detalles_pedido(self, e):
        self.detalles_activo_visible = True
        self.seccion_pedido_activo.visible = True
        self.btn_ver_pedido_activo.visible = False
        self.seccion_historial.visible = False
        self.seccion_pedido_activo.update()
        self.btn_ver_pedido_activo.update()
        self.seccion_historial.update()

    def tarjeta_pedido(self, id_pedido, fecha, total, estado):
        return ft.Container(
            col={
                ft.ResponsiveRowBreakpoint.XS: 12,
                ft.ResponsiveRowBreakpoint.LG: 6,
            },
            padding=12,
            margin=10,
            bgcolor=ft.Colors.WHITE,
            border_radius=8,
            border=ft.Border(left=ft.BorderSide(4, ft.Colors.GREEN_700)),
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(
                                f"Pedido #{id_pedido}",
                                weight=ft.FontWeight.BOLD,
                                size=15,
                                color=ft.Colors.BLACK_87,
                            ),
                            ft.Text(
                                estado,
                                weight=ft.FontWeight.BOLD,
                                size=13,
                                color=ft.Colors.GREEN_700,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Divider(height=10, color=ft.Colors.GREY_300),
                    ft.Row(
                        controls=[
                            ft.Text(
                                f"Fecha: {fecha}",
                                size=13,
                                color=ft.Colors.GREY_700,
                                expand=True,
                            ),
                            ft.Text(
                                f"Total: ${total:.2f}",
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                color="#6A0404",
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                ],
            ),
        )
