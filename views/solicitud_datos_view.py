from datetime import datetime, timedelta

import flet as ft
from components.validaciones import correo_valido, nombre_valido, telefono_valido

class SolicitudDatosView(ft.Column):
    def __init__(self, items_estado, on_regresar, on_continuar_pago, es_movil=False):
        super().__init__()
        self.expand = False
        self.spacing = 0
        self.items_estado = items_estado
        self.on_regresar = on_regresar
        self.on_continuar_pago = on_continuar_pago

        tamano_campo = 16 if es_movil else 14
        alto_campo = 48 if es_movil else 44
        padding_campo = 12 if es_movil else 10
        padding_panel = 18 if es_movil else 14
        tamano_resumen = 15 if es_movil else 14
        tamano_total = 16 if es_movil else 15
        tamano_opcion = 14 if es_movil else 13

        self.datos_pedido = {
            "tipo_servicio": "A Domicilio",
            "direccion": "",
            "referencias": "",
            "hora_recoleccion": None,
            "subtotal": 0.0,
            "envio": 35.00,
            "total": 0.0,
        }

        self.txt_dir = ft.TextField(
            label="Dirección",
            text_size=tamano_campo,
            height=alto_campo,
            content_padding=padding_campo,
            expand=True,
        )
        self.txt_ref = ft.TextField(
            label="Indique alguna(s) referencia(s)",
            text_size=tamano_campo,
            height=alto_campo,
            content_padding=padding_campo,
            expand=True,
        )
        self.txt_nombre_contacto = ft.TextField(
            label="Nombre completo",
            text_size=tamano_campo,
            height=alto_campo,
            content_padding=padding_campo,
        )
        self.txt_telefono_contacto = ft.TextField(
            label="Teléfono",
            text_size=tamano_campo,
            height=alto_campo,
            content_padding=padding_campo,
            expand=True,
        )
        self.txt_correo_contacto = ft.TextField(
            label="Correo",
            text_size=tamano_campo,
            height=alto_campo,
            content_padding=padding_campo,
            expand=True,
        )
        self.lbl_error = ft.Text("", color=ft.Colors.RED_700, size=14, weight="bold")

        self.campos_direccion = ft.Column(
            controls=[self.txt_dir, self.txt_ref],
            spacing=10,
            visible=True
        )
        self.horarios_recoleccion = self.generar_horarios_recoleccion()
        self.selector_hora_recoleccion = ft.Dropdown(
            hint_text="Selecciona la hora de recolección",
            value=None,
            options=self.crear_opciones_horarios(),
            text_size=16,
            height=58,
            leading_icon=ft.Icons.ACCESS_TIME,
            selected_trailing_icon=ft.Icons.CHECK_CIRCLE,
            menu_height=280,
            menu_style=ft.MenuStyle(
                bgcolor="#FFFCFA",
                elevation=10,
                padding=8,
                side=ft.BorderSide(1, "#F0D8CA"),
                shape=ft.RoundedRectangleBorder(radius=14),
            ),
            content_padding=ft.Padding(left=16, top=12, right=16, bottom=12),
            border_color="#E7C8B8",
            focused_border_color="#6A0404",
            border_radius=14,
            filled=True,
            fill_color=ft.Colors.WHITE,
            hover_color="#FFF3EA",
            hint_style=ft.TextStyle(color="#806B63", size=16),
            on_select=self.cambiar_hora_recoleccion,
        )
        self.aviso_sin_horarios = ft.Text(
            "Ya no hay horarios de recogida disponibles hoy. "
            "Elige A Domicilio para continuar.",
            size=14,
            color="#8A3B2E",
            weight=ft.FontWeight.W_500,
            visible=not self.horarios_recoleccion,
        )
        self.campos_hora_recoleccion = ft.Column(
            controls=[
                ft.Container(
                    padding=16,
                    bgcolor="#FFF7F0",
                    border_radius=18,
                    border=ft.Border(
                        top=ft.BorderSide(1, "#F0D8CA"),
                        bottom=ft.BorderSide(1, "#F0D8CA"),
                        left=ft.BorderSide(4, "#6A0404"),
                        right=ft.BorderSide(1, "#F0D8CA"),
                    ),
                    content=ft.Column(
                        spacing=14,
                        controls=[
                            ft.Row(
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Container(
                                        width=44,
                                        height=44,
                                        alignment=ft.Alignment.CENTER,
                                        bgcolor="#F4E2D8",
                                        border_radius=14,
                                        content=ft.Icon(
                                            ft.Icons.STORE_MALL_DIRECTORY,
                                            color="#6A0404",
                                            size=24,
                                        ),
                                    ),
                                    ft.Column(
                                        expand=True,
                                        spacing=2,
                                        controls=[
                                            ft.Text(
                                                "Recoge en tienda",
                                                size=17,
                                                weight=ft.FontWeight.BOLD,
                                                color="#3D2520",
                                            ),
                                            ft.Text(
                                                "Tu pedido, listo para recoger · Cierre 10:00 p. m.",
                                                size=13,
                                                color="#806B63",
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                            ft.Row(
                                spacing=8,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Icon(
                                        ft.Icons.SCHEDULE,
                                        color="#6A0404",
                                        size=19,
                                    ),
                                    ft.Text(
                                        "Preparación: 30 minutos",
                                        size=14,
                                        weight=ft.FontWeight.W_500,
                                        color="#54423B",
                                    ),
                                ],
                            ),
                            ft.Text(
                                "Selecciona la hora de recolección",
                                size=13,
                                weight=ft.FontWeight.W_500,
                                color="#54423B",
                            ),
                            self.selector_hora_recoleccion,
                            self.aviso_sin_horarios,
                        ],
                    ),
                ),
            ],
            spacing=0,
            visible=False,
        )

        self.btn_domicilio = ft.Container(
            expand=True,
            padding=12 if es_movil else 10,
            height=78 if es_movil else 72,
            bgcolor="#FFF4EC",
            border_radius=14,
            border=ft.Border(
                top=ft.BorderSide(2, "#6A0404"),
                bottom=ft.BorderSide(2, "#6A0404"),
                left=ft.BorderSide(2, "#6A0404"),
                right=ft.BorderSide(2, "#6A0404"),
            ),
            content=ft.Column([
                ft.Row(
                    [
                        ft.Icon(
                            ft.Icons.LOCAL_SHIPPING,
                            color="#6A0404",
                            size=20 if es_movil else 18,
                        ),
                        ft.Text(
                            "A Domicilio",
                            weight="bold",
                            size=tamano_opcion,
                            color="#6A0404",
                        ),
                        ft.Icon(ft.Icons.CHECK_CIRCLE, color="#6A0404", size=18),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Text(
                    "35-45 min",
                    size=12 if es_movil else 11,
                    color="#806B63",
                    text_align=ft.TextAlign.CENTER,
                ),
            ], spacing=4),
            on_click=lambda e: self.seleccionar_metodo(True)
        )

        self.btn_tienda = ft.Container(
            expand=True,
            padding=12 if es_movil else 10,
            height=78 if es_movil else 72,
            bgcolor="#FAF8F6",
            border_radius=14,
            border=ft.Border(
                top=ft.BorderSide(1, "#E9DED7"),
                bottom=ft.BorderSide(1, "#E9DED7"),
                left=ft.BorderSide(1, "#E9DED7"),
                right=ft.BorderSide(1, "#E9DED7"),
            ),
            content=ft.Column([
                ft.Row(
                    [
                        ft.Icon(
                            ft.Icons.STORE,
                            color="#806B63",
                            size=20 if es_movil else 18,
                        ),
                        ft.Text(
                            "En Tienda",
                            weight="bold",
                            size=tamano_opcion,
                            color="#806B63",
                        ),
                        ft.Icon(
                            ft.Icons.CHECK_CIRCLE,
                            color="#6A0404",
                            size=18,
                            visible=False,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Text(
                    "Listo en 30 min",
                    size=12 if es_movil else 11,
                    color="#806B63",
                    text_align=ft.TextAlign.CENTER,
                ),
            ], spacing=4),
            on_click=lambda e: self.seleccionar_metodo(False)
        )

        filas_resumen = []
        subtotal = 0.0

        for item in self.items_estado:
            if item["cantidad"] > 0:
                total_item = item["cantidad"] * item["precio"]
                subtotal += total_item
                filas_resumen.append(
                    ft.Row([
                        ft.Text(
                            f"{item['cantidad']}x {item['nombre']}",
                            size=tamano_resumen,
                        ),
                        ft.Text(
                            f"${total_item:.2f}",
                            size=tamano_resumen,
                        ),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                )

        costo_envio = 35.00
        total_pagar = subtotal + costo_envio

        self.datos_pedido["subtotal"] = subtotal
        self.datos_pedido["envio"] = costo_envio
        self.datos_pedido["total"] = total_pagar
        self.lbl_total = ft.Text(
            f"${total_pagar:.2f}",
            size=tamano_total,
            weight="bold",
            color="#6A0404",
        )
        self.fila_costo_envio = ft.Row(
            [
                ft.Text(
                    "Costo de Envío",
                    size=tamano_resumen,
                ),
                ft.Text(
                    f"${costo_envio:.2f}",
                    size=tamano_resumen,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        resumen_widget = ft.Container(
            padding=padding_panel,
            bgcolor="#FFF8F2",
            border_radius=16,
            border=ft.Border(
                top=ft.BorderSide(1, "#F0D8CA"),
                bottom=ft.BorderSide(1, "#F0D8CA"),
                left=ft.BorderSide(1, "#F0D8CA"),
                right=ft.BorderSide(1, "#F0D8CA"),
            ),
            shadow=ft.BoxShadow(
                blur_radius=12,
                color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
                offset=ft.Offset(0, 4),
            ),
            content=ft.Column([
                ft.Text(
                    "Resumen del Pedido",
                    size=tamano_total,
                    weight="bold",
                    color="#6A0404",
                ),
                ft.Divider(height=5),
                *filas_resumen,
                ft.Divider(height=5),
                ft.Row(
                    [
                        ft.Text(
                            "Subtotal",
                            size=tamano_resumen,
                        ),
                        ft.Text(
                            f"${subtotal:.2f}",
                            size=tamano_resumen,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                self.fila_costo_envio,
                ft.Divider(height=5),
                ft.Row(
                    [
                        ft.Text(
                            "Total a Pagar",
                            size=tamano_total,
                            weight="bold",
                        ),
                        self.lbl_total,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            ], spacing=5)
        )

        self.controls = [
            ft.Container(
                content=ft.Row([
                    ft.TextButton(
                        content=ft.Row([ft.Icon(ft.Icons.ARROW_BACK, size=16, color="#6A0404"), ft.Text("", color="#6A0404", weight="bold")], spacing=2),
                        on_click=lambda e: self.on_regresar(),
                        style=ft.ButtonStyle(padding=5)
                    ),
                    ft.Text(
                        "DETALLES DEL PEDIDO",
                        size=14,
                        weight="bold",
                        color="#6A0404",
                    ),
                    ft.Container(width=50)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=5,
                bgcolor="#FEEFE5D8"
            ),
            ft.Container(
                expand=True,
                content=ft.Column(
                    scroll=ft.ScrollMode.AUTO,
                    spacing=15,
                    controls=[
                        ft.ResponsiveRow(
                            spacing=20,
                            run_spacing=16,
                            controls=[
                                ft.Container(
                                    col={
                                        ft.ResponsiveRowBreakpoint.XS: 12,
                                        ft.ResponsiveRowBreakpoint.LG: 5,
                                    },
                                    content=resumen_widget,
                                ),
                                ft.Container(
                                    col={
                                        ft.ResponsiveRowBreakpoint.XS: 12,
                                        ft.ResponsiveRowBreakpoint.LG: 7,
                                    },
                                    padding=padding_panel,
                                    bgcolor=ft.Colors.WHITE,
                                    border_radius=16,
                                    content=ft.Column(
                                        spacing=16 if es_movil else 14,
                                        controls=[
                                            ft.Column(
                                                spacing=8,
                                                controls=[
                                                    ft.Text(
                                                        "Tipos de servicio",
                                                        size=18 if es_movil else 16,
                                                        weight=ft.FontWeight.BOLD,
                                                        color=ft.Colors.BLACK_87,
                                                    ),
                                                    ft.Row(
                                                        [
                                                            self.btn_domicilio,
                                                            self.btn_tienda,
                                                        ],
                                                        spacing=10,
                                                    ),
                                                ],
                                            ),
                                            ft.Column(
                                                spacing=10,
                                                controls=[
                                                    ft.Text(
                                                        "Datos de contacto",
                                                        size=18 if es_movil else 16,
                                                        weight=ft.FontWeight.BOLD,
                                                        color="#6A0404",
                                                    ),
                                                    self.txt_nombre_contacto,
                                                    ft.ResponsiveRow(
                                                        spacing=8,
                                                        controls=[
                                                            ft.Container(
                                                                content=self.txt_telefono_contacto,
                                                                col={
                                                                    ft.ResponsiveRowBreakpoint.XS: 12,
                                                                    ft.ResponsiveRowBreakpoint.MD: 6,
                                                                },
                                                            ),
                                                            ft.Container(
                                                                content=self.txt_correo_contacto,
                                                                col={
                                                                    ft.ResponsiveRowBreakpoint.XS: 12,
                                                                    ft.ResponsiveRowBreakpoint.MD: 6,
                                                                },
                                                            ),
                                                        ],
                                                    ),
                                                ],
                                            ),
                                            self.campos_direccion,
                                            self.campos_hora_recoleccion,
                                            ft.Divider(color=ft.Colors.GREY_400),
                                            self.lbl_error,
                                            ft.Row(
                                                [
                                                    ft.OutlinedButton(
                                                        content=ft.Text(
                                                            "Cancelar",
                                                            size=16 if es_movil else 14,
                                                            color=ft.Colors.RED_900,
                                                            weight="bold",
                                                        ),
                                                        width=150 if es_movil else 140,
                                                        height=48 if es_movil else 44,
                                                        style=ft.ButtonStyle(
                                                            side=ft.BorderSide(
                                                                1,
                                                                ft.Colors.RED_900,
                                                            )
                                                        ),
                                                        on_click=lambda e: self.on_regresar(),
                                                    ),
                                                    ft.FilledButton(
                                                        content=ft.Text(
                                                            "Continuar",
                                                            size=16 if es_movil else 14,
                                                            color=ft.Colors.WHITE,
                                                            weight="bold",
                                                        ),
                                                        bgcolor="#6A0404",
                                                        width=150 if es_movil else 140,
                                                        height=48 if es_movil else 44,
                                                        on_click=self.continuar,
                                                    ),
                                                ],
                                                alignment=ft.MainAxisAlignment.END,
                                                spacing=10,
                                                wrap=True,
                                            ),
                                        ],
                                    ),
                                ),
                            ],
                        ),
                        ft.Container(height=20),
                    ]
                ),
                padding=10
            )
        ]
        if es_movil:
            self.controls[1] = ft.Container(
                expand=True,
                content=ft.Column(
                    scroll=ft.ScrollMode.AUTO,
                    spacing=15,
                    controls=[
                        resumen_widget,
                        ft.Column(
                            [
                                ft.Text(
                                    "Tipos de servicio",
                                    size=16,
                                    weight="bold",
                                    color=ft.Colors.BLACK_87,
                                ),
                                ft.Column(
                                    [self.btn_domicilio, self.btn_tienda],
                                    spacing=8,
                                ),
                            ],
                            spacing=5,
                        ),
                        ft.Column(
                            [
                                ft.Text(
                                    "Datos de Contacto",
                                    size=16,
                                    weight="bold",
                                    color="#6A0404",
                                ),
                                self.txt_nombre_contacto,
                                ft.Row(
                                    [
                                        self.txt_telefono_contacto,
                                        self.txt_correo_contacto,
                                    ],
                                    spacing=8,
                                ),
                            ],
                            spacing=10,
                        ),
                        self.campos_direccion,
                        self.campos_hora_recoleccion,
                        ft.Divider(color=ft.Colors.GREY_400),
                        self.lbl_error,
                        ft.Row(
                            [
                                ft.OutlinedButton(
                                    content=ft.Text(
                                        "Cancelar",
                                        size=16,
                                        color=ft.Colors.RED_900,
                                        weight="bold",
                                    ),
                                    width=150,
                                    height=45,
                                    style=ft.ButtonStyle(
                                        side=ft.BorderSide(
                                            1,
                                            ft.Colors.RED_900,
                                        )
                                    ),
                                    on_click=lambda e: self.on_regresar(),
                                ),
                                ft.FilledButton(
                                    content=ft.Text(
                                        "Continuar",
                                        size=16,
                                        color=ft.Colors.WHITE,
                                        weight="bold",
                                    ),
                                    bgcolor="#6A0404",
                                    width=150,
                                    height=45,
                                    on_click=self.continuar,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=10,
                        ),
                        ft.Container(height=20),
                    ],
                ),
                padding=10,
            )

    def seleccionar_metodo(self, es_domicilio):
        tipo_servicio_anterior = self.datos_pedido["tipo_servicio"]
        if es_domicilio:
            self.datos_pedido["tipo_servicio"] = "A Domicilio"
            self.campos_direccion.visible = True
            self.campos_hora_recoleccion.visible = False
            self.datos_pedido["hora_recoleccion"] = None
        else:
            self.datos_pedido["tipo_servicio"] = "En Tienda"
            self.campos_direccion.visible = False
            if tipo_servicio_anterior != "En Tienda":
                self.actualizar_horarios_recoleccion()
            self.campos_hora_recoleccion.visible = True

        self.estilizar_boton_servicio(self.btn_domicilio, es_domicilio)
        self.estilizar_boton_servicio(self.btn_tienda, not es_domicilio)
        costo_envio = 35.00 if es_domicilio else 0.0
        self.datos_pedido["envio"] = costo_envio
        self.datos_pedido["total"] = self.datos_pedido["subtotal"] + costo_envio
        self.fila_costo_envio.visible = es_domicilio
        self.lbl_total.value = f"${self.datos_pedido['total']:.2f}"

        self.campos_direccion.update()
        self.campos_hora_recoleccion.update()
        self.btn_domicilio.update()
        self.btn_tienda.update()
        self.fila_costo_envio.update()
        self.lbl_total.update()

    @staticmethod
    def estilizar_boton_servicio(boton, seleccionado):
        color = "#6A0404" if seleccionado else "#806B63"
        color_borde = "#6A0404" if seleccionado else "#E9DED7"
        grosor_borde = 2 if seleccionado else 1
        boton.bgcolor = "#FFF4EC" if seleccionado else "#FAF8F6"
        boton.border = ft.Border(
            top=ft.BorderSide(grosor_borde, color_borde),
            bottom=ft.BorderSide(grosor_borde, color_borde),
            left=ft.BorderSide(grosor_borde, color_borde),
            right=ft.BorderSide(grosor_borde, color_borde),
        )
        boton.content.controls[0].controls[0].color = color
        boton.content.controls[0].controls[1].color = color
        boton.content.controls[0].controls[2].visible = seleccionado

    def generar_horarios_recoleccion(self):
        ahora = datetime.now().astimezone()
        primer_horario = ahora.replace(second=0, microsecond=0) + timedelta(
            minutes=30
        )
        cierre = ahora.replace(hour=22, minute=0, second=0, microsecond=0)
        if primer_horario.date() != ahora.date():
            return []
        return [
            (
                horario.isoformat(timespec="minutes"),
                horario.strftime("%H:%M"),
            )
            for horario in (
                primer_horario + timedelta(minutes=30 * indice)
                for indice in range(24)
            )
            if horario.date() == ahora.date() and horario < cierre
        ]

    def actualizar_horarios_recoleccion(self):
        self.horarios_recoleccion = self.generar_horarios_recoleccion()
        self.selector_hora_recoleccion.options = self.crear_opciones_horarios()
        self.selector_hora_recoleccion.value = None
        self.selector_hora_recoleccion.visible = bool(self.horarios_recoleccion)
        self.aviso_sin_horarios.visible = not self.horarios_recoleccion
        self.datos_pedido["hora_recoleccion"] = None

    def crear_opciones_horarios(self):
        return [
            ft.DropdownOption(
                key=valor,
                text=etiqueta,
                leading_icon=ft.Icons.SCHEDULE,
                style=ft.ButtonStyle(
                    color={
                        ft.ControlState.DEFAULT: "#3D2520",
                        ft.ControlState.SELECTED: "#6A0404",
                    },
                    bgcolor={
                        ft.ControlState.DEFAULT: "#FFFCFA",
                        ft.ControlState.HOVERED: "#FFF3EA",
                        ft.ControlState.SELECTED: "#FCE5D8",
                    },
                    text_style=ft.TextStyle(
                        size=15,
                        weight=ft.FontWeight.W_500,
                    ),
                    padding=ft.Padding(left=14, top=8, right=14, bottom=8),
                    shape=ft.RoundedRectangleBorder(radius=8),
                ),
            )
            for valor, etiqueta in self.horarios_recoleccion
        ]

    def cambiar_hora_recoleccion(self, e):
        self.datos_pedido["hora_recoleccion"] = e.control.value

    def continuar(self, e):
        self.lbl_error.value = ""
        if not any(item.get("cantidad", 0) > 0 for item in self.items_estado):
            self.mostrar_alerta_validacion(
                "Tu carrito está vacío. Regresa al menú y agrega al menos un producto."
            )
            return

        nombre = (self.txt_nombre_contacto.value or "").strip()
        telefono = (self.txt_telefono_contacto.value or "").strip()
        correo = (self.txt_correo_contacto.value or "").strip()
        direccion = (self.txt_dir.value or "").strip()
        referencias = (self.txt_ref.value or "").strip()

        errores = []
        faltantes = [
            nombre_campo
            for nombre_campo, valor in (
                ("Nombre completo", nombre),
                ("Teléfono", telefono),
                ("Correo", correo),
            )
            if not valor
        ]
        if self.datos_pedido["tipo_servicio"] == "A Domicilio":
            if not direccion:
                faltantes.append("Dirección")
            if not referencias:
                faltantes.append("Referencias")
        elif not self.datos_pedido["hora_recoleccion"]:
            errores.append(
                "No quedan horarios de recogida antes del cierre de las 10:00 p. m. "
                "Elige A Domicilio para continuar."
            )
        else:
            ahora_minuto = datetime.now().astimezone().replace(
                second=0,
                microsecond=0,
            )
            hora_recoleccion = datetime.fromisoformat(
                self.datos_pedido["hora_recoleccion"]
            ).astimezone()
            if hora_recoleccion < ahora_minuto + timedelta(minutes=30):
                self.actualizar_horarios_recoleccion()
                self.campos_hora_recoleccion.update()
                errores.append(
                    "El horario seleccionado ya no está disponible. "
                    "Selecciona otro horario para continuar."
                )
        if faltantes:
            errores.append(f"Completa los siguientes campos: {', '.join(faltantes)}.")
        if nombre and not nombre_valido(nombre):
            errores.append("El nombre solo debe contener letras, espacios, guiones o apóstrofos.")
        if telefono and not telefono_valido(telefono):
            errores.append("El teléfono debe contener exactamente 10 dígitos.")
        if correo and not correo_valido(correo):
            errores.append("Ingresa un correo electrónico válido.")

        if errores:
            self.mostrar_alerta_validacion("\n".join(errores))
            return

        self.lbl_error.value = ""
        self.datos_pedido["nombre_contacto"] = nombre
        self.datos_pedido["direccion"] = direccion if self.datos_pedido["tipo_servicio"] == "A Domicilio" else ""
        self.datos_pedido["referencias"] = referencias if self.datos_pedido["tipo_servicio"] == "A Domicilio" else ""
        self.on_continuar_pago(self.datos_pedido)

    def mostrar_alerta_validacion(self, mensaje):
        self.lbl_error.value = mensaje
        try:
            page = self.page
        except RuntimeError:
            page = None
        if page:
            titulo_alerta = ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Icon(
                            ft.Icons.ERROR_OUTLINE,
                            color="#6A0404",
                            size=28,
                        ),
                        width=58,
                        height=58,
                        alignment=ft.Alignment.CENTER,
                        bgcolor="#FCE8E6",
                        border_radius=29,
                    ),
                    ft.Text(
                        "Revisa tus datos",
                        size=21,
                        weight=ft.FontWeight.BOLD,
                        color="#2B2B2B",
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                spacing=12,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                tight=True,
            )
            alerta = ft.AlertDialog(
                modal=True,
                bgcolor=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=24),
                elevation=12,
                shadow_color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK),
                title=titulo_alerta,
                title_padding=ft.Padding(left=24, top=24, right=24, bottom=8),
                content=ft.Container(
                    width=280,
                    content=ft.Text(
                        mensaje,
                        size=15,
                        color=ft.Colors.GREY_700,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ),
                content_padding=ft.Padding(left=24, top=8, right=24, bottom=8),
                actions=[
                    ft.FilledButton(
                        "Entendido",
                        icon=ft.Icons.CHECK,
                        bgcolor="#6A0404",
                        color=ft.Colors.WHITE,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=14),
                            padding=ft.Padding(
                                left=20,
                                top=12,
                                right=20,
                                bottom=12,
                            ),
                        ),
                        on_click=lambda e: page.pop_dialog(),
                    )
                ],
                actions_alignment=ft.MainAxisAlignment.CENTER,
                actions_padding=ft.Padding(left=20, top=8, right=20, bottom=20),
            )
            page.show_dialog(alerta)