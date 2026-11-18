# Hotel Grand Plaza — Sistema de Reservas Distribuido

## 1. Descripción del sistema
La gestión de reservas de un hotel suele depender de procesos manuales donde no existe un registro centralizado de clientes, las reservas se duplican o pierden y el personal no puede consultar ni actualizar estados en tiempo real.

**Hotel Grand Plaza** resuelve este problema mediante una arquitectura distribuida basada en microservicios independientes, un **API Gateway** como punto único de entrada en el puerto `5000`, persistencia aislada por servicio y mecanismos de tolerancia a fallos (**Timeout** y **Circuit Breaker**).

### Funcionalidades principales
- **Clientes:** Inicio de sesión, registro de nuevas reservas y consulta de su historial de reservas.
- **Administradores (`admin`):** Visualización global de todas las reservas, filtrado por documento y actualización de estado (`confirmada`, `pagada`, `cancelada`).
- **Administradores del sistema (`sysadmin`):** Gestión completa (CRUD) de cuentas de usuario y asignación de roles (`cliente`, `admin`, `sysadmin`).
- **Consulta distribuida y tolerancia a fallos:** Consolidación de datos de reserva junto con la información del cliente mediante comunicación HTTP protegida con Timeout y Circuit Breaker.

### Decisiones de arquitectura
- **Punto de entrada único:** Los microservicios y bases de datos no exponen puertos hacia el host; únicamente `home` (`8080`) y `gateway` (`5000`) son accesibles externamente.
- **Aislamiento de datos:** Cada microservicio administra exclusivamente su propia base de datos MySQL 8.

---

## 3. Microservicios (Inventario de servicios)

| Microservicio | Responsabilidad | Base de datos | Comunicación con otros servicios | Estado |
| :--- | :--- | :--- | :--- | :--- |
| **Home** (`home`) | Interfaz web para clientes, administradores y sysadmin. | Ninguna (cliente web) | Consume el **API Gateway** (`http://localhost:5000`). | Implementado |
| **API Gateway** (`gateway`) | Punto de entrada único (`:5000`), enrutamiento HTTP, preservación de códigos de estado y manejo de indisponibilidad (`503`/`504`). | Ninguna | Redirige peticiones hacia **Usuarios** y **Reservas** por red interna. | Implementado |
| **Usuarios** (`usuarios`) | Gestión CRUD de cuentas, roles y autenticación (`login`). | `db_usuarios` (MySQL 8) | Responde consultas HTTP de **Reservas** sobre datos de clientes. | Implementado |
| **Reservas** (`reservas`) | Gestión CRUD de reservas de habitaciones, estados y detalles consolidados. | `db_reservas` (MySQL 8) | Consulta a **Usuarios** (`GET /usuarios/{id}`) con Timeout y Circuit Breaker. | Implementado |

---

## 4. Endpoints y manejo de errores HTTP

Todas las peticiones externas pasan a través del **API Gateway** (`http://localhost:5000`).

### Códigos HTTP estandarizados
| Código | Significado | Uso en el sistema |
| :--- | :--- | :--- |
| `200` | OK | Consulta, actualización o eliminación exitosa. |
| `201` | Created | Registro exitoso de un usuario o una reserva (`POST`). |
| `400` | Bad Request | Datos obligatorios faltantes o formato inválido. |
| `401` | Unauthorized | Credenciales incorrectas en `POST /login`. |
| `404` | Not Found | El identificador de usuario o reserva no existe en la base de datos. |
| `500` | Internal Server Error | Error interno no controlado en el servidor o base de datos. |
| `503` | Service Unavailable | Microservicio destino caído o **Circuit Breaker en estado `OPEN`**. |
| `504` | Gateway Timeout | Tiempo máximo de espera excedido en comunicación entre servicios. |

