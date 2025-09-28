from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

import os

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "data")
os.makedirs(DB_DIR, exist_ok=True)
SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.abspath(os.path.join(DB_DIR, 'app.db'))}"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()