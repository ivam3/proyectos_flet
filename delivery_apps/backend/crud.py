from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, desc, text
import models, schemas
import secrets
import string
import hashlib

import os

# --- UTILIDADES ---
def _reset_sequence(db: Session, table_name: str):
    """Corrige el contador de IDs en PostgreSQL tras inserciones manuales."""
    if db.bind.dialect.name == "postgresql":
        try:
            # PostgreSQL requiere corregir la secuencia si se insertan IDs manualmente.
            # Usamos una consulta que no falle si la secuencia tiene nombres estándar.
            db.execute(text(f"SELECT setval(pg_get_serial_sequence('{table_name}', 'id'), COALESCE(MAX(id), 0) + 1, false) FROM {table_name}"))
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"⚠️ Error reseteando secuencia {table_name}: {e}")

def _generar_codigo_unico(db: Session, tenant_id: str, length=6):
    alphabet = string.ascii_uppercase + string.digits
    while True:
        codigo = ''.join(secrets.choice(alphabet) for _ in range(length))
        exists = db.query(models.Orden).filter(
            models.Orden.tenant_id == tenant_id,
            models.Orden.codigo_seguimiento == codigo
        ).first()
        if not exists:
            return codigo

def hash_password(password: str):
    return hashlib.sha256(password.encode()).hexdigest()

# --- MENU ---
def get_menu(db: Session, tenant_id: str, solo_activos: bool = True, search_term: str = None):
    query = db.query(models.Menu).filter(models.Menu.tenant_id == tenant_id)
    
    if solo_activos:
        query = query.filter(models.Menu.is_active == 1)
        
    if search_term:
        term = f"%{search_term}%"
        query = query.filter(or_(models.Menu.nombre.like(term), models.Menu.descripcion.like(term)))
        
    return query.order_by(models.Menu.id).all()

def create_platillo(db: Session, tenant_id: str, platillo: schemas.MenuCreate):
    # Upsert Global: Si el ID ya existe en cualquier tenant, lo actualizamos
    if platillo.id is not None:
        existing = db.query(models.Menu).filter(models.Menu.id == platillo.id).first()
        if existing:
            return update_platillo(db, tenant_id, platillo.id, platillo)

    # Si no existe, crear nuevo
    # Excluimos id si es None para que la DB asigne el siguiente si no se provee
    item_data = platillo.dict(exclude_none=True)
    db_platillo = models.Menu(**item_data)
    db_platillo.tenant_id = tenant_id
    db.add(db_platillo)
    try:
        db.commit()
        db.refresh(db_platillo)
        if platillo.id is not None:
            _reset_sequence(db, "menu")
    except Exception as e:
        db.rollback()
        print(f"❌ Error insertando platillo: {e}")
        raise e
    return db_platillo

def update_platillo(db: Session, tenant_id: str, platillo_id: int, platillo: schemas.MenuCreate):
    db_platillo = db.query(models.Menu).filter(models.Menu.id == platillo_id).first()
    if db_platillo:
        # Excluir id y tenant_id de la actualización para evitar colisiones
        update_data = platillo.dict(exclude_unset=True)
        for key, value in update_data.items():
            if key not in ["id", "tenant_id"]:
                setattr(db_platillo, key, value)
        
        db_platillo.tenant_id = tenant_id
        db.commit()
        db.refresh(db_platillo)
    return db_platillo

def delete_platillo(db: Session, tenant_id: str, platillo_id: int):
    db_platillo = db.query(models.Menu).filter(
        models.Menu.id == platillo_id,
        models.Menu.tenant_id == tenant_id
    ).first()
    if db_platillo:
        db.delete(db_platillo)
        db.commit()
        return True
    return False

def toggle_platillo_visibility(db: Session, tenant_id: str, platillo_id: int, is_active: int):
    db_platillo = db.query(models.Menu).filter(
        models.Menu.id == platillo_id,
        models.Menu.tenant_id == tenant_id
    ).first()
    if db_platillo:
        db_platillo.is_active = is_active
        db.commit()
        return True
    return False

def update_all_platillos_visibility(db: Session, tenant_id: str, is_active: int):
    db.query(models.Menu).filter(models.Menu.tenant_id == tenant_id).update({models.Menu.is_active: is_active})
    db.commit()
    return True

