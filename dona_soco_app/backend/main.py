from fastapi import FastAPI, Depends, HTTPException, status, Header, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os

import crud, models, schemas
from database import SessionLocal, engine, get_db

# --- SEGURIDAD ---
API_KEY_NAME = "X-API-KEY"
API_KEY = os.getenv("API_SECRET_KEY", "ads2026_Ivam3byCinderella")

async def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Acceso denegado: API Key inválida"
        )
    return x_api_key

# Crear tablas automáticamente
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Antojitos Doña Soco API")

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
    file_location = f"backend/static/uploads/{file.filename}"
    with open(file_location, "wb+") as file_object:
        file_object.write(file.file.read())
    return {"filename": file.filename}

# --- ARCHIVOS ESTÁTICOS ---

# 1. Servir las subidas de imágenes
os.makedirs("backend/static/uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="backend/static"), name="static")

# 2. Servir la Web App (si existe la carpeta 'web')
if os.path.exists("web"):
    app.mount("/", StaticFiles(directory="web", html=True), name="web")

@app.get("/")
def read_root():
    if os.path.exists("web/index.html"):
        return FileResponse("web/index.html")
    return {"message": "API de Antojitos Doña Soco funcionando"}

# Fallback para SPA
@app.exception_handler(404)
async def spa_fallback(request, exc):
    # Si la ruta no empieza con /static o endpoints de la API, servimos index.html
    api_paths = ("/menu", "/opciones", "/configuracion", "/pedidos", "/admin", "/upload")
    if not request.url.path.startswith(api_paths) and not request.url.path.startswith("/static"):
        if os.path.exists("web/index.html"):
            return FileResponse("web/index.html")
    return JSONResponse({"detail": "Not Found"}, status_code=404)
