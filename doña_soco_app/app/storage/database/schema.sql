-- TABLA DE USUARIOS (Clientes y Administrador)
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    telefono TEXT,
    direccion TEXT,
    es_admin INTEGER DEFAULT 0  -- 0 = Cliente / 1 = Admin
);

-- TABLA DE CATEGORÍAS
CREATE TABLE IF NOT EXISTS categorias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL
);

-- TABLA DE PLATILLOS / PRODUCTOS
CREATE TABLE IF NOT EXISTS menu (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    categoria_id INTEGER,
    nombre TEXT NOT NULL,
    descripcion TEXT,
    precio REAL NOT NULL,
    imagen TEXT,
    is_active INTEGER DEFAULT 1,
    FOREIGN KEY(categoria_id) REFERENCES categorias(id)
);

-- Tabla de órdenes (pedidos)
CREATE TABLE IF NOT EXISTS ordenes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_cliente TEXT NOT NULL,
    telefono TEXT NOT NULL,
    direccion TEXT NOT NULL,
    referencias TEXT,
    total REAL NOT NULL,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    estado TEXT DEFAULT 'Nuevo',
    codigo_seguimiento TEXT UNIQUE
);

-- Tabla de detalles de orden (productos dentro de cada pedido)
CREATE TABLE IF NOT EXISTS orden_detalle (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    orden_id INTEGER,
    producto TEXT NOT NULL,
    cantidad INTEGER NOT NULL,
    precio_unitario REAL NOT NULL,
    FOREIGN KEY (orden_id) REFERENCES ordenes(id)
);

-- Historial de cambios de estado de pedidos
CREATE TABLE IF NOT EXISTS historial_estados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    orden_id INTEGER NOT NULL,
    nuevo_estado TEXT NOT NULL,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (orden_id) REFERENCES ordenes(id)
);
