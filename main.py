from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import init_db, get_session
from app.api import otdel, post, employee, action
from contextlib import asynccontextmanager

from app.models import Employee


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print("База данных собрана")
    yield
    print("Приложение отключено...")

app = FastAPI(
    title="Employee Overtime API",
    description="API для учета переработок сотрудников",
    version="1.0.0",
    lifespan=lifespan
)

# Подключаем роутеры
app.include_router(otdel.router)
app.include_router(post.router)
app.include_router(employee.router)
app.include_router(action.router)

@app.get("/")
async def root():
    return {"message": "API для учета переработок сотрудников"}

@app.get("/health")
async def health_check():
    return {"status": "работает"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)