import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker


DB_USER = os.getenv("DB_USER", "admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "admin123")
DB_HOST = os.getenv("DB_HOST", "database-1.crkk4ikcqcb2.ap-south-1.rds.amazonaws.com")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "tasks")

if not DB_PASSWORD:
    raise RuntimeError("DB_PASSWORD is not set. Please configure it before starting the app.")

CONNECTION_STRING = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}"
DATABASE_URL = f"{CONNECTION_STRING}/{DB_NAME}"


def initialize_database() -> None:
    """Ensure database and all required tables exist before usage."""
    bootstrap_engine = create_engine(CONNECTION_STRING, echo=True, future=True)
    try:
        with bootstrap_engine.connect() as connection:
            connection.execute(text(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}`"))
            connection.commit()
    finally:
        bootstrap_engine.dispose()

    from db.models import Base

    Base.metadata.create_all(bind=engine)

    required_tables = set(Base.metadata.tables.keys())
    existing_tables = set(inspect(engine).get_table_names())
    missing_tables = required_tables - existing_tables
    if missing_tables:
        raise RuntimeError(
            f"Database initialization failed. Missing tables: {sorted(missing_tables)}"
        )


engine = create_engine(DATABASE_URL, echo=True, future=True)
session_local = sessionmaker(bind=engine)

initialize_database()