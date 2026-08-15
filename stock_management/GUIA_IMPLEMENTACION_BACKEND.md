# 📘 Guía de Implementación Backend: Risk Shoes Stock

Este documento describe las especificaciones técnicas necesarias para reconstruir la API y la Base de Datos que requiere el frontend de **Risk Shoes Stock**. Está diseñado para que un desarrollador pueda replicar el funcionamiento exacto que el frontend espera.

## 1. Arquitectura del Sistema
- **Lenguaje:** Python 3.10+
- **Framework API:** FastAPI (Recomendado por validación automática y velocidad).
- **Base de Datos:** PostgreSQL.
- **Servidor de Producción:** Uvicorn + Gunicorn.

---

## 2. Estructura de la Base de Datos (PostgreSQL)

### Tabla: `products`
Información general del calzado.
| Campo | Tipo | Restricción |
| :--- | :--- | :--- |
| `id` | Serial (INT) | Primary Key |
| `model_name` | VARCHAR(255) | NOT NULL (Nombre del modelo) |
| `sku` | VARCHAR(100) | UNIQUE, INDEX (Código único) |
| `brand` | VARCHAR(100) | NULLABLE (Marca) |
| `price` | DECIMAL(10,2) | DEFAULT 0.0 |
| `cost` | DECIMAL(10,2) | DEFAULT 0.0 |
| `created_at` | TIMESTAMP | DEFAULT NOW() |

### Tabla: `product_sizes`
Variantes de talla, color y stock.
| Campo | Tipo | Restricción |
| :--- | :--- | :--- |
| `id` | Serial (INT) | Primary Key |
| `product_id` | INT | Foreign Key (products.id) ON DELETE CASCADE |
| `size` | VARCHAR(20) | NOT NULL (Ej: "27", "9.5") |
| `color` | VARCHAR(50) | DEFAULT "N/A" |
| `stock` | INT | DEFAULT 0 |

### Tabla: `product_photos`
Rutas de archivos de imágenes.
| Campo | Tipo | Restricción |
| :--- | :--- | :--- |
| `id` | Serial (INT) | Primary Key |
| `product_id` | INT | Foreign Key (products.id) ON DELETE CASCADE |
| `file_path` | TEXT | NOT NULL (Ruta relativa al servidor) |

### Tabla: `movements`
Historial de entradas y ventas (Auditoría).
| Campo | Tipo | Restricción |
| :--- | :--- | :--- |
| `id` | Serial (INT) | Primary Key |
| `size_id` | INT | Foreign Key (product_sizes.id) |
| `movement_type` | VARCHAR(10) | 'IN' (Entrada) / 'OUT' (Venta) |
| `quantity` | INT | NOT NULL |
| `customer_name`| VARCHAR(255) | NULLABLE |
| `status` | VARCHAR(50) | 'COMPLETED', 'PRE-SALE' |
| `created_at` | TIMESTAMP | DEFAULT NOW() |

---

## 3. Módulos del Backend (Python)

Se recomienda la siguiente estructura de archivos:
- `main.py`: Punto de entrada, configuración de CORS y definición de Endpoints.
- `database.py`: Motor de conexión a PostgreSQL (SQLAlchemy).
- `models.py`: Definición de clases que mapean a las tablas de la BD.
- `schemas.py`: Modelos Pydantic para validación de JSON de entrada/salida.
- `crud.py`: Funciones puras de base de datos (Insertar, Consultar, Actualizar).

---

## 4. Especificación de Endpoints (API REST)

El frontend de Flet espera los siguientes endpoints exactos:

### Productos
- **GET `/products`**
  - *Función:* `get_all_products()`
  - *Retorno:* Lista de objetos con tallas y fotos anidadas.
- **POST `/products`**
  - *Función:* `create_product(data)`
  - *Input:* `{"model_name": str, "sku": str, "price": float, "initial_sizes": list}`
- **DELETE `/products/{id}`**
  - *Función:* `delete_product(id)`
  - *Acción:* Debe eliminar en cascada tallas y referencias de fotos.

### Stock y Ventas
- **POST `/movements`**
  - *Función:* `register_movement(data)`
  - *Lógica:* Si es 'OUT' (Venta), debe restar del campo `stock` en `product_sizes`.
- **GET `/movements`**
  - *Función:* `get_movements()`
  - *Retorno:* Historial de transacciones para reportes.

### Imágenes
- **POST `/photos/upload/{product_id}`**
  - *Función:* `upload_photo(id, file)`
  - *Acción:* Guardar archivo en disco (`uploads/photos/`) y registrar ruta en BD.
- **GET `/upload/list`**
  - *Función:* `list_server_files()`
  - *Retorno:* `{"files": ["foto1.jpg", "foto2.png"]}`

---

## 5. Notas de Implementación (Seguridad y CORS)

1. **CORS:** Es OBLIGATORIO habilitar CORS en FastAPI para permitir peticiones desde cualquier origen (especialmente si el frontend corre en un dominio distinto).
2. **API KEY:** El frontend envía un header `X-API-KEY`. El backend debe validar que coincida con la variable de entorno `API_SECRET_KEY` para permitir el acceso.
3. **Optimización de Imágenes:** Se sugiere usar la librería `Pillow` para redimensionar fotos a un máximo de 800px de ancho al subirlas para ahorrar espacio.
4. **Respuesta JSON:** Siempre usar el formato CamelCase o snake_case consistente con los modelos de Pydantic definidos.

---
*Fin del documento de guía técnica.*
