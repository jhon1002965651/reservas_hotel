# Definición de los Sistemas y Componentes

El proyecto **Reservas Hotel** está diseñado sobre una arquitectura distribuida por servicios, dividiendo las responsabilidades principales en subsistemas independientes[cite: 1].

---

### 1. Subsistema de Usuarios (`/usuarios`)
Encargado de la gestión de identidades, perfiles, registro e inicio de sesión de los usuarios del sistema[cite: 1].
* **Lógica de negocio (`app.py`)**: Expone los endpoints de la API REST para el manejo de usuarios[cite: 1].
* **Persistencia de datos (`database.py`)**: Administra la conexión y las transacciones con la base de datos de usuarios[cite: 1].
* **Entorno y Dependencias (`dockerfile`, `requirements.txt`)**: Define la imagen de Docker aislada y las librerías necesarias para ejecutar el servicio[cite: 1].

---

### 2. Subsistema de Reservas (`/reservas`)
Encargado del procesamiento, disponibilidad y ciclo de vida de las reservas hoteleras[cite: 1].
* **Lógica de negocio (`app.py`)**: Maneja la creación, cancelación y consulta de reservas a través de sus rutas REST[cite: 1].
* **Persistencia de datos (`database.py`)**: Gestiona el almacenamiento de las reservas y su relación con las habitaciones o servicios[cite: 1].
* **Entorno y Dependencias (`dockerfile`, `requirements.txt`)**: Configura el contenedor independiente y el paquete de dependencias requeridas[cite: 1].

---

### 3. Interfaz de Usuario - Frontend (`index.html`)
* **Interfaz de Cliente (`index.html`)**: Punto de entrada visual en el navegador que consume las API públicas de los servicios de usuarios y reservas[cite: 1].

---

### 4. Orquestación y Entorno Global
* **Orquestador de Servicios (`docker-compose.yml`)**: Define y coordina el despliegue conjunto de todos los contenedores (servicios y bases de datos), facilitando la comunicación interna[cite: 1].
* **Variables de Entorno (`.env`)**: Contiene las configuraciones globales, credenciales y claves de conexión de manera centralizada[cite: 1].
