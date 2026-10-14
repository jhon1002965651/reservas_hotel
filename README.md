# reservas_hotel
# Hotel Grand Plaza — Sistema de Reservas Distribuido

## Problema que resuelve

La gestión de reservas de un hotel suele depender de procesos manuales: no hay un registro central de clientes, las reservas se pierden o se duplican y el personal no puede consultar ni cambiar el estado de una reserva fácilmente. Este proyecto propone un sistema distribuido, dividido en microservicios independientes, donde:

- Los **clientes** inician sesión, crean y consultan sus reservas.
- Los **administradores** ven todas las reservas y cambian su estado (confirmada, pagada, cancelada).
- Los **administradores del sistema (sysadmin)** gestionan las cuentas de usuario y sus roles.

## Servicios implementados

| Servicio | Puerto host | Responsabilidad | Base de datos |
| --- | --- | --- | --- |
| Usuarios | 5001 | Cuentas, login y roles | MySQL `db_usuarios` (puerto 3310) |
| Reservas | 5002 | Reservas de habitaciones y su estado | MySQL `db_reservas` (puerto 3309) |
| Home | (archivo estático) | Interfaz web que consume ambas APIs | — |

## Endpoints

**Usuarios** (`http://localhost:5001`)

| Método | Endpoint | Descripción |
| --- | --- | --- |
| GET | /usuarios | Listar usuarios |
| GET | /usuarios/{id} | Consultar usuario por documento |
| POST | /usuarios | Crear usuario |
| PUT | /usuarios/{id} | Actualizar nombre, correo, rol o contraseña |
| DELETE | /usuarios/{id} | Eliminar usuario |
| POST | /login | Iniciar sesión |

**Reservas** (`http://localhost:5002`)

| Método | Endpoint | Descripción |
| --- | --- | --- |
| GET | /reservas | Listar todas las reservas |
| GET | /reservas/usuario/{usuario_id} | Reservas de un cliente |
| GET | /reservas/{id}/detalles | Reserva + datos del cliente (consulta a Usuarios) |
| POST | /reservas | Crear reserva |
| PUT | /reservas/{id}/estado | Cambiar estado de la reserva |
| DELETE | /reservas/{id} | Eliminar reserva |

## Bases de datos

Cada servicio tiene su propio contenedor MySQL 8 (base de datos por servicio):

| Servicio | Base de datos | Tabla principal |
| --- | --- | --- |
| Usuarios | db_usuarios | usuarios |
| Reservas | db_reservas | reservas |

Los scripts de creación de tablas están en [`bases_datos/`](bases_datos/).

## Variables de entorno

Copia `.env.example` a `.env` y ajusta los valores.

| Variable | Uso |
| --- | --- |
| USUARIOS_SERVICE_URL | URL del servicio Usuarios usada por Reservas |
| DB_HOST_USUARIOS / DB_HOST_RESERVAS | Host del contenedor MySQL de cada servicio |
| DB_PORT_USUARIOS / DB_PORT_RESERVAS | Puerto interno de MySQL (3306) |
| DB_USER_USUARIOS / DB_USER_RESERVAS | Usuario de la base de datos |
| DB_PASSWORD_USUARIOS / DB_PASSWORD_RESERVAS | Contraseña de la base de datos |
| DB_NAME_USUARIOS / DB_NAME_RESERVAS | Nombre de la base de datos |

## Cómo ejecutar el sistema

```bash
cp .env.example .env
docker compose up --build
```

Luego abre `index.html` en el navegador. Las APIs quedan en `http://localhost:5001` (Usuarios) y `http://localhost:5002` (Reservas).

Para detener: `docker compose down` (agrega `-v` si quieres borrar los datos).

## Estructura del repositorio

```
reservas_hotel/
├── index.html            # Home
├── usuarios/             # Servicio Usuarios (app.py, database.py, dockerfile)
├── reservas/             # Servicio Reservas (app.py, database.py, dockerfile)
├── bases_datos/          # Scripts SQL por servicio
├── docs/arquitectura/    # Diagrama y documentación
├── docker-compose.yml
├── .env.example
└── README.md
