from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime

# --- SCHEMAS DE MENU ---
class MenuBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    precio: float
    descuento: Optional[float] = 0.0
    imagen: Optional[str] = None
    is_active: Optional[int] = 1
    is_configurable: Optional[int] = 0
    is_configurable_salsa: Optional[int] = 0
    piezas: Optional[int] = 1
    printer_target: Optional[str] = "cocina"
    grupos_opciones_ids: Optional[str] = "[]"

class MenuCreate(MenuBase):
    pass

class Menu(MenuBase):
    id: int
    categoria_id: Optional[int] = None

    class Config:
        from_attributes = True # Antes orm_mode = True

# --- SCHEMAS DE GRUPOS OPCIONES ---
class GrupoOpcionesBase(BaseModel):
    nombre: str
    opciones: str # JSON list string
    seleccion_multiple: Optional[int] = 0
    obligatorio: Optional[int] = 0

class GrupoOpcionesCreate(GrupoOpcionesBase):
    pass

class GrupoOpciones(GrupoOpcionesBase):
    id: int
    class Config:
        from_attributes = True

# --- SCHEMAS DE ORDEN ---
class OrdenDetalleBase(BaseModel):
    producto: str
    cantidad: int
    precio_unitario: float

class OrdenDetalleCreate(OrdenDetalleBase):
    # Para recibir detalles extras desde el frontend si es necesario concatenar antes
    # O el frontend manda el string ya formado en 'producto'
    pass 

class OrdenDetalle(OrdenDetalleBase):
    id: int
    orden_id: int
    class Config:
        from_attributes = True

class OrdenBase(BaseModel):
    nombre_cliente: str
    telefono: str
    direccion: str
    referencias: Optional[str] = None
    total: float
    metodo_pago: Optional[str] = None
    paga_con: Optional[float] = None

class OrdenCreate(OrdenBase):
    items: List[OrdenDetalleCreate] # Lista de productos al crear

class HistorialEstado(BaseModel):
    nuevo_estado: str
    fecha: datetime
    class Config:
        from_attributes = True

class Orden(OrdenBase):
    id: int
    fecha: datetime
    estado: str
    codigo_seguimiento: str
    motivo_cancelacion: Optional[str] = None
    detalles: List[OrdenDetalle] = []
    historial: List[HistorialEstado] = []

    class Config:
        from_attributes = True

class PagoUpdate(BaseModel):
    metodo_pago: str
    paga_con: float

# --- SCHEMAS DE CONFIGURACION ---
class ConfiguracionBase(BaseModel):
    horario: Optional[str] = None
    codigos_postales: Optional[str] = None
    metodos_pago_activos: Optional[str] = None # JSON string
    tipos_tarjeta: Optional[str] = None # JSON string
    contactos: Optional[str] = None # JSON string
    guisos_disponibles: Optional[str] = None
    salsas_disponibles: Optional[str] = None
    categorias_disponibles: Optional[str] = None
    costo_envio: Optional[float] = 20.0

class ConfiguracionUpdate(ConfiguracionBase):
    pass

class Configuracion(ConfiguracionBase):
    id: int
    admin_password: Optional[str] = None # Solo enviar si es necesario, cuidado con la seguridad

    class Config:
        from_attributes = True

# --- SCHEMAS DE AUTH/ADMIN ---
class LoginRequest(BaseModel):
    password: str

class PasswordUpdate(BaseModel):
    new_password: str
