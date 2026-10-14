import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from database import conectar

app = Flask(__name__)
CORS(app)

# 1. OBTENER TODOS LOS USUARIOS
@app.route('/usuarios', methods=['GET'])
def obtener_usuarios():
    try:
        db = conectar()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT id, nombre, correo, rol FROM usuarios")
        usuarios = cursor.fetchall()
        cursor.close()
        db.close()
        return jsonify(usuarios), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 2. OBTENER UN USUARIO POR SU DOCUMENTO DE IDENTIDAD (ID)
@app.route('/usuarios/<id>', methods=['GET'])
def obtener_usuario_por_id(id):
    try:
        db = conectar()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT id, nombre, correo, rol FROM usuarios WHERE id = %s", (id,))
        usuario = cursor.fetchone()
        cursor.close()
        db.close()
        if usuario:
            return jsonify(usuario), 200
        return jsonify({"error": "Usuario no encontrado"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 3. CREAR NUEVO USUARIO (Con Documento, Contraseña y Rol)
@app.route('/usuarios', methods=['POST'])
def crear_usuario():
    try:
        datos = request.get_json()
        doc_id = str(datos.get('id')).strip()
        nombre = datos.get('nombre')
        correo = datos.get('correo')
        contrasena = datos.get('contrasena')
        rol = datos.get('rol', 'cliente')

        if not doc_id or not nombre or not correo or not contrasena:
            return jsonify({"error": "Faltan campos obligatorios (id, nombre, correo, contrasena)"}), 400

        db = conectar()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO usuarios (id, nombre, correo, contrasena, rol) VALUES (%s, %s, %s, %s, %s)",
            (doc_id, nombre, correo, contrasena, rol)
        )
        db.commit()
        cursor.close()
        db.close()
        return jsonify({"mensaje": "Usuario creado exitosamente", "id": doc_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 4. INICIO DE SESIÓN (LOGIN)
@app.route('/login', methods=['POST'])
def login():
    try:
        datos = request.get_json()
        correo = datos.get('correo')
        contrasena = datos.get('contrasena')

        if not correo or not contrasena:
            return jsonify({"error": "Correo y contraseña obligatorios"}), 400

        db = conectar()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, nombre, correo, rol FROM usuarios WHERE correo = %s AND contrasena = %s",
            (correo, contrasena)
        )
        usuario = cursor.fetchone()
        cursor.close()
        db.close()

        if usuario:
            return jsonify({"mensaje": "Login exitoso", "usuario": usuario}), 200
        else:
            return jsonify({"error": "Credenciales inválidas"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 5. ACTUALIZAR USUARIO O ROL
@app.route('/usuarios/<id>', methods=['PUT'])
def actualizar_usuario(id):
    try:
        datos = request.get_json()
        nombre = datos.get('nombre')
        correo = datos.get('correo')
        rol = datos.get('rol')
        contrasena = datos.get('contrasena')

        db = conectar()
        cursor = db.cursor()
        
        campos = []
        valores = []
        if nombre:
            campos.append("nombre = %s")
            valores.append(nombre)
        if correo:
            campos.append("correo = %s")
            valores.append(correo)
        if rol:
            campos.append("rol = %s")
            valores.append(rol)
        if contrasena:
            campos.append("contrasena = %s")
            valores.append(contrasena)

        if not campos:
            return jsonify({"error": "No hay campos para actualizar"}), 400

        valores.append(id)
        sql = f"UPDATE usuarios SET {', '.join(campos)} WHERE id = %s"
        cursor.execute(sql, tuple(valores))
        db.commit()
        cursor.close()
        db.close()
        return jsonify({"mensaje": "Usuario actualizado exitosamente"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 6. ELIMINAR USUARIO
@app.route('/usuarios/<id>', methods=['DELETE'])
def eliminar_usuario(id):
    try:
        db = conectar()
        cursor = db.cursor()
        cursor.execute("DELETE FROM usuarios WHERE id = %s", (id,))
        db.commit()
        cursor.close()
        db.close()
        return jsonify({"mensaje": "Usuario eliminado exitosamente"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)