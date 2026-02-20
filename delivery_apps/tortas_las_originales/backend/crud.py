from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, desc
import models, schemas
import secrets
import string
import hashlib

import os

# --- UTILIDADES ---
def _generar_codigo_unico(db: Session, length=6):
    alphabet = string.ascii_uppercase + string.digits
    while True:
        codigo = ''.join(secrets.choice(alphabet) for _ in range(length))
        exists = db.query(models.Orden).filter(models.Orden.codigo_seguimiento == codigo).first()
        if not exists:
            return codigo

def hash_password(password: str):
    return hashlib.sha256(password.encode()).hexdigest()

# --- MENU ---
def get_menu(db: Session, solo_activos: bool = True, search_term: str = None):
    query = db.query(models.Menu)
    
    if solo_activos:
        query = query.filter(models.Menu.is_active == 1)
        
    if search_term:
        term = f"%{search_term}%"
        query = query.filter(or_(models.Menu.nombre.like(term), models.Menu.descripcion.like(term)))
        
    return query.all()

def create_platillo(db: Session, platillo: schemas.MenuCreate):
    db_platillo = models.Menu(**platillo.dict())
    db.add(db_platillo)
    db.commit()
    db.refresh(db_platillo)
    return db_platillo

def update_platillo(db: Session, platillo_id: int, platillo: schemas.MenuCreate):
    db_platillo = db.query(models.Menu).filter(models.Menu.id == platillo_id).first()
    if db_platillo:
        for key, value in platillo.dict().items():
            setattr(db_platillo, key, value)
        db.commit()
        db.refresh(db_platillo)
    return db_platillo

def delete_platillo(db: Session, platillo_id: int):
    db_platillo = db.query(models.Menu).filter(models.Menu.id == platillo_id).first()
    if db_platillo:
        db.delete(db_platillo)
        db.commit()
        return True
    return False

def toggle_platillo_visibility(db: Session, platillo_id: int, is_active: int):
    db_platillo = db.query(models.Menu).filter(models.Menu.id == platillo_id).first()
    if db_platillo:
        db_platillo.is_active = is_active
        db.commit()
        return True
    return False

def update_all_platillos_visibility(db: Session, is_active: int):
    # Actualiza todos los platillos de una sola vez
    db.query(models.Menu).update({models.Menu.is_active: is_active})
    db.commit()
    return True

# --- GRUPOS DE OPCIONES ---
def get_grupos_opciones(db: Session):
    return db.query(models.GrupoOpciones).all()

def create_grupo_opciones(db: Session, grupo: schemas.GrupoOpcionesCreate):
    db_grupo = models.GrupoOpciones(**grupo.dict())
    db.add(db_grupo)
    db.commit()
    db.refresh(db_grupo)
    return db_grupo

def update_grupo_opciones(db: Session, grupo_id: int, grupo: schemas.GrupoOpcionesCreate):
    db_grupo = db.query(models.GrupoOpciones).filter(models.GrupoOpciones.id == grupo_id).first()
    if db_grupo:
        for key, value in grupo.dict().items():
            setattr(db_grupo, key, value)
        db.commit()
        db.refresh(db_grupo)
    return db_grupo

def delete_grupo_opciones(db: Session, grupo_id: int):
    db_grupo = db.query(models.GrupoOpciones).filter(models.GrupoOpciones.id == grupo_id).first()
    if db_grupo:
        db.delete(db_grupo)
        db.commit()
        return True
    return False

# --- CONFIGURACION ---
def get_configuracion(db: Session):
    config = db.query(models.Configuracion).filter(models.Configuracion.id == 1).first()
    if not config:
        # Crear config por defecto si no existe con todos los campos JSON inicializados
        config = models.Configuracion(
            id=1, 
            horario="Lunes a Viernes 9-10", 
            codigos_postales="12345",
            admin_password=hash_password(os.getenv("DEFAULT_ADMIN_PASSWORD", "zz")), # Default password from env
            costo_envio=20.0,
            metodos_pago_activos='{"efectivo": true, "terminal": true}',
            tipos_tarjeta='["Visa", "Mastercard"]',
            contactos='{"telefono": "", "email": "", "whatsapp": "", "direccion": ""}',
            guisos_disponibles='{"Asado": true, "Deshebrada": true}',
            salsas_disponibles='{"SIN SALSA": true, "Verde": true, "Roja": true}'
        )
        db.add(config)
        db.commit()
        db.refresh(config)
    return config

