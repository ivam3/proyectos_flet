import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Cargar variables desde .env si existe
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Producción → PostgreSQL
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True
    )
else:
    # Local → SQLite (en carpeta uploads para persistencia)
    os.makedirs("static/uploads", exist_ok=True)
    DATABASE_URL = "sqlite:///./static/uploads/stock_management.db"
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
