import logging
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger(__name__)


async def add_user(user_data, session: AsyncSession):
    """
    Добавляет пользователя в базу данных, если он еще не существует.

    Проверяет наличие пользователя по Telegram ID и, в случае отсутствия,
    создает новую запись в таблице `User`.

    Parameters
    ----------
    user_data
        Объект пользователя Telegram (обычно `message.from_user`).
        Используется для получения идентификатора и базовой информации
        о пользователе.
    session : AsyncSession
        Асинхронная SQLAlchemy-сессия.

    Returns
    -------
    None
        Функция не возвращает значение.
    """
    try:
        user = await session.scalar(
            select(User).where(User.tg_id == user_data.id)
        )

        if not user:
            session.add(User(
                tg_id=user_data.id,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                username=user_data.username
            ))
            await session.commit()
    except Exception as e:
        logger.warning(f'add_user error: {e}')


async def delete_user(tg_id: int, session: AsyncSession):
    """
    Удаляет пользователя из базы данных, если он существует.

    Parameters
    ----------
    tg_id : int
        Telegram ID пользователя.
    session : AsyncSession
        Асинхронная SQLAlchemy-сессия.

    Returns
    -------
    None
        Функция не возвращает значение.
    """
    user = await session.scalar(select(User).where(User.tg_id == tg_id))

    if user:
        await session.delete(user)
        await session.commit()


async def update_user(tg_id: int, session: AsyncSession, **update_data) -> bool:
    """
    Обновляет данные пользователя.

    Позволяет изменить любые поля модели User, переданные через `update_data`.
    Автоматически обновляет поле `updated_at` текущей датой и временем.

    Parameters
    ----------
    tg_id : int
        Telegram ID пользователя.
    session : AsyncSession
        Асинхронная SQLAlchemy-сессия.
    **update_data
        Поля для обновления (например: first_name, last_name, username).

    Returns
    -------
    bool
        True, если была обновлена хотя бы одна запись, иначе False.
    """
    if not update_data:
        return False
    
    update_data['updated_at'] = datetime.now()
            
    stmt = (update(User).where(User.tg_id == tg_id).values(**update_data)
    )
            
    result = await session.execute(stmt)
    await session.commit()
            
    return result.rowcount > 0


async def get_data_user(tg_id: int, session: AsyncSession) -> User:
    """
    Получает данные пользователя по Telegram ID.

    Проводит поиск в таблице `User` через SQLAlchemy ORM.

    Parameters
    ----------
    tg_id : int
        Telegram ID пользователя.
    session : AsyncSession
        Асинхронная SQLAlchemy-сессия.

    Returns
    -------
    User
        Объект пользователя.
    """
    user: User = await session.scalar(select(User).where(User.tg_id == tg_id))
        
    return user