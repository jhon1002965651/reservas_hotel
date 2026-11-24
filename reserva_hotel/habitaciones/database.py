import mysql.connector
import os 
import time 

def conectar():
    for intento in range(10):
        try: 
            conexion = mysql.connector.connect(
                host = os.getenv("DB_HOST_HABITACIONES", "mysql_habitaciones"),
                port = int(os.getenv("DB_PORT_HABITACIONES", 3306)),
                user = os.getenv("DB_USER_HABITACIONES", "root"),
                password = os.getenv("DB_PASSWORD_HABITACIONES", "root"),
                database = os.getenv("DB_NAME_HABITACIONES", "db_habitaciones")
            )

            return conexion 
        except mysql.connector.Error:
            print("La base de datos de habitaciones aún está cargando...")


def inicializar_tabla():
    db = conectar()
    if not db:
        print("No se pudo conectar a MySQL para inicializar la tabla habitaciones.")
        return