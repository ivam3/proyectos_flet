from fastapi import FastAPI, Depends, HTTPException, status, Header, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import mimetypes
import shutil

import crud, models, schemas
from database import SessionLocal, engine, get_db

# --- PERSISTENCIA DE BASE DE DATOS (AUTO-SEEDING) ---
# Si la base de datos no existe en el volumen persistente pero sí en la raíz, moverla.
DB_SOURCE = "backend_dona_soco.db"
DB_DESTINATION = "static/uploads/backend_dona_soco.db"

if not os.path.exists(DB_DESTINATION) and os.path.exists(DB_SOURCE):
    print(f"DEBUG: Moviendo base de datos inicial a volumen persistente: {DB_DESTINATION}")
    os.makedirs("static/uploads", exist_ok=True)
    shutil.copy(DB_SOURCE, DB_DESTINATION)

# Registro de tipos MIME para soporte Web estable
mimetypes.add_type('application/javascript', '.js')
mimetypes.add_type('application/wasm', '.wasm')

# --- SEGURIDAD Y TENANT ---
API_KEY = os.getenv("API_SECRET_KEY")

if not API_KEY:
    print("❌ ERROR CRÍTICO: API_SECRET_KEY no configurada en las variables de entorno.")
    # En producción esto detendrá el arranque para evitar que la API sea pública
    # raise RuntimeError("API_SECRET_KEY is required")

async def verify_api_key(x_api_key: Optional[str] = Header(None, alias="X-API-KEY")):
    """Verifica que el cliente envíe la llave correcta en el encabezado X-API-KEY."""
    if not x_api_key or x_api_key != API_KEY:
        print(f"ALERTA SEGURIDAD: Acceso rechazado. Header: {x_api_key}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Acceso denegado: Credenciales inválidas"
        )
    return x_api_key

async def get_tenant_id(x_tenant_id: str = Header(..., alias="X-Tenant-ID")):
    """Obtiene el ID del tenant desde los encabezados. Obligatorio para garantizar aislamiento."""
    if not x_tenant_id or x_tenant_id.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Tenant-ID header is required for data isolation"
        )
    return x_tenant_id

# Inicialización de Base de Datos
models.Base.metadata.create_all(bind=engine)

# --- MIGRACIÓN MANUAL (Asegurar columnas nuevas) ---
def ensure_columns():
    from sqlalchemy import text, inspect
    inspector = inspect(engine)
    
    with engine.connect() as conn:
        # 1. Columnas generales del menú
        try:
            menu_columns = [c['name'] for c in inspector.get_columns("menu")]
            cols_to_add = {
                "is_configurable": "INTEGER DEFAULT 0",
                "is_configurable_salsa": "INTEGER DEFAULT 0",
                "piezas": "INTEGER DEFAULT 1",
                "printer_target": "VARCHAR DEFAULT 'cocina'",
                "grupos_opciones_ids": "TEXT DEFAULT '[]'",
                "categoria_id": "VARCHAR"
            }
            for col, type_def in cols_to_add.items():
                if col not in menu_columns:
                    conn.execute(text(f"ALTER TABLE menu ADD COLUMN {col} {type_def}"))
                    conn.commit()
        except Exception: pass
        
        # 2. Multi-tenancy: tenant_id en todas las tablas
        tables = ["menu", "grupos_opciones", "configuracion", "ordenes", "orden_detalle", "historial_estados"]
        for table in tables:
            try:
                columns = [c['name'] for c in inspector.get_columns(table)]
                if "tenant_id" not in columns:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN tenant_id VARCHAR"))
                    # Poblar con valor por defecto solo si se acaba de crear la columna
                    conn.execute(text(f"UPDATE {table} SET tenant_id = 'dona_soco' WHERE tenant_id IS NULL"))
                    conn.commit()
                    print(f"DEBUG: Columna 'tenant_id' añadida y poblada en {table}")
            except Exception as e:
                print(f"ERROR MIGRACION {table}: {e}")
                try: conn.rollback()
                except Exception: pass

        # 3. Columnas extras en configuración
        try:
            config_cols = [c['name'] for c in inspector.get_columns("configuracion")]
            if "categorias_disponibles" not in config_cols:
                conn.execute(text("ALTER TABLE configuracion ADD COLUMN categorias_disponibles TEXT DEFAULT '[]'"))
                conn.commit()
        except Exception: pass

        # 4. Migración de ShortLinks (Quitar unicidad global, poner por tenant)
        if engine.name == "postgresql":
            try:
                # Intentar borrar la restricción global antigua si existe
                conn.execute(text("ALTER TABLE short_links DROP CONSTRAINT IF EXISTS short_links_short_code_key"))
                # Intentar borrar el índice único si se creó como índice
                conn.execute(text("DROP INDEX IF EXISTS ix_short_links_short_code"))
                conn.commit()
                print("DEBUG: Restricciones de ShortLink actualizadas en PostgreSQL")
            except Exception as e:
                print(f"DEBUG: Nota migración ShortLink: {e}")
                try: conn.rollback()
                except: pass

