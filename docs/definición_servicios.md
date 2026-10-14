# Definición de los Sistemas y Componentes

El proyecto **Reservas Hotel** está diseñado sobre una arquitectura distribuida por servicios, dividiendo las responsabilidades principales en subsistemas independientes.

---

### 1. Subsistema de Usuarios (`/usuarios`)
Encargado de la gestión de identidades, perfiles, registro e inicio de sesión de los usuarios del sistema.
* **Lógica de negocio (`app.py`)**: Expone los endpoints de la API REST para el manejo de usuarios.
* **Persistencia de datos (`database.py`)**: Administra la conexión y las transacciones con la base de datos de usuarios.
* **Entorno y Dependencias (`dockerfile`, `requirements.txt`)**: Define la imagen de Docker aislada y las librerías necesarias para ejecutar el servicio.
---

### 2. Subsistema de Reservas (`/reservas`)
Encargado del procesamiento, disponibilidad y ciclo de vida de las reservas hoteleras.
* **Lógica de negocio (`app.py`)**: Maneja la creación, cancelación y consulta de reservas a través de sus rutas REST.
* **Persistencia de datos (`database.py`)**: Gestiona el almacenamiento de las reservas y su relación con las habitaciones o servicios.
* **Entorno y Dependencias (`dockerfile`, `requirements.txt`)**: Configura el contenedor independiente y el paquete de dependencias requeridas.

---

### 3. Interfaz de Usuario - Frontend (`index.html`)
* **Interfaz de Cliente (`index.html`)**: Punto de entrada visual en el navegador que consume las API públicas de los servicios de usuarios y reservas.

---

### 4. Orquestación y Entorno Global
* **Orquestador de Servicios (`docker-compose.yml`)**: Define y coordina el despliegue conjunto de todos los contenedores (servicios y bases de datos), facilitando la comunicación interna.
* **Variables de Entorno (`.env`)**: Contiene las configuraciones globales, credenciales y claves de conexión de manera centralizada.
