from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True, default="shoes_stock")
    model_name = Column(String, index=True)
    sku = Column(String, unique=True, index=True)
    brand = Column(String, nullable=True)
    category = Column(String, nullable=True)
    provider = Column(String, nullable=True)
    gender = Column(String, default="U") # M, F, U
    condition = Column(String, nullable=True) # Nuevo, Usado, etc.
    
    cost = Column(Float, default=0.0)
    tax = Column(Float, default=0.0)
    price = Column(Float, default=0.0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones con cascada en SQLAlchemy
    sizes = relationship("ProductSize", back_populates="product", cascade="all, delete-orphan")
    photos = relationship("ProductPhoto", back_populates="product", cascade="all, delete-orphan")

class ProductSize(Base):
    __tablename__ = "product_sizes"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE")) # NUEVO: ondelete="CASCADE"
    size = Column(String)
    color = Column(String, default="N/A")
    stock = Column(Integer, default=0)

    product = relationship("Product", back_populates="sizes")
    movements = relationship("Movement", back_populates="product_size", cascade="all, delete-orphan")

class ProductPhoto(Base):
    __tablename__ = "product_photos"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE")) # NUEVO: ondelete="CASCADE"
    file_path = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product", back_populates="photos")

class Movement(Base):
    __tablename__ = "movements"

    id = Column(Integer, primary_key=True, index=True)
    size_id = Column(Integer, ForeignKey("product_sizes.id", ondelete="CASCADE")) # NUEVO: ondelete="CASCADE"
    movement_type = Column(String) # 'IN' para entrada, 'OUT' para venta
    quantity = Column(Integer)
    description = Column(String, nullable=True)
    
    # Datos de Venta Detallada
    color = Column(String, nullable=True) 
    distribution_channel = Column(String, nullable=True) 
    offer_type = Column(String, nullable=True) 
    offer_value = Column(Float, default=0.0)
    final_price = Column(Float, nullable=True) 
    sales_id = Column(String, index=True, nullable=True) 
    comments = Column(Text, nullable=True)
    
    # Datos del Cliente
    customer_name = Column(String, nullable=True)
    customer_phone = Column(String, nullable=True)
    status = Column(String, default="COMPLETED") # 'COMPLETED', 'PRE-SALE', 'CANCELLED'
    
    # Datos de Cancelación / Merma
    cancel_reason = Column(Text, nullable=True)
    is_waste = Column(Integer, default=0) 
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    product_size = relationship("ProductSize", back_populates="movements")
