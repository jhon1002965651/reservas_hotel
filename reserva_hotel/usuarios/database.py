import mysql.connector
import os 
import time 

def conectar():
    for intento in range(10):
        try: 
            conexion = mysql.connector.connect(
                host = os.getenv("DB_HOST_USUARIOS", "mysql_usuarios"),
                port = int(os.getenv("DB_PORT_USUARIOS", 3306)),
                user = os.getenv("DB_USER_USUARIOS", "root"),
                password = os.getenv("DB_PASSWORD_USUARIOS", "root"),
                database = os.getenv("DB_NAME_USUARIOS", "db_usuarios")
            )
            return conexion 
        except mysql.connector.Error:
            print("La base de datos de usuarios aún está cargando...")
            time.sleep(3)