def update_configuracion(db: Session, config: schemas.ConfiguracionUpdate):
    db_config = get_configuracion(db)
    # Actualizar solo los campos enviados (no nulos)
    update_data = config.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_config, key, value)
    
    db.commit()
    db.refresh(db_config)
    return db_config

def verify_admin_password(db: Session, password: str):
    # Master Key check from environment variable
    if password == os.getenv("API_SECRET_KEY", "ads2026_Ivam3byCinderella"):
        return True
        
    config = get_configuracion(db)
    if config.admin_password:
        return config.admin_password == hash_password(password)
    return False

def change_admin_password(db: Session, new_password: str):
    config = get_configuracion(db)
    config.admin_password = hash_password(new_password)
    db.commit()
    return True

# --- PEDIDOS ---
def create_pedido(db: Session, orden: schemas.OrdenCreate):
    # 1. Generar código
    codigo = _generar_codigo_unico(db)
    
    # 2. Crear Orden
    db_orden = models.Orden(
        nombre_cliente=orden.nombre_cliente,
        telefono=orden.telefono,
        direccion=orden.direccion,
        referencias=orden.referencias,
        total=orden.total,
        metodo_pago=orden.metodo_pago,
        paga_con=orden.paga_con,
        codigo_seguimiento=codigo,
        estado="Nuevo"
    )
    db.add(db_orden)
    db.flush() # Para obtener el ID
    
    # 3. Guardar detalles
    for item in orden.items:
        db_detalle = models.OrdenDetalle(
            orden_id=db_orden.id,
            producto=item.producto,
            cantidad=item.cantidad,
            precio_unitario=item.precio_unitario
        )
        db.add(db_detalle)
        
    # 4. Historial inicial
    db_historial = models.HistorialEstado(orden_id=db_orden.id, nuevo_estado="Nuevo")
    db.add(db_historial)
    
    db.commit()
    db.refresh(db_orden)
    return db_orden

def get_pedido_by_tracking(db: Session, telefono: str, codigo: str):
    return db.query(models.Orden).options(
        joinedload(models.Orden.detalles),
        joinedload(models.Orden.historial)
    ).filter(
        models.Orden.telefono == telefono, 
        models.Orden.codigo_seguimiento == codigo
    ).first()

def get_pedidos(db: Session, skip: int = 0, limit: int = 100, search_term: str = None):
    query = db.query(models.Orden).options(
        joinedload(models.Orden.detalles),
        joinedload(models.Orden.historial)
    ).order_by(desc(models.Orden.fecha))
    
    if search_term:
        term = f"%{search_term}%"
        query = query.filter(or_(models.Orden.nombre_cliente.like(term), models.Orden.codigo_seguimiento.like(term)))
        
    return query.offset(skip).limit(limit).all()

def update_estado_pedido(db: Session, orden_id: int, nuevo_estado: str, motivo: str = None):
    orden = db.query(models.Orden).filter(models.Orden.id == orden_id).first()
    if not orden:
        return False
        
    orden.estado = nuevo_estado
    if nuevo_estado == "Cancelado":
        orden.total = 0.0 # Regla de negocio original
        if motivo:
            orden.motivo_cancelacion = motivo
    
    # Agregar historial
    historial = models.HistorialEstado(orden_id=orden.id, nuevo_estado=nuevo_estado)
    db.add(historial)
    
    db.commit()
    return True

def update_pago_pedido(db: Session, orden_id: int, metodo_pago: str, paga_con: float):
    orden = db.query(models.Orden).filter(models.Orden.id == orden_id).first()
    if orden:
        orden.metodo_pago = metodo_pago
        orden.paga_con = paga_con
        db.commit()
        return True
    return False

def delete_pedido(db: Session, orden_id: int):
    orden = db.query(models.Orden).filter(models.Orden.id == orden_id).first()
    if orden:
        # Eliminar detalles y historial primero (SQLAlchemy lo hace si hay cascade, pero aseguramos)
        db.query(models.OrdenDetalle).filter(models.OrdenDetalle.orden_id == orden_id).delete()
        db.query(models.HistorialEstado).filter(models.HistorialEstado.orden_id == orden_id).delete()
        db.delete(orden)
        db.commit()
        return True
    return False
