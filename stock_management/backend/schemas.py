from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# --- FOTOS ---
class ProductPhotoBase(BaseModel):
    file_path: str

class ProductPhoto(ProductPhotoBase):
    id: int
    product_id: int
    created_at: datetime
    class Config:
        from_attributes = True

# --- TALLAS (STOCK / VARIANTES) ---
class ProductSizeBase(BaseModel):
    size: str
    color: Optional[str] = "N/A"
    stock: int

class ProductSizeCreate(ProductSizeBase):
    pass

class ProductSize(ProductSizeBase):
    id: int
    product_id: int
    class Config:
        from_attributes = True

# --- PRODUCTOS ---
class ProductBase(BaseModel):
    model_name: str
    sku: str
    brand: Optional[str] = None
    category: Optional[str] = None
    provider: Optional[str] = None
    gender: Optional[str] = "U"
    condition: Optional[str] = "Nuevo"
    cost: Optional[float] = 0.0
    tax: Optional[float] = 0.0
    price: Optional[float] = 0.0

class ProductCreate(ProductBase):
    initial_sizes: List[ProductSizeCreate] = [] # Para crear producto con tallas iniciales

class Product(ProductBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    sizes: List[ProductSize] = []
    photos: List[ProductPhoto] = []
    class Config:
        from_attributes = True

# --- MOVIMIENTOS ---
class MovementCreate(BaseModel):
    size_id: int
    movement_type: str # 'IN' or 'OUT'
    quantity: int
    description: Optional[str] = None
    
    # Nuevos campos de venta
    color: Optional[str] = None
    distribution_channel: Optional[str] = None
    offer_type: Optional[str] = None
    offer_value: Optional[float] = 0.0
    final_price: Optional[float] = None
    sales_id: Optional[str] = None
    comments: Optional[str] = None
    
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    status: Optional[str] = "COMPLETED"
    
    # Cancelación
    cancel_reason: Optional[str] = None
    is_waste: Optional[int] = 0

class Movement(MovementCreate):
    id: int
    created_at: datetime
    product_name: Optional[str] = None # Para visualización en el historial
    size_label: Optional[str] = None   # Para visualización en el historial
    brand: Optional[str] = None        # Nuevo para historial
    sku: Optional[str] = None          # Nuevo para historial
    
    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj):
        # Mapeo manual para incluir datos de relaciones en la respuesta plana
        instance = super().from_orm(obj)
        if obj.product_size:
            instance.size_label = obj.product_size.size
            if obj.product_size.product:
                instance.product_name = obj.product_size.product.model_name
                instance.brand = obj.product_size.product.brand
                instance.sku = obj.product_size.product.sku
        return instance
