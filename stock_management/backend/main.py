from fastapi import FastAPI, Depends, HTTPException, status, Header, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
import uuid

import crud, models, schemas
from database import engine, get_db

# Inicializar Base de Datos
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Risk Shoes Stock API")

# Configuración de Seguridad
API_KEY_MASTER = os.getenv("API_SECRET_KEY", "risk2026_Ivam3byCinderella")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DEPENDENCIAS ---
async def get_tenant_id(x_tenant_id: str = Header(..., alias="X-Tenant-ID")):
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="X-Tenant-ID required")
    return x_tenant_id

async def verify_api_key(x_api_key: Optional[str] = Header(None, alias="X-API-KEY")):
    if not x_api_key or x_api_key != API_KEY_MASTER:
        raise HTTPException(status_code=401, detail="Invalid API KEY")
    return True

# --- RUTAS ---
@app.get("/")
def read_root():
    return {"message": "Risk Shoes Stock API working"}

@app.get("/products", response_model=List[schemas.Product])
def read_products(
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
):
    return crud.get_products(db, tenant_id, search)

@app.post("/products", response_model=schemas.Product, dependencies=[Depends(verify_api_key)])
def create_product(
    product: schemas.ProductCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
):
    result = crud.create_product(db, tenant_id, product)
    if result == "DUPLICATE_SKU":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="PRODUCT_ALREADY_IN_STOCK"
        )
    if result is None:
        raise HTTPException(status_code=500, detail="Error creating product")
    return result

@app.put("/products/{product_id}", response_model=schemas.Product, dependencies=[Depends(verify_api_key)])
def update_product(
    product_id: int,
    product: schemas.ProductCreate,
    db: Session = Depends(get_db)
):
    db_product = crud.update_product(db, product_id, product)
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product

from fastapi.responses import FileResponse, StreamingResponse
import pandas as pd
import io
from datetime import datetime

@app.delete("/products/{product_id}", dependencies=[Depends(verify_api_key)])
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
):
    if not crud.delete_product(db, tenant_id, product_id):
        raise HTTPException(status_code=404, detail="Product not found")
    return {"ok": True}

@app.post("/movements", dependencies=[Depends(verify_api_key)])
def create_movement(
    movement: schemas.MovementCreate,
    db: Session = Depends(get_db)
):
    result = crud.update_stock(db, movement)
    if result == "DUPLICATE_SALES_ID":
        raise HTTPException(status_code=409, detail="SALES_ID_ALREADY_EXISTS")
    if result is None:
        raise HTTPException(status_code=404, detail="Size not found")
    if result is False:
        raise HTTPException(status_code=400, detail="Insufficient stock")
    return {"ok": True, "new_stock": result.stock}

@app.post("/movements/{movement_id}/cancel", dependencies=[Depends(verify_api_key)])
def cancel_movement(
    movement_id: int,
    cancel_data: dict, # { "reason": str, "is_waste": bool }
    db: Session = Depends(get_db)
):
    reason = cancel_data.get("reason", "Sin motivo")
    is_waste = cancel_data.get("is_waste", False)
    
    result = crud.cancel_movement(db, movement_id, reason, is_waste)
    if result is None:
        raise HTTPException(status_code=404, detail="Movement not found")
    if result == "ALREADY_CANCELLED":
        raise HTTPException(status_code=400, detail="Already cancelled")
    
    return {"ok": True, "status": "CANCELLED"}

@app.get("/movements", response_model=List[schemas.Movement])
def read_movements(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
):
    movements = crud.get_movements(db, tenant_id)
    # Usamos from_orm manual por la lógica de mapeo que añadimos en schemas.py
    return [schemas.Movement.from_orm(m) for m in movements]

@app.put("/movements/{movement_id}/status", dependencies=[Depends(verify_api_key)])
def update_movement_status(
    movement_id: int,
    new_status: str,
    db: Session = Depends(get_db)
):
    db_move = db.query(models.Movement).filter(models.Movement.id == movement_id).first()
    if not db_move:
        raise HTTPException(status_code=404, detail="Movement not found")
    db_move.status = new_status
    db.commit()
    return {"ok": True}

