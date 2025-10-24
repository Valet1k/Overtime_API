from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.database import get_session  # импорт асинхронной сессии
from app.models import Otdel

class OtdelCreate(BaseModel):
    name_otdel: str

class OtdelResponse(BaseModel):
    otdel_id: int
    name_otdel: str

    class Config:
        from_attributes = True


router = APIRouter(prefix="/otdels", tags=["otdels"])


@router.post("/create", response_model=OtdelResponse)
async def create_otdel(otdel: OtdelCreate, db: AsyncSession = Depends(get_session)):
    """
    Создание нового отдела
    """
    try:
        # Проверяем, существует ли отдел с таким названием
        result = await db.execute(
            select(Otdel).where(Otdel.name_otdel == otdel.name_otdel)
        )
        existing_otdel = result.scalars().first()

        if existing_otdel:
            raise HTTPException(status_code=400, detail="Отдел с таким названием уже существует")

        # Создаем новый отдел
        db_otdel = Otdel(name_otdel=otdel.name_otdel)
        db.add(db_otdel)
        await db.commit()
        await db.refresh(db_otdel)

        return db_otdel

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при создании отдела: {str(e)}")


@router.get("/all", response_model=List[OtdelResponse])
async def get_all_otdels(db: AsyncSession = Depends(get_session)):
    """
    Получение всех отделов
    """
    result = await db.execute(select(Otdel))
    otdels = result.scalars().all()
    return otdels


@router.get("/{otdel_id}", response_model=OtdelResponse)
async def get_otdel(otdel_id: int, db: AsyncSession = Depends(get_session)):
    """
    Получение отдела по ID
    """
    result = await db.execute(select(Otdel).where(Otdel.otdel_id == otdel_id))
    otdel = result.scalar_one_or_none()

    if not otdel:
        raise HTTPException(status_code=404, detail="Отдел не найден")
    return otdel


@router.put("/{otdel_id}", response_model=OtdelResponse)
async def update_otdel(otdel_id: int, otdel: OtdelCreate, db: AsyncSession = Depends(get_session)):
    """
    Обновление отдела
    """
    result = await db.execute(select(Otdel).where(Otdel.otdel_id == otdel_id))
    db_otdel = result.scalar_one_or_none()

    if not db_otdel:
        raise HTTPException(status_code=404, detail="Отдел не найден")

    db_otdel.name_otdel = otdel.name_otdel
    await db.commit()
    await db.refresh(db_otdel)
    return db_otdel


@router.delete("/{otdel_id}")
async def delete_otdel(otdel_id: int, db: AsyncSession = Depends(get_session)):
    """
    Удаление отдела
    """
    result = await db.execute(select(Otdel).where(Otdel.otdel_id == otdel_id))
    otdel = result.scalar_one_or_none()

    if not otdel:
        raise HTTPException(status_code=404, detail="Отдел не найден")

    await db.delete(otdel)
    await db.commit()
    return {"message": "Отдел успешно удален"}