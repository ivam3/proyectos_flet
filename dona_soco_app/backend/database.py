import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Render / Producción → PostgreSQL
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True
    )
else:
    # Local / Railway SQLite → Usar la subcarpeta 'uploads' que es donde está el volumen
    os.makedirs("static/uploads", exist_ok=True)
    DATABASE_URL = "sqlite:///./static/uploads/backend_dona_soco.db"
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
