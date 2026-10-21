import os
import smtplib
import ssl
from dotenv import load_dotenv

load_dotenv(override=True)

user = os.getenv("MAIL_USERNAME")
# Limpiamos espacios que puedan quedar en la clave de aplicación
password = os.getenv("MAIL_PASSWORD", "").replace(" ", "")

print("=== DIAGNÓSTICO AVANZADO DE RED Y GMAIL ===")
print(f"Usuario: {user}")
print(f"Longitud de clave: {len(password)} caracteres\n")

# 1. Intentar Puerto 587 (STARTTLS - Recomendado para Windows/Antivirus)
print("--> Intentando Puerto 587 (STARTTLS)...")
try:
    context = ssl.create_default_context()
    with smtplib.SMTP("smtp.gmail.com", 587, timeout=12) as server:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(user, password)
        print(" SUCCESS: ¡Conexión exitosa por el Puerto 587! 🎉")
except Exception as e:
    print(f"❌ Falló Puerto 587: {type(e).__name__} -> {e}\n")

# 2. Intentar Puerto 465 (SSL Directo)
print("--> Intentando Puerto 465 (SSL Directo)...")
try:
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context, timeout=12) as server:
        server.login(user, password)
        print(" SUCCESS: ¡Conexión exitosa por el Puerto 465! 🎉")
except Exception as e:
    print(f"❌ Falló Puerto 465: {type(e).__name__} -> {e}\n")