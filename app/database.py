from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base
from app.models import Role, ActionType


DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def create_default_roles():
    async with async_session() as session:
        if not await session.get(Role, 1):  # Проверяем по первой роли
            session.add_all([
                Role(role_id=1, name_role="админ"),
                Role(role_id=2, name_role="сотрудник")
            ])
            await session.commit()

async def create_defualt_actiontypes():
 async with async_session() as session:
     if not await session.get(ActionType, 1):
         session.add_all([
             ActionType(actiontype_id=1, name_type="Выходной"),
             ActionType(actiontype_id=2, name_type="Переработка")
         ])
         await session.commit()

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await create_default_roles()
    await create_defualt_actiontypes()

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session