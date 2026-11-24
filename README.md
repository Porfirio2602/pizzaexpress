# pizzaexpress

## Restablecimiento de contraseña

El API envía un código de confirmación de 6 letras por SMTP al correo
registrado en una cuenta. Configura estas variables
de entorno en el servidor:

- `SMTP_HOST`: servidor SMTP.
- `SMTP_PORT`: puerto SMTP (587 para STARTTLS o 465 para SSL).
- `SMTP_USER` y `SMTP_PASSWORD`: credenciales SMTP.
- `SMTP_FROM`: remitente visible (opcional; por defecto usa `SMTP_USER`).

El código vence después de 3 minutos y permite hasta 5 intentos. Tras
verificarlo, la aplicación abre la pantalla para crear la contraseña nueva.
