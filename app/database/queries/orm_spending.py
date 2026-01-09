from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User, Spending


async def add_spending(*, tg_id: int, data: dict, session: AsyncSession) -> Spending:
    """
    Добавляет запись о расходах пользователя (Spending) в базу данных.

    Функция создаёт объект Spending на основе переданных данных о покупке прокси
    и сохраняет его в базе данных, связывая с пользователем через Telegram ID.

    Parameters
    ----------
    tg_id : int
        Telegram ID пользователя.
    data : dict
        Данные о расходе, ожидаемая структура:
        {
            "price": str | float,
            "currency": str,           # По умолчанию "RUB"
            "version": int,
            "type": str,
            "country": str,
            "count": int,
            "period": int,
            "order_id": str | None
        }
    session : AsyncSession
        Асинхронная SQLAlchemy-сессия.

    Returns
    -------
    Spending
        Добавленный объект Spending, содержащий информацию о расходах пользователя.
    """
    
    result = await session.execute(
        select(User).where(User.tg_id == tg_id)
    )
    user = result.scalar_one()

    spending = Spending(
        user_id=user.id,

        amount=int(float(data['price']) * 100),
        currency=data.get('currency', 'RUB'),

        proxy_version=int(data['version']),
        proxy_type=data['type'],
        country=data['country'],
        count=int(data['count']),
        period=int(data['period']),

        payment_id=str(data.get('order_id'))
    )

    session.add(spending)
    await session.commit()
    return spending