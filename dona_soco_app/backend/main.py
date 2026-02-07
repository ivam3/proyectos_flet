from fastapi import FastAPI, Depends, HTTPException, status, Header, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional
import os

import crud, models, schemas
from database import SessionLocal, engine, get_db

# --- SEGURIDAD ---
API_KEY_NAME = "X-API-KEY"
# Esta llave DEBE configurarse en las variables de entorno de Railway
API_KEY = os.getenv("API_SECRET_KEY", "ads2025_super_secret_key_99")

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

# --- RUTAS DE MENU ---
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

# --- RUTAS DE GRUPOS DE OPCIONES ---
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

# --- RUTAS DE CONFIGURACION ---
@app.get("/configuracion", response_model=schemas.Configuracion)
def read_config(db: Session = Depends(get_db)):
    return crud.get_configuracion(db)

@app.put("/configuracion", response_model=schemas.Configuracion, dependencies=[Depends(verify_api_key)])
def update_config(config: schemas.ConfiguracionUpdate, db: Session = Depends(get_db)):
    return crud.update_configuracion(db, config)

# --- RUTAS DE PEDIDOS ---
@app.post("/pedidos", response_model=schemas.Orden)
def create_pedido(orden: schemas.OrdenCreate, db: Session = Depends(get_db)):
    # Los pedidos son públicos para que los clientes compren, pero puedes protegerlo si gustas.
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

# --- RUTAS DE AUTH ADMIN ---
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

# --- ARCHIVOS ESTÁTICOS ---
os.makedirs("backend/static/uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="backend/static"), name="static")

@app.post("/upload", dependencies=[Depends(verify_api_key)])
async def upload_file(file: UploadFile = File(...)):
    file_location = f"backend/static/uploads/{file.filename}"
    with open(file_location, "wb+") as file_object:
        file_object.write(file.file.read())
    return {"filename": file.filename}

@app.get("/")
def read_root():
    return {"message": "API de Antojitos Doña Soco funcionando"}