from flask import Flask, render_template, request, redirect, url_for, session, flash
from auth import (registrar_cliente, iniciar_sesion, solicitar_recuperacion, 
                  restablecer_contrasena_con_token, obtener_usuario_por_id, actualizar_perfil_usuario)
from email_service import enviar_correo_bienvenida, enviar_correo_recuperacion
from inventario import (obtener_todos_medicamentos, obtener_resumen_dashboard, guardar_medicamento, eliminar_medicamento)
import os
import re
import uuid
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "clave_secreta_medilink_2026")

UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
UPLOAD_PERFILES = os.path.join(app.root_path, 'static', 'uploads', 'perfiles')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_PERFILES, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['UPLOAD_PERFILES'] = UPLOAD_PERFILES


def limpiar_precio(valor_str):
    """Extrae únicamente los dígitos de una cadena ($ 10.000 -> 10000.0)."""
    if not valor_str:
        return 0.0
    numeros = re.sub(r'[^\d]', '', str(valor_str))
    return float(numeros) if numeros else 0.0


@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if "usuario_id" in session:
        return redirigir_segun_rol(session.get("rol"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        usuario, mensaje = iniciar_sesion(email, password)

        if usuario:
            session["usuario_id"] = usuario["id"]
            session["nombre"] = usuario["nombre_completo"]
            session["email"] = usuario["email"]
            session["rol"] = usuario["rol"]
            session["foto_perfil"] = usuario["foto_perfil"]
            return redirigir_segun_rol(usuario["rol"])
        else:
            flash(mensaje, "danger")

    return render_template("login.html")


@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        nombre = request.form.get("nombre")
        email = request.form.get("email")
        telefono = request.form.get("telefono")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if password != confirm_password:
            flash("Las contraseñas no coinciden.", "warning")
            return render_template("registro.html")

        exito, mensaje = registrar_cliente(nombre, email, telefono, password)

        if exito:
            enviar_correo_bienvenida(email, nombre)
            flash("¡Cuenta creada exitosamente! Te hemos enviado un correo de bienvenida.", "success")
            return redirect(url_for("login"))
        else:
            flash(mensaje, "danger")

    return render_template("registro.html")


@app.route("/olvide-password", methods=["GET", "POST"])
def olvide_password():
    if request.method == "POST":
        email = request.form.get("email")
        datos_rec, mensaje = solicitar_recuperacion(email)

        if datos_rec:
            enviar_correo_recuperacion(datos_rec["email"], datos_rec["nombre"], datos_rec["token"])

        flash("Si el correo electrónico está registrado, recibirás las instrucciones.", "info")
        return redirect(url_for("login"))

    return render_template("olvide.html")


@app.route("/restablecer-password/<token>", methods=["GET", "POST"])
def restablecer_password(token):
    if request.method == "POST":
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if password != confirm_password:
            flash("Las contraseñas no coinciden.", "warning")
            return render_template("restablecer.html", token=token)

        exito, mensaje = restablecer_contrasena_con_token(token, password)

        if exito:
            flash("¡Contraseña actualizada exitosamente! Ya puedes iniciar sesión.", "success")
            return redirect(url_for("login"))
        else:
            flash(mensaje, "danger")

    return render_template("restablecer.html", token=token)


@app.route("/cliente/inicio")
def dashboard_cliente():
    if "usuario_id" not in session or session.get("rol") != "cliente":
        return redirect(url_for("login"))
    return render_template("dashboard_cliente.html", nombre=session.get("nombre"))


@app.route("/droguero/inicio")
def dashboard_droguero():
    if "usuario_id" not in session or session.get("rol") != "droguero":
        flash("Acceso denegado. No tienes permisos de Droguero.", "danger")
        return redirect(url_for("login"))
    
    medicamentos = obtener_todos_medicamentos()
    usuario = obtener_usuario_por_id(session.get("usuario_id"))
    
    return render_template(
        "dashboard_droguero.html", 
        nombre=usuario["nombre_completo"],
        email=usuario["email"],
        foto_perfil=usuario["foto_perfil"],
        medicamentos=medicamentos
    )


@app.route("/perfil", methods=["GET", "POST"])
def perfil():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    usuario_id = session["usuario_id"]

    if request.method == "POST":
        nombre = request.form.get("nombre_completo")
        telefono = request.form.get("telefono")
        nombre_establecimiento = request.form.get("nombre_establecimiento")
        departamento = request.form.get("departamento")
        municipio = request.form.get("municipio")
        
        nueva_password = request.form.get("nueva_password")
        confirmar_password = request.form.get("confirmar_password")

        if nueva_password and nueva_password.strip():
            if nueva_password != confirmar_password:
                flash("Las contraseñas no coinciden.", "warning")
                usuario = obtener_usuario_por_id(usuario_id)
                return render_template("perfil.html", usuario=usuario)

        foto_file = request.files.get("foto_perfil")
        ruta_foto = None

        if foto_file and foto_file.filename != "":
            nombre_orig = secure_filename(foto_file.filename)
            ext = os.path.splitext(nombre_orig)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png', '.webp']:
                nuevo_nombre = f"avatar_usr_{usuario_id}_{uuid.uuid4().hex[:8]}{ext}"
                dest = os.path.join(app.config['UPLOAD_PERFILES'], nuevo_nombre)
                foto_file.save(dest)
                ruta_foto = url_for('static', filename=f'uploads/perfiles/{nuevo_nombre}')

        exito, mensaje = actualizar_perfil_usuario(
            usuario_id, nombre, telefono, nombre_establecimiento, 
            departamento, municipio, ruta_foto, nueva_password
        )

        if exito:
            session["nombre"] = nombre
            if ruta_foto:
                session["foto_perfil"] = ruta_foto
            flash("¡Perfil actualizado correctamente!", "success")
        else:
            flash(mensaje, "danger")

        return redirect(url_for("perfil"))

    usuario = obtener_usuario_por_id(usuario_id)
    return render_template("perfil.html", usuario=usuario)


@app.route("/droguero/medicamento/guardar", methods=["POST"])
def guardar_producto():
    if "usuario_id" not in session or session.get("rol") != "droguero":
        return redirect(url_for("login"))

    id_med = request.form.get("id")
    codigo = request.form.get("codigo_barras")
    nombre = request.form.get("nombre")
    descripcion = request.form.get("descripcion")
    presentacion = request.form.get("presentacion") or "Unidad"
    
    imagen_file = request.files.get("imagen_file")
    imagen_url = request.form.get("imagen_url_actual") or ""

    if imagen_file and imagen_file.filename != "":
        nombre_original = secure_filename(imagen_file.filename)
        extension = os.path.splitext(nombre_original)[1].lower()
        if extension in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
            nuevo_nombre = f"{uuid.uuid4().hex}{extension}"
            ruta_guardado = os.path.join(app.config['UPLOAD_FOLDER'], nuevo_nombre)
            imagen_file.save(ruta_guardado)
            imagen_url = url_for('static', filename=f'uploads/{nuevo_nombre}')

    precio_caja = limpiar_precio(request.form.get("precio_caja"))
    precio_tableta = limpiar_precio(request.form.get("precio_tableta"))
    precio_unidad = limpiar_precio(request.form.get("precio_unidad"))
    
    laboratorio = request.form.get("laboratorio")
    categoria = request.form.get("categoria")
    lote = request.form.get("lote")
    stock = int(limpiar_precio(request.form.get("stock")))
    requiere_receta = True if request.form.get("requiere_receta") == "on" else False
    fecha_vencimiento = request.form.get("fecha_vencimiento")

    exito, mensaje = guardar_medicamento(
        nombre, descripcion, imagen_url, presentacion, 
        precio_caja, precio_tableta, precio_unidad, 
        laboratorio, categoria, lote, stock, 
        requiere_receta, fecha_vencimiento, codigo, id_med
    )

    if exito:
        flash(mensaje, "success")
    else:
        flash(mensaje, "danger")

    return redirect(url_for("dashboard_droguero"))


@app.route("/droguero/medicamento/eliminar/<int:id_med>", methods=["POST"])
def borrar_producto(id_med):
    if "usuario_id" not in session or session.get("rol") != "droguero":
        return redirect(url_for("login"))

    exito, mensaje = eliminar_medicamento(id_med)
    if exito:
        flash(mensaje, "info")
    else:
        flash(mensaje, "danger")

    return redirect(url_for("dashboard_droguero"))


@app.route("/logout")
def logout():
    session.clear()
    flash("Has cerrado sesión correctamente.", "info")
    return redirect(url_for("login"))


def redirigir_segun_rol(rol):
    if rol == "droguero":
        return redirect(url_for("dashboard_droguero"))
    return redirect(url_for("dashboard_cliente"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)