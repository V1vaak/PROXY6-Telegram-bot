from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Basket, User


async def add_data_proxies_to_basket(tg_id: int, data: dict, session: AsyncSession) -> Basket:
    """
    Добавляет выбранные пользователем параметры прокси в корзину.

    Parameters
    ----------
    tg_id : int
        Telegram ID пользователя
    data : dict
        Данные из FSM:
        {
            proxy_version: int,
            proxy_type: str,
            country: str,
            count: int,
            period: int
        }
    session : AsyncSession
        SQLAlchemy async session

    Returns
    -------
    Basket
        Созданная позиция корзины
    """

    result = await session.execute(
        select(User).where(User.tg_id == tg_id)
    )
    user = result.scalar_one()

    item = Basket(
        user_id=user.id,
        proxy_version=data['proxy_version'],
        proxy_type=data['proxy_type'],
        country=data['country'],
        count=data['count'],
        period=data['period'],
    )

    session.add(item)
    await session.commit()
    await session.refresh(item)

    return item

async def delete_user_basket(tg_id: int, session: AsyncSession) -> None:
    """
    Удаляет все элементы корзины пользователя по Telegram ID.

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
    await session.execute(
        delete(Basket)
        .where(Basket.user_id == select(User.id).where(User.tg_id == tg_id).scalar_subquery())
    )
    await session.commit()


async def delete_basket_items(basket_ids: list[int], session: AsyncSession) -> None:
    """
    Удаляет конкретные элементы корзины по их ID.

    Parameters
    ----------
    basket_ids : list[int]
        Список ID элементов корзины для удаления.
    session : AsyncSession
        Асинхронная SQLAlchemy-сессия.

    Returns
    -------
    None
        Функция не возвращает значение.
    """
    await session.execute(
        delete(Basket).where(Basket.id.in_(basket_ids))
    )
    await session.commit()


async def get_user_basket_proxies(tg_id: int, session: AsyncSession) -> list[Basket]:
    """
    Возвращает все прокси, добавленные в корзину.

    Parameters
    ----------
    tg_id : int
        Telegram ID пользователя.
    session : AsyncSession
        Асинхронная SQLAlchemy-сессия.

    Returns
    -------
    list[Basket]
        Список объектов Basket, добавленных пользователем.
    """
    result = await session.scalars(
        select(Basket).join(User).where(User.tg_id == tg_id)
    )
    return list(result)