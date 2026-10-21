from db import obtener_conexion

def obtener_todos_medicamentos():
    """Retorna la lista completa de medicamentos registrados en el inventario."""
    conexion = obtener_conexion()
    if not conexion:
        return []
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT *, DATE_FORMAT(fecha_registro, '%Y-%m-%d') as fecha_reg_formato FROM medicamentos ORDER BY id DESC")
        return cursor.fetchall()
    finally:
        cursor.close()
        conexion.close()


def obtener_resumen_dashboard():
    """Calcula el resumen de métricas para el panel del droguero."""
    conexion = obtener_conexion()
    if not conexion:
        return {"total": 0, "agotados": 0, "bajo_stock": 0, "receta": 0}
    try:
        cursor = conexion.cursor(dictionary=True)
        
        cursor.execute("SELECT COUNT(*) AS total FROM medicamentos")
        total = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS agotados FROM medicamentos WHERE stock = 0")
        agotados = cursor.fetchone()["agotados"]

        cursor.execute("SELECT COUNT(*) AS bajo_stock FROM medicamentos WHERE stock > 0 AND stock <= 10")
        bajo_stock = cursor.fetchone()["bajo_stock"]

        cursor.execute("SELECT COUNT(*) AS receta FROM medicamentos WHERE requiere_receta = TRUE")
        receta = cursor.fetchone()["receta"]

        return {
            "total": total,
            "agotados": agotados,
            "bajo_stock": bajo_stock,
            "receta": receta
        }
    finally:
        cursor.close()
        conexion.close()


def guardar_medicamento(nombre, descripcion, imagen_url, presentacion, precio_caja, precio_tableta, precio_unidad, laboratorio, categoria, lote, stock, requiere_receta, fecha_vencimiento, codigo_barras=None, id_medicamento=None):
    """Crea o actualiza un medicamento en el inventario."""
    conexion = obtener_conexion()
    if not conexion:
        return False, "Error de conexión con la base de datos."
    
    if not imagen_url or imagen_url.strip() == "":
        imagen_url = "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=500&auto=format&fit=crop&q=60"

    try:
        cursor = conexion.cursor()
        
        # Verificar duplicados de código de barras
        if codigo_barras and codigo_barras.strip():
            if id_medicamento:
                cursor.execute("SELECT id FROM medicamentos WHERE codigo_barras = %s AND id != %s", (codigo_barras, id_medicamento))
            else:
                cursor.execute("SELECT id FROM medicamentos WHERE codigo_barras = %s", (codigo_barras,))
            if cursor.fetchone():
                return False, f"El código de barras '{codigo_barras}' ya pertenece a otro medicamento registrado."

        if id_medicamento:
            query = """
                UPDATE medicamentos 
                SET codigo_barras=%s, nombre=%s, descripcion=%s, imagen_url=%s, presentacion=%s,
                    precio_caja=%s, precio_tableta=%s, precio_unidad=%s, laboratorio=%s, categoria=%s, 
                    lote=%s, stock=%s, requiere_receta=%s, fecha_vencimiento=%s
                WHERE id=%s
            """
            cursor.execute(query, (
                codigo_barras, nombre, descripcion, imagen_url, presentacion,
                precio_caja, precio_tableta, precio_unidad, laboratorio, categoria,
                lote, stock, requiere_receta, fecha_vencimiento, id_medicamento
            ))
            msg = "Medicamento actualizado correctamente."
        else:
            query = """
                INSERT INTO medicamentos (codigo_barras, nombre, descripcion, imagen_url, presentacion, precio_caja, precio_tableta, precio_unidad, laboratorio, categoria, lote, stock, requiere_receta, fecha_vencimiento)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                codigo_barras, nombre, descripcion, imagen_url, presentacion,
                precio_caja, precio_tableta, precio_unidad, laboratorio, categoria,
                lote, stock, requiere_receta, fecha_vencimiento
            ))
            msg = "Medicamento registrado exitosamente en el inventario."
        
        conexion.commit()
        return True, msg
    except Exception as e:
        return False, f"Error al guardar en la base de datos: {e}"
    finally:
        cursor.close()
        conexion.close()


def eliminar_medicamento(id_medicamento):
    """Elimina un producto del inventario."""
    conexion = obtener_conexion()
    if not conexion:
        return False, "Error de conexión con la base de datos."
    try:
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM medicamentos WHERE id = %s", (id_medicamento,))
        conexion.commit()
        return True, "Medicamento eliminado del inventario."
    except Exception as e:
        return False, f"Error al eliminar: {e}"
    finally:
        cursor.close()
        conexion.close()