# --- EXPORTACIÓN ---
@app.get("/export/inventory", dependencies=[Depends(verify_api_key)])
def export_inventory(
    format: str = "csv",
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
):
    products = crud.get_products(db, tenant_id)
    
    # Aplanar datos: Un registro por cada talla
    flattened_data = []
    for p in products:
        for s in p.sizes:
            flattened_data.append({
                "ID": p.id,
                "Modelo": p.model_name,
                "Marca": p.brand or "",
                "Categoría": p.category or "",
                "Género": p.gender,
                "Condición": p.condition or "Nuevo",
                "SKU": p.sku,
                "Talla": s.size,
                "Stock": s.stock,
                "Precio": p.price,
                "Tax": p.tax or 0.0,
                "Costo": p.cost,
                "Proveedor": p.provider or ""
            })
    
    df = pd.DataFrame(flattened_data)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"inventario_{tenant_id}_{timestamp}"

    if format == "excel":
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Stock')
        output.seek(0)
        headers = {'Content-Disposition': f'attachment; filename="{filename}.xlsx"'}
        return StreamingResponse(output, headers=headers, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    
    # Default CSV
    stream = io.StringIO()
    df.to_csv(stream, index=False)
    response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename={filename}.csv"
    return response

# --- CARGA DE FOTOS ---
UPLOAD_DIR = "static/uploads/photos"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/photos", StaticFiles(directory=UPLOAD_DIR), name="photos")

from PIL import Image
import io

@app.post("/photos/upload/{product_id}", dependencies=[Depends(verify_api_key)])
async def upload_photo(
    product_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        # Abrir imagen usando Pillow
        img = Image.open(file.file)
        
        # Generar nombre con extensión .webp
        filename = f"{uuid.uuid4()}.webp"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        # Guardar como WebP optimizado
        img.save(file_path, "WEBP", quality=80)
        
        return crud.add_product_photo(db, product_id, filename)
    except Exception as e:
        print(f"Error procesando imagen: {e}")
        raise HTTPException(status_code=500, detail="Error processing image")

@app.delete("/photos/{photo_id}", dependencies=[Depends(verify_api_key)])
def delete_photo(photo_id: int, db: Session = Depends(get_db)):
    filename = crud.delete_photo(db, photo_id)
    if not filename:
        raise HTTPException(status_code=404, detail="Photo not found")
    
    # Eliminar archivo físico
    file_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    
    return {"ok": True}

# --- MANTENIMIENTO Y ADMIN ---
@app.post("/admin/reset-password", dependencies=[Depends(verify_api_key)])
def reset_password(data: dict):
    return {"ok": True, "message": "Password reset simulated successfully"}

@app.get("/upload/list", dependencies=[Depends(verify_api_key)])
def list_uploads():
    files = []
    if os.path.exists(UPLOAD_DIR):
        files = os.listdir(UPLOAD_DIR)
    return {"files": [f for f in files if os.path.isfile(os.path.join(UPLOAD_DIR, f))]}

@app.delete("/upload/{filename}", dependencies=[Depends(verify_api_key)])
def delete_upload(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return {"ok": True}
    raise HTTPException(status_code=404, detail="File not found")

@app.post("/admin/maintenance/wipe", dependencies=[Depends(verify_api_key)])
def wipe_database(db: Session = Depends(get_db), tenant_id: str = Depends(get_tenant_id)):
    # ... (lógica existente)
    pass

@app.post("/admin/maintenance/recreate-tables", dependencies=[Depends(verify_api_key)])
def recreate_tables():
    try:
        # ¡ATENCIÓN! Esto borra TODA la estructura y datos de todas las tablas
        models.Base.metadata.drop_all(bind=engine)
        models.Base.metadata.create_all(bind=engine)
        return {"ok": True, "message": "Tables recreated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
