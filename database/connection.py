import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config.settings import settings

db_url = settings.DATABASE_URL
# Let's check if we can connect to postgres, if not fallback to sqlite automatically for local development
if "postgresql" in db_url:
    try:
        # Check connection quickly, otherwise fallback
        import psycopg2
        # simple check
        conn = psycopg2.connect(
            dsn=db_url,
            connect_timeout=2
        )
        conn.close()
    except Exception:
        print("PostgreSQL connection failed. Falling back to local SQLite database (aerosafe.db).")
        db_url = "sqlite:///./aerosafe.db"

engine = create_engine(db_url, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
