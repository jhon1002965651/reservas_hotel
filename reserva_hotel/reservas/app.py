import os
import requests
import pybreaker
from flask import Flask, request, jsonify
from flask_cors import CORS
from database import conectar

app = Flask(__name__)
CORS(app)

USUARIOS_SERVICE_URL = os.getenv("USUARIOS_SERVICE_URL", "http://usuarios:5000")

circuito_usuarios = pybreaker.CircuitBreaker(fail_max=int(os.getenv("CB_MAX_FALLOS", "3")), reset_timeout=int(os.getenv("CB_RECUPERACION", "30")), throw_new_error_on_trip=False)

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


@app.route("/reservas/<int:id>/detalles", methods=["GET"])
def detalles_reserva(id):
    tiempo_maximo = float(os.getenv("USUARIOS_TIMEOUT", "2"))
    
    conexion = conectar()
    if not conexion:
        return jsonify({"mensaje": "No se pudo conectar a la base de datos"}), 500

    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT * FROM reservas WHERE id = %s", (id,))
    reserva = cursor.fetchone()
    cursor.close()
    conexion.close()

    if reserva is None:
        return jsonify({"mensaje": "Reserva no encontrada"}), 404

    usuario_id = reserva["usuario_id"]
    url = f"{USUARIOS_SERVICE_URL}/usuarios/{usuario_id}"

    try:
        with circuito_usuarios.calling():
            respuesta = requests.get(url, timeout=tiempo_maximo)
            if respuesta.status_code >= 500:
                respuesta.raise_for_status()
    except pybreaker.CircuitBreakerError:
        return jsonify({"mensaje": "Circuito abierto. Servicio de usuarios no disponible"}), 503
    except requests.exceptions.Timeout:
        return jsonify({"mensaje": "El servicio de usuarios no responde"}), 504
    except requests.exceptions.ConnectionError:
        return jsonify({"mensaje": "No se pudo conectar con el servicio de usuarios"}), 503
    except requests.exceptions.HTTPError:
        return jsonify({"mensaje": "Error en el servicio de usuarios"}), 502

    if respuesta.status_code == 404:
        return jsonify({"mensaje": "Usuario no encontrado"}), 404
    if respuesta.status_code != 200:
        return jsonify({"mensaje": "Error en el servicio de usuarios"}), 502

    usuario = respuesta.json()

    # Formato de campos tipo fecha a string para prevenir fallos al serializar JSON
    if "fecha_reserva" in reserva and reserva["fecha_reserva"] is not None:
        reserva["fecha_reserva"] = str(reserva["fecha_reserva"])

    return jsonify({
        "reserva": reserva,
        "usuario": usuario
    }), 200

@app.route("/reservas/circuito/usuarios", methods=["GET"])
def estado_circuito_usuarios():
    return jsonify({
        "estado": circuito_usuarios.current_state.upper(),
        "fallos_consecutivos": circuito_usuarios.fail_counter,
        "max_fallos_permitidos": circuito_usuarios.fail_max,
        "periodo_recuperacion": circuito_usuarios.reset_timeout
    }), 200
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)