from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

#this creates actual file on cpu
SQLALCHEMY_DATABASE_URL = "sqlite:///./adoptimizer.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

#This is helping function to get db session
#Helper for fast api
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()