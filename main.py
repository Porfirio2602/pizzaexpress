import flet as ft
import asyncio
import os
import json
import sqlite3
from pizza_express import inicializar_base_datos
from components.menu_lateral import MenuLateral
from views.inicio_view import InicioView
from views.login_view import LoginView
from views.registro_view import RegistroView
from views.menu_view import MenuView
from views.solicitud_datos_view import SolicitudDatosView
from views.pago_view import PagoView
from views.mis_pedidos_view import MisPedidosView
from views.personal_login_view import PersonalLoginView
from views.vendedor_view import VendedorView
from views.gerencia_view import GerenciaView

# Archivo local para persistencia de sesión
SESION_FILE = "sesion.json"
SESION_PERSONAL_FILE = "sesion_personal.json"

def cargar_sesion():
    if os.path.exists(SESION_FILE):
        try:
            with open(SESION_FILE, "r") as f:
                sesion = json.load(f)
                sesion.setdefault("token", None)
                return sesion
        except:
            pass
    return {"id": None, "nombre": None, "apellido": None, "token": None}

def guardar_sesion(id_usu, nom, ape, token):
    try:
        with open(SESION_FILE, "w") as f:
            json.dump(
                {"id": id_usu, "nombre": nom, "apellido": ape, "token": token},
                f,
            )
    except:
            pass

def limpiar_sesion():
    if os.path.exists(SESION_FILE):
        try:
            os.remove(SESION_FILE)
        except:
            pass


def cargar_sesion_personal():
    if os.path.exists(SESION_PERSONAL_FILE):
        try:
            with open(SESION_PERSONAL_FILE, "r") as archivo:
                sesion = json.load(archivo)
            if sesion.get("token") and sesion.get("rol") in ("gerente", "vendedor"):
                return sesion
        except (OSError, ValueError):
            pass
    return {}


def guardar_sesion_personal(personal):
    with open(SESION_PERSONAL_FILE, "w") as archivo:
        json.dump(
            {
                "id": personal["id"],
                "nombre": personal["nombre"],
                "correo": personal["correo"],
                "rol": personal["rol"],
                "token": personal["token"],
            },
            archivo,
        )


def limpiar_sesion_personal():
    if os.path.exists(SESION_PERSONAL_FILE):
        os.remove(SESION_PERSONAL_FILE)


def main(page: ft.Page):
    page.title = "PizzaExpress"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#FFF8F2"
    page.padding = 0
    page.spacing = 0

    progreso = ft.ProgressRing(color="#6A0404", width=34, height=34)
    estado = ft.Text(
        "Preparando tu experiencia...",
        size=14,
        color=ft.Colors.GREY_700,
        text_align=ft.TextAlign.CENTER,
    )
    splash = ft.Container(
        expand=True,
        alignment=ft.Alignment.CENTER,
        content=ft.Column(
            controls=[
                ft.Image(
                    src="imagenes/pizzaicon.png",
                    width=112,
                    height=112,
                    fit=ft.BoxFit.CONTAIN,
                ),
                ft.Text(
                    "PIZZA EXPRESS",
                    size=26,
                    weight=ft.FontWeight.BOLD,
                    color="#6A0404",
                ),
                ft.Text(
                    "El sabor que alegra tu día",
                    size=14,
                    color=ft.Colors.GREY_700,
                ),
                ft.Container(height=8),
                progreso,
                estado,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=12,
        ),
    )
    page.add(splash)

    async def iniciar_aplicacion():
        await asyncio.sleep(0.8)
        try:
            await asyncio.to_thread(inicializar_base_datos)
        except (sqlite3.Error, OSError):
            progreso.visible = False
            estado.value = (
                "No se pudo iniciar la aplicación. "
                "Revisa el almacenamiento e inténtalo de nuevo."
            )
            page.update()
            return

        page.clean()
        construir_aplicacion(page)

    page.run_task(iniciar_aplicacion)


def construir_aplicacion(page: ft.Page):
    page.title = "PizzaExpress"
    page.theme_mode = ft.ThemeMode.LIGHT

    plataformas_moviles = (
        ft.PagePlatform.ANDROID,
        ft.PagePlatform.IOS,
    )
    es_movil = page.platform in plataformas_moviles
    es_escritorio = not es_movil
    nav_rail: ft.NavigationRail | None = None

    if es_movil:
        page.padding = 0
    else:
        page.window.width = 1200
        page.window.height = 850
        page.window.resizable = True

    page.bgcolor = "white"
    page.vertical_alignment = ft.MainAxisAlignment.START 
    page.padding = 0 if es_movil else 16
    page.spacing = 0

    def actualizar_visibilidad_navegacion(visible):
        page.navigation_bar.visible = visible and not es_escritorio
        if nav_rail is not None:
            nav_rail.visible = visible and es_escritorio

    def actualizar_indice_navegacion(indice):
        page.navigation_bar.selected_index = indice
        if nav_rail is not None:
            nav_rail.selected_index = indice

    ruta_icono = os.path.join(os.path.dirname(__file__), "assets", "imagenes", "pizzaicon.png")
    if os.path.exists(ruta_icono):
        page.window.icon = ruta_icono

    # Cargar usuario actual desde el archivo local
    usuario_actual = cargar_sesion()
    if usuario_actual.get("id") and not usuario_actual.get("token"):
        limpiar_sesion()
        usuario_actual = {
            "id": None,
            "nombre": None,
            "apellido": None,
            "token": None,
        }
    personal_actual = cargar_sesion_personal()
    indice_ventana_actual = [0]

    # Transición profesional con AnimatedSwitcher corregida
    contenido_principal = ft.AnimatedSwitcher(
        content=ft.Container(expand=True),
        transition=ft.AnimatedSwitcherTransition.FADE,
        duration=350,
        reverse_duration=250,
        switch_in_curve=ft.AnimationCurve.EASE_IN_OUT,
        switch_out_curve=ft.AnimationCurve.EASE_IN_OUT,
        expand=True
    )
    
    contenedor_comprar = ft.Container()

    # EL TÍTULO DE LA BARRA SE QUEDA FIJO SIEMPRE
    txt_titulo_app = ft.Text(
        "PIZZA EXPRESS",
        size=18,
        weight="bold",
        color=ft.Colors.WHITE,
    )

    def cerrar_drawer(e=None):
        menu_lateral.visible = False
        overlay_oscuro.visible = False
        page.update()

    def abrir_drawer(e):
        menu_lateral.visible = True
        overlay_oscuro.visible = True
        page.update()

    def ir_a_login(e=None):
        cerrar_drawer()
        actualizar_visibilidad_navegacion(False)
        contenedor_comprar.content = None
        contenido_principal.content = LoginView(
            on_volver=regresar_inicio_general,
            on_login_exitoso=manejar_login_exitoso,
            es_movil=es_movil,
            on_registro=ir_a_registro,
        )
        page.update()

    def ir_a_registro(e=None):
        cerrar_drawer()
        actualizar_visibilidad_navegacion(False)
        contenedor_comprar.content = None
        contenido_principal.content = RegistroView(
            on_volver=regresar_inicio_general,
            on_registro_exitoso=manejar_registro_exitoso,
            es_movil=es_movil,
        )
        page.update()

    def mostrar_panel_personal():
        cerrar_drawer()
        actualizar_visibilidad_navegacion(False)
        contenedor_comprar.content = None
        if personal_actual.get("rol") == "gerente":
            contenido_principal.content = GerenciaView(
                personal=personal_actual,
                on_cerrar_sesion=cerrar_sesion_personal,
                es_movil=es_movil,
            )
        else:
            contenido_principal.content = VendedorView(
                personal=personal_actual,
                on_cerrar_sesion=cerrar_sesion_personal,
                es_movil=es_movil,
            )
        page.update()

    def ir_a_vendedor(e=None):
        cerrar_drawer()
        if personal_actual.get("rol") == "vendedor" and personal_actual.get("token"):
            mostrar_panel_personal()
            return
        actualizar_visibilidad_navegacion(False)
        contenedor_comprar.content = None
        contenido_principal.content = PersonalLoginView(
            rol="vendedor",
            on_login_exitoso=manejar_login_personal,
            on_volver=regresar_inicio_general,
            es_movil=es_movil,
        )
        page.update()

    def ir_a_gerencia(e=None):
        cerrar_drawer()
        if personal_actual.get("rol") == "gerente" and personal_actual.get("token"):
            mostrar_panel_personal()
            return
        actualizar_visibilidad_navegacion(False)
        contenedor_comprar.content = None
        contenido_principal.content = PersonalLoginView(
            rol="gerente",
            on_login_exitoso=manejar_login_personal,
            on_volver=regresar_inicio_general,
            es_movil=es_movil,
        )
        page.update()

    def manejar_login_personal(personal):
        personal_actual.clear()
        personal_actual.update(personal)
        guardar_sesion_personal(personal)
        menu_lateral.actualizar_personal(personal_actual)
        mostrar_panel_personal()

    def cerrar_sesion_personal():
        personal_actual.clear()
        limpiar_sesion_personal()
        menu_lateral.actualizar_personal(personal_actual)
        regresar_inicio_general()

    def manejar_login_exitoso(id_usu, nom, ape, token):
        usuario_actual["id"] = id_usu
        usuario_actual["nombre"] = nom
        usuario_actual["apellido"] = ape
        usuario_actual["token"] = token
        
        # Guardar sesión en archivo local
        guardar_sesion(id_usu, nom, ape, token)
        
        menu_lateral.actualizar_menu()
        regresar_inicio_general()

    def manejar_registro_exitoso(id_usu, nom, ape, token):
        usuario_actual["id"] = id_usu
        usuario_actual["nombre"] = nom
        usuario_actual["apellido"] = ape
        usuario_actual["token"] = token
        
        # Guardar sesión en archivo local
        guardar_sesion(id_usu, nom, ape, token)
        
        menu_lateral.actualizar_menu()
        regresar_inicio_general()

    def cerrar_sesion(e):
        usuario_actual["id"] = None
        usuario_actual["nombre"] = None
        usuario_actual["apellido"] = None
        usuario_actual["token"] = None
        
        # Borrar archivo de sesión local
        limpiar_sesion()
        
        menu_lateral.actualizar_menu()
        cerrar_drawer()
        regresar_inicio_general()

    menu_lateral = MenuLateral(
        usuario_actual=usuario_actual,
        on_login_click=ir_a_login,
        on_registro_click=ir_a_registro,
        on_logout_click=cerrar_sesion,
        on_close_click=cerrar_drawer,
        personal_actual=personal_actual,
        on_vendedor_click=ir_a_vendedor,
        on_gerencia_click=ir_a_gerencia,
        on_personal_logout_click=lambda e: cerrar_sesion_personal(),
    )
    menu_lateral.height = page.height or 760

    def actualizar_alto_menu(e):
        menu_lateral.height = page.height or 760
        if menu_lateral.page is not None:
            menu_lateral.update()

    page.on_resize = actualizar_alto_menu

    overlay_oscuro = ft.Container(
        bgcolor=ft.Colors.with_opacity(0.4, ft.Colors.BLACK),
        visible=False,
        expand=True,
        on_click=cerrar_drawer
    )

    def regresar_inicio_general():
        menu_view_instancia.limpiar_carrito()
        actualizar_visibilidad_navegacion(True)
        actualizar_indice_navegacion(0)
        indice_ventana_actual[0] = 0
        contenido_principal.content = inicio_view_instancia
        contenedor_comprar.content = btn_comprar
        page.update()

    barra_superior = ft.Container(
        content=ft.Row(
            controls=[
                ft.IconButton(icon=ft.Icons.MENU, icon_color=ft.Colors.WHITE, on_click=abrir_drawer),
                txt_titulo_app,
                ft.Container(width=40),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        bgcolor="#6A0404", padding=15
    )

    # Instancia del menú aceptando la categoría
    menu_view_instancia = MenuView(
        on_cart_change=lambda: verificar_estado_compra(),
        categoria_inicial="Pizzas",
        es_movil=es_movil,
    )

    # Instancia de inicio enviando la función para saltar al carrito/menú con categoría
    def navegar_a_categoria(cat):
        actualizar_indice_navegacion(1)
        indice_ventana_actual[0] = 1
        menu_view_instancia.cambiar_categoria(cat)
        contenido_principal.content = menu_view_instancia
        verificar_estado_compra()
        page.update()

    inicio_view_instancia = InicioView(
        on_ir_a_menu=navegar_a_categoria,
        es_movil=es_movil,
    )

    def mostrar_alerta_inicio_sesion():
        animacion_activa = [True]
        icono_animado = ft.AnimatedSwitcher(
            content=ft.Icon(ft.Icons.LOCK_PERSON, size=52, color="#6A0404"),
            duration=600,
            transition=ft.AnimatedSwitcherTransition.ROTATION,
            width=88,
            height=88,
            align=ft.Alignment.CENTER,
        )

        def detener_animacion(e=None):
            animacion_activa[0] = False

        def cerrar_alerta(e):
            detener_animacion()
            page.pop_dialog()

        def ir_a_login_desde_alerta(e):
            cerrar_alerta(e)
            ir_a_login()

        dialogo = ft.AlertDialog(
            modal=True,
            content=ft.Column(
                [
                    ft.Container(
                        content=icono_animado,
                        width=96,
                        height=96,
                        alignment=ft.Alignment.CENTER,
                        bgcolor="#FCE8E6",
                        border_radius=48,
                    ),
                    ft.Text(
                        "Inicia sesión primero",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color="#2B2B2B",
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        "Para continuar con tu compra, inicia sesión en tu cuenta.",
                        size=14,
                        color=ft.Colors.GREY_700,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                tight=True,
                spacing=12,
            ),
            actions=[
                ft.TextButton("Ahora no", on_click=cerrar_alerta),
                ft.FilledButton(
                    "Iniciar sesión",
                    bgcolor="#6A0404",
                    color=ft.Colors.WHITE,
                    on_click=ir_a_login_desde_alerta,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.CENTER,
            on_dismiss=detener_animacion,
        )

        async def animar_icono():
            iconos = (ft.Icons.LOCK_PERSON, ft.Icons.KEY)
            indice = 0
            while animacion_activa[0]:
                await asyncio.sleep(0.8)
                if not animacion_activa[0]:
                    break
                indice = 1 - indice
                icono_animado.content = ft.Icon(iconos[indice], size=52, color="#6A0404")
                if icono_animado.page is not None:
                    icono_animado.update()

        page.show_dialog(dialogo)
        page.run_task(animar_icono)

    def realizar_compra(e):
        if not usuario_actual.get("id"):
            mostrar_alerta_inicio_sesion()
            return

        items = menu_view_instancia.obtener_items_estado()
        if not items:
            page.show_dialog(
                ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Tu carrito está vacío"),
                    content=ft.Text(
                        "Agrega al menos un producto al menú antes de continuar."
                    ),
                    actions=[
                        ft.TextButton(
                            "Entendido",
                            on_click=lambda e: page.pop_dialog(),
                        )
                    ],
                    actions_alignment=ft.MainAxisAlignment.CENTER,
                )
            )
            return

        actualizar_visibilidad_navegacion(False)
        contenido_principal.content = SolicitudDatosView(
            items_estado=items,
            on_regresar=lambda: regresar_a_menu_carrito(),
            on_continuar_pago=lambda datos_ped: ir_a_pago(datos_ped, items),
            es_movil=es_movil,
        )
        btn_comprar.visible = False
        page.update()

    def regresar_a_menu_carrito():
        actualizar_visibilidad_navegacion(True)
        actualizar_indice_navegacion(1)
        indice_ventana_actual[0] = 1
        contenido_principal.content = menu_view_instancia
        verificar_estado_compra()
        page.update()

    def ir_a_pago(datos_ped, items):
        contenido_principal.content = PagoView(
            usuario_actual=usuario_actual,
            datos_pedido=datos_ped,
            items_estado=items,
            on_cancelar=lambda: regresar_a_menu_carrito(),
            on_compra_finalizada=lambda: finalizar_todo_exito(),
            es_movil=es_movil,
        )
        page.update()

    def cargar_pedidos_en_segundo_plano(vista, vista_inicio=False):
        async def cargar():
            vista_cargada = await vista.cargar_pedidos()
            if vista_inicio:
                if (
                    vista_cargada.pedido_activo
                    and indice_ventana_actual[0] == 0
                    and contenido_principal.content is inicio_view_instancia
                ):
                    contenido_principal.content = vista_cargada
                    page.update()
            elif contenido_principal.content is vista:
                contenido_principal.content = vista_cargada
                page.update()

        page.run_task(cargar)

    def finalizar_todo_exito():
        menu_view_instancia.limpiar_carrito()
        actualizar_visibilidad_navegacion(True)
        actualizar_indice_navegacion(2)
        indice_ventana_actual[0] = 2
        vista_pedidos = MisPedidosView(
            usuario_actual=usuario_actual,
            es_movil=es_movil,
            cargando=True,
        )
        contenido_principal.content = vista_pedidos
        contenedor_comprar.content = btn_comprar
        btn_comprar.visible = False
        page.update()
        cargar_pedidos_en_segundo_plano(vista_pedidos)

    def crear_contenido_boton_pagar(total=""):
        return ft.Row(
            controls=[
                ft.Container(
                    content=ft.Icon(
                        ft.Icons.PAYMENT,
                        color="#6A0404",
                        size=30 if es_escritorio else 22,
                    ),
                    width=56 if es_escritorio else 44,
                    height=56 if es_escritorio else 44,
                    alignment=ft.Alignment.CENTER,
                    bgcolor=ft.Colors.WHITE,
                    border_radius=16,
                ),
                ft.Column(
                    controls=[
                        ft.Text(
                            "Pagar ahora",
                            size=19 if es_escritorio else 15,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Text(
                            "Continúa con tu pedido",
                            size=14 if es_escritorio else 11,
                        ),
                    ],
                    spacing=2,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Container(expand=True),
                ft.Column(
                    controls=[
                        ft.Text(
                            "TOTAL",
                            size=13 if es_escritorio else 10,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Text(
                            total,
                            size=22 if es_escritorio else 17,
                            weight=ft.FontWeight.BOLD,
                        ),
                    ],
                    spacing=2,
                    horizontal_alignment=ft.CrossAxisAlignment.END,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
            ],
            spacing=14 if es_escritorio else 10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    btn_comprar = ft.FilledButton(
        content=crear_contenido_boton_pagar(),
        bgcolor="#6A0404",
        width=440 if es_escritorio else 330,
        height=96 if es_escritorio else 74,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=20),
            padding=ft.Padding(
                left=20 if es_escritorio else 14,
                top=14 if es_escritorio else 10,
                right=20 if es_escritorio else 14,
                bottom=14 if es_escritorio else 10,
            ),
            elevation=8,
            shadow_color="#3A0202",
            overlay_color=ft.Colors.with_opacity(0.12, ft.Colors.WHITE),
            animation_duration=180,
        ),
        visible=False,
        on_click=realizar_compra,
    )

    contenedor_comprar.content = btn_comprar
    contenedor_comprar.alignment = ft.Alignment.CENTER
    contenedor_comprar.padding = ft.Padding(left=15, top=12, right=15, bottom=12)
    contenedor_comprar.bgcolor = ft.Colors.TRANSPARENT
    contenedor_comprar.expand = False

    contenido_principal.content = inicio_view_instancia
    page.update()

    def verificar_estado_compra():
        if page.navigation_bar.selected_index == 1:
            items = menu_view_instancia.obtener_items_estado()
            hay_seleccion = any(item["cantidad"] > 0 for item in items)
            if hay_seleccion:
                total_general = sum(item["cantidad"] * item["precio"] for item in items)
                btn_comprar.content = crear_contenido_boton_pagar(f"${total_general:.2f}")
                btn_comprar.visible = True
            else:
                btn_comprar.visible = False
        else:
            btn_comprar.visible = False
            
        if btn_comprar.page is not None:
            btn_comprar.update()

    def mostrar_ventana(indice):
        indice_ventana_actual[0] = indice
        actualizar_indice_navegacion(indice)
        if indice == 0:
            contenido_principal.content = inicio_view_instancia
        elif indice == 1:
            contenido_principal.content = menu_view_instancia
        elif indice == 2:
            vista_pedidos = MisPedidosView(
                usuario_actual=usuario_actual,
                es_movil=es_movil,
                cargando=True,
            )
            contenido_principal.content = vista_pedidos
            cargar_pedidos_en_segundo_plano(vista_pedidos)
            
        verificar_estado_compra()
        page.update()

    def cambiar_ventana(e):
        indice = e.control.selected_index
        if (
            indice_ventana_actual[0] == 1
            and indice in (0, 2)
            and menu_view_instancia.obtener_items_estado()
        ):
            actualizar_indice_navegacion(1)
            page.update()

            def continuar_compra(e):
                page.pop_dialog()

            def cancelar_compra(e):
                page.pop_dialog()
                menu_view_instancia.limpiar_carrito()
                mostrar_ventana(indice)

            dialogo_carrito = ft.AlertDialog(
                modal=True,
                bgcolor=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=24),
                elevation=12,
                shadow_color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK),
                title=ft.Column(
                    controls=[
                        ft.Container(
                            content=ft.Icon(
                                ft.Icons.SHOPPING_BAG_OUTLINED,
                                color="#6A0404",
                                size=34 if es_escritorio else 28,
                            ),
                            width=68 if es_escritorio else 58,
                            height=68 if es_escritorio else 58,
                            alignment=ft.Alignment.CENTER,
                            bgcolor="#FCE8E6",
                            border_radius=34 if es_escritorio else 29,
                        ),
                        ft.Text(
                            "Tu pedido te espera",
                            size=26 if es_escritorio else 21,
                            weight=ft.FontWeight.BOLD,
                            color="#2B2B2B",
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    spacing=12,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    tight=True,
                ),
                title_padding=ft.Padding(
                    left=32 if es_escritorio else 24,
                    top=32 if es_escritorio else 24,
                    right=32 if es_escritorio else 24,
                    bottom=10 if es_escritorio else 8,
                ),
                content=ft.Container(
                    width=380 if es_escritorio else 280,
                    content=ft.Text(
                        "Tienes productos seleccionados. ¿Quieres seguir con tu compra o vaciar el carrito?",
                        size=18 if es_escritorio else 15,
                        color=ft.Colors.GREY_700,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ),
                content_padding=ft.Padding(
                    left=32 if es_escritorio else 24,
                    top=10 if es_escritorio else 8,
                    right=32 if es_escritorio else 24,
                    bottom=10 if es_escritorio else 8,
                ),
                actions=[
                    ft.Row(
                        controls=[
                            ft.OutlinedButton(
                                "Seguir comprando",
                                icon=ft.Icons.ARROW_BACK,
                                width=178 if es_escritorio else 142,
                                height=54 if es_escritorio else 46,
                                style=ft.ButtonStyle(
                                    color="#6A0404",
                                    side=ft.BorderSide(1, "#6A0404"),
                                    shape=ft.RoundedRectangleBorder(radius=14),
                                    text_style=ft.TextStyle(
                                        size=14 if es_escritorio else 12
                                    ),
                                ),
                                on_click=continuar_compra,
                            ),
                            ft.FilledButton(
                                "Vaciar carrito",
                                icon=ft.Icons.DELETE_OUTLINE,
                                bgcolor="#6A0404",
                                color=ft.Colors.WHITE,
                                width=178 if es_escritorio else 142,
                                height=54 if es_escritorio else 46,
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=14),
                                    text_style=ft.TextStyle(
                                        size=14 if es_escritorio else 12
                                    ),
                                ),
                                on_click=cancelar_compra,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=10 if es_escritorio else 8,
                        tight=True,
                    )
                ],
                actions_alignment=ft.MainAxisAlignment.CENTER,
                actions_padding=ft.Padding(
                    left=12 if es_escritorio else 8,
                    top=10 if es_escritorio else 8,
                    right=12 if es_escritorio else 8,
                    bottom=26 if es_escritorio else 20,
                ),
            )
            page.show_dialog(
                dialogo_carrito
            )
            return

        mostrar_ventana(indice)

    page.navigation_bar = ft.NavigationBar(
        selected_index=0,
        visible=not es_escritorio,
        bgcolor="#6A0404",
        indicator_color=ft.Colors.WHITE, 
        label_behavior=ft.NavigationBarLabelBehavior.ALWAYS_SHOW,
        on_change=cambiar_ventana,
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.LOCAL_PIZZA_OUTLINED, selected_icon=ft.Icons.LOCAL_PIZZA, label="Inicio"),
            ft.NavigationBarDestination(icon=ft.Icons.SHOPPING_CART_OUTLINED, selected_icon=ft.Icons.SHOPPING_CART, label="Carrito"),
            ft.NavigationBarDestination(icon=ft.Icons.SHOPPING_BAG_SHARP, selected_icon=ft.Icons.SHOPPING_BAG_SHARP, label="PEDIDOS"),
        ]
    )
    def crear_icono_rail(icono, seleccionado):
        return ft.Container(
            padding=5,
            content=ft.Icon(
                icono,
                size=30 if seleccionado else 28,
                color="#6A0404" if seleccionado else "#776963",
            ),
        )

    nav_rail = ft.NavigationRail(
        selected_index=0,
        visible=es_escritorio,
        bgcolor=ft.Colors.WHITE,
        indicator_color="#FCE8E6",
        indicator_shape=ft.RoundedRectangleBorder(radius=18),
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=92,
        selected_label_text_style=ft.TextStyle(
            color="#6A0404",
            size=17,
            weight=ft.FontWeight.BOLD,
        ),
        unselected_label_text_style=ft.TextStyle(
            color="#776963",
            size=15,
            weight=ft.FontWeight.W_500,
        ),
        destinations=[
            ft.NavigationRailDestination(
                icon=crear_icono_rail(ft.Icons.LOCAL_PIZZA_OUTLINED, False),
                selected_icon=crear_icono_rail(ft.Icons.LOCAL_PIZZA, True),
                label="Inicio",
            ),
            ft.NavigationRailDestination(
                icon=crear_icono_rail(ft.Icons.SHOPPING_CART_OUTLINED, False),
                selected_icon=crear_icono_rail(ft.Icons.SHOPPING_CART, True),
                label="Carrito",
            ),
            ft.NavigationRailDestination(
                icon=crear_icono_rail(ft.Icons.SHOPPING_BAG_SHARP, False),
                selected_icon=crear_icono_rail(ft.Icons.SHOPPING_BAG_SHARP, True),
                label="Pedidos",
            ),
        ],
        on_change=cambiar_ventana,
    )
    nav_rail_contenedor = ft.Container(
        content=nav_rail,
        border=ft.Border(
            right=ft.BorderSide(1, "#E8DDD8"),
        ),
    )

    page.add(
        ft.Stack(
            controls=[
                ft.Row(
                    controls=[
                        nav_rail_contenedor,
                        ft.Column(
                            [
                                barra_superior,
                                contenido_principal,
                                contenedor_comprar,
                            ],
                            spacing=0,
                            expand=True,
                        ),
                    ],
                    spacing=0,
                    expand=True,
                ),
                overlay_oscuro,
                menu_lateral
            ],
            expand=True
        )
    )

    if usuario_actual.get("id"):
        vista_pedidos_inicio = MisPedidosView(
            usuario_actual=usuario_actual,
            vista_inicio=True,
            es_movil=es_movil,
            cargando=True,
        )
        cargar_pedidos_en_segundo_plano(vista_pedidos_inicio, vista_inicio=True)

if __name__ == "__main__":
    ft.run(main, assets_dir="assets")