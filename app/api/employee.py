from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from sqlalchemy.orm import joinedload

from app.database import get_session
from app.models import Employee, Otdel, Post, Role

class EmployeeCreate(BaseModel):
    surname: str
    name: str
    patronymic: str
    login: str
    password: str
    otdel_id: int
    post_id: int
    role_id: int

class EmployeeResponse(BaseModel):
    employee_id: int
    surname: str
    name: str
    patronymic: str
    login: str
    idle_hours: int
    name_otdel: str
    name_role: str
    name_post: str

    class Config:
        from_attributes = True

class EmployeeUpdate(BaseModel):
    surname: Optional[str] = None
    name: Optional[str] = None
    patronymic: Optional[str] = None
    login: Optional[str] = None
    password: Optional[str] = None
    otdel_id: Optional[int] = None
    post_id: Optional[int] = None
    role_id: Optional[int] = None

class EmployeeAddHours(BaseModel):
    idle_hours: int


router = APIRouter(prefix="/employees", tags=["employees"])


@router.post("/create", response_model=EmployeeResponse)
async def create_employee(employee: EmployeeCreate, db: AsyncSession = Depends(get_session)):
    """
    Создание нового сотрудника
    """
    try:

        otdel_result = await db.execute(select(Otdel).where(Otdel.otdel_id == employee.otdel_id))
        existing_otdel = otdel_result.scalars().first()
        if not existing_otdel:
            raise HTTPException(status_code=400, detail="Отдела с таким id не существует")

        # Проверяем существование должности
        post_result = await db.execute(select(Post).where(Post.post_id == employee.post_id))
        existing_post = post_result.scalars().first()
        if not existing_post:
            raise HTTPException(status_code=400, detail="Должности с таким id не существует")

        # Проверяем существование роли
        role_result = await db.execute(select(Role).where(Role.role_id == employee.role_id))
        existing_role = role_result.scalars().first()
        if not existing_role:
            raise HTTPException(status_code=400, detail="Роли с таким id не существует")

        # Создаем сотрудника
        db_employee = Employee(
            surname=employee.surname,
            name=employee.name,
            patronymic=employee.patronymic,
            login=employee.login,
            password=employee.password,  # В реальном приложении хэшируйте пароль!
            idle_hours=0,
            otdel_id=employee.otdel_id,
            post_id=employee.post_id,
            role_id=employee.role_id
        )

        db.add(db_employee)
        await db.commit()
        await db.refresh(db_employee)

        # Получаем сотрудника с JOIN для связанных данных
        result = await db.execute(
            select(Employee).options(
                joinedload(Employee.otdel),
                joinedload(Employee.post),
                joinedload(Employee.role)
            ).where(Employee.employee_id == db_employee.employee_id)
        )

        created_employee = result.scalars().first()

        return EmployeeResponse(
            employee_id=created_employee.employee_id,
            surname=created_employee.surname,
            name=created_employee.name,
            patronymic=created_employee.patronymic,
            login=created_employee.login,
            idle_hours=created_employee.idle_hours,
            name_otdel=created_employee.otdel.name_otdel,
            name_post=created_employee.post.name_post,
            name_role=created_employee.role.name_role
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при создании сотрудника: {str(e)}")


@router.get("/all", response_model=List[EmployeeResponse])
async def get_all_employees(db: AsyncSession = Depends(get_session)):
    """
    Получение всех сотрудников
    """
    result = await db.execute(
        select(Employee).options(
            joinedload(Employee.otdel),
            joinedload(Employee.post),
            joinedload(Employee.role)
        )
    )
    employees = result.scalars().unique().all()

    return [
        EmployeeResponse(
            employee_id=emp.employee_id,
            surname=emp.surname,
            name=emp.name,
            patronymic=emp.patronymic,
            login=emp.login,
            idle_hours=emp.idle_hours,
            name_otdel=emp.otdel.name_otdel,
            name_post=emp.post.name_post,
            name_role=emp.role.name_role
        )
        for emp in employees
    ]


@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(employee_id: int, db: AsyncSession = Depends(get_session)):
    """
    Получение сотрудника по ID
    """
    result = await db.execute(
        select(Employee).options(
            joinedload(Employee.otdel),
            joinedload(Employee.post),
            joinedload(Employee.role)
        ).where(Employee.employee_id == employee_id)
    )

    employee = result.scalars().first()

    if not employee:
        raise HTTPException(status_code=404, detail="Такой сотрудник не найден")
    return EmployeeResponse(
            employee_id=employee.employee_id,
            surname=employee.surname,
            name=employee.name,
            patronymic=employee.patronymic,
            login=employee.login,
            idle_hours=employee.idle_hours,
            name_otdel=employee.otdel.name_otdel,
            name_post=employee.post.name_post,
            name_role=employee.role.name_role)

@router.put("/{employee_id}/add-hours", response_model= EmployeeResponse)
async def add_hours(employee_id: int, employee_add_hours: EmployeeAddHours, db: AsyncSession = Depends(get_session)):

    #Получение сотрудника
    result = await db.execute(
        select(Employee).where(Employee.employee_id == employee_id)
    )
    db_employee = result.scalar_one_or_none()

    if not db_employee:
        raise HTTPException(status_code=404, detail="Такой сотрудник не найден")

    db_employee.idle_hours += employee_add_hours.idle_hours

    await db.commit()
    await db.refresh(db_employee)

    # Получаем обновленного сотрудника с связанными данными
    result = await db.execute(
        select(Employee).options(
            joinedload(Employee.otdel),
            joinedload(Employee.post),
            joinedload(Employee.role)
        ).where(Employee.employee_id == employee_id)
    )

    employee_with_relations = result.scalars().first()

    return EmployeeResponse(
        employee_id=employee_with_relations.employee_id,
        surname=employee_with_relations.surname,
        name=employee_with_relations.name,
        patronymic=employee_with_relations.patronymic,
        login=employee_with_relations.login,
        idle_hours=employee_with_relations.idle_hours,
        name_otdel=employee_with_relations.otdel.name_otdel,
        name_post=employee_with_relations.post.name_post,
        name_role=employee_with_relations.role.name_role
    )



@router.patch("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
        employee_id: int,
        employee_update: EmployeeUpdate,
        db: AsyncSession = Depends(get_session)
):
    """
    Частичное обновление сотрудника
    """
    # Получаем сотрудника
    result = await db.execute(
        select(Employee).where(Employee.employee_id == employee_id)
    )
    db_employee = result.scalar_one_or_none()

    if not db_employee:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")

    # Проверяем и обновляем только переданные поля
    update_data = employee_update.dict(exclude_unset=True)

    # Если переданы ID связанных сущностей, проверяем их существование
    if 'otdel_id' in update_data:
        otdel_result = await db.execute(select(Otdel).where(Otdel.otdel_id == update_data['otdel_id']))
        if not otdel_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Отдела с таким id не существует")

    if 'post_id' in update_data:
        post_result = await db.execute(select(Post).where(Post.post_id == update_data['post_id']))
        if not post_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Должности с таким id не существует")

    if 'role_id' in update_data:
        role_result = await db.execute(select(Role).where(Role.role_id == update_data['role_id']))
        if not role_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Роли с таким id не существует")

    # Обновляем поля
    for field, value in update_data.items():
        setattr(db_employee, field, value)

    await db.commit()
    await db.refresh(db_employee)

    # Получаем обновленного сотрудника с связанными данными
    result = await db.execute(
        select(Employee).options(
            joinedload(Employee.otdel),
            joinedload(Employee.post),
            joinedload(Employee.role)
        ).where(Employee.employee_id == employee_id)
    )

    updated_employee = result.scalars().first()

    return EmployeeResponse(
        employee_id=updated_employee.employee_id,
        surname=updated_employee.surname,
        name=updated_employee.name,
        patronymic=updated_employee.patronymic,
        login=updated_employee.login,
        idle_hours=updated_employee.idle_hours,
        name_otdel=updated_employee.otdel.name_otdel,
        name_post=updated_employee.post.name_post,
        name_role=updated_employee.role.name_role
    )


@router.delete("/{employee_id}")
async def delete_employee(employee_id: int, db: AsyncSession = Depends(get_session)):
    """
    Удаление сотрудника
    """
    result = await db.execute(select(Employee).where(Employee.employee_id == employee_id))
    employee = result.scalar_one_or_none()

    if not employee:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")

    await db.delete(employee)
    await db.commit()
    return {"message": "Сотрудник успешно удален"}