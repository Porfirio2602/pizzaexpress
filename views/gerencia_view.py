import asyncio
from datetime import datetime

import requests
import flet as ft
from config import BASE_URL


class GerenciaView(ft.Column):
    def __init__(self, personal, on_cerrar_sesion, es_movil=False):
        super().__init__()
        self.personal = personal
        self.on_cerrar_sesion = on_cerrar_sesion
        self._actualizacion_activa = False
        self._generacion_actualizacion = 0
        self.es_movil = es_movil
        self.expand = True
        self.spacing = 12
        self.token_headers = {
            "Authorization": f"Bearer {personal.get('token', '')}",
        }
        self.txt_fecha = ft.TextField(
            label="Fecha del reporte (DD/MM/AAAA)",
            value=datetime.now().astimezone().strftime("%d/%m/%Y"),
            width=260,
        )
        self.lbl_error = ft.Text("", color=ft.Colors.RED_700, size=13)
        self.lbl_ingresos = ft.Text(
            "$0.00",
            size=25,
            weight=ft.FontWeight.BOLD,
            color="#6A0404",
        )
        self.lbl_cantidad_pedidos = ft.Text(
            "0",
            size=25,
            weight=ft.FontWeight.BOLD,
            color="#6A0404",
        )
        self.lbl_promedio_pedido = ft.Text(
            "$0.00",
            size=25,
            weight=ft.FontWeight.BOLD,
            color="#6A0404",
        )
        self.tarjetas_kpi = ft.ResponsiveRow(
            spacing=12,
            run_spacing=12,
            controls=[
                self.crear_tarjeta_kpi(
                    ft.Icons.ATTACH_MONEY,
                    "Ingresos totales",
                    self.lbl_ingresos,
                    "$",
                ),
                self.crear_tarjeta_kpi(
                    ft.Icons.RECEIPT_LONG,
                    "Pedidos",
                    self.lbl_cantidad_pedidos,
                    "#C56A22",
                ),
                self.crear_tarjeta_kpi(
                    ft.Icons.TRENDING_UP,
                    "Promedio por pedido",
                    self.lbl_promedio_pedido,
                    "#397A5B",
                ),
            ],
        )
        self.lista_vendedores = ft.Column(spacing=8)
        self.lista_servicios = ft.Column(spacing=6)
        self.lista_ventas_vendedor = ft.Column(spacing=6)
        self.lista_pedidos = ft.Column(spacing=8)
        self.pedidos_actuales = []
        self.txt_buscar_pedido = ft.TextField(
            label="Buscar pedido por código",
            hint_text="Ej. PE-000019",
            prefix_icon=ft.Icons.SEARCH,
            on_change=self.filtrar_pedidos,
        )
        self.txt_nombre = ft.TextField(
            label="Nombre completo",
            border_radius=12,
            filled=True,
            fill_color=ft.Colors.WHITE,
        )
        self.txt_correo = ft.TextField(
            label="Correo electrónico",
            keyboard_type=ft.KeyboardType.EMAIL,
            border_radius=12,
            filled=True,
            fill_color=ft.Colors.WHITE,
        )
        self.txt_telefono = ft.TextField(
            label="Teléfono",
            keyboard_type=ft.KeyboardType.PHONE,
            max_length=10,
            border_radius=12,
            filled=True,
            fill_color=ft.Colors.WHITE,
        )
        self.txt_contrasena = ft.TextField(
            label="Contraseña temporal (12+ caracteres)",
            password=True,
            can_reveal_password=True,
        )
        self.txt_contrasena.border_radius = 12
        self.txt_contrasena.filled = True
        self.txt_contrasena.fill_color = ft.Colors.WHITE
        self.encabezado = ft.Container(
            padding=ft.Padding(left=8, top=8, right=8, bottom=8),
            bgcolor=ft.Colors.TRANSPARENT,
            border_radius=14,
            content=ft.Row(
                [
                    ft.CircleAvatar(
                        content=ft.Icon(ft.Icons.ADMIN_PANEL_SETTINGS),
                        bgcolor="#6A0404",
                        color=ft.Colors.WHITE,
                        radius=24,
                    ),
                    ft.Column(
                        [
                            ft.Text(
                                personal.get("nombre", "Gerencia"),
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color="#3F302B",
                            ),
                            ft.Text(
                                "Gerente de tienda",
                                size=12,
                                color="#806B63",
                            ),
                        ],
                        expand=True,
                        spacing=2,
                    ),
                    ft.TextButton(
                        "Cerrar sesión",
                        style=ft.ButtonStyle(color="#6A0404"),
                        on_click=lambda e: self.on_cerrar_sesion(),
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
            ),
        )
        self.seccion_finanzas = ft.Container(
            padding=14,
            bgcolor="#FFF8F2",
            border_radius=14,
            content=ft.Column(
                spacing=14,
                controls=[
                    ft.Text(
                        "Corte y finanzas",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color="#6A0404",
                    ),
                    ft.Container(
                        padding=12,
                        bgcolor=ft.Colors.WHITE,
                        border_radius=12,
                        shadow=ft.BoxShadow(
                            blur_radius=10,
                            color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK),
                            offset=ft.Offset(0, 3),
                        ),
                        content=ft.Row(
                            [
                                ft.Icon(
                                    ft.Icons.CALENDAR_MONTH,
                                    color="#6A0404",
                                ),
                                self.txt_fecha,
                                ft.FilledButton(
                                    "Actualizar",
                                    icon=ft.Icons.REFRESH,
                                    bgcolor="#6A0404",
                                    color=ft.Colors.WHITE,
                                    on_click=self.cargar_datos,
                                ),
                            ],
                            wrap=True,
                            spacing=10,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ),
                    self.tarjetas_kpi,
                    self.crear_tarjeta_desglose(
                        "Ventas por tipo de servicio",
                        "Ingresos y pedidos según la modalidad.",
                        ft.Icons.STORE,
                        self.lista_servicios,
                    ),
                    self.crear_tarjeta_desglose(
                        "Ventas por vendedor",
                        "Comparativo de actividad del personal.",
                        ft.Icons.PERSON,
                        self.lista_ventas_vendedor,
                    ),
                ],
            ),
        )
        self.seccion_pedidos = ft.Container(
            padding=14,
            bgcolor="#FFF8F2",
            border_radius=14,
            content=ft.Column(
                spacing=10,
                controls=[
                    ft.Text(
                        "Pedidos del día",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color="#6A0404",
                    ),
                    ft.Text(
                        "App y mostrador, del más reciente al más antiguo.",
                        size=12,
                        color="#806B63",
                    ),
                    ft.Text(
                        "Actualización automática cada 30 segundos.",
                        size=12,
                        color="#806B63",
                    ),
                    self.txt_buscar_pedido,
                    self.lista_pedidos,
                ],
            ),
        )
        self.seccion_personal = ft.Container(
            padding=14,
            bgcolor="#FFF8F2",
            border_radius=14,
            content=ft.Column(
                spacing=14,
                controls=[
                    ft.Text(
                        "Personal de ventas",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color="#6A0404",
                    ),
                    self.lista_vendedores,
                    ft.Container(
                        padding=16,
                        bgcolor=ft.Colors.WHITE,
                        border_radius=16,
                        shadow=ft.BoxShadow(
                            blur_radius=12,
                            color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK),
                            offset=ft.Offset(0, 3),
                        ),
                        content=ft.Column(
                            spacing=12,
                            controls=[
                                ft.Row(
                                    [
                                        ft.CircleAvatar(
                                            content=ft.Icon(ft.Icons.PERSON_ADD_ALT_1),
                                            bgcolor="#FFF1E7",
                                            color="#6A0404",
                                            radius=20,
                                        ),
                                        ft.Column(
                                            [
                                                ft.Text(
                                                    "Dar de alta vendedor",
                                                    size=16,
                                                    weight=ft.FontWeight.BOLD,
                                                    color="#3F302B",
                                                ),
                                                ft.Text(
                                                    "Completa los datos de acceso y contacto.",
                                                    size=12,
                                                    color="#806B63",
                                                ),
                                            ],
                                            spacing=2,
                                            expand=True,
                                        ),
                                    ],
                                    spacing=10,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                                ft.ResponsiveRow(
                                    spacing=10,
                                    run_spacing=4,
                                    controls=[
                                        ft.Container(
                                            col={
                                                ft.ResponsiveRowBreakpoint.XS: 12,
                                                ft.ResponsiveRowBreakpoint.MD: 6,
                                            },
                                            content=self.txt_nombre,
                                        ),
                                        ft.Container(
                                            col={
                                                ft.ResponsiveRowBreakpoint.XS: 12,
                                                ft.ResponsiveRowBreakpoint.MD: 6,
                                            },
                                            content=self.txt_correo,
                                        ),
                                        ft.Container(
                                            col={
                                                ft.ResponsiveRowBreakpoint.XS: 12,
                                                ft.ResponsiveRowBreakpoint.MD: 6,
                                            },
                                            content=self.txt_telefono,
                                        ),
                                        ft.Container(
                                            col={
                                                ft.ResponsiveRowBreakpoint.XS: 12,
                                                ft.ResponsiveRowBreakpoint.MD: 6,
                                            },
                                            content=self.txt_contrasena,
                                        ),
                                    ],
                                ),
                                ft.Text(
                                    "Mínimo 12 caracteres; incluye mayúscula, minúscula, "
                                    "número y símbolo.",
                                    size=12,
                                    color="#806B63",
                                ),
                                ft.FilledButton(
                                    "Crear cuenta de vendedor",
                                    icon=ft.Icons.PERSON_ADD_ALT_1,
                                    bgcolor="#6A0404",
                                    color=ft.Colors.WHITE,
                                    height=46,
                                    on_click=self.crear_vendedor,
                                ),
                            ],
                        ),
                    ),
                ],
            ),
        )
        self.secciones = [
            self.seccion_finanzas,
            self.seccion_pedidos,
            self.seccion_personal,
        ]
        self.contenido_seccion = ft.Column(
            controls=[self.seccion_finanzas],
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )
        self.navegacion_secciones = ft.NavigationBar(
            selected_index=0,
            bgcolor="#6A0404",
            indicator_color=ft.Colors.WHITE,
            label_behavior=ft.NavigationBarLabelBehavior.ALWAYS_SHOW,
            on_change=self.cambiar_seccion,
            destinations=[
                ft.NavigationBarDestination(
                    icon=ft.Icons.ANALYTICS_OUTLINED,
                    selected_icon=ft.Icons.ANALYTICS,
                    label="Finanzas",
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.RECEIPT_LONG_OUTLINED,
                    selected_icon=ft.Icons.RECEIPT_LONG,
                    label="Pedidos",
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.PEOPLE_OUTLINE,
                    selected_icon=ft.Icons.PEOPLE,
                    label="Personal",
                ),
            ],
        )
        self.controls = [
            self.encabezado,
            self.contenido_seccion,
            self.lbl_error,
            self.navegacion_secciones,
        ]
        self.cargar_datos(None)

    def crear_tarjeta_kpi(self, icono, titulo, valor, color_icono):
        return ft.Container(
            col={
                ft.ResponsiveRowBreakpoint.XS: 12,
                ft.ResponsiveRowBreakpoint.SM: 6,
                ft.ResponsiveRowBreakpoint.LG: 4,
            },
            padding=14,
            bgcolor=ft.Colors.WHITE,
            border_radius=14,
            shadow=ft.BoxShadow(
                blur_radius=12,
                color=ft.Colors.with_opacity(0.07, ft.Colors.BLACK),
                offset=ft.Offset(0, 4),
            ),
            content=ft.Row(
                [
                    ft.Container(
                        width=44,
                        height=44,
                        alignment=ft.Alignment.CENTER,
                        bgcolor=ft.Colors.with_opacity(0.12, color_icono),
                        border_radius=12,
                        content=ft.Icon(icono, color=color_icono, size=23),
                    ),
                    ft.Column(
                        [
                            ft.Text(titulo, size=12, color="#806B63"),
                            valor,
                        ],
                        spacing=2,
                        expand=True,
                    ),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def crear_tarjeta_desglose(self, titulo, subtitulo, icono, lista):
        return ft.Container(
            padding=14,
            bgcolor=ft.Colors.WHITE,
            border_radius=14,
            shadow=ft.BoxShadow(
                blur_radius=10,
                color=ft.Colors.with_opacity(0.05, ft.Colors.BLACK),
                offset=ft.Offset(0, 3),
            ),
            content=ft.Column(
                spacing=10,
                controls=[
                    ft.Row(
                        [
                            ft.Container(
                                width=38,
                                height=38,
                                alignment=ft.Alignment.CENTER,
                                bgcolor="#FFF1E7",
                                border_radius=11,
                                content=ft.Icon(icono, color="#6A0404", size=21),
                            ),
                            ft.Column(
                                [
                                    ft.Text(
                                        titulo,
                                        size=15,
                                        weight=ft.FontWeight.BOLD,
                                        color="#3F302B",
                                    ),
                                    ft.Text(
                                        subtitulo,
                                        size=12,
                                        color="#806B63",
                                    ),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                        ],
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Divider(height=1, color="#F1E5DE"),
                    lista,
                ],
            ),
        )

    def crear_fila_financiera(
        self,
        icono,
        titulo,
        detalle,
        ingresos,
        color_icono="#6A0404",
    ):
        return ft.Container(
            padding=ft.Padding(left=2, top=5, right=2, bottom=5),
            content=ft.Row(
                [
                    ft.Icon(icono, color=color_icono, size=19),
                    ft.Column(
                        [
                            ft.Text(titulo, size=13, weight=ft.FontWeight.W_500),
                            ft.Text(detalle, size=11, color="#806B63"),
                        ],
                        spacing=1,
                        expand=True,
                    ),
                    ft.Text(
                        f"${ingresos:.2f}",
                        size=13,
                        weight=ft.FontWeight.BOLD,
                        color="#3F302B",
                    ),
                ],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def did_mount(self):
        self._actualizacion_activa = True
        self._generacion_actualizacion += 1
        self.page.run_task(
            self.actualizar_automaticamente,
            self._generacion_actualizacion,
        )

    def will_unmount(self):
        self._actualizacion_activa = False
        self._generacion_actualizacion += 1

    def cambiar_seccion(self, e):
        indice = e.control.selected_index
        if not 0 <= indice < len(self.secciones):
            return
        self.contenido_seccion.controls = [self.secciones[indice]]
        try:
            if self.contenido_seccion.page is not None:
                self.contenido_seccion.update()
        except RuntimeError:
            return

    def cargar_datos(self, e):
        self.lbl_error.value = ""
        try:
            fecha = self.obtener_fecha_reporte_iso()
        except ValueError:
            self.mostrar_error("Usa una fecha válida con formato DD/MM/AAAA.")
            return False

        try:
            respuestas = self.consultar_datos(fecha)
        except requests.RequestException:
            self.mostrar_error("No se pudo conectar con el servidor.")
            return False

        return self.mostrar_respuestas(respuestas)

    def obtener_fecha_reporte_iso(self):
        fecha_visible = (self.txt_fecha.value or "").strip()
        return datetime.strptime(fecha_visible, "%d/%m/%Y").date().isoformat()

    def consultar_datos(self, fecha):
        reporte = requests.get(
            f"{BASE_URL}/api/gerencia/reporte",
            params={"fecha": fecha},
            headers=self.token_headers,
            timeout=15,
        )
        vendedores = requests.get(
            f"{BASE_URL}/api/gerencia/vendedores",
            headers=self.token_headers,
            timeout=15,
        )
        pedidos = requests.get(
            f"{BASE_URL}/api/gerencia/pedidos",
            params={"fecha": fecha},
            headers=self.token_headers,
            timeout=15,
        )
        return reporte, vendedores, pedidos

    def mostrar_respuestas(self, respuestas):
        for respuesta in respuestas:
            if respuesta.status_code != 200:
                try:
                    detalle = respuesta.json().get("detail")
                except ValueError:
                    detalle = None
                self.mostrar_error(
                    detalle
                    if isinstance(detalle, str)
                    else "No se pudieron cargar los datos de gerencia."
                )
                return False

        reporte, vendedores, pedidos = respuestas
        self.mostrar_reporte(reporte.json())
        self.mostrar_vendedores(vendedores.json().get("vendedores", []))
        self.mostrar_pedidos(pedidos.json().get("pedidos", []))
        self.actualizar_estado()
        return True

    async def actualizar_automaticamente(self, generacion):
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
                fecha = self.obtener_fecha_reporte_iso()
            except ValueError:
                continue
            try:
                respuestas = await asyncio.to_thread(self.consultar_datos, fecha)
            except requests.RequestException:
                self.lbl_error.value = "No se pudo actualizar la información."
                self.actualizar_estado()
                continue
            if (
                self._actualizacion_activa
                and generacion == self._generacion_actualizacion
            ):
                self.mostrar_respuestas(respuestas)

    def mostrar_reporte(self, reporte):
        self.lbl_ingresos.value = f"${reporte.get('ingresos', 0):.2f}"
        cantidad = reporte.get("cantidad_pedidos", 0)
        self.lbl_cantidad_pedidos.value = str(cantidad)
        promedio = reporte.get("ingresos", 0) / cantidad if cantidad else 0
        self.lbl_promedio_pedido.value = f"${promedio:.2f}"
        self.lista_servicios.controls = [
            self.crear_fila_financiera(
                ft.Icons.RESTAURANT
                if "comer" in fila["tipo_servicio"].lower()
                else ft.Icons.STORE,
                fila["tipo_servicio"],
                f"{fila['cantidad']} pedidos",
                fila["ingresos"],
                "#C56A22" if "comer" in fila["tipo_servicio"].lower() else "#397A5B",
            )
            for fila in reporte.get("por_servicio", [])
        ] or [ft.Text("Sin ventas registradas.", color="#806B63")]
        self.lista_ventas_vendedor.controls = [
            self.crear_fila_financiera(
                ft.Icons.PERSON,
                fila["vendedor"],
                f"{fila['cantidad']} pedidos",
                fila["ingresos"],
                "#6A0404",
            )
            for fila in reporte.get("por_vendedor", [])
        ] or [ft.Text("Sin ventas registradas.", color="#806B63")]

    def mostrar_vendedores(self, vendedores):
        self.lista_vendedores.controls = [
            self.crear_tarjeta_vendedor(vendedor)
            for vendedor in vendedores
        ] or [ft.Text("Todavía no hay vendedores.", color="#806B63")]

    def crear_tarjeta_vendedor(self, vendedor):
        nombre = vendedor.get("nombre", "").strip()
        iniciales = "".join(
            palabra[0].upper() for palabra in nombre.split()[:2]
        ) or "V"
        activo = bool(vendedor["activo"])
        color_estado = "#28734D" if activo else "#8A3B2E"
        fondo_estado = "#E8F4EC" if activo else "#F8EAE7"
        return ft.Container(
            padding=14,
            bgcolor=ft.Colors.WHITE,
            border_radius=14,
            border=ft.Border(
                top=ft.BorderSide(1, "#F0E5DF"),
                bottom=ft.BorderSide(1, "#F0E5DF"),
                left=ft.BorderSide(1, "#F0E5DF"),
                right=ft.BorderSide(1, "#F0E5DF"),
            ),
            shadow=ft.BoxShadow(
                blur_radius=8,
                color=ft.Colors.with_opacity(0.04, ft.Colors.BLACK),
                offset=ft.Offset(0, 2),
            ),
            content=ft.ResponsiveRow(
                spacing=12,
                run_spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        col={
                            ft.ResponsiveRowBreakpoint.XS: 12,
                            ft.ResponsiveRowBreakpoint.MD: 8,
                        },
                        content=ft.Row(
                            [
                                ft.CircleAvatar(
                                    content=ft.Text(
                                        iniciales,
                                        size=15,
                                        weight=ft.FontWeight.BOLD,
                                        color="#6A0404",
                                    ),
                                    bgcolor="#FFF1E7",
                                    radius=23,
                                ),
                                ft.Column(
                                    [
                                        ft.Text(
                                            nombre or "Vendedor",
                                            size=14,
                                            weight=ft.FontWeight.BOLD,
                                            color="#3F302B",
                                        ),
                                        ft.Row(
                                            [
                                                ft.Icon(
                                                    ft.Icons.EMAIL_OUTLINED,
                                                    size=14,
                                                    color="#806B63",
                                                ),
                                                ft.Text(
                                                    vendedor.get("correo", ""),
                                                    size=12,
                                                    color="#54423B",
                                                    selectable=True,
                                                ),
                                            ],
                                            spacing=5,
                                        ),
                                        ft.Row(
                                            [
                                                ft.Icon(
                                                    ft.Icons.PHONE_OUTLINED,
                                                    size=14,
                                                    color="#806B63",
                                                ),
                                                ft.Text(
                                                    vendedor.get("telefono", ""),
                                                    size=12,
                                                    color="#54423B",
                                                ),
                                            ],
                                            spacing=5,
                                        ),
                                    ],
                                    spacing=3,
                                    expand=True,
                                ),
                                ft.Container(
                                    padding=ft.Padding(
                                        left=9,
                                        top=5,
                                        right=9,
                                        bottom=5,
                                    ),
                                    bgcolor=fondo_estado,
                                    border_radius=20,
                                    content=ft.Row(
                                        [
                                            ft.Icon(
                                                ft.Icons.CHECK_CIRCLE
                                                if activo
                                                else ft.Icons.BLOCK,
                                                size=14,
                                                color=color_estado,
                                            ),
                                            ft.Text(
                                                "Activo" if activo else "Inactivo",
                                                size=11,
                                                weight=ft.FontWeight.BOLD,
                                                color=color_estado,
                                            ),
                                        ],
                                        spacing=4,
                                        tight=True,
                                    ),
                                ),
                            ],
                            spacing=12,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ),
                    ft.Container(
                        col={
                            ft.ResponsiveRowBreakpoint.XS: 12,
                            ft.ResponsiveRowBreakpoint.MD: 4,
                        },
                        alignment=ft.Alignment.CENTER_RIGHT,
                        content=ft.OutlinedButton(
                            "Desactivar" if activo else "Activar",
                            icon=ft.Icons.TOGGLE_OFF if activo else ft.Icons.TOGGLE_ON,
                            style=ft.ButtonStyle(
                                color="#8A3B2E" if activo else "#28734D",
                                shape=ft.RoundedRectangleBorder(radius=10),
                            ),
                            on_click=lambda e, item=vendedor: self.cambiar_estado_vendedor(
                                item
                            ),
                        ),
                    ),
                ],
            ),
        )

    def mostrar_pedidos(self, pedidos):
        self.pedidos_actuales = list(pedidos)
        self.filtrar_pedidos(None)

    def filtrar_pedidos(self, e):
        busqueda = (self.txt_buscar_pedido.value or "").strip().upper()
        codigo_busqueda = busqueda.replace("PE", "").replace("-", "").strip()
        pedidos_filtrados = [
            pedido
            for pedido in self.pedidos_actuales
            if codigo_busqueda in f"{pedido['id_pedido']:06d}"
        ] if codigo_busqueda else self.pedidos_actuales

        self.lista_pedidos.controls = [
            self.crear_tarjeta_pedido(pedido)
            for pedido in pedidos_filtrados
        ] or [
            ft.Text(
                "No hay pedidos que coincidan con ese código."
                if codigo_busqueda
                else "No hay pedidos para esta fecha.",
                color="#806B63",
            )
        ]
        self.actualizar_lista_pedidos()

    def crear_tarjeta_pedido(self, pedido):
        return ft.Container(
            padding=12,
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            border=ft.Border(
                top=ft.BorderSide(1, "#F0D8CA"),
                bottom=ft.BorderSide(1, "#F0D8CA"),
                left=ft.BorderSide(1, "#F0D8CA"),
                right=ft.BorderSide(1, "#F0D8CA"),
            ),
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
                        f"{pedido['fecha']} · {pedido['estado']}",
                        size=12,
                    ),
                    ft.Text(
                        f"{pedido['nombre_contacto']} · {pedido['tipo_servicio']}",
                        size=13,
                    ),
                    ft.Text(
                        f"Registró: {pedido['vendedor']}",
                        size=12,
                        color="#806B63",
                    ),
                    ft.Text(
                        f"Pago: {pedido.get('metodo_pago') or 'No especificado'}",
                        size=12,
                        color="#806B63",
                    ),
                    ft.Text(
                        " · ".join(
                            f"{item['cantidad']}× {item['nombre_pizza']}"
                            for item in pedido.get("detalles", [])
                        ),
                        size=12,
                    ),
                    ft.Text(
                        f"Teléfono: {pedido['telefono_contacto']}"
                        if pedido.get("telefono_contacto")
                        else "",
                        size=12,
                        visible=bool(pedido.get("telefono_contacto")),
                    ),
                    ft.OutlinedButton(
                        "Cancelar pedido",
                        on_click=lambda e, pedido_id=pedido["id_pedido"]: self.cancelar_pedido(
                            pedido_id
                        ),
                        visible=pedido["estado"] != "Cancelada",
                    ),
                ],
            ),
        )

    def actualizar_lista_pedidos(self):
        try:
            if self.lista_pedidos.page is not None:
                self.lista_pedidos.update()
        except RuntimeError:
            return

    def crear_vendedor(self, e):
        nombre = (self.txt_nombre.value or "").strip()
        correo = (self.txt_correo.value or "").strip().lower()
        telefono = (self.txt_telefono.value or "").strip()
        contrasena = self.txt_contrasena.value or ""
        if not nombre or not correo or not telefono or not contrasena:
            self.mostrar_error("Completa todos los datos del vendedor.")
            return
        if len(telefono) != 10 or not telefono.isdigit():
            self.mostrar_error("El teléfono debe contener exactamente 10 dígitos.")
            return
        if (
            len(contrasena) < 12
            or not any(caracter.isupper() for caracter in contrasena)
            or not any(caracter.islower() for caracter in contrasena)
            or not any(caracter.isdigit() for caracter in contrasena)
            or not any(not caracter.isalnum() for caracter in contrasena)
        ):
            self.mostrar_error(
                "La contraseña debe tener al menos 12 caracteres e incluir "
                "mayúscula, minúscula, número y símbolo."
            )
            return
        try:
            respuesta = requests.post(
                f"{BASE_URL}/api/gerencia/vendedores",
                json={
                    "nombre": nombre,
                    "correo": correo,
                    "telefono": telefono,
                    "contrasena": contrasena,
                },
                headers=self.token_headers,
                timeout=15,
            )
        except requests.RequestException:
            self.mostrar_error("No se pudo conectar con el servidor.")
            return
        if respuesta.status_code != 201:
            self.mostrar_respuesta_error(respuesta)
            return
        self.txt_nombre.value = ""
        self.txt_correo.value = ""
        self.txt_telefono.value = ""
        self.txt_contrasena.value = ""
        actualizados = self.cargar_datos(None)
        self.lbl_error.value = (
            "Cuenta de vendedor creada."
            if actualizados
            else "Cuenta creada, pero no se pudieron actualizar los datos."
        )
        self.actualizar_estado()

    def cambiar_estado_vendedor(self, vendedor):
        try:
            respuesta = requests.patch(
                f"{BASE_URL}/api/gerencia/vendedores/"
                f"{vendedor['id_personal']}/estado",
                json={"activo": not bool(vendedor["activo"])},
                headers=self.token_headers,
                timeout=15,
            )
        except requests.RequestException:
            self.mostrar_error("No se pudo conectar con el servidor.")
            return
        if respuesta.status_code != 200:
            self.mostrar_respuesta_error(respuesta)
            return
        actualizados = self.cargar_datos(None)
        self.lbl_error.value = (
            "Estado del vendedor actualizado."
            if actualizados
            else "Estado actualizado, pero no se pudieron refrescar los datos."
        )
        self.actualizar_estado()

    def cancelar_pedido(self, id_pedido):
        try:
            respuesta = requests.patch(
                f"{BASE_URL}/api/gerencia/pedidos/{id_pedido}/cancelar",
                headers=self.token_headers,
                timeout=15,
            )
        except requests.RequestException:
            self.mostrar_error("No se pudo conectar con el servidor.")
            return
        if respuesta.status_code != 200:
            self.mostrar_respuesta_error(respuesta)
            return
        actualizados = self.cargar_datos(None)
        self.lbl_error.value = (
            "Pedido cancelado."
            if actualizados
            else "Pedido cancelado, pero no se pudieron refrescar los datos."
        )
        self.actualizar_estado()

    def mostrar_respuesta_error(self, respuesta):
        try:
            contenido = respuesta.json()
        except ValueError:
            contenido = {}
        detalle = contenido.get("detail")
        if isinstance(detalle, str):
            mensaje = detalle
        elif isinstance(detalle, list):
            errores_contrasena = [
                error
                for error in detalle
                if isinstance(error, dict)
                and "contrasena" in error.get("loc", [])
            ]
            if errores_contrasena:
                mensaje = (
                    "La contraseña debe tener al menos 12 caracteres e incluir "
                    "mayúscula, minúscula, número y símbolo."
                )
            else:
                mensajes = [
                    error["msg"]
                    for error in detalle
                    if isinstance(error, dict) and isinstance(error.get("msg"), str)
                ]
                mensaje = (
                    "; ".join(mensajes)
                    if mensajes
                    else "No se pudo completar la operación."
                )
        else:
            mensaje = "No se pudo completar la operación."
        self.mostrar_error(mensaje)

    def mostrar_error(self, mensaje):
        self.lbl_error.value = mensaje
        self.actualizar_estado()

    def actualizar_estado(self):
        try:
            if self.page is not None:
                self.update()
        except RuntimeError:
            return
