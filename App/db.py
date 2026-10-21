import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

# Cargar las variables de entorno del archivo .env
load_dotenv()

def obtener_conexion():
    """Establece y retorna una conexión a la base de datos MySQL."""
    try:
        conexion = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "drogueria_db")
        )
        if conexion.is_connected():
            return conexion
    except Error as e:
        print(f"Error de conexión a MySQL: {e}")
        return None