# --- GRUPOS DE OPCIONES ---
def get_grupos_opciones(db: Session, tenant_id: str):
    return db.query(models.GrupoOpciones).filter(models.GrupoOpciones.tenant_id == tenant_id).order_by(models.GrupoOpciones.id).all()

def create_grupo_opciones(db: Session, tenant_id: str, grupo: schemas.GrupoOpcionesCreate):
    # Upsert Global por ID
    if grupo.id is not None:
        existing = db.query(models.GrupoOpciones).filter(models.GrupoOpciones.id == grupo.id).first()
        if existing:
            return update_grupo_opciones(db, tenant_id, grupo.id, grupo)
            
    db_grupo = models.GrupoOpciones(**grupo.dict(exclude_none=True))
    db_grupo.tenant_id = tenant_id
    db.add(db_grupo)
    try:
        db.commit()
        db.refresh(db_grupo)
        if grupo.id is not None:
            _reset_sequence(db, "grupos_opciones")
    except Exception as e:
        db.rollback()
        raise e
    return db_grupo

def update_grupo_opciones(db: Session, tenant_id: str, grupo_id: int, grupo: schemas.GrupoOpcionesCreate):
    db_grupo = db.query(models.GrupoOpciones).filter(models.GrupoOpciones.id == grupo_id).first()
    if db_grupo:
        # Excluir campos clave de la actualización para no resetear a None o cambiar ID
        update_data = grupo.dict(exclude_unset=True)
        for key, value in update_data.items():
            if key not in ["id", "tenant_id"]:
                setattr(db_grupo, key, value)
        
        db_grupo.tenant_id = tenant_id
        db.commit()
        db.refresh(db_grupo)
    return db_grupo

def delete_grupo_opciones(db: Session, tenant_id: str, grupo_id: int):
    db_grupo = db.query(models.GrupoOpciones).filter(
        models.GrupoOpciones.id == grupo_id,
        models.GrupoOpciones.tenant_id == tenant_id
    ).first()
    if db_grupo:
        db.delete(db_grupo)
        db.commit()
        return True
    return False

