import bcrypt
import re
import secrets
from datetime import datetime, timedelta
from db import obtener_conexion

def validar_contrasena_fuerte(password):
    """Valida los requisitos mínimos de seguridad para la contraseña."""
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres."
    if not re.search(r'[A-Z]', password):
        return False, "La contraseña debe incluir al menos una letra mayúscula."
    if not re.search(r'[0-9]', password):
        return False, "La contraseña debe incluir al menos un número."
    if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-]', password):
        return False, "La contraseña debe incluir al menos un símbolo especial ($ . _ - # @ !)."
    return True, ""


def registrar_cliente(nombre_completo, email, telefono, password):
    """Registra un nuevo usuario con rol predeterminado de 'cliente' (id_rol = 1)."""
    es_valida, mensaje_val = validar_contrasena_fuerte(password)
    if not es_valida:
        return False, mensaje_val

    conexion = obtener_conexion()
    if not conexion:
        return False, "Error de conexión con la base de datos."
    
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
        if cursor.fetchone():
            return False, "El correo electrónico ya está registrado."
        
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        
        query = """
            INSERT INTO usuarios (nombre_completo, email, telefono, password_hash, id_rol) 
            VALUES (%s, %s, %s, %s, 1)
        """
        cursor.execute(query, (nombre_completo, email, telefono, password_hash))
        conexion.commit()
        
        return True, "Cuenta creada exitosamente."
    except Exception as e:
        return False, f"Error al registrar: {e}"
    finally:
        cursor.close()
        conexion.close()


def iniciar_sesion(email, password):
    """Verifica credenciales y retorna el perfil del usuario incluyendo su rol."""
    conexion = obtener_conexion()
    if not conexion:
        return None, "Error de conexión con la base de datos."
    
    try:
        cursor = conexion.cursor(dictionary=True)
        query = """
            SELECT u.id, u.nombre_completo, u.email, u.telefono, u.password_hash, u.activo, 
                   u.foto_perfil, u.nombre_establecimiento, u.departamento, u.municipio, r.nombre AS rol
            FROM usuarios u
            JOIN roles r ON u.id_rol = r.id
            WHERE u.email = %s
        """
        cursor.execute(query, (email,))
        usuario = cursor.fetchone()
        
        if not usuario:
            return None, "Correo o contraseña incorrectos."
        
        if not usuario['activo']:
            return None, "Esta cuenta ha sido desactivada."
        
        if bcrypt.checkpw(password.encode('utf-8'), usuario['password_hash'].encode('utf-8')):
            del usuario['password_hash']
            return usuario, "Inicio de sesión correcto."
        else:
            return None, "Correo o contraseña incorrectos."
    except Exception as e:
        return None, f"Error en el servidor: {e}"
    finally:
        cursor.close()
        conexion.close()


def obtener_usuario_por_id(id_usuario):
    """Consulta la información completa del perfil de un usuario."""
    conexion = obtener_conexion()
    if not conexion:
        return None
    try:
        cursor = conexion.cursor(dictionary=True)
        query = """
            SELECT u.id, u.nombre_completo, u.email, u.telefono, u.foto_perfil, 
                   u.nombre_establecimiento, u.departamento, u.municipio, r.nombre AS rol
            FROM usuarios u
            JOIN roles r ON u.id_rol = r.id
            WHERE u.id = %s
        """
        cursor.execute(query, (id_usuario,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conexion.close()


def actualizar_perfil_usuario(id_usuario, nombre_completo, telefono, nombre_establecimiento, departamento, municipio, foto_perfil=None, nueva_password=None):
    """Actualiza la información personal, la foto del perfil y opcionalmente la contraseña del usuario."""
    conexion = obtener_conexion()
    if not conexion:
        return False, "Error de conexión con la base de datos."
    
    try:
        cursor = conexion.cursor()
        campos = ["nombre_completo=%s", "telefono=%s", "nombre_establecimiento=%s", "departamento=%s", "municipio=%s"]
        valores = [nombre_completo, telefono, nombre_establecimiento, departamento, municipio]

        if foto_perfil:
            campos.append("foto_perfil=%s")
            valores.append(foto_perfil)

        if nueva_password and nueva_password.strip():
            es_valida, msg_val = validar_contrasena_fuerte(nueva_password)
            if not es_valida:
                return False, msg_val
            salt = bcrypt.gensalt()
            password_hash = bcrypt.hashpw(nueva_password.encode('utf-8'), salt).decode('utf-8')
            campos.append("password_hash=%s")
            valores.append(password_hash)

        valores.append(id_usuario)
        query = f"UPDATE usuarios SET {', '.join(campos)} WHERE id=%s"
        cursor.execute(query, tuple(valores))
        
        conexion.commit()
        return True, "Perfil actualizado exitosamente."
    except Exception as e:
        return False, f"Error al actualizar el perfil: {e}"
    finally:
        cursor.close()
        conexion.close()


def solicitar_recuperacion(email):
    """Genera token de recuperación con expiración de 1 hora."""
    conexion = obtener_conexion()
    if not conexion:
        return None, "Error de conexión con la base de datos."
    
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT id, nombre_completo, email FROM usuarios WHERE email = %s", (email,))
        usuario = cursor.fetchone()

        if not usuario:
            return None, "Si el correo está registrado, recibirás las instrucciones."

        token = secrets.token_urlsafe(32)
        expiracion = datetime.now() + timedelta(hours=1)

        cursor.execute("""
            UPDATE usuarios 
            SET token_recuperacion = %s, token_expiracion = %s 
            WHERE email = %s
        """, (token, expiracion, email))
        conexion.commit()

        return {
            "nombre": usuario["nombre_completo"],
            "email": usuario["email"],
            "token": token
        }, "Token generado."
    finally:
        cursor.close()
        conexion.close()


def restablecer_contrasena_con_token(token, nueva_password):
    """Valida token y actualiza la contraseña."""
    es_valida, mensaje_val = validar_contrasena_fuerte(nueva_password)
    if not es_valida:
        return False, mensaje_val

    conexion = obtener_conexion()
    if not conexion:
        return False, "Error de conexión."

    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT id FROM usuarios 
            WHERE token_recuperacion = %s AND token_expiracion > NOW()
        """, (token,))
        usuario = cursor.fetchone()

        if not usuario:
            return False, "El enlace de recuperación es inválido o ha expirado."

        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(nueva_password.encode('utf-8'), salt).decode('utf-8')

        cursor.execute("""
            UPDATE usuarios 
            SET password_hash = %s, token_recuperacion = NULL, token_expiracion = NULL 
            WHERE id = %s
        """, (password_hash, usuario["id"]))
        conexion.commit()

        return True, "Contraseña actualizada exitosamente."
    finally:
        cursor.close()
        conexion.close()