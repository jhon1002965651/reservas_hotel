import mysql.connector
import os 
import time 

def conectar():
    for intento in range(10):
        try: 
            conexion = mysql.connector.connect(
                host = os.getenv("DB_HOST_RESERVAS", "mysql_reservas"),
                port = int(os.getenv("DB_PORT_RESERVAS", 3306)),
                user = os.getenv("DB_USER_RESERVAS", "root"),
                password = os.getenv("DB_PASSWORD_RESERVAS", "root"),
                database = os.getenv("DB_NAME_RESERVAS", "db_reservas")
            )
            return conexion 
        except mysql.connector.Error:
            print("La base de datos de reservas aún está cargando...")
            time.sleep(3)