from sqlmodel import create_engine, Session, SQLModel, text
from src.core.config import settings
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# We use connection pooling arguments suitable for a production app
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    echo=False, 
    pool_pre_ping=True, 
    pool_size=10, 
    max_overflow=20
)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    # Safely migrate existing databases with new Auth columns
    with Session(engine) as session:
        try:
            session.exec(text("ALTER TABLE \"user\" ADD COLUMN hashed_password VARCHAR"))
            session.commit()
        except Exception:
            session.rollback()

def get_session():
    """Dependency for getting a database session."""
    with Session(engine) as session:
        yield session
