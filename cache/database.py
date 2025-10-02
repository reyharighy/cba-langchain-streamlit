"""Module to cache data and resource from database package."""

# standard
import os

# third-party
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

# internal
from utils import streamlit_cache

@streamlit_cache("Connecting to database", "resource")
def db_connect() -> Engine:
    """Establish a connection to PostgreSQL database.
    
    The connection pool is cached using the default Streamlit st.cache_resource decorator.
    """
    host = os.getenv("PGSQL_HOST", "host")
    user = os.getenv("POSTGRES_USER", "admin")
    pwd = os.getenv("POSTGRES_PASSWORD", "admin")
    port = os.getenv("PGSQL_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "db")

    db_url = f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{db}"

    return create_engine(db_url)
