from fastapi import FastAPI, Depends, HTTPException, status, Header, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
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

# --- SEGURIDAD ESTRICTA ---
# Se requiere configurar API_SECRET_KEY en las variables de entorno de Railway
API_KEY = os.getenv("API_SECRET_KEY", "ads2026_Ivam3byCinderella")

async def verify_api_key(x_api_key: Optional[str] = Header(None, alias="X-API-KEY")):
    """Verifica que el cliente envíe la llave correcta en el encabezado X-API-KEY."""
    if not x_api_key or x_api_key != API_KEY:
        # El log de error solo es visible para ti en el panel de Railway
        print(f"ALERTA SEGURIDAD: Acceso rechazado. Header: {x_api_key}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Acceso denegado: Credenciales inválidas"
        )
    return x_api_key

# Inicialización de Base de Datos
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Antojitos Doña Soco API")

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

@app.get("/menu", response_model=List[schemas.Menu])
def read_menu(solo_activos: bool = True, search: Optional[str] = None, db: Session = Depends(get_db)):
    return crud.get_menu(db, solo_activos, search)

@app.post("/menu", response_model=schemas.Menu, dependencies=[Depends(verify_api_key)])
def create_menu_item(item: schemas.MenuCreate, db: Session = Depends(get_db)):
    return crud.create_platillo(db, item)

@app.put("/menu/{item_id}", response_model=schemas.Menu, dependencies=[Depends(verify_api_key)])
def update_menu_item(item_id: int, item: schemas.MenuCreate, db: Session = Depends(get_db)):
    db_item = crud.update_platillo(db, item_id, item)
    if not db_item:
        raise HTTPException(status_code=404, detail="Platillo no encontrado")
    return db_item