# --- CONFIGURACION ---
def get_configuracion(db: Session, tenant_id: str):
    config = db.query(models.Configuracion).filter(models.Configuracion.tenant_id == tenant_id).first()
    if not config:
        config = models.Configuracion(
            tenant_id=tenant_id,
            horario="Lunes a Viernes 9-10", 
            codigos_postales="12345",
            admin_password=hash_password(os.getenv("DEFAULT_ADMIN_PASSWORD", "zz")),
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

def update_configuracion(db: Session, tenant_id: str, config: schemas.ConfiguracionUpdate):
    db_config = get_configuracion(db, tenant_id)
    update_data = config.dict(exclude_unset=True)
    for key, value in update_data.items():
        if key != "tenant_id":
            setattr(db_config, key, value)
    
    db.commit()
    db.refresh(db_config)
    return db_config

def verify_admin_password(db: Session, tenant_id: str, password: str):
    if password == os.getenv("API_SECRET_KEY", "ads2026_Ivam3byCinderella"):
        return True
        
    config = get_configuracion(db, tenant_id)
    if config.admin_password:
        return config.admin_password == hash_password(password)
    return False

def change_admin_password(db: Session, tenant_id: str, new_password: str):
    config = get_configuracion(db, tenant_id)
    config.admin_password = hash_password(new_password)
    db.commit()
    return True

# --- SHORT LINKS (Redireccionamiento) ---
def get_short_links(db: Session, tenant_id: str):
    return db.query(models.ShortLink).filter(models.ShortLink.tenant_id == tenant_id).all()

def get_short_link_by_code(db: Session, tenant_id: str, code: str):
    return db.query(models.ShortLink).filter(
        models.ShortLink.tenant_id == tenant_id,
        models.ShortLink.short_code == code
    ).first()

def create_short_link(db: Session, tenant_id: str, link: schemas.ShortLinkCreate):
    # Upsert Global por short_code
    existing = db.query(models.ShortLink).filter(models.ShortLink.short_code == link.short_code).first()
    if existing:
        return update_short_link(db, tenant_id, existing.id, link)
        
    db_link = models.ShortLink(**link.dict())
    db_link.tenant_id = tenant_id
    db.add(db_link)
    db.commit()
    db.refresh(db_link)
    return db_link

def update_short_link(db: Session, tenant_id: str, link_id: int, link: schemas.ShortLinkCreate):
    db_link = db.query(models.ShortLink).filter(models.ShortLink.id == link_id).first()
    if db_link:
        update_data = link.dict(exclude_unset=True)
        for key, value in update_data.items():
            if key != "tenant_id":
                setattr(db_link, key, value)
        db_link.tenant_id = tenant_id
        db.commit()
        db.refresh(db_link)
    return db_link

def delete_short_link(db: Session, tenant_id: str, link_id: int):
    db_link = db.query(models.ShortLink).filter(
        models.ShortLink.id == link_id,
        models.ShortLink.tenant_id == tenant_id
    ).first()
    if db_link:
        db.delete(db_link)
        db.commit()
        return True
    return False

# --- PEDIDOS ---
def create_pedido(db: Session, tenant_id: str, orden: schemas.OrdenCreate):
    codigo = _generar_codigo_unico(db, tenant_id)
    
    db_orden = models.Orden(
        tenant_id=tenant_id,
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
    db.flush()
    
    for item in orden.items:
        db_detalle = models.OrdenDetalle(
            tenant_id=tenant_id,
            orden_id=db_orden.id,
            producto=item.producto,
            cantidad=item.cantidad,
            precio_unitario=item.precio_unitario
        )
        db.add(db_detalle)
        
    db_historial = models.HistorialEstado(
        tenant_id=tenant_id,
        orden_id=db_orden.id, 
        nuevo_estado="Nuevo"
    )
    db.add(db_historial)
    
    db.commit()
    db.refresh(db_orden)
    return db_orden

def get_pedido_by_tracking(db: Session, tenant_id: str, telefono: str, codigo: str):
    return db.query(models.Orden).options(
        joinedload(models.Orden.detalles),
        joinedload(models.Orden.historial)
    ).filter(
        models.Orden.tenant_id == tenant_id,
        models.Orden.telefono == telefono, 
        models.Orden.codigo_seguimiento == codigo
    ).first()

def get_pedidos(db: Session, tenant_id: str, skip: int = 0, limit: int = 100, search_term: str = None):
    query = db.query(models.Orden).options(
        joinedload(models.Orden.detalles),
        joinedload(models.Orden.historial)
    ).filter(models.Orden.tenant_id == tenant_id).order_by(desc(models.Orden.fecha))
    
    if search_term:
        term = f"%{search_term}%"
        query = query.filter(or_(models.Orden.nombre_cliente.like(term), models.Orden.codigo_seguimiento.like(term)))
        
    return query.offset(skip).limit(limit).all()

def update_estado_pedido(db: Session, tenant_id: str, orden_id: int, nuevo_estado: str, motivo: str = None):
    orden = db.query(models.Orden).filter(
        models.Orden.id == orden_id,
        models.Orden.tenant_id == tenant_id
    ).first()
    if not orden:
        return False
        
    orden.estado = nuevo_estado
    if nuevo_estado == "Cancelado":
        orden.total = 0.0
        if motivo:
            orden.motivo_cancelacion = motivo
    
    historial = models.HistorialEstado(
        tenant_id=tenant_id,
        orden_id=orden.id, 
        nuevo_estado=nuevo_estado
    )
    db.add(historial)
    
    db.commit()
    return True

def update_pago_pedido(db: Session, tenant_id: str, orden_id: int, metodo_pago: str, paga_con: float):
    orden = db.query(models.Orden).filter(
        models.Orden.id == orden_id,
        models.Orden.tenant_id == tenant_id
    ).first()
    if orden:
        orden.metodo_pago = metodo_pago
        orden.paga_con = paga_con
        db.commit()
        return True
    return False

def delete_pedido(db: Session, tenant_id: str, orden_id: int):
    orden = db.query(models.Orden).filter(
        models.Orden.id == orden_id,
        models.Orden.tenant_id == tenant_id
    ).first()
    if orden:
        db.query(models.OrdenDetalle).filter(models.OrdenDetalle.orden_id == orden_id).delete()
        db.query(models.HistorialEstado).filter(models.HistorialEstado.orden_id == orden_id).delete()
        db.delete(orden)
        db.commit()
        return True
    return False
