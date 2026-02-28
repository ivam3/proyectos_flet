from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Menu(Base):
    __tablename__ = "menu"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True, default="dona_soco")
    categoria_id = Column(String, nullable=True)
    nombre = Column(String, index=True)
    descripcion = Column(String, nullable=True)
    precio = Column(Float)
    descuento = Column(Float, default=0.0)
    imagen = Column(String, nullable=True)
    is_active = Column(Integer, default=1)
    
    # ... resto de campos
    is_configurable = Column(Integer, default=0)
    is_configurable_salsa = Column(Integer, default=0)
    piezas = Column(Integer, default=1)
    printer_target = Column(String, default="cocina")
    grupos_opciones_ids = Column(Text, default="[]")

class GrupoOpciones(Base):
    __tablename__ = "grupos_opciones"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True, default="dona_soco")
    nombre = Column(String, index=True)
    opciones = Column(Text)
    seleccion_multiple = Column(Integer, default=0)
    obligatorio = Column(Integer, default=0)

class Configuracion(Base):
    __tablename__ = "configuracion"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String, index=True, default="dona_soco")
    horario = Column(String, nullable=True)
    codigos_postales = Column(String, nullable=True)
    # ... rest
    metodos_pago_activos = Column(Text, nullable=True)
    tipos_tarjeta = Column(Text, nullable=True)
    contactos = Column(Text, nullable=True)
    admin_password = Column(String, nullable=True)
    guisos_disponibles = Column(Text, nullable=True)
    salsas_disponibles = Column(Text, nullable=True)
    categorias_disponibles = Column(Text, nullable=True)
    costo_envio = Column(Float, default=20.0)

class ShortLink(Base):
    __tablename__ = "short_links"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True, default="dona_soco")
    short_code = Column(String, unique=True, index=True)
    destination_url = Column(String)

class Orden(Base):
    __tablename__ = "ordenes"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True, default="dona_soco")
    nombre_cliente = Column(String)
    telefono = Column(String)
    direccion = Column(String)
    referencias = Column(String, nullable=True)
    total = Column(Float)
    metodo_pago = Column(String, nullable=True)
    paga_con = Column(Float, nullable=True)
    fecha = Column(DateTime(timezone=True), server_default=func.now())
    estado = Column(String, default="Nuevo")
    codigo_seguimiento = Column(String, unique=True, index=True)
    motivo_cancelacion = Column(String, nullable=True)

    detalles = relationship("OrdenDetalle", back_populates="orden")
    historial = relationship("HistorialEstado", back_populates="orden")

class OrdenDetalle(Base):
    __tablename__ = "orden_detalle"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True, default="dona_soco")
    orden_id = Column(Integer, ForeignKey("ordenes.id"))
    producto = Column(String)
    cantidad = Column(Integer)
    precio_unitario = Column(Float)

    orden = relationship("Orden", back_populates="detalles")

class HistorialEstado(Base):
    __tablename__ = "historial_estados"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True, default="dona_soco")
    orden_id = Column(Integer, ForeignKey("ordenes.id"))
    nuevo_estado = Column(String)
    fecha = Column(DateTime(timezone=True), server_default=func.now())

    orden = relationship("Orden", back_populates="historial")

