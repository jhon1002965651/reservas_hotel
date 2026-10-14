import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from database import conectar

app = Flask(__name__)
CORS(app)

USUARIOS_SERVICE_URL = os.getenv("USUARIOS_SERVICE_URL", "http://usuarios:5000")

# 1. OBTENER TODAS LAS RESERVAS
@app.route('/reservas', methods=['GET'])
def obtener_reservas():
    try:
        db = conectar()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT id, habitacion, usuario_id, DATE_FORMAT(fecha_reserva, '%Y-%m-%d') as fecha_reserva, estado FROM reservas")
        reservas = cursor.fetchall()
        cursor.close()
        db.close()
        return jsonify(reservas), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 2. OBTENER RESERVAS DE UN CLIENTE ESPECÍFICO (Por Documento)
@app.route('/reservas/usuario/<usuario_id>', methods=['GET'])
def obtener_reservas_usuario(usuario_id):
    try:
        db = conectar()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT id, habitacion, usuario_id, DATE_FORMAT(fecha_reserva, '%Y-%m-%d') as fecha_reserva, estado FROM reservas WHERE usuario_id = %s", (usuario_id,))
        reservas = cursor.fetchall()
        cursor.close()
        db.close()
        return jsonify(reservas), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 3. CREAR NUEVA RESERVA
@app.route('/reservas', methods=['POST'])
def crear_reserva():
    try:
        datos = request.get_json()
        habitacion = datos.get('habitacion')
        usuario_id = str(datos.get('usuario_id')).strip()
        fecha_reserva = datos.get('fecha_reserva')
        estado = datos.get('estado', 'confirmada')

        if not habitacion or not usuario_id or not fecha_reserva:
            return jsonify({"error": "Habitación, usuario_id y fecha_reserva son obligatorios"}), 400

        db = conectar()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO reservas (habitacion, usuario_id, fecha_reserva, estado) VALUES (%s, %s, %s, %s)",
            (habitacion, usuario_id, fecha_reserva, estado)
        )
        db.commit()
        reserva_id = cursor.lastrowid
        cursor.close()
        db.close()
        return jsonify({"mensaje": "Reserva creada exitosamente", "id": reserva_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 4. ACTUALIZAR ESTADO DE LA RESERVA (Para Administradores)
@app.route('/reservas/<int:id>/estado', methods=['PUT'])
def actualizar_estado(id):
    try:
        datos = request.get_json()
        nuevo_estado = datos.get('estado')

        if not nuevo_estado:
            return jsonify({"error": "El nuevo estado es obligatorio"}), 400

        db = conectar()
        cursor = db.cursor()
        cursor.execute("UPDATE reservas SET estado = %s WHERE id = %s", (nuevo_estado, id))
        db.commit()
        cursor.close()
        db.close()
        return jsonify({"mensaje": "Estado de reserva actualizado"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 5. CONSULTA DISTRIBUIDA (Detalles consolidados)
@app.route('/reservas/<int:id>/detalles', methods=['GET'])
def detalles_reserva(id):
    try:
        db = conectar()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT id, habitacion, usuario_id, DATE_FORMAT(fecha_reserva, '%Y-%m-%d') as fecha_reserva, estado FROM reservas WHERE id = %s", (id,))
        reserva = cursor.fetchone()
        cursor.close()
        db.close()

        if not reserva:
            return jsonify({"error": "Reserva no encontrada"}), 404

        # Petición HTTP interna al microservicio de Usuarios
        resp = requests.get(f"{USUARIOS_SERVICE_URL}/usuarios/{reserva['usuario_id']}")
        if resp.status_code == 200:
            usuario = resp.json()
            reserva['cliente'] = f"{usuario['nombre']} ({usuario['correo']})"
        else:
            reserva['cliente'] = "Cliente desconocido"

        return jsonify(reserva), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 6. ELIMINAR RESERVA
@app.route('/reservas/<int:id>', methods=['DELETE'])
def eliminar_reserva(id):
    try:
        db = conectar()
        cursor = db.cursor()
        cursor.execute("DELETE FROM reservas WHERE id = %s", (id,))
        db.commit()
        cursor.close()
        db.close()
        return jsonify({"mensaje": "Reserva eliminada exitosamente"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)