ensure_columns()

app = FastAPI(title="Delivery Multi-tenant API")

# --- MIDDLEWARE DE SEGURIDAD GLOBAL (CRÍTICO PARA FLET WEB) ---
@app.middleware("http")
async def add_security_headers(request, call_next):
    # Interceptar peticiones al service worker para anularlo
    if "flutter_service_worker.js" in request.url.path:
        from fastapi.responses import Response
        return Response(
            content="", 
            media_type="application/javascript",
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
        )

    response = await call_next(request)
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
    
    # Prevenir cacheo de archivos de ejecución
    if request.url.path.endswith((".js", ".wasm", ".zip", ".html")):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- RUTAS DE API ---

@app.get("/shortlinks/resolve/{code}")
def resolve_short_link(
    code: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
):
    """Consulta la URL de destino para un código corto en el tenant actual."""
    link = crud.get_short_link_by_code(db, tenant_id, code)
    if not link:
        raise HTTPException(status_code=404, detail="Código no encontrado para este negocio")
    return {"url": link.destination_url}

@app.get("/shortlinks", response_model=List[schemas.ShortLink], dependencies=[Depends(verify_api_key)])
def read_short_links(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
):
    return crud.get_short_links(db, tenant_id)

@app.post("/shortlinks", response_model=schemas.ShortLink, dependencies=[Depends(verify_api_key)])
def create_short_link(
    link: schemas.ShortLinkCreate, 
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
):
    return crud.create_short_link(db, tenant_id, link)

@app.delete("/shortlinks/{link_id}", dependencies=[Depends(verify_api_key)])
def delete_short_link(
    link_id: int, 
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
):
    success = crud.delete_short_link(db, tenant_id, link_id)
    if not success:
        raise HTTPException(status_code=404, detail="Enlace no encontrado")
    return {"ok": True}

@app.get("/r/{tenant_id}/{code}")
async def public_redirect(tenant_id: str, code: str, db: Session = Depends(get_db)):
    """Redirección pública rápida mediante HTTP 302."""
    link = crud.get_short_link_by_code(db, tenant_id, code)
    if not link:
        # Si no existe el link, mandarlo al home del tenant (opcional)
        return JSONResponse({"detail": "Enlace no encontrado"}, status_code=404)
    return RedirectResponse(url=link.destination_url, status_code=302)

@app.get("/menu", response_model=List[schemas.Menu])
def read_menu(
    solo_activos: bool = True, 
    search: Optional[str] = None, 
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
):
    return crud.get_menu(db, tenant_id, solo_activos, search)