### Servicio Usuarios (vía Gateway: `http://localhost:5000`)
| Método | Endpoint | Descripción | Entrada (JSON) | Respuesta |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/usuarios` | Listar todos los usuarios | Ninguna | `200` Lista de usuarios |
| `GET` | `/usuarios/{id}` | Consultar usuario por documento | Parámetro `id` | `200` Objeto usuario / `404` No encontrado |
| `POST` | `/usuarios` | Crear nuevo usuario | `{id, nombre, correo, contrasena, rol}` | `201` Confirmación / `400` Datos inválidos |
| `PUT` | `/usuarios/{id}` | Actualizar datos o rol de usuario | `{nombre, correo, rol, contrasena}` | `200` Actualizado / `404` No encontrado |
| `DELETE` | `/usuarios/{id}` | Eliminar usuario por documento | Parámetro `id` | `200` Eliminado / `404` No encontrado |
| `POST` | `/login` | Autenticar usuario | `{correo, contrasena}` | `200` Datos y rol / `401` Credenciales inválidas |

### Servicio Reservas (vía Gateway: `http://localhost:5000`)
| Método | Endpoint | Descripción | Entrada (JSON) | Respuesta |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/reservas` | Listar todas las reservas | Ninguna | `200` Lista de reservas |
| `GET` | `/reservas/{id}` | Consultar una reserva por ID | Parámetro `id` | `200` Objeto reserva / `404` No encontrada |
| `GET` | `/reservas/usuario/{usuario_id}` | Listar reservas de un cliente | Parámetro `usuario_id` | `200` Lista filtrada de reservas |
| `GET` | `/reservas/{id}/detalles` | Reserva + datos del cliente (consulta distribuida a Usuarios) | Parámetro `id` | `200` Reserva consolidada / `404` / `503` / `504` |
| `POST` | `/reservas` | Crear nueva reserva | `{habitacion, usuario_id, fecha_reserva, estado}` | `201` Reserva creada / `400` Datos inválidos |
| `PUT` | `/reservas/{id}/estado` | Cambiar estado de una reserva | `{estado}` | `200` Estado actualizado / `404` No encontrada |
| `DELETE` | `/reservas/{id}` | Eliminar una reserva | Parámetro `id` | `200` Eliminada / `404` No encontrada |
| `GET` | `/reservas/circuit-breaker` | Consultar estado actual del Circuit Breaker | Ninguna | `200` `{estado, fallos_consecutivos, ...}` |

---

## 5. Bases de datos

Cada microservicio opera con su propio contenedor MySQL 8 independiente:

| Microservicio | Base de datos | Tabla principal | Columnas | Operaciones implementadas |
| :--- | :--- | :--- | :--- | :--- |
| **Usuarios** | `db_usuarios` | `usuarios` | `id` (PK), `nombre`, `correo`, `contrasena`, `rol` | `SELECT`, `INSERT`, `UPDATE`, `DELETE` |
| **Reservas** | `db_reservas` | `reservas` | `id` (PK AI), `habitacion`, `usuario_id`, `fecha_reserva`, `estado` | `SELECT`, `INSERT`, `UPDATE`, `DELETE` |

---

## 6. Persistencia

La persistencia de datos se garantiza mediante volúmenes nombrados en `docker-compose.yml`:
- `vol_usuarios` montado en `/var/lib/mysql` del contenedor `mysql_usuarios`.
- `vol_reservas` montado en `/var/lib/mysql` del contenedor `mysql_reservas`.

### Prueba de persistencia verificada
1. Se registran usuarios y reservas mediante `POST /usuarios` y `POST /reservas`.
2. Se detienen y recrean los contenedores de aplicación sin eliminar volúmenes (`docker compose stop usuarios reservas` y `docker compose up -d`).
3. Al consultar nuevamente `GET /usuarios` y `GET /reservas`, todos los registros previos permanecen intactos.

---

## 7. Comunicación entre servicios

| Servicio solicitante | Servicio destino | Endpoint | Método HTTP | Información intercambiada |
| :--- | :--- | :--- | :--- | :--- |
| **Reservas** | **Usuarios** | `/usuarios/{usuario_id}` | `GET` | **Envía:** `usuario_id` en la URL.<br>**Recibe:** JSON `{id, nombre, correo, rol}` para enriquecer `GET /reservas/{id}/detalles`. |
| **API Gateway** | **Usuarios** | `/usuarios/*`, `/login` | `GET`, `POST`, `PUT`, `DELETE` | Reenvía cabeceras, parámetros y cuerpo JSON del cliente; retorna respuesta y código HTTP original. |
| **API Gateway** | **Reservas** | `/reservas/*` | `GET`, `POST`, `PUT`, `DELETE` | Reenvía cabeceras, parámetros y cuerpo JSON del cliente; retorna respuesta y código HTTP original. |

---

## 8. Timeout y Circuit Breaker

La comunicación síncrona entre **Reservas** y **Usuarios** (`GET /reservas/{id}/detalles`) está protegida mediante **Timeout** y **Circuit Breaker**.

### Parámetros configurados
| Parámetro | Valor implementado | Descripción |
| :--- | :--- | :--- |
| **Servicio que realiza la solicitud** | `reservas` | Microservicio consumidor de datos de cliente. |
| **Servicio protegido** | `usuarios` | Dependencia consultada en `GET /usuarios/{usuario_id}`. |
| **Timeout configurado** | `3 segundos` | Tiempo máximo de espera de respuesta HTTP (`requests.get(..., timeout=3)`). Si se supera, retorna `504 Gateway Timeout`. |
| **Umbral de fallos (`failure_threshold`)** | `3 fallos` | Número de fallos consecutivos necesarios para abrir el circuito. |
| **Tiempo de recuperación (`recovery_timeout`)** | `30 segundos` | Tiempo que el circuito permanece en `OPEN` antes de pasar a `HALF_OPEN`. |

### Comportamiento de los estados del Circuit Breaker
1. **`CLOSED` (Normal):** Las solicitudes hacia `usuarios` se ejecutan normalmente. Cada fallo técnico (conexión rechazada, `500` o timeout) incrementa el contador de fallos; una respuesta exitosa lo reinicia a `0`.
2. **`OPEN` (Circuito abierto):** Al alcanzar **3 fallos consecutivos**, el circuito se abre. Durante los siguientes **15 segundos**, las peticiones se rechazan inmediatamente con **`503 Service Unavailable`** sin esperar el timeout de red.
3. **`HALF_OPEN` (Semi-abierto):** Transcurridos los 15 segundos, el circuito permite **1 solicitud de prueba** hacia `usuarios`. Si responde correctamente (`200` o `404`), el circuito vuelve a **`CLOSED`**; si vuelve a fallar, retorna a **`OPEN`**.

---

## 9. API Gateway

El servicio `gateway` actúa como fachada única del sistema distribuido en `http://localhost:5000`:

| Ruta pública en Gateway | Servicio interno destino | Métodos soportados |
| :--- | :--- | :--- |
| `/usuarios` y `/usuarios/{id}` | `http://usuarios:5000` | `GET`, `POST`, `PUT`, `DELETE` |
| `/login` | `http://usuarios:5000` | `POST` |
| `/reservas` y `/reservas/{id}` | `http://reservas:5000` | `GET`, `POST`, `DELETE` |
| `/reservas/usuario/{usuario_id}` | `http://reservas:5000` | `GET` |
| `/reservas/{id}/detalles` | `http://reservas:5000` | `GET` |
| `/reservas/{id}/estado` | `http://reservas:5000` | `PUT` |
| `/reservas/circuit-breaker` | `http://reservas:5000` | `GET` |

---

## 10. Docker Compose y ejecución

### Variables de entorno (`.env.example`)
```env
USUARIOS_SERVICE_URL=http://usuarios:5000
RESERVAS_SERVICE_URL=http://reservas:5000

DB_HOST_RESERVAS=mysql_reservas
DB_PORT_RESERVAS=3306
DB_USER_RESERVAS=root
DB_PASSWORD_RESERVAS=root
DB_NAME_RESERVAS=db_reservas

DB_HOST_USUARIOS=mysql_usuarios
DB_PORT_USUARIOS=3306
DB_USER_USUARIOS=root
DB_PASSWORD_USUARIOS=root
DB_NAME_USUARIOS=db_usuarios
```

### Procedimiento de ejecución
```bash
# 1. Crear archivo de entorno
cp .env.example .env

# 2. Construir y levantar toda la arquitectura en segundo plano
docker compose up -d --build

# 3. Verificar estado de los 6 contenedores
docker compose ps
```
- **Vista Home:** `http://localhost:8080`
- **API Gateway:** `http://localhost:5000`
- **Detener sin borrar datos:** `docker compose down`

---

## 11. Pruebas (Matriz de verificación integral)

| Prueba | Resultado esperado | Resultado obtenido | Evidencia |
| :--- | :--- | :--- | :--- |
| **Arquitectura completa** | Todos los servicios definidos (`home`, `gateway`, `usuarios`, `reservas`, BDs) implementados. | Cumplido | `docs/arquitectura/` |
| **Docker Compose** | 6 contenedores levantados en la red `hotel_net` sin errores. | Cumplido | `docs/pruebas/docker_ps.png` |
| **CRUD Usuarios** | Ciclo completo `POST` (201) → `GET` (200) → `PUT` (200) → `DELETE` (200) → `GET` inexistente (404). | Cumplido | `docs/pruebas/crud_usuarios.png` |
| **CRUD Reservas** | Ciclo completo `POST` (201) → `GET` (200) → `PUT /estado` (200) → `DELETE` (200) → `GET` inexistente (404). | Cumplido | `docs/pruebas/crud_reservas.png` |
| **Bases de datos** | Datos conservados tras `docker compose stop usuarios reservas` y recreación. | Cumplido | `docs/pruebas/persistencia.png` |
| **Comunicación HTTP** | `GET /reservas/{id}/detalles` retorna datos de reserva + nombre y correo desde `usuarios`. | Cumplido | `docs/pruebas/comunicacion.png` |
| **Timeout** | Demora mayor a 3 s en `usuarios` retorna error controlado `504 Gateway Timeout`. | Cumplido | `docs/pruebas/timeout.png` |
| **Circuit Breaker CLOSED** | Con `usuarios` activo, el estado es `CLOSED` y las peticiones pasan normalmente. | Cumplido | `docs/pruebas/cb_closed.png` |
| **Circuit Breaker OPEN** | Tras detener `usuarios` (`docker compose stop usuarios`) y generar 3 fallos, cambia a `OPEN` y responde `503`. | Cumplido | `docs/pruebas/cb_open.png` |
| **Recuperación (HALF_OPEN → CLOSED)** | Al iniciar `usuarios` (`docker compose start usuarios`) y pasar 15 s, prueba con `HALF_OPEN` y vuelve a `CLOSED`. | Cumplido | `docs/pruebas/cb_recovery.png` |
| **API Gateway** | Todas las operaciones de `usuarios` y `reservas` funcionan desde `http://localhost:5000`. | Cumplido | `docs/pruebas/gateway.png` |
| **Vista Home** | Inicio de sesión, creación y consulta de reservas desde `http://localhost:8080` vía Gateway. | Cumplido | `docs/pruebas/home_integrado.png` |

---

## 12. Estado actual y equipo

### Funcionalidades terminadas
- Microservicios `usuarios` y `reservas` con operaciones CRUD completas y bases de datos MySQL independientes.
- Integración centralizada mediante `API Gateway` (`:5000`) y contenedor web `Home` (`:8080`).
- Tolerancia a fallos con `Timeout` (3 s) y `Circuit Breaker` (`CLOSED`, `OPEN`, `HALF_OPEN`).
- Persistencia mediante volúmenes Docker y aislamiento de puertos internos.

### Aspectos pendientes (mejoras futuras)
- Encriptación de contraseñas con hashing (`bcrypt`) y tokens JWT.
- Incorporación de un servicio de notificaciones por correo al confirmar o cancelar reservas.

### Estructura del repositorio
```text
reserva_hotel/
├── home/
│   └── index.html
├── gateway/
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
├── usuarios/
│   ├── app.py
│   ├── database.py
│   ├── Dockerfile
│   └── requirements.txt
├── reservas/
│   ├── app.py
│   ├── database.py
│   ├── Dockerfile
│   └── requirements.txt
├── bases_datos/
├── docs/
│   ├── arquitectura/
│   ├── endpoints/
│   └── pruebas/
├── docker-compose.yml
├── .env.example
└── README.md
```
