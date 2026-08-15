from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
import models, schemas

# --- PRODUCTOS ---
def get_products(db: Session, tenant_id: str, search: str = None):
    query = db.query(models.Product).options(
        joinedload(models.Product.sizes),
        joinedload(models.Product.photos)
    ).filter(models.Product.tenant_id == tenant_id)
    
    if search:
        search_filter = f"%{search}%"
        query = query.filter(or_(
            models.Product.model_name.ilike(search_filter),
            models.Product.sku.ilike(search_filter),
            models.Product.brand.ilike(search_filter)
        ))
    
    return query.order_by(models.Product.created_at.desc()).all()

def get_product_by_sku(db: Session, sku: str):
    return db.query(models.Product).filter(models.Product.sku == sku).first()

def create_product(db: Session, tenant_id: str, product: schemas.ProductCreate):
    # Validar SKU duplicado manualmente para dar mensaje amigable
    if get_product_by_sku(db, product.sku):
        return "DUPLICATE_SKU"

    try:
        # 1. Crear el producto base
        db_product = models.Product(
            tenant_id=tenant_id,
            model_name=product.model_name,
            sku=product.sku,
            brand=product.brand,
            category=product.category,
            provider=product.provider,
            gender=product.gender,
            condition=product.condition,
            cost=product.cost,
            tax=product.tax,
            price=product.price
        )
        db.add(db_product)
        db.flush() 

        # 2. Crear las variantes iniciales (Color + Talla + Stock)
        for var_data in product.initial_sizes:
            db_variant = models.ProductSize(
                product_id=db_product.id,
                size=var_data.size,
                color=var_data.color or "N/A",
                stock=var_data.stock
            )
            db.add(db_variant)
            db.flush()
            
            if var_data.stock > 0:
                db_move = models.Movement(
                    size_id=db_variant.id,
                    movement_type='IN',
                    quantity=var_data.stock,
                    description="Carga inicial de inventario"
                )
                db.add(db_move)

        db.commit()
        db.refresh(db_product)
        return db_product
    except Exception as e:
        db.rollback()
        print(f"Error en crud.create_product: {e}")
        return None

def update_product(db: Session, product_id: int, product_data: schemas.ProductCreate):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        return None
    
    # Actualizar campos básicos
    for key, value in product_data.dict(exclude={'initial_sizes'}).items():
        setattr(db_product, key, value)
    
    db.commit()
    db.refresh(db_product)
    return db_product

def delete_product(db: Session, tenant_id: str, product_id: int):
    db_product = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.tenant_id == tenant_id
    ).first()
    if db_product:
        db.delete(db_product)
        db.commit()
        return True
    return False

def update_stock(db: Session, movement: schemas.MovementCreate):
    db_size = db.query(models.ProductSize).filter(models.ProductSize.id == movement.size_id).first()
    if not db_size:
        return None
    
    # Si tiene sales_id, verificar que no exista ya para evitar duplicados
    if movement.sales_id:
        existing_sale = db.query(models.Movement).filter(models.Movement.sales_id == movement.sales_id).first()
        if existing_sale:
            return "DUPLICATE_SALES_ID"

    # Validar stock suficiente para salidas
    if movement.movement_type == 'OUT' and db_size.stock < movement.quantity:
        return False # Indicar falta de stock
    
    # Actualizar stock según tipo de movimiento
    if movement.movement_type == 'IN':
        db_size.stock += movement.quantity
    elif movement.movement_type == 'OUT':
        db_size.stock -= movement.quantity
    
    # Registrar el movimiento con todos los campos
    db_move = models.Movement(**movement.dict())
    db.add(db_move)
    db.commit()
    db.refresh(db_size)
    return db_size

def cancel_movement(db: Session, movement_id: int, reason: str, is_waste: bool):
    db_move = db.query(models.Movement).filter(models.Movement.id == movement_id).first()
    if not db_move:
        return None
    
    if db_move.status == "CANCELLED":
        return "ALREADY_CANCELLED"

    # Cambiar estado
    db_move.status = "CANCELLED"
    db_move.cancel_reason = reason
    db_move.is_waste = 1 if is_waste else 0

    # Si NO es merma, devolver al stock
    if not is_waste:
        db_size = db.query(models.ProductSize).filter(models.ProductSize.id == db_move.size_id).first()
        if db_size:
            # Si era una salida (venta), devolvemos sumando. Si era entrada, restamos (raro pero lógico).
            if db_move.movement_type == 'OUT':
                db_size.stock += db_move.quantity
            else:
                db_size.stock -= db_move.quantity
    
    db.commit()
    db.refresh(db_move)
    return db_move

# --- FOTOS ---
def add_product_photo(db: Session, product_id: int, file_path: str):
    db_photo = models.ProductPhoto(product_id=product_id, file_path=file_path)
    db.add(db_photo)
    db.commit()
    db.refresh(db_photo)
    return db_photo

def get_movements(db: Session, tenant_id: str):
    return db.query(models.Movement).join(models.ProductSize).join(models.Product).filter(
        models.Product.tenant_id == tenant_id
    ).order_by(models.Movement.created_at.desc()).all()

def delete_photo(db: Session, photo_id: int):
    db_photo = db.query(models.ProductPhoto).filter(models.ProductPhoto.id == photo_id).first()
    if db_photo:
        path = db_photo.file_path
        db.delete(db_photo)
        db.commit()
        return path
    return None