@app.post("/menu", response_model=schemas.Menu, dependencies=[Depends(verify_api_key)])
def create_menu_item(
    item: schemas.MenuCreate, 
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
):
    try:
        return crud.create_platillo(db, tenant_id, item)
    except Exception as e:
        print(f"ERROR CRÍTICO CREANDO PLATILLO: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.put("/menu/{item_id}", response_model=schemas.Menu, dependencies=[Depends(verify_api_key)])
def update_menu_item(
    item_id: int, 
    item: schemas.MenuCreate, 
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
):
    db_item = crud.update_platillo(db, tenant_id, item_id, item)
    if not db_item:
        raise HTTPException(status_code=404, detail="Platillo no encontrado")
    return db_item

@app.delete("/menu/{item_id}", dependencies=[Depends(verify_api_key)])
def delete_menu_item(
    item_id: int, 
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
):
    success = crud.delete_platillo(db, tenant_id, item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Platillo no encontrado")
    return {"ok": True}

@app.get("/opciones", response_model=List[schemas.GrupoOpciones])
def read_grupos_opciones(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
):
    return crud.get_grupos_opciones(db, tenant_id)

@app.post("/opciones", response_model=schemas.GrupoOpciones, dependencies=[Depends(verify_api_key)])
def create_grupo_opciones(
    grupo: schemas.GrupoOpcionesCreate, 
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
):
    return crud.create_grupo_opciones(db, tenant_id, grupo)

@app.put("/opciones/{grupo_id}", response_model=schemas.GrupoOpciones, dependencies=[Depends(verify_api_key)])
def update_grupo_opciones(
    grupo_id: int, 
    grupo: schemas.GrupoOpcionesCreate, 
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
):
    db_grupo = crud.update_grupo_opciones(db, tenant_id, grupo_id, grupo)
    if not db_grupo:
        raise HTTPException(status_code=404, detail="Grupo no encontrado")
    return db_grupo

@app.delete("/opciones/{grupo_id}", dependencies=[Depends(verify_api_key)])
def delete_grupo_opciones(
    grupo_id: int, 
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
):
    success = crud.delete_grupo_opciones(db, tenant_id, grupo_id)
    if not success:
        raise HTTPException(status_code=404, detail="Grupo no encontrado")
    return {"ok": True}

@app.get("/configuracion", response_model=schemas.Configuracion)
def read_config(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
):
    return crud.get_configuracion(db, tenant_id)

@app.put("/configuracion", response_model=schemas.Configuracion, dependencies=[Depends(verify_api_key)])
def update_config(
    config: schemas.ConfiguracionUpdate, 
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
):
    return crud.update_configuracion(db, tenant_id, config)

@app.post("/pedidos", response_model=schemas.Orden)
def create_pedido(
    orden: schemas.OrdenCreate, 
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
):
    return crud.create_pedido(db, tenant_id, orden)

@app.get("/pedidos/seguimiento", response_model=schemas.Orden)
def track_pedido(
    telefono: str, 
    codigo: str, 
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
):
    orden = crud.get_pedido_by_tracking(db, tenant_id, telefono, codigo)
    if not orden:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return orden

@app.get("/pedidos", response_model=List[schemas.Orden], dependencies=[Depends(verify_api_key)])
def read_pedidos(
    skip: int = 0, 
    limit: int = 100, 
    search: Optional[str] = None, 
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
):
    return crud.get_pedidos(db, tenant_id, skip, limit, search)

@app.put("/pedidos/{orden_id}/estado", dependencies=[Depends(verify_api_key)])
def update_estado(
    orden_id: int, 
    nuevo_estado: str, 
    motivo: Optional[str] = None, 
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
):
    success = crud.update_estado_pedido(db, tenant_id, orden_id, nuevo_estado, motivo)
    if not success:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return {"ok": True}

@app.put("/pedidos/{orden_id}/pago", dependencies=[Depends(verify_api_key)])
def update_pago(
    orden_id: int, 
    data: schemas.PagoUpdate, 
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
):
    success = crud.update_pago_pedido(db, tenant_id, orden_id, data.metodo_pago, data.paga_con)
    if not success:
         raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return {"ok": True}

@app.delete("/pedidos/{orden_id}", dependencies=[Depends(verify_api_key)])
def delete_pedido(
    orden_id: int, 
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
):
    success = crud.delete_pedido(db, tenant_id, orden_id)
    if not success:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return {"ok": True}

@app.put("/admin/menu/visibilidad-global", dependencies=[Depends(verify_api_key)])
def toggle_global_visibility(
    is_active: int, 
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
):
    crud.update_all_platillos_visibility(db, tenant_id, is_active)
    return {"ok": True}

@app.put("/menu/{item_id}/visibilidad", dependencies=[Depends(verify_api_key)])
def toggle_menu_item(
    item_id: int, 
    is_active: int, 
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
):
    success = crud.toggle_platillo_visibility(db, tenant_id, item_id, is_active)
    if not success:
         raise HTTPException(status_code=404, detail="Platillo no encontrado")
    return {"ok": True}

@app.post("/admin/login")
def admin_login(
    creds: schemas.LoginRequest, 
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
):
    is_valid = crud.verify_admin_password(db, tenant_id, creds.password)
    if not is_valid:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    return {"authenticated": True}

@app.post("/admin/change-password", dependencies=[Depends(verify_api_key)])
def admin_change_pass(
    data: schemas.PasswordUpdate, 
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
):
    crud.change_admin_password(db, tenant_id, data.new_password)
    return {"ok": True}

@app.post("/upload", dependencies=[Depends(verify_api_key)])
async def upload_file(
    file: UploadFile = File(...),
    tenant_id: str = Depends(get_tenant_id)
):
    from PIL import Image
    import io
    
    # 1. Asegurar directorio del tenant
    tenant_upload_dir = os.path.join(UPLOAD_DIR, tenant_id)
    os.makedirs(tenant_upload_dir, exist_ok=True)
    
    # 2. Leer contenido
    content = await file.read()
    
    # 3. Generar nombre con extensión .webp
    base_name = os.path.splitext(file.filename)[0]
    filename = f"{base_name}.webp"
    file_location = os.path.join(tenant_upload_dir, filename)
    
    try:
        # 4. Abrir imagen desde memoria y convertir a WebP
        img = Image.open(io.BytesIO(content))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        img.save(file_location, "WEBP", quality=80, method=6)
        return {"filename": filename}
    except Exception as e:
        print(f"Error procesando imagen para tenant {tenant_id}: {e}")
        with open(file_location, "wb+") as file_object:
            file_object.write(content)
        return {"filename": filename}

@app.delete("/upload/{filename}", dependencies=[Depends(verify_api_key)])
async def delete_file(
    filename: str,
    tenant_id: str = Depends(get_tenant_id)
):
    file_location = os.path.join(UPLOAD_DIR, tenant_id, filename)
    # Solo eliminar si existe y es un archivo (evita errores con lost+found o subcarpetas)
    if os.path.exists(file_location) and os.path.isfile(file_location):
        os.remove(file_location)
        return {"ok": True, "message": f"Archivo {filename} eliminado para {tenant_id}"}
    raise HTTPException(status_code=404, detail="Archivo no encontrado o es un directorio protegido")

@app.get("/upload/list", dependencies=[Depends(verify_api_key)])
async def list_uploads(tenant_id: str = Depends(get_tenant_id)):
    """Retorna una lista de todos los archivos en la carpeta del tenant, ignorando carpetas de sistema."""
    tenant_upload_dir = os.path.join(UPLOAD_DIR, tenant_id)
    print(f"DEBUG: Listando archivos para tenant '{tenant_id}' en: {tenant_upload_dir}")
    if not os.path.exists(tenant_upload_dir):
        return {"files": []}
    
    # Filtrar: solo archivos, ignorar lost+found y archivos ocultos
    files = [
        f for f in os.listdir(tenant_upload_dir) 
        if os.path.isfile(os.path.join(tenant_upload_dir, f)) 
        and f != "lost+found" 
        and not f.startswith(".")
    ]
    return {"files": files}

@app.post("/admin/maintenance/purge-root-webp", dependencies=[Depends(verify_api_key)])
async def purge_root_webp():
    """Elimina archivos .webp que quedaron en la raíz tras la migración a subcarpetas."""
    import glob
    # Buscar solo archivos .webp en la raíz de UPLOAD_DIR
    files = glob.glob(os.path.join(UPLOAD_DIR, "*.webp"))
    deleted_count = 0
    errors = []
    
    for f in files:
        try:
            if os.path.isfile(f):
                os.remove(f)
                deleted_count += 1
        except Exception as e:
            errors.append(f"{os.path.basename(f)}: {str(e)}")
            
    return {
        "ok": True, 
        "deleted_count": deleted_count,
        "errors": errors
    }

# --- ARCHIVOS ESTÁTICOS (WEB Y RECURSOS) ---

# Carpeta de subidas
UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Montar archivos estáticos del API (para imágenes subidas)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_root():
    if os.path.exists("web/index.html"):
        return FileResponse(
            "web/index.html",
            headers={
                "Cross-Origin-Opener-Policy": "same-origin",
                "Cross-Origin-Embedder-Policy": "require-corp",
                "Cache-Control": "no-cache, no-store, must-revalidate"
            }
        )
    return {"message": "API de delivery apps by Ivam3byCinderella funcionando"}

@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    # 1. Rutas de API y Estáticos del Backend
    if full_path.startswith(("menu", "opciones", "configuracion", "pedidos", "admin/", "upload", "static", "shortlinks")):
        return JSONResponse({"detail": "Not Found"}, status_code=404)

    # 2. Intentar servir archivos estáticos reales del build de Flet (js, css, wasm, etc)
    file_path = os.path.join("web", full_path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        media_type, _ = mimetypes.guess_type(file_path)
        if file_path.endswith(".js"): media_type = "application/javascript"
        elif file_path.endswith(".wasm"): media_type = "application/wasm"
        
        return FileResponse(
            file_path, 
            media_type=media_type,
            headers={
                "Cross-Origin-Opener-Policy": "same-origin",
                "Cross-Origin-Embedder-Policy": "require-corp"
            }
        )

    # 3. REDIRECCIÓN SPA (CRÍTICO): Para cualquier otra ruta (ej: /seguimiento, /admin, /carrito), 
    # incluso si el navegador la pide directamente tras un reload, servimos el index.html.
    # El enrutador interno de Flet leerá la URL y cargará la vista correcta.
    index_path = "web/index.html"
    if os.path.exists(index_path):
        return FileResponse(
            index_path,
            headers={
                "Cross-Origin-Opener-Policy": "same-origin",
                "Cross-Origin-Embedder-Policy": "require-corp",
                "Cache-Control": "no-cache, no-store, must-revalidate"
            }
        )

    return JSONResponse({"detail": "Frontend not found"}, status_code=404)
