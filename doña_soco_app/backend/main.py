from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional
import os

from . import crud, models, schemas
from .database import SessionLocal, engine

# Crear tablas automáticamente (en producción usar Alembic para migraciones)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Doña Soco API")

# Configurar CORS para permitir que Flet (Web/Android) se conecte
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En producción restringir a dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency para obtener la sesión de BD
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- RUTAS DE MENU ---
@app.get("/menu", response_model=List[schemas.Menu])
def read_menu(solo_activos: bool = True, search: Optional[str] = None, db: Session = Depends(get_db)):
    return crud.get_menu(db, solo_activos, search)

@app.post("/menu", response_model=schemas.Menu)
def create_menu_item(item: schemas.MenuCreate, db: Session = Depends(get_db)):
    return crud.create_platillo(db, item)

@app.put("/menu/{item_id}", response_model=schemas.Menu)
def update_menu_item(item_id: int, item: schemas.MenuCreate, db: Session = Depends(get_db)):
    db_item = crud.update_platillo(db, item_id, item)
    if not db_item:
        raise HTTPException(status_code=404, detail="Platillo no encontrado")
    return db_item

@app.delete("/menu/{item_id}")
def delete_menu_item(item_id: int, db: Session = Depends(get_db)):
    success = crud.delete_platillo(db, item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Platillo no encontrado")
    return {"ok": True}

# --- RUTAS DE CONFIGURACION ---
@app.get("/configuracion", response_model=schemas.Configuracion)
def read_config(db: Session = Depends(get_db)):
    return crud.get_configuracion(db)

@app.put("/configuracion", response_model=schemas.Configuracion)
def update_config(config: schemas.ConfiguracionUpdate, db: Session = Depends(get_db)):
    return crud.update_configuracion(db, config)

# --- RUTAS DE PEDIDOS ---
@app.post("/pedidos", response_model=schemas.Orden)
def create_pedido(orden: schemas.OrdenCreate, db: Session = Depends(get_db)):
    return crud.create_pedido(db, orden)

@app.get("/pedidos/seguimiento", response_model=schemas.Orden)
def track_pedido(telefono: str, codigo: str, db: Session = Depends(get_db)):
    orden = crud.get_pedido_by_tracking(db, telefono, codigo)
    if not orden:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return orden

@app.get("/pedidos", response_model=List[schemas.Orden])
def read_pedidos(skip: int = 0, limit: int = 100, search: Optional[str] = None, db: Session = Depends(get_db)):
    return crud.get_pedidos(db, skip, limit, search)

@app.put("/pedidos/{orden_id}/estado")
def update_estado(orden_id: int, nuevo_estado: str, motivo: Optional[str] = None, db: Session = Depends(get_db)):
    success = crud.update_estado_pedido(db, orden_id, nuevo_estado, motivo)
    if not success:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return {"ok": True}

@app.put("/pedidos/{orden_id}/pago")
def update_pago(orden_id: int, data: schemas.PagoUpdate, db: Session = Depends(get_db)):
    success = crud.update_pago_pedido(db, orden_id, data.metodo_pago, data.paga_con)
    if not success:
         raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return {"ok": True}

@app.put("/admin/menu/visibilidad-global")
def toggle_global_visibility(is_active: int, db: Session = Depends(get_db)):
    crud.update_all_platillos_visibility(db, is_active)
    return {"ok": True}

@app.put("/menu/{item_id}/visibilidad")
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

@app.post("/admin/change-password")
def admin_change_pass(data: schemas.PasswordUpdate, db: Session = Depends(get_db)):
    crud.change_admin_password(db, data.new_password)
    return {"ok": True}

# --- ARCHIVOS ESTÁTICOS (IMÁGENES) ---
# Creamos carpeta si no existe
os.makedirs("backend/static/uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="backend/static"), name="static")

from fastapi import UploadFile, File
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_location = f"backend/static/uploads/{file.filename}"
    with open(file_location, "wb+") as file_object:
        file_object.write(file.file.read())
    return {"filename": file.filename}

@app.get("/")
def read_root():
    return {"message": "API de Antojitos Doña Soco funcionando"}
