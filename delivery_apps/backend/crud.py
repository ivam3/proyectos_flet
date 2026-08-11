from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, desc, text
import models, schemas
import secrets
import string
import hashlib
import os
from passlib.context import CryptContext

# Configuración de seguridad para contraseñas (Grado Industrial)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- UTILIDADES ---
def _reset_sequence(db: Session, table_name: str):
    """Corrige el contador de IDs en PostgreSQL tras inserciones manuales."""
    if db.bind.dialect.name == "postgresql":
        try:
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
    return pwd_context.hash(password)

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
    if platillo.id is not None:
        existing = db.query(models.Menu).filter(
            models.Menu.id == platillo.id,
            models.Menu.tenant_id == tenant_id
        ).first()
        if existing:
            return update_platillo(db, tenant_id, platillo.id, platillo)
        check_global = db.query(models.Menu).filter(models.Menu.id == platillo.id).first()
        if check_global:
            platillo.id = None
    item_data = platillo.dict(exclude_none=True)
    db_platillo = models.Menu(**item_data)
    db_platillo.tenant_id = tenant_id
    db.add(db_platillo)
    try:
        db.commit()
        db.refresh(db_platillo)
        if platillo.id is not None and db.bind.dialect.name == "postgresql":
             _reset_sequence(db, "menu")
    except Exception as e:
        db.rollback()
        raise e
    return db_platillo

