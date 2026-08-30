from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from config import get_settings

settings = get_settings()
CONNECTION_URL = (
    f"postgresql://{settings.postgres_user}:{settings.postgres_password}"
    f"@localhost:5432/{settings.postgres_db}"
)

engine = create_engine(CONNECTION_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
