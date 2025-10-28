from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from datetime import date, datetime


from app.database import get_session  # импорт асинхронной сессии
from app.models import Action, Employee, ActionType
from app.api.employee import add_hours, EmployeeAddHours

class ActionCreate(BaseModel):
    hours: int
    date_action: str
    employee_id: int
    actiontype_id: int

class ActionResponse(BaseModel):
    action_id: int
    hours: int
    date_action: date
    employee_id: int
    actiontype_id: int

    class Config:
        from_attributes = True


router = APIRouter(prefix="/actions", tags=["actions"])


@router.post("/create", response_model=ActionResponse)
async def create_action(action: ActionCreate, db: AsyncSession = Depends(get_session)):
    """
    Создание нового действия
    """
    try:
        # Проверка существование сотрудника
        employee_result = await db.execute(select(Employee).where(Employee.employee_id == action.employee_id))
        existing_employee = employee_result.scalars().first()
        if not existing_employee:
            raise HTTPException(status_code=400, detail="Сотрудника с таким id не существует")

        actiontype_result = await db.execute(select(ActionType).where(ActionType.actiontype_id == action.actiontype_id))
        existing_actiontype = actiontype_result.scalars().first()
        if not existing_actiontype:
            raise HTTPException(status_code=400, detail="Типа действия с таким id не существует")

        # Создаем новое действие сотруднику
        db_action = Action( hours = action.hours,
                            date_action = datetime.strptime(action.date_action, "%Y-%m-%d"),
                            employee_id = action.employee_id,
                            actiontype_id = action.actiontype_id)
        db.add(db_action)
        existing_employee.idle_hours += action.hours
        await db.commit()
        await db.refresh(db_action)

        return db_action

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при создании действия: {str(e)}")


@router.get("/all", response_model=List[ActionResponse])
async def get_all_actions(db: AsyncSession = Depends(get_session)):
    """
    Получение всех действий
    """
    result = await db.execute(select(Action))
    actions = result.scalars().all()
    return actions


@router.get("/{action_id}", response_model=ActionResponse)
async def get_actions(action_id: int, db: AsyncSession = Depends(get_session)):
    """
    Получение типа дейсвия  по ID
    """
    result = await db.execute(select(Action).where(Action.action_id == action_id))
    action = result.scalar_one_or_none()

    if not action:
        raise HTTPException(status_code=404, detail="Такое действие не найдено")
    return action


# @router.put("/{post_id}", response_model=ActionResponse)
# async def update_post(post_id: int, post: ActionCreate, db: AsyncSession = Depends(get_session)):
#     """
#     Обновление действия
#     """
#     result = await db.execute(select(Action).where(Action.action_id))
#     db_action = result.scalar_one_or_none()
#
#     if not db_action:
#         raise HTTPException(status_code=404, detail="Действие не найдено")
#
#     db_action.action_id =
#     await db.commit()
#     await db.refresh(db_action)
#     return db_action


@router.delete("/{action_id}")
async def delete_action(action_id: int, db: AsyncSession = Depends(get_session)):
    """
    Удаление должности
    """
    result = await db.execute(select(Action).where(Action.action_id == action_id))
    action = result.scalar_one_or_none()

    if not action:
        raise HTTPException(status_code=404, detail="Действие не найдено")

    await db.delete(action)
    await db.commit()
    return {"message": "Действие успешно удалено"}