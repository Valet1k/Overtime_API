from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.database import get_session  # импорт асинхронной сессии
from app.models import Post

class PostCreate(BaseModel):
    name_post: str

class PostResponse(BaseModel):
    post_id: int
    name_post: str

    class Config:
        from_attributes = True


router = APIRouter(prefix="/posts", tags=["posts"])


@router.post("/create", response_model=PostResponse)
async def create_post(post: PostCreate, db: AsyncSession = Depends(get_session)):
    """
    Создание новой должности
    """
    try:
        # Проверяем, существует ли должность с таким названием
        result = await db.execute(
            select(Post).where(Post.name_post == post.name_post)
        )
        existing_post = result.scalars().first()

        if existing_post:
            raise HTTPException(status_code=400, detail="Такая должность уже существует")

        # Создаем новую должность
        db_post = Post(name_post=post.name_post)
        db.add(db_post)
        await db.commit()
        await db.refresh(db_post)

        return db_post

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при создании должности: {str(e)}")


@router.get("/all", response_model=List[PostResponse])
async def get_all_posts(db: AsyncSession = Depends(get_session)):
    """
    Получение всех должностей
    """
    try:
        result = await db.execute(select(Post))
        posts = result.scalars().all()

        # Если Post уже соответствует PostResponse, можно вернуть напрямую
        # Если нет - преобразуем
        return [
            PostResponse(
                post_id=post.post_id,
                name_post=post.name_post
            )
            for post in posts
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении должностей: {str(e)}")


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: int, db: AsyncSession = Depends(get_session)):
    """
    Получение должности по ID
    """
    result = await db.execute(select(Post).where(Post.post_id == post_id))
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="Такая должность не найдена")
    return post


@router.put("/{post_id}", response_model=PostResponse)
async def update_post(post_id: int, post: PostCreate, db: AsyncSession = Depends(get_session)):
    """
    Обновление должности
    """
    result = await db.execute(select(Post).where(Post.post_id == post_id))
    db_post = result.scalar_one_or_none()

    if not db_post:
        raise HTTPException(status_code=404, detail="Должность не найдена")

    db_post.name_otdel = post.name_post
    await db.commit()
    await db.refresh(db_post)
    return db_post


@router.delete("/{post_id}")
async def delete_post(post_id: int, db: AsyncSession = Depends(get_session)):
    """
    Удаление должности
    """
    result = await db.execute(select(Post).where(Post.post_id == post_id))
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="Должность не найдена")

    await db.delete(post)
    await db.commit()
    return {"message": "Должность успешно удалена"}