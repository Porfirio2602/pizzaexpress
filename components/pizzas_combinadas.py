import requests
import flet as ft
from config import BASE_URL

TAMANOS_PIZZA = [
    {
        "clave": "individual",
        "nombre": "Individual",
        "porciones": "4 rebanadas",
        "max_combinaciones": 2,
        "precio": 110.00,
    },
    {
        "clave": "chica",
        "nombre": "Chica",
        "porciones": "4 piezas",
        "max_combinaciones": 2,
        "precio": 140.00,
    },
    {
        "clave": "mediana",
        "nombre": "Mediana",
        "porciones": "6 piezas",
        "max_combinaciones": 2,
        "precio": 185.00,
    },
    {
        "clave": "grande",
        "nombre": "Grande",
        "porciones": "8 piezas",
        "max_combinaciones": 2,
        "precio": 230.00,
    },
    {
        "clave": "jumbo",
        "nombre": "Jumbo",
        "porciones": "12 rebanadas",
        "max_combinaciones": 4,
        "precio": 310.00,
    },
    {
        "clave": "mega",
        "nombre": "Mega",
        "porciones": "24 piezas",
        "max_combinaciones": 4,
        "precio": 520.00,
    },
    {
        "clave": "cuadripizza_24",
        "nombre": "Cuadripizza (24 reb.)",
        "porciones": "24 rebanadas",
        "max_combinaciones": 4,
        "precio": 540.00,
    },
    {
        "clave": "cuadripizza_32",
        "nombre": "Cuadripizza (32 reb.)",
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


def obtener_mapa_disponibilidad():
    mapa = {sabor: True for sabor in SABORES_BASE}
    try:
        resp = requests.get(f"{BASE_URL}/api/pizzas/disponibilidad", timeout=10)
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
    tamano_actual = [TAMANOS_PIZZA[1]]
    sabores_sel = []
    lbl_info = ft.Text("", size=12, color="#806B63")
    lbl_err = ft.Text("", size=12, color=ft.Colors.RED_700)
    col_sabores = ft.Column(spacing=6, tight=True)
    col_tamanos = ft.Column(spacing=6, tight=True)

    def cerrar(_=None):
        try:
            page.pop_dialog()
        except RuntimeError:
            pass

    def refrescar_ui():
        t = tamano_actual[0]
        max_c = t["max_combinaciones"]
        lbl_info.value = (
            f"{t['nombre']} ({t['porciones']}) · Precio fijo: ${t['precio']:.2f} "
            f"· Máx. {max_c} combinaciones"
        )

        col_tamanos.controls = [
            ft.Container(
                padding=10,
                bgcolor="#FFF1E7" if item["clave"] == t["clave"] else ft.Colors.WHITE,
                border=ft.Border.all(
                    2 if item["clave"] == t["clave"] else 1,
                    "#6A0404" if item["clave"] == t["clave"] else "#E7C8B8",
                ),
                border_radius=12,
                ink=True,
                on_click=lambda e, opt=item: seleccionar_tamano(opt),
                content=ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text(
                                    f"{item['nombre']} · {item['porciones']}",
                                    size=13,
                                    weight=ft.FontWeight.BOLD,
                                    color="#3F302B",
                                ),
                                ft.Text(
                                    f"Hasta {item['max_combinaciones']} sabores · Precio fijo",
                                    size=11,
                                    color="#806B63",
                                ),
                            ],
                            spacing=1,
                            expand=True,
                        ),
                        ft.Text(
                            f"${item['precio']:.2f}",
                            size=14,
                            weight=ft.FontWeight.BOLD,
                            color="#6A0404",
                        ),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )
            for item in TAMANOS_PIZZA
        ]

        col_sabores.controls = []
        for sabor in SABORES_BASE:
            disp = mapa_disp.get(sabor, True)
            marcado = sabor in sabores_sel

            def toggle_sabor(e, sb=sabor, disponible=disp):
                if not disponible:
                    return
                if sb in sabores_sel:
                    sabores_sel.remove(sb)
                    lbl_err.value = ""
                else:
                    if len(sabores_sel) >= tamano_actual[0]["max_combinaciones"]:
                        lbl_err.value = (
                            f"Solo se permiten hasta {tamano_actual[0]['max_combinaciones']} "
                            f"combinaciones en tamaño {tamano_actual[0]['nombre']}."
                        )
                    else:
                        sabores_sel.append(sb)
                        lbl_err.value = ""
                refrescar_ui()

            col_sabores.controls.append(
                ft.Container(
                    padding=10,
                    bgcolor="#F5F5F5"
                    if not disp
                    else ("#FCE8E6" if marcado else ft.Colors.WHITE),
                    border=ft.Border.all(
                        1.5 if marcado else 1,
                        "#6A0404" if marcado else "#E7C8B8",
                    ),
                    border_radius=12,
                    ink=disp,
                    on_click=toggle_sabor if disp else None,
                    content=ft.Row(
                        [
                            ft.Icon(
                                ft.Icons.CHECK_BOX
                                if marcado
                                else (
                                    ft.Icons.BLOCK
                                    if not disp
                                    else ft.Icons.CHECK_BOX_OUTLINED
                                ),
                                color="#9E9E9E" if not disp else "#6A0404",
                                size=20,
                            ),
                            ft.Text(
                                sabor
                                if disp
                                else f"{sabor} (No disponible)",
                                size=13,
                                weight=ft.FontWeight.W_600,
                                color="#888888" if not disp else "#2B2B2B",
                                expand=True,
                            ),
                        ],
                        spacing=10,
                    ),
                )
            )

        try:
            page.update()
        except RuntimeError:
            pass

    def seleccionar_tamano(opt):
        tamano_actual[0] = opt
        if len(sabores_sel) > opt["max_combinaciones"]:
            del sabores_sel[opt["max_combinaciones"] :]
        lbl_err.value = ""
        refrescar_ui()

    def confirmar(_=None):
        if not sabores_sel:
            lbl_err.value = "Elige al menos 1 sabor para la pizza."
            refrescar_ui()
            return
        t = tamano_actual[0]
        if len(sabores_sel) > t["max_combinaciones"]:
            lbl_err.value = (
                f"Máximo {t['max_combinaciones']} combinaciones para {t['nombre']}."
            )
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

    dialogo = ft.AlertDialog(
        modal=True,
        bgcolor=ft.Colors.WHITE,
        shape=ft.RoundedRectangleBorder(radius=22),
        title=ft.Text("Combinar pizza a precio fijo", color="#6A0404"),
        content=ft.Container(
            width=330 if es_movil else 460,
            height=460,
            content=ft.Column(
                scroll=ft.ScrollMode.AUTO,
                tight=True,
                spacing=10,
                controls=[
                    lbl_info,
                    ft.Text(
                        "1. Elige el tamaño y porciones (precio fijo):",
                        size=13,
                        weight=ft.FontWeight.BOLD,
                        color="#3F302B",
                    ),
                    col_tamanos,
                    ft.Text(
                        "2. Elige las combinaciones (máx. 2 de Chica a Grande; hasta 4 de Jumbo a Cuadripizza):",
                        size=13,
                        weight=ft.FontWeight.BOLD,
                        color="#3F302B",
                    ),
                    col_sabores,
                    lbl_err,
                ],
            ),
        ),
        actions=[
            ft.TextButton("Cancelar", on_click=cerrar),
            ft.FilledButton(
                "Agregar al pedido",
                icon=ft.Icons.ADD_SHOPPING_CART,
                bgcolor="#6A0404",
                color=ft.Colors.WHITE,
                on_click=confirmar,
            ),
        ],
    )

    refrescar_ui()
    try:
        page.show_dialog(dialogo)
    except RuntimeError as error:
        if "Dialog is already opened" in str(error):
            page.pop_dialog()
            page.show_dialog(dialogo)