@app.delete("/menu/{item_id}", dependencies=[Depends(verify_api_key)])
def delete_menu_item(item_id: int, db: Session = Depends(get_db)):
    success = crud.delete_platillo(db, item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Platillo no encontrado")
    return {"ok": True}

@app.get("/opciones", response_model=List[schemas.GrupoOpciones])
def read_grupos_opciones(db: Session = Depends(get_db)):
    return crud.get_grupos_opciones(db)

@app.post("/opciones", response_model=schemas.GrupoOpciones, dependencies=[Depends(verify_api_key)])
def create_grupo_opciones(grupo: schemas.GrupoOpcionesCreate, db: Session = Depends(get_db)):
    return crud.create_grupo_opciones(db, grupo)

@app.put("/opciones/{grupo_id}", response_model=schemas.GrupoOpciones, dependencies=[Depends(verify_api_key)])
def update_grupo_opciones(grupo_id: int, grupo: schemas.GrupoOpcionesCreate, db: Session = Depends(get_db)):
    db_grupo = crud.update_grupo_opciones(db, grupo_id, grupo)
    if not db_grupo:
        raise HTTPException(status_code=404, detail="Grupo no encontrado")
    return db_grupo

@app.delete("/opciones/{grupo_id}", dependencies=[Depends(verify_api_key)])
def delete_grupo_opciones(grupo_id: int, db: Session = Depends(get_db)):
    success = crud.delete_grupo_opciones(db, grupo_id)
    if not success:
        raise HTTPException(status_code=404, detail="Grupo no encontrado")
    return {"ok": True}

@app.get("/configuracion", response_model=schemas.Configuracion)
def read_config(db: Session = Depends(get_db)):
    return crud.get_configuracion(db)

@app.put("/configuracion", response_model=schemas.Configuracion, dependencies=[Depends(verify_api_key)])
def update_config(config: schemas.ConfiguracionUpdate, db: Session = Depends(get_db)):
    return crud.update_configuracion(db, config)

@app.post("/pedidos", response_model=schemas.Orden)
def create_pedido(orden: schemas.OrdenCreate, db: Session = Depends(get_db)):
    return crud.create_pedido(db, orden)

@app.get("/pedidos/seguimiento", response_model=schemas.Orden)
def track_pedido(telefono: str, codigo: str, db: Session = Depends(get_db)):
    orden = crud.get_pedido_by_tracking(db, telefono, codigo)
    if not orden:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return orden

@app.get("/pedidos", response_model=List[schemas.Orden], dependencies=[Depends(verify_api_key)])
def read_pedidos(skip: int = 0, limit: int = 100, search: Optional[str] = None, db: Session = Depends(get_db)):
    return crud.get_pedidos(db, skip, limit, search)

@app.put("/pedidos/{orden_id}/estado", dependencies=[Depends(verify_api_key)])
def update_estado(orden_id: int, nuevo_estado: str, motivo: Optional[str] = None, db: Session = Depends(get_db)):
    success = crud.update_estado_pedido(db, orden_id, nuevo_estado, motivo)
    if not success:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return {"ok": True}

@app.put("/pedidos/{orden_id}/pago", dependencies=[Depends(verify_api_key)])
def update_pago(orden_id: int, data: schemas.PagoUpdate, db: Session = Depends(get_db)):
    success = crud.update_pago_pedido(db, orden_id, data.metodo_pago, data.paga_con)
    if not success:
         raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return {"ok": True}

@app.delete("/pedidos/{orden_id}", dependencies=[Depends(verify_api_key)])
def delete_pedido(orden_id: int, db: Session = Depends(get_db)):
    success = crud.delete_pedido(db, orden_id)
    if not success:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return {"ok": True}

@app.put("/admin/menu/visibilidad-global", dependencies=[Depends(verify_api_key)])
def toggle_global_visibility(is_active: int, db: Session = Depends(get_db)):
    crud.update_all_platillos_visibility(db, is_active)
    return {"ok": True}

@app.put("/menu/{item_id}/visibilidad", dependencies=[Depends(verify_api_key)])
def toggle_menu_item(item_id: int, is_active: int, db: Session = Depends(get_db)):
    success = crud.toggle_platillo_visibility(db, item_id, is_active)
    if not success:
         raise HTTPException(status_code=404, detail="Platillo no encontrado")
    return {"ok": True}

@app.post("/admin/login")
def admin_login(creds: schemas.LoginRequest, db: Session = Depends(get_db)):
    is_valid = crud.verify_admin_password(db, creds.password)
    if not is_valid:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    return {"authenticated": True}

@app.post("/admin/change-password", dependencies=[Depends(verify_api_key)])
def admin_change_pass(data: schemas.PasswordUpdate, db: Session = Depends(get_db)):
    crud.change_admin_password(db, data.new_password)
    return {"ok": True}

@app.post("/upload", dependencies=[Depends(verify_api_key)])
async def upload_file(file: UploadFile = File(...)):
    from PIL import Image
    import io
    
    # 1. Leer contenido de forma asíncrona
    content = await file.read()
    
    # 2. Generar nombre con extensión .webp
    base_name = os.path.splitext(file.filename)[0]
    filename = f"{base_name}.webp"
    file_location = os.path.join(UPLOAD_DIR, filename)
    
    try:
        # 3. Abrir imagen desde memoria y convertir a WebP
        img = Image.open(io.BytesIO(content))
        # Convertir a RGB si es necesario (ej: de RGBA o CMYK)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        # 4. Guardar optimizada
        img.save(file_location, "WEBP", quality=80, method=6)
        return {"filename": filename}
    except Exception as e:
        print(f"Error procesando imagen: {e}")
        # Fallback: guardar tal cual si Pillow falla (aunque no es lo ideal)
        with open(file_location, "wb+") as file_object:
            file_object.write(content)
        return {"filename": filename}

@app.delete("/upload/{filename}", dependencies=[Depends(verify_api_key)])
async def delete_file(filename: str):
    file_location = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(file_location):
        os.remove(file_location)
        return {"ok": True, "message": f"Archivo {filename} eliminado"}
    raise HTTPException(status_code=404, detail="Archivo no encontrado")

@app.get("/upload/list", dependencies=[Depends(verify_api_key)])
async def list_uploads():
    """Retorna una lista de todos los archivos en la carpeta de subidas."""
    if not os.path.exists(UPLOAD_DIR):
        return {"files": []}
    return {"files": os.listdir(UPLOAD_DIR)}

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
    return {"message": "API de Antojitos Doña Soco funcionando"}

@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    # 1. Rutas de API y Estáticos del Backend: Dejar que FastAPI las maneje normalmente
    if full_path.startswith(("menu", "opciones", "configuracion", "pedidos", "admin/", "upload", "static")):
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
