from flask import Flask, jsonify, Response, request
import os 
import requests


app = Flask(__name__)
RESERVAS_URL = os.getenv("RESERVAS_URL", "http://reservas:5000")
USUARIOS_URL = os.getenv("USUARIOS_URL", "http://usuarios:5000")


def reenviar(metodo, url):
    try:
        respuesta = requests.request(
            metodo,
            url,
            params=request.args,
            json=request.get_json(silent=True),
            timeout=5
        )
        return Response(
            respuesta.content,
            status=respuesta.status_code,
            content_type=respuesta.headers.get("Content-Type", "application/json")
        )

    except requests.exceptions.Timeout:
        return jsonify({
            "mensaje": "El servicio destino tardó demasiado"
        }), 504

    except requests.exceptions.ConnectionError:
        return jsonify({
            "mensaje": "No fue posible conectar con el servicio destino"
        }), 503


 # --- RUTAS RESERVAS ---   
@app.route("/reservas", methods=["GET", "POST"])
def ruta_reservas():
    return reenviar(request.method, RESERVAS_URL + "/reservas")

@app.route("/reservas/<path:ruta>", methods=["GET", "POST", "PUT", "DELETE"])
def ruta_reserva_detalle(ruta):
    return reenviar(request.method, RESERVAS_URL + "/reservas/" + ruta)

# --- RUTAS USUARIOS ---
@app.route("/usuarios", methods=["GET", "POST"])
def ruta_usuarios():
    return reenviar(request.method, USUARIOS_URL + "/usuarios")

@app.route("/usuarios/<path:ruta>", methods=["GET", "PUT", "DELETE"])
def ruta_usuario_detalle(ruta):
    return reenviar(request.method, USUARIOS_URL + "/usuarios/" + ruta)

# --- LOGIN ---
@app.route("/login", methods=["POST"])
def ruta_login():
    return reenviar(request.method, USUARIOS_URL + "/login")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
