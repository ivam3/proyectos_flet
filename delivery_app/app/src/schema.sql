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
    descuento REAL DEFAULT 0,
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
    metodo_pago TEXT,
    paga_con REAL,
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

-- TABLA DE CONFIGURACIÓN DE LA PLATAFORMA
CREATE TABLE IF NOT EXISTS configuracion (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    horario TEXT,
    codigos_postales TEXT,
    metodos_pago_activos TEXT,
    tipos_tarjeta TEXT,
    contactos TEXT
);

-- Inicializa la configuración con valores por defecto si la tabla está vacía
INSERT INTO configuracion (id, horario, codigos_postales, metodos_pago_activos, tipos_tarjeta, contactos, guisos_disponibles, salsas_disponibles)
SELECT 1, 'Lunes a Viernes de 9:00 a 22:00', '12345,54321', 
       '{"efectivo": true, "terminal": true}', 
       '["Visa", "Mastercard"]', 
       '{"telefono": "", "email": "", "whatsapp": "", "direccion": ""}',
       '{"Guiso 1": true}',
       '{"Salsa 1": true}'
WHERE NOT EXISTS (SELECT 1 FROM configuracion WHERE id = 1);