def update_platillo(db: Session, tenant_id: str, platillo_id: int, platillo: schemas.MenuCreate):
    db_platillo = db.query(models.Menu).filter(
        models.Menu.id == platillo_id,
        models.Menu.tenant_id == tenant_id
    ).first()
    if db_platillo:
        update_data = platillo.dict(exclude_unset=True)
        for key, value in update_data.items():
            if key not in ["id", "tenant_id"]:
                setattr(db_platillo, key, value)
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
    if grupo.id is not None:
        existing = db.query(models.GrupoOpciones).filter(
            models.GrupoOpciones.id == grupo.id,
            models.GrupoOpciones.tenant_id == tenant_id
        ).first()
        if existing:
            return update_grupo_opciones(db, tenant_id, grupo.id, grupo)
        check_global = db.query(models.GrupoOpciones).filter(models.GrupoOpciones.id == grupo.id).first()
        if check_global:
            grupo.id = None
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
    db_grupo = db.query(models.GrupoOpciones).filter(
        models.GrupoOpciones.id == grupo_id,
        models.GrupoOpciones.tenant_id == tenant_id
    ).first()
    if db_grupo:
        update_data = grupo.dict(exclude_unset=True)
        for key, value in update_data.items():
            if key not in ["id", "tenant_id"]:
                setattr(db_grupo, key, value)
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
        # Nunca usar una contraseña por defecto conocida ("zz"): si no hay
        # DEFAULT_ADMIN_PASSWORD se genera una aleatoria y se documenta el reset.
        default_pw = os.getenv("DEFAULT_ADMIN_PASSWORD")
        if not default_pw:
            default_pw = secrets.token_urlsafe(12)
            print(f"⚠️ DEFAULT_ADMIN_PASSWORD no configurado para el nuevo tenant '{tenant_id}'. "
                  "Se generó una contraseña aleatoria; usa 'db_admin.py passwd' para reestablecerla.")
        config = models.Configuracion(
            tenant_id=tenant_id,
            horario="Lunes a Viernes 9-10", 
            codigos_postales="12345",
            admin_password=hash_password(default_pw),
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
    config = get_configuracion(db, tenant_id)
    if not config or not config.admin_password:
        return False

    # 1. Verificar con Bcrypt (Estándar actual)
    try:
        if pwd_context.verify(password, config.admin_password):
            return True
    except Exception:
        pass

    # 2. Migración: hash SHA256 sin sal (legacy). Al validar correctamente,
    #    se re-hashea con bcrypt para eliminar el hash débil de la base.
    legacy_hash = hashlib.sha256(password.encode()).hexdigest()
    if config.admin_password == legacy_hash:
        config.admin_password = hash_password(password)
        db.commit()
        return True

    return False

def change_admin_password(db: Session, tenant_id: str, current_password: str, new_password: str):
    # 1. Validaciones de entrada básicas
    if not current_password or not new_password:
        return 400 # Bad Request
        
    if current_password == new_password:
        return 400 # No hay cambio real

    # 2. Verificar contraseña actual de forma estricta contra la DB
    if not verify_admin_password(db, tenant_id, current_password):
        return 401 # Unauthorized (Contraseña actual incorrecta)
        
    # 3. Aplicar cambio con hashing seguro (Bcrypt)
    config = get_configuracion(db, tenant_id)
    config.admin_password = hash_password(new_password)
    db.commit()
    return 200 # Success (Actualizada correctamente)

# --- SHORT LINKS ---
def get_short_links(db: Session, tenant_id: str):
    return db.query(models.ShortLink).filter(models.ShortLink.tenant_id == tenant_id).all()

def get_short_link_by_code(db: Session, tenant_id: str, code: str):
    return db.query(models.ShortLink).filter(
        models.ShortLink.tenant_id == tenant_id,
        models.ShortLink.short_code == code
    ).first()

def create_short_link(db: Session, tenant_id: str, link: schemas.ShortLinkCreate):
    existing = db.query(models.ShortLink).filter(
        models.ShortLink.tenant_id == tenant_id,
        models.ShortLink.short_code == link.short_code
    ).first()
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
    # --- VALIDACIÓN SERVER-SIDE CONTRA EL MENÚ DEL TENANT ---
    # El cliente NO es confiable: precios y total se validan contra la DB.
    menu_items = db.query(models.Menu).filter(models.Menu.tenant_id == tenant_id).all()
    price_map = {}
    for m in menu_items:
        discount = (m.descuento or 0) / 100.0
        price_map[m.nombre.strip().lower()] = m.precio * (1 - discount)

    expected_items_total = 0.0
    validated_items = []
    for item in orden.items:
        if item.cantidad <= 0 or item.precio_unitario <= 0:
            raise ValueError("Datos de producto inválidos en el pedido")
        full_name = item.producto.strip().lower()
        base_name = full_name if full_name in price_map else item.producto.split("(")[0].strip().lower()
        unit_price = price_map.get(base_name)
        if unit_price is None:
            raise ValueError(f"El producto '{item.producto}' ya no está disponible en el menú")
        if abs(item.precio_unitario - unit_price) > 0.5:
            raise ValueError(f"El precio de '{item.producto}' no es válido. Actualiza tu carrito.")
        expected_items_total += unit_price * item.cantidad
        validated_items.append(item)

    config = get_configuracion(db, tenant_id)
    try:
        envio = float(config.costo_envio or 0)
    except (TypeError, ValueError):
        envio = 0.0

    client_total = float(orden.total or 0)
    allowed_totals = [expected_items_total, expected_items_total + envio]
    if not any(abs(client_total - t) <= 0.5 for t in allowed_totals):
        raise ValueError("El total del pedido no coincide con el menú")

    if orden.metodo_pago == "efectivo" and (orden.paga_con is None or orden.paga_con < client_total):
        raise ValueError("El monto indicado no cubre el total del pedido")

    codigo = _generar_codigo_unico(db, tenant_id)
    db_orden = models.Orden(
        tenant_id=tenant_id,
        nombre_cliente=orden.nombre_cliente,
        telefono=orden.telefono,
        direccion=orden.direccion,
        referencias=orden.referencias,
        total=client_total,
        metodo_pago=orden.metodo_pago,
        paga_con=orden.paga_con,
        codigo_seguimiento=codigo,
        estado="Nuevo"
    )
    db.add(db_orden)
    db.flush()
    for item in validated_items:
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

def count_pedidos(db: Session, tenant_id: str, search_term: str = None):
    """Cuenta pedidos con COUNT(*) (sin cargar filas), para paginación eficiente."""
    query = db.query(models.Orden).filter(models.Orden.tenant_id == tenant_id)
    if search_term:
        term = f"%{search_term}%"
        query = query.filter(or_(models.Orden.nombre_cliente.like(term), models.Orden.codigo_seguimiento.like(term)))
    return query.count()

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
