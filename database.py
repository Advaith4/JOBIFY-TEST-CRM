import os
from dotenv import load_dotenv
from sqlmodel import SQLModel, create_engine, Session

load_dotenv()

# We read DATABASE_URL out of the environment (set via .env)
# The user will supply their Supabase Postgres URL here
DATABASE_URL = os.environ.get("DATABASE_URL")

engine = None

if DATABASE_URL:
    # Supabase gives connection strings starting with postgres:// instead of postgresql://
    # SQLAlchemy requires postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    engine = create_engine(DATABASE_URL, echo=False)

def create_db_and_tables():
    if engine:
        SQLModel.metadata.create_all(engine)

def get_session():
    if not engine:
        # Yield none if database setup is incomplete, handling it in endpoints
        yield None
    else:
        with Session(engine) as session:
            yield session
