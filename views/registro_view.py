import flet as ft
import requests
from config import BASE_URL
from components.validaciones import correo_valido, nombre_valido, telefono_valido

class RegistroView(ft.Container):
    def __init__(self, on_volver, on_registro_exitoso, es_movil=False):
        super().__init__()
        self.on_volver = on_volver
        self.on_registro_exitoso = on_registro_exitoso
        
        self.expand = True
        self.alignment = ft.Alignment.CENTER
        
        ancho_campo = 280 if es_movil else None
        alto_campo = 45 if es_movil else 52
        expandir_campo = not es_movil
        self.txt_nombre = ft.TextField(label="Nombre", width=ancho_campo, height=alto_campo, expand=expandir_campo)
        self.txt_primer_apellido = ft.TextField(label="Primer Apellido", width=ancho_campo, height=alto_campo, expand=expandir_campo)
        self.txt_segundo_apellido = ft.TextField(label="Segundo Apellido", width=ancho_campo, height=alto_campo, expand=expandir_campo)
        self.txt_telefono = ft.TextField(
            label="Teléfono",
            helper="Ingresa 10 dígitos",
            width=ancho_campo,
            height=alto_campo,
            expand=expandir_campo,
            on_change=self.validar_telefono,
        )
        self.txt_correo = ft.TextField(
            label="Correo electrónico",
            helper="Ejemplo: nombre@correo.com",
            width=ancho_campo,
            height=alto_campo,
            expand=expandir_campo,
            on_change=self.validar_correo_en_tiempo_real,
        )
        self.txt_contrasena = ft.TextField(label="Contraseña", password=True, width=ancho_campo, height=alto_campo, expand=expandir_campo)
        self.txt_confirmar_contrasena = ft.TextField(label="Confirmar contraseña", password=True, width=ancho_campo, height=alto_campo, expand=expandir_campo)
        self.txt_contrasena.can_reveal_password = True
        self.txt_confirmar_contrasena.can_reveal_password = True
        self.txt_contrasena.on_change = self.validar_contrasena
        self.ayuda_contrasena = ft.Text(
            "La contraseña debe tener al menos 8 caracteres.",
            size=12,
            color="#806B63",
        )
        self.txt_error = ft.Text("", color=ft.Colors.RED, size=12)

        self.content = ft.Column(
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
                                ft.ResponsiveRowBreakpoint.MD: 10,
                                ft.ResponsiveRowBreakpoint.LG: 8,
                                ft.ResponsiveRowBreakpoint.XL: 7,
                            },
                            padding=32,
                            bgcolor=ft.Colors.WHITE,
                            border_radius=24,
                            shadow=ft.BoxShadow(
                                blur_radius=18,
                                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                                offset=ft.Offset(0, 6),
                            ),
                            content=ft.Column(
                                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                                spacing=14,
                                controls=[
                                    ft.Icon(
                                        ft.Icons.PERSON_ADD_ALT_1,
                                        size=42,
                                        color="#6A0404",
                                    ),
                                    ft.Text(
                                        "Crear cuenta",
                                        size=28,
                                        weight=ft.FontWeight.BOLD,
                                        color="#6A0404",
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                    ft.ResponsiveRow(
                                        spacing=12,
                                        run_spacing=4,
                                        controls=[
                                            ft.Container(
                                                content=campo,
                                                col={
                                                    ft.ResponsiveRowBreakpoint.XS: 12,
                                                    ft.ResponsiveRowBreakpoint.MD: 6,
                                                },
                                            )
                                            for campo in (
                                                self.txt_nombre,
                                                self.txt_primer_apellido,
                                                self.txt_segundo_apellido,
                                                self.txt_telefono,
                                                self.txt_correo,
                                                self.txt_contrasena,
                                                self.txt_confirmar_contrasena,
                                            )
                                        ],
                                    ),
                                    self.ayuda_contrasena,
                                    self.txt_error,
                                    ft.FilledButton(
                                        "Registrar",
                                        bgcolor="#6A0404",
                                        color=ft.Colors.WHITE,
                                        height=48,
                                        on_click=self.intentar_registro,
                                    ),
                                    ft.TextButton(
                                        "Volver",
                                        on_click=self.on_volver,
                                    ),
                                ],
                            ),
                        )
                    ],
                ),
            ],
        )
        if es_movil:
            self.content = ft.Column(
                [
                    ft.Text("Registrarse", size=24, weight=ft.FontWeight.BOLD),
                    self.txt_nombre,
                    self.txt_primer_apellido,
                    self.txt_segundo_apellido,
                    self.txt_telefono,
                    self.txt_correo,
                    self.txt_contrasena,
                    self.ayuda_contrasena,
                    self.txt_confirmar_contrasena,
                    self.txt_error,
                    ft.FilledButton(
                        "Registrar",
                        bgcolor="#6A0404",
                        color=ft.Colors.WHITE,
                        height=48,
                        on_click=self.intentar_registro,
                    ),
                    ft.TextButton("Volver", on_click=self.on_volver),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                tight=True,
                scroll=ft.ScrollMode.AUTO,
            )

    def intentar_registro(self, e):
        try:
            self.txt_error.value = ""
            url = f"{BASE_URL}/api/registro"
            
            datos_usuario = {
                "nombre": self.txt_nombre.value.strip() if self.txt_nombre.value else "",
                "primer_apellido": self.txt_primer_apellido.value.strip() if self.txt_primer_apellido.value else "",
                "segundo_apellido": self.txt_segundo_apellido.value.strip() if self.txt_segundo_apellido.value else "",
                "telefono": self.txt_telefono.value.strip() if self.txt_telefono.value else "",
                "correo": self.txt_correo.value.strip().lower() if self.txt_correo.value else "",
                "contrasena": self.txt_contrasena.value.strip() if self.txt_contrasena.value else ""
            }

            confirmar_contrasena = self.txt_confirmar_contrasena.value.strip() if self.txt_confirmar_contrasena.value else ""
            errores = []
            campos_obligatorios = (
                ("Nombre", datos_usuario["nombre"]),
                ("Primer apellido", datos_usuario["primer_apellido"]),
                ("Segundo apellido", datos_usuario["segundo_apellido"]),
                ("Teléfono", datos_usuario["telefono"]),
                ("Correo electrónico", datos_usuario["correo"]),
                ("Contraseña", datos_usuario["contrasena"]),
                ("Confirmación de contraseña", confirmar_contrasena),
            )
            faltantes = [nombre for nombre, valor in campos_obligatorios if not valor]
            if faltantes:
                errores.append(f"Completa los siguientes campos: {', '.join(faltantes)}.")
            if datos_usuario["nombre"] and not nombre_valido(datos_usuario["nombre"]):
                errores.append("El nombre solo debe contener letras, espacios, guiones o apóstrofos.")
            if datos_usuario["primer_apellido"] and not nombre_valido(datos_usuario["primer_apellido"]):
                errores.append("El primer apellido solo debe contener letras, espacios, guiones o apóstrofos.")
            if datos_usuario["segundo_apellido"] and not nombre_valido(datos_usuario["segundo_apellido"]):
                errores.append("El segundo apellido solo debe contener letras, espacios, guiones o apóstrofos.")
            if datos_usuario["telefono"] and not telefono_valido(datos_usuario["telefono"]):
                errores.append("El teléfono debe contener exactamente 10 dígitos.")
            if datos_usuario["correo"] and not correo_valido(datos_usuario["correo"]):
                errores.append("Ingresa un correo electrónico válido.")
            if datos_usuario["contrasena"] and len(datos_usuario["contrasena"]) < 8:
                errores.append("La contraseña debe tener al menos 8 caracteres.")
            if (
                datos_usuario["contrasena"]
                and confirmar_contrasena
                and datos_usuario["contrasena"] != confirmar_contrasena
            ):
                errores.append("Las contraseñas no coinciden.")

            if errores:
                self.mostrar_alerta_validacion("\n".join(errores))
                return

            respuesta = requests.post(
                url,
                json=datos_usuario,
                headers={"ngrok-skip-browser-warning": "true"},
                timeout=15,
            )

            if respuesta.status_code == 200:
                datos = respuesta.json()
                token = datos.get("token")
                if not token:
                    self.txt_error.value = (
                        "El servidor debe actualizarse para sincronizar pedidos."
                    )
                    if self.page:
                        self.page.update()
                    return
                self.on_registro_exitoso(
                    datos.get("id"), 
                    datos_usuario["nombre"], 
                    datos_usuario["primer_apellido"],
                    token,
                )
            else:
                try:
                    detalle = respuesta.json().get("detail", "")
                except ValueError:
                    detalle = ""

                detalle_normalizado = str(detalle).casefold()
                correo_duplicado = (
                    respuesta.status_code == 409
                    or "unique constraint failed" in detalle_normalizado
                    and "correo" in detalle_normalizado
                    or "ya existe una cuenta con ese correo" in detalle_normalizado
                )

                if correo_duplicado:
                    alerta = ft.AlertDialog(
                        modal=True,
                        title=ft.Text("Correo ya registrado"),
                        content=ft.Text("Ya existe una cuenta con ese correo. Inicia sesión o usa otro correo."),
                        actions=[
                            ft.TextButton(
                                "Entendido",
                                on_click=lambda e: self.page.pop_dialog(),
                            )
                        ],
                    )
                    if self.page:
                        self.page.show_dialog(alerta)
                    else:
                        self.txt_error.value = "Ya existe una cuenta con ese correo"
                else:
                    self.txt_error.value = "Error al registrar el usuario"
                    if self.page:
                        self.page.update()
        except Exception as ex:
            self.txt_error.value = "No se pudo conectar con el servidor"
            if self.page:
                self.page.update()

    def validar_correo_en_tiempo_real(self, e):
        valor = (e.control.value or "").strip()
        e.control.error_text = (
            "Ingresa un correo electrónico válido."
            if valor and not correo_valido(valor)
            else None
        )
        e.control.update()

    def validar_telefono(self, e):
        valor = (e.control.value or "").strip()
        e.control.error_text = (
            "El teléfono debe contener exactamente 10 dígitos."
            if valor and not telefono_valido(valor)
            else None
        )
        e.control.update()

    def validar_contrasena(self, e):
        valor = e.control.value or ""
        e.control.error_text = (
            "Usa al menos 8 caracteres."
            if valor and len(valor) < 8
            else None
        )
        e.control.update()

    def mostrar_alerta_validacion(self, mensaje):
        self.txt_error.value = mensaje
        try:
            page = self.page
        except RuntimeError:
            page = None
        if page:
            alerta = ft.AlertDialog(
                modal=True,
                title=ft.Text("Revisa los datos"),
                content=ft.Text(mensaje),
                actions=[
                    ft.TextButton("Entendido", on_click=lambda e: page.pop_dialog())
                ],
            )
            page.show_dialog(alerta)