import requests
import flet as ft
from config import BASE_URL

TAMANOS_PIZZA = [
    {
        "clave": "individual",
        "nombre": "Individual",
        "titulo_ui": "Individual",
        "porciones": "4 rebanadas",
        "max_combinaciones": 2,
        "precio": 110.00,
    },
    {
        "clave": "chica",
        "nombre": "Chica",
        "titulo_ui": "Chica",
        "porciones": "4 piezas",
        "max_combinaciones": 2,
        "precio": 140.00,
    },
    {
        "clave": "mediana",
        "nombre": "Mediana",
        "titulo_ui": "Mediana",
        "porciones": "6 piezas",
        "max_combinaciones": 2,
        "precio": 185.00,
    },
    {
        "clave": "grande",
        "nombre": "Grande",
        "titulo_ui": "Grande",
        "porciones": "8 piezas",
        "max_combinaciones": 2,
        "precio": 230.00,
    },
    {
        "clave": "jumbo",
        "nombre": "Jumbo",
        "titulo_ui": "Jumbo",
        "porciones": "12 rebanadas",
        "max_combinaciones": 4,
        "precio": 310.00,
    },
    {
        "clave": "mega",
        "nombre": "Mega",
        "titulo_ui": "Mega",
        "porciones": "24 piezas",
        "max_combinaciones": 4,
        "precio": 520.00,
    },
    {
        "clave": "cuadripizza_24",
        "nombre": "Cuadripizza (24 reb.)",
        "titulo_ui": "Cuadripizza",
        "porciones": "24 rebanadas",
        "max_combinaciones": 4,
        "precio": 540.00,
    },
    {
        "clave": "cuadripizza_32",
        "nombre": "Cuadripizza (32 reb.)",
        "titulo_ui": "Cuadripizza",
        "porciones": "32 rebanadas",
        "max_combinaciones": 4,
        "precio": 640.00,
    },
]

SABORES_BASE = [
    "Pizza Pepperoni",
    "Pizza Hawaiana",
    "Pizza Carnívora",
    "Pizza Mexicana",
]

DESCRIPCION_SABORES = {
    "Pizza Pepperoni": "Mozzarella fundido y pepperoni dorado",
    "Pizza Hawaiana": "Jamón ahumado, piña dulce y mozzarella",
    "Pizza Carnívora": "Pepperoni, chorizo, carne molida y tocino",
    "Pizza Mexicana": "Chorizo, jalapeño, cebolla y pimiento",
}


def obtener_mapa_disponibilidad():
    mapa = {sabor: True for sabor in SABORES_BASE}
    try:
        resp = requests.get(f"{BASE_URL}/api/pizzas/disponibilidad", timeout=8)
        if resp.status_code == 200:
            for item in resp.json().get("pizzas", []):
                nombre = item.get("nombre_pizza")
                if nombre:
                    mapa[nombre] = bool(item.get("disponible", True))
    except requests.RequestException:
        pass
    return mapa


def pizza_disponible_en_todas_versiones(nombre_o_combinacion, mapa_disp):
    for sabor in SABORES_BASE:
        if sabor.casefold() in (nombre_o_combinacion or "").casefold():
            if not mapa_disp.get(sabor, True):
                return False
    return True


def abrir_modal_combinar_pizza(
    page: ft.Page,
    es_movil: bool,
    on_agregar_combinacion,
):
    if page is None:
        return

    mapa_disp = obtener_mapa_disponibilidad()
    paso_actual = [1]  # 1 = Elegir tamaño, 2 = Elegir sabores
    tamano_actual = [None]
    sabores_sel = []

    ancho_modal = 320 if es_movil else 450
    alto_contenido = 410 if es_movil else 440

    lbl_subtitulo = ft.Text(
        "Paso 1 de 2 · Elige el tamaño",
        size=12,
        color="#806B63",
    )
    barra_pasos = ft.Row(spacing=8)
    contenedor_paso = ft.Column(
        spacing=10,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )
    lbl_err = ft.Text("", size=12, color="#B3261E", visible=False)
    fila_acciones = ft.Row(
        alignment=ft.MainAxisAlignment.END,
        spacing=8,
    )

    def cerrar(_=None):
        try:
            page.pop_dialog()
        except RuntimeError:
            pass

    def _crear_indicador_paso(numero, etiqueta, activo, completado):
        bgcolor = "#6A0404" if (activo or completado) else "#F5E9E2"
        color_num = ft.Colors.WHITE if (activo or completado) else "#806B63"
        color_txt = "#6A0404" if activo else ("#3F302B" if completado else "#9B8A82")
        return ft.Row(
            spacing=6,
            tight=True,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    width=22,
                    height=22,
                    border_radius=11,
                    bgcolor=bgcolor,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Icon(
                        ft.Icons.CHECK,
                        size=13,
                        color=ft.Colors.WHITE,
                    )
                    if completado
                    else ft.Text(
                        str(numero),
                        size=11,
                        weight=ft.FontWeight.BOLD,
                        color=color_num,
                    ),
                ),
                ft.Text(
                    etiqueta,
                    size=12,
                    weight=ft.FontWeight.BOLD if activo else ft.FontWeight.W_500,
                    color=color_txt,
                ),
            ],
        )

    def seleccionar_tamano(opt):
        tamano_actual[0] = opt
        if len(sabores_sel) > opt["max_combinaciones"]:
            del sabores_sel[opt["max_combinaciones"] :]
        paso_actual[0] = 2
        lbl_err.value = ""
        lbl_err.visible = False
        refrescar_ui()

    def volver_a_tamanos(_=None):
        paso_actual[0] = 1
        lbl_err.value = ""
        lbl_err.visible = False
        refrescar_ui()

    def toggle_sabor(sabor, disponible):
        if not disponible or tamano_actual[0] is None:
            return
        max_c = tamano_actual[0]["max_combinaciones"]
        if sabor in sabores_sel:
            sabores_sel.remove(sabor)
            lbl_err.value = ""
            lbl_err.visible = False
        else:
            if len(sabores_sel) >= max_c:
                lbl_err.value = (
                    f"Máximo {max_c} sabores para {tamano_actual[0]['titulo_ui']}."
                )
                lbl_err.visible = True
            else:
                sabores_sel.append(sabor)
                lbl_err.value = ""
                lbl_err.visible = False
        refrescar_ui()

    def confirmar(_=None):
        t = tamano_actual[0]
        if t is None:
            volver_a_tamanos()
            return
        if not sabores_sel:
            lbl_err.value = "Elige al menos 1 sabor para continuar."
            lbl_err.visible = True
            refrescar_ui()
            return
        titulo_combo = (
            f"{t['nombre']} ({t['porciones']}) - Comb.: {' + '.join(sabores_sel)}"
            if len(sabores_sel) > 1
            else f"{t['nombre']} ({t['porciones']}) - {sabores_sel[0]}"
        )
        cerrar()
        on_agregar_combinacion(
            {
                "nombre": titulo_combo,
                "precio": float(t["precio"]),
                "cantidad": 1,
                "tamano": t["nombre"],
                "sabores": list(sabores_sel),
            }
        )

    def construir_paso_tamanos():
        tarjetas = []
        for item in TAMANOS_PIZZA:
            seleccionado = (
                tamano_actual[0] is not None
                and tamano_actual[0]["clave"] == item["clave"]
            )
            tarjetas.append(
                ft.Container(
                    padding=ft.Padding(left=14, top=11, right=12, bottom=11),
                    bgcolor="#FFF3EB" if seleccionado else ft.Colors.WHITE,
                    border=ft.Border.all(
                        2 if seleccionado else 1,
                        "#6A0404" if seleccionado else "#ECD6C9",
                    ),
                    border_radius=14,
                    ink=True,
                    on_click=lambda e, opt=item: seleccionar_tamano(opt),
                    content=ft.Row(
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Column(
                                spacing=4,
                                expand=True,
                                controls=[
                                    ft.Row(
                                        spacing=6,
                                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                        controls=[
                                            ft.Text(
                                                item["titulo_ui"],
                                                size=15,
                                                weight=ft.FontWeight.BOLD,
                                                color="#2B2B2B",
                                            ),
                                            ft.Text(
                                                f"· {item['porciones']}",
                                                size=12,
                                                color="#806B63",
                                            ),
                                        ],
                                    ),
                                    ft.Container(
                                        padding=ft.Padding(
                                            left=8, top=2, right=8, bottom=2
                                        ),
                                        bgcolor="#FCE8E6"
                                        if item["max_combinaciones"] == 4
                                        else "#F7EFEA",
                                        border_radius=8,
                                        content=ft.Text(
                                            f"Hasta {item['max_combinaciones']} sabores",
                                            size=11,
                                            weight=ft.FontWeight.W_600,
                                            color="#6A0404"
                                            if item["max_combinaciones"] == 4
                                            else "#6E554B",
                                        ),
                                    ),
                                ],
                            ),
                            ft.Text(
                                f"${item['precio']:.2f}",
                                size=16,
                                weight=ft.FontWeight.BOLD,
                                color="#6A0404",
                            ),
                            ft.Icon(
                                ft.Icons.CHEVRON_RIGHT,
                                size=20,
                                color="#9B8A82",
                            ),
                        ],
                    ),
                )
            )
        return tarjetas

    def construir_paso_sabores():
        t = tamano_actual[0]
        max_c = t["max_combinaciones"]

        resumen_tamano = ft.Container(
            padding=ft.Padding(left=14, top=10, right=10, bottom=10),
            bgcolor="#FFF5EE",
            border=ft.Border.all(1, "#E7C8B8"),
            border_radius=14,
            content=ft.Row(
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(ft.Icons.LOCAL_PIZZA, color="#6A0404", size=22),
                    ft.Column(
                        spacing=1,
                        expand=True,
                        controls=[
                            ft.Text(
                                f"{t['titulo_ui']} · {t['porciones']}",
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                color="#3F302B",
                            ),
                            ft.Text(
                                f"${t['precio']:.2f}",
                                size=13,
                                weight=ft.FontWeight.BOLD,
                                color="#6A0404",
                            ),
                        ],
                    ),
                    ft.TextButton(
                        "Cambiar",
                        style=ft.ButtonStyle(color="#6A0404"),
                        on_click=volver_a_tamanos,
                    ),
                ],
            ),
        )

        encabezado_sabores = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(
                    "Selecciona tus sabores",
                    size=14,
                    weight=ft.FontWeight.BOLD,
                    color="#3F302B",
                ),
                ft.Container(
                    padding=ft.Padding(left=10, top=4, right=10, bottom=4),
                    bgcolor="#6A0404" if sabores_sel else "#F5E9E2",
                    border_radius=12,
                    content=ft.Text(
                        f"{len(sabores_sel)} / {max_c}",
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.WHITE if sabores_sel else "#806B63",
                    ),
                ),
            ],
        )

        tarjetas_sabores = []
        for sabor in SABORES_BASE:
            disp = mapa_disp.get(sabor, True)
            marcado = sabor in sabores_sel
            limite_lleno = (not marcado) and (len(sabores_sel) >= max_c)
            habilitado = disp and not limite_lleno

            tarjetas_sabores.append(
                ft.Container(
                    padding=ft.Padding(left=12, top=11, right=14, bottom=11),
                    bgcolor="#F4F1EF"
                    if not disp
                    else (
                        "#FCE8E6"
                        if marcado
                        else ("#FAF7F5" if limite_lleno else ft.Colors.WHITE)
                    ),
                    border=ft.Border.all(
                        2 if marcado else 1,
                        "#6A0404" if marcado else "#ECD6C9",
                    ),
                    border_radius=14,
                    opacity=0.6 if limite_lleno else 1.0,
                    ink=habilitado or marcado,
                    on_click=(
                        lambda e, sb=sabor, d=disp: toggle_sabor(sb, d)
                    )
                    if disp
                    else None,
                    content=ft.Row(
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(
                                ft.Icons.CHECK_CIRCLE
                                if marcado
                                else (
                                    ft.Icons.BLOCK
                                    if not disp
                                    else ft.Icons.RADIO_BUTTON_UNCHECKED
                                ),
                                color="#9E9E9E"
                                if not disp
                                else ("#6A0404" if marcado else "#B79E92"),
                                size=22,
                            ),
                            ft.Column(
                                spacing=2,
                                expand=True,
                                controls=[
                                    ft.Text(
                                        sabor
                                        if disp
                                        else f"{sabor} · Agotada",
                                        size=14,
                                        weight=ft.FontWeight.BOLD,
                                        color="#888888"
                                        if not disp
                                        else "#2B2B2B",
                                    ),
                                    ft.Text(
                                        DESCRIPCION_SABORES.get(sabor, ""),
                                        size=11,
                                        color="#806B63",
                                        max_lines=2,
                                    ),
                                ],
                            ),
                        ],
                    ),
                )
            )

        return [resumen_tamano, encabezado_sabores, *tarjetas_sabores]

    def refrescar_ui():
        en_paso_1 = paso_actual[0] == 1
        lbl_subtitulo.value = (
            "Paso 1 de 2 · Selecciona el tamaño"
            if en_paso_1
            else "Paso 2 de 2 · Elige las combinaciones"
        )
        barra_pasos.controls = [
            _crear_indicador_paso(1, "Tamaño", en_paso_1, not en_paso_1),
            ft.Container(
                width=24,
                height=2,
                bgcolor="#6A0404" if not en_paso_1 else "#E7C8B8",
            ),
            _crear_indicador_paso(2, "Sabores", not en_paso_1, False),
        ]

        if en_paso_1:
            contenedor_paso.controls = construir_paso_tamanos()
            fila_acciones.controls = [
                ft.TextButton(
                    "Cancelar",
                    style=ft.ButtonStyle(color="#6A0404"),
                    on_click=cerrar,
                ),
            ]
        else:
            t = tamano_actual[0]
            contenedor_paso.controls = construir_paso_sabores()
            fila_acciones.controls = [
                ft.OutlinedButton(
                    "Atrás",
                    icon=ft.Icons.ARROW_BACK,
                    style=ft.ButtonStyle(
                        color="#6A0404",
                        side=ft.BorderSide(1, "#6A0404"),
                        shape=ft.RoundedRectangleBorder(radius=12),
                    ),
                    on_click=volver_a_tamanos,
                ),
                ft.FilledButton(
                    f"Agregar · ${t['precio']:.2f}",
                    icon=ft.Icons.ADD_SHOPPING_CART,
                    bgcolor="#6A0404",
                    color=ft.Colors.WHITE,
                    disabled=not sabores_sel,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=12),
                    ),
                    on_click=confirmar,
                ),
            ]

        try:
            if dialogo.page is not None:
                dialogo.update()
        except RuntimeError:
            pass

    dialogo = ft.AlertDialog(
        modal=True,
        bgcolor=ft.Colors.WHITE,
        shape=ft.RoundedRectangleBorder(radius=24),
        title_padding=ft.Padding(left=20, top=18, right=20, bottom=8),
        content_padding=ft.Padding(left=20, top=6, right=20, bottom=8),
        actions_padding=ft.Padding(left=20, top=6, right=20, bottom=16),
        title=ft.Column(
            spacing=10,
            tight=True,
            controls=[
                ft.Row(
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(
                            width=38,
                            height=38,
                            border_radius=12,
                            bgcolor="#FCE8E6",
                            alignment=ft.Alignment.CENTER,
                            content=ft.Icon(
                                ft.Icons.LOCAL_PIZZA,
                                color="#6A0404",
                                size=21,
                            ),
                        ),
                        ft.Column(
                            spacing=1,
                            expand=True,
                            controls=[
                                ft.Text(
                                    "Combinar pizza",
                                    size=19,
                                    weight=ft.FontWeight.BOLD,
                                    color="#6A0404",
                                ),
                                lbl_subtitulo,
                            ],
                        ),
                    ],
                ),
                barra_pasos,
            ],
        ),
        content=ft.Container(
            width=ancho_modal,
            height=alto_contenido,
            content=ft.Column(
                spacing=8,
                expand=True,
                controls=[
                    contenedor_paso,
                    lbl_err,
                ],
            ),
        ),
        actions=[fila_acciones],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    refrescar_ui()
    try:
        page.show_dialog(dialogo)
    except RuntimeError as error:
        if "Dialog is already opened" in str(error):
            page.pop_dialog()
            page.show_dialog(dialogo)