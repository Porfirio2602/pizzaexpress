import flet as ft

def main (page: ft.Page):
    page.title = "Registro de pacientes"
    page.window.width = 480
    page.window.height = 750
    page.scroll = ft.ScrollMode.AUTO
    
    
        # Configuración de región a español
    page.locale_configuration = ft.LocaleConfiguration(
            supported_locales=[
                ft.Locale("es", "ES"),
                ft.Locale("es", "MX"),
            ],
            current_locale=ft.Locale("es", "ES"),
        )
    
    page.appbar = ft.AppBar(
            leading=ft.Icon(ft.Icons.PERSON_2),
            title=ft.Text("Registro de pacientes"),
            bgcolor="Green",
            color="White",
        )

ft.run(main)