from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./booking.db" #change this when start use postgres

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()  # Создаем реальный объект сессии
    try:
        yield db         # Отдаем сессию в FastAPI эндпоинт
    finally:
        db.close()       # Гарантированно закрываем её после ответа сервера