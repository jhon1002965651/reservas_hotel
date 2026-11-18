import os
import time
import mysql.connector

def conectar():
    max_intentos = 3
    for intento in range(max_intentos):
        try:
            conexion = mysql.connector.connect(
                host=os.getenv("DB_HOST_RESERVAS", "db_reservas"),
                port=int(os.getenv("DB_PORT_RESERVAS", 3306)),
                user=os.getenv("DB_USER_RESERVAS", "root"),
                password=os.getenv("DB_PASSWORD_RESERVAS", "root"),
                database=os.getenv("DB_NAME_RESERVAS", "hotel_reservas"),
                connection_timeout=3
            )
            if conexion.is_connected():
                return conexion
        except mysql.connector.Error as err:
            print(
                f"ERROR DE CONEXIÓN A BD RESERVAS (Intento {intento + 1}/{max_intentos}): {err}"
            )
        
       # if intento < max_intentos - 1:
            #time.sleep(1)
            
    return None