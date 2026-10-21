import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

def enviar_correo(destino, asunto, contenido_html):
    remitente = os.getenv("MAIL_USERNAME")
    password = os.getenv("MAIL_PASSWORD")

    if not remitente or not password:
        print("Error: Credenciales de correo no configuradas en el .env")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = asunto
    msg["From"] = f"Medilink Droguería <{remitente}>"
    msg["To"] = destino

    parte_html = MIMEText(contenido_html, "html")
    msg.attach(parte_html)

    try:
        puerto = int(os.getenv("MAIL_PORT", 465))
        servidor = os.getenv("MAIL_SERVER", "smtp.gmail.com")
        contexto = ssl.create_default_context()

        # Conexión directa mediante SSL (Puerto 465)
        if puerto == 465:
            with smtplib.SMTP_SSL(servidor, puerto, context=contexto) as server:
                server.login(remitente, password)
                server.sendmail(remitente, destino, msg.as_string())
        else:
            with smtplib.SMTP(servidor, puerto) as server:
                server.starttls(context=contexto)
                server.login(remitente, password)
                server.sendmail(remitente, destino, msg.as_string())

        return True
    except Exception as e:
        print(f"Error al enviar correo: {e}")
        return False


def enviar_correo_bienvenida(destino, nombre):
    asunto = "¡Bienvenido a Medilink! 💊"
    html = f"""
    <div style="font-family: Arial, sans-serif; padding: 25px; color: #1E293B; max-width: 500px; border: 1px solid #E2E8F0; border-radius: 12px;">
        <h2 style="color: #0284C7; margin-top: 0;">¡Hola, {nombre}! 👋</h2>
        <p>Tu cuenta en <strong>Medilink Droguería</strong> se ha creado exitosamente.</p>
        <p>Ya puedes acceder a nuestra plataforma para realizar pedidos, explorar medicamentos y gestionar tu información.</p>
        <hr style="border: none; border-top: 1px solid #E2E8F0; margin: 20px 0;">
        <p style="font-size: 0.8rem; color: #64748B;">Mensaje automático enviado por Medilink. No respondas a este correo.</p>
    </div>
    """
    return enviar_correo(destino, asunto, html)


def enviar_correo_recuperacion(destino, nombre, token):
    link = f"http://127.0.0.1:5000/restablecer-password/{token}"
    asunto = "Recuperación de Contraseña - Medilink 💊"
    html = f"""
    <div style="font-family: Arial, sans-serif; padding: 25px; color: #1E293B; max-width: 500px; border: 1px solid #E2E8F0; border-radius: 12px;">
        <h2 style="color: #0284C7; margin-top: 0;">Restablecer Contraseña</h2>
        <p>Hola {nombre}, recibimos una solicitud para restablecer la contraseña de tu cuenta en Medilink.</p>
        <p>Haz clic en el botón para ingresar tu nueva contraseña (este enlace es válido durante 1 hora):</p>
        <div style="text-align: center; margin: 25px 0;">
            <a href="{link}" style="background-color: #0284C7; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">Restablecer Contraseña</a>
        </div>
        <p style="font-size: 0.85rem; color: #64748B;">Si no solicitaste este cambio, puedes ignorar este mensaje.</p>
    </div>
    """
    return enviar_correo(destino, asunto, html)