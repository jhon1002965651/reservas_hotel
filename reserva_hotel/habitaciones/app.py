from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from database import conectar, inicializar_tabla

app = Flask(__name__)
CORS(app)

# Inicializar la tabla automáticamente al arrancar el servicio
inicializar_tabla()


def formatear_habitacion(hab):
    if hab and "precio" in hab and hab["precio"] is not None:
        hab["precio"] = float(hab["precio"])
    return hab


# 1. OBTENER TODAS LAS HABITACIONES (O FILTRAR POR ESTADO)
@app.route('/habitaciones', methods=['GET'])
def obtener_habitaciones():
    try:
        estado = request.args.get('estado')
        db = conectar()
        if not db:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

        cursor = db.cursor(dictionary=True)
        if estado:
            cursor.execute(
                "SELECT id, numero, tipo, capacidad, precio, estado, descripcion FROM habitaciones WHERE estado = %s ORDER BY numero ASC",
                (estado,)
            )
        else:
            cursor.execute(
                "SELECT id, numero, tipo, capacidad, precio, estado, descripcion FROM habitaciones ORDER BY numero ASC"
            )
        habitaciones = [formatear_habitacion(h) for h in cursor.fetchall()]
        cursor.close()
        db.close()
        return jsonify(habitaciones), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 2. OBTENER UNA HABITACIÓN POR ID
@app.route('/habitaciones/<int:id>', methods=['GET'])
def obtener_habitacion_por_id(id):
    try:
        db = conectar()
        if not db:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, numero, tipo, capacidad, precio, estado, descripcion FROM habitaciones WHERE id = %s",
            (id,)
        )
        habitacion = cursor.fetchone()
        cursor.close()
        db.close()

        if habitacion:
            return jsonify(formatear_habitacion(habitacion)), 200
        return jsonify({"error": "Habitación no encontrada"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 2B. OBTENER UNA HABITACIÓN POR NÚMERO (Para comunicación con microservicio Reservas)
@app.route('/habitaciones/numero/<numero>', methods=['GET'])
def obtener_habitacion_por_numero(numero):
    try:
        db = conectar()
        if not db:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, numero, tipo, capacidad, precio, estado, descripcion FROM habitaciones WHERE numero = %s",
            (str(numero).strip(),)
        )
        habitacion = cursor.fetchone()
        cursor.close()
        db.close()

        if habitacion:
            return jsonify(formatear_habitacion(habitacion)), 200
        return jsonify({"error": f"Habitación {numero} no encontrada"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 3. CREAR / AÑADIR NUEVA HABITACIÓN
@app.route('/habitaciones', methods=['POST'])
def crear_habitacion():
    try:
        datos = request.get_json() or {}
        numero = str(datos.get('numero', '')).strip()
        tipo = str(datos.get('tipo', '')).strip()
        capacidad = datos.get('capacidad', 1)
        precio = datos.get('precio')
        estado = str(datos.get('estado', 'disponible')).strip().lower()
        descripcion = str(datos.get('descripcion', '')).strip()

        if not numero or not tipo or precio is None:
            return jsonify({"error": "Los campos numero, tipo y precio son obligatorios"}), 400

        try:
            capacidad = int(capacidad)
            precio = float(precio)
        except (ValueError, TypeError):
            return jsonify({"error": "Capacidad debe ser entero y precio debe ser numérico"}), 400

        db = conectar()
        if not db:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

        cursor = db.cursor()
        cursor.execute(
            """INSERT INTO habitaciones (numero, tipo, capacidad, precio, estado, descripcion)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (numero, tipo, capacidad, precio, estado, descripcion)
        )
        db.commit()
        habitacion_id = cursor.lastrowid
        cursor.close()
        db.close()

        return jsonify({
            "mensaje": "Habitación creada exitosamente",
            "id": habitacion_id
        }), 201
    except mysql.connector.IntegrityError:
        return jsonify({"error": "Ya existe una habitación con ese número"}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 4. ACTUALIZAR HABITACIÓN POR ID
@app.route('/habitaciones/<int:id>', methods=['PUT'])
def actualizar_habitacion(id):
    try:
        datos = request.get_json() or {}
        numero = datos.get('numero')
        tipo = datos.get('tipo')
        capacidad = datos.get('capacidad')
        precio = datos.get('precio')
        estado = datos.get('estado')
        descripcion = datos.get('descripcion')

        db = conectar()
        if not db:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

        cursor = db.cursor()

        campos = []
        valores = []
        if numero is not None and str(numero).strip() != "":
            campos.append("numero = %s")
            valores.append(str(numero).strip())
        if tipo is not None and str(tipo).strip() != "":
            campos.append("tipo = %s")
            valores.append(str(tipo).strip())
        if capacidad is not None and str(capacidad).strip() != "":
            campos.append("capacidad = %s")
            valores.append(int(capacidad))
        if precio is not None and str(precio).strip() != "":
            campos.append("precio = %s")
            valores.append(float(precio))
        if estado is not None and str(estado).strip() != "":
            campos.append("estado = %s")
            valores.append(str(estado).strip().lower())
        if descripcion is not None:
            campos.append("descripcion = %s")
            valores.append(str(descripcion).strip())

        if not campos:
            return jsonify({"error": "No hay campos para actualizar"}), 400

        valores.append(id)
        sql = f"UPDATE habitaciones SET {', '.join(campos)} WHERE id = %s"
        cursor.execute(sql, tuple(valores))
        db.commit()
        filas = cursor.rowcount
        cursor.close()
        db.close()

        if filas == 0:
            return jsonify({"error": "Habitación no encontrada"}), 404

        return jsonify({"mensaje": "Habitación actualizada exitosamente"}), 200
    except mysql.connector.IntegrityError:
        return jsonify({"error": "Ya existe otra habitación con ese número"}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 4B. ACTUALIZAR ESTADO DE HABITACIÓN POR NÚMERO (Para sincronización con Reservas)
@app.route('/habitaciones/numero/<numero>/estado', methods=['PUT'])
def actualizar_estado_por_numero(numero):
    try:
        datos = request.get_json() or {}
        nuevo_estado = str(datos.get('estado', '')).strip().lower()
        if not nuevo_estado:
            return jsonify({"error": "El campo estado es obligatorio"}), 400

        db = conectar()
        if not db:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

        cursor = db.cursor()
        cursor.execute(
            "UPDATE habitaciones SET estado = %s WHERE numero = %s",
            (nuevo_estado, str(numero).strip())
        )
        db.commit()
        filas = cursor.rowcount
        cursor.close()
        db.close()

        if filas == 0:
            return jsonify({"error": f"Habitación {numero} no encontrada"}), 404

        return jsonify({"mensaje": f"Estado de habitación {numero} actualizado a {nuevo_estado}"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 5. ELIMINAR HABITACIÓN
@app.route('/habitaciones/<int:id>', methods=['DELETE'])
def eliminar_habitacion(id):
    try:
        db = conectar()
        if not db:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

        cursor = db.cursor()
        cursor.execute("DELETE FROM habitaciones WHERE id = %s", (id,))
        db.commit()
        filas_afectadas = cursor.rowcount
        cursor.close()
        db.close()

        if filas_afectadas == 0:
            return jsonify({"error": "Habitación no encontrada"}), 404

        return jsonify({"mensaje": "Habitación eliminada exitosamente"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
