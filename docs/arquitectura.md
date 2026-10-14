```mermaid
graph TD
    A[Navegador Web - index.html] -->|Peticiones HTTP| B[API Gateway / Router]
    
    B -->|/api/reservas| C[Microservicio RESERVAS - 5002:5000]
    B -->|/api/usuarios| D[Microservicio USUARIOS - 5001:5000]
    
    C -->|Comunicación Interna| D
    
    C --> E[(Base de Datos mysql_reservas - 3309:3006)]
    D --> F[(Base de Datos mysql_usuarios - 3310:3006)]
