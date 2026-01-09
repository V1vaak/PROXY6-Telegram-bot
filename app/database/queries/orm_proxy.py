from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.models import User, Proxy


async def add_proxies(tg_id: int, data: dict, session: AsyncSession) -> None:
    """
    Добавляет прокси пользователя в базу данных.

    Функция получает пользователя по Telegram ID, создаёт объекты `Proxy`
    на основе данных, полученных от внешнего API, и сохраняет их в базе.

    Parameters
    ----------
    tg_id : int
        Telegram ID пользователя.
    data : dict
        Данные с прокси, полученные от API. Ожидаемая структура:
        {
            "country": str,
            "list": {
                "<proxy_id>": {
                    "host": str,
                    "port": int,
                    "user": str,
                    "pass": str,
                    "type": str,
                    "version": int,
                    "unixtime": int,
                    "unixtime_end": int,
                    "id": str | int
                }
            }
        }
    session : AsyncSession
        Асинхронная SQLAlchemy-сессия.

    Returns
    -------
    None
        Функция не возвращает значение.

    Raises
    ------
    NoResultFound
        Если пользователь с указанным Telegram ID не найден.
    """

    result = await session.execute(
        select(User).where(User.tg_id == tg_id)
    )
    user = result.scalar_one()

    country = data['country']

    for proxy_data in data['list'].values():
        item = Proxy(
            user_id=user.id,

            ip=proxy_data['host'],
            port=proxy_data['port'],
            login=proxy_data['user'],
            password=proxy_data['pass'],

            proxy_type=proxy_data['type'],
            proxy_version=proxy_data['version'],
            country=country,

            date_start=datetime.fromtimestamp(proxy_data['unixtime']),
            date_end=datetime.fromtimestamp(proxy_data['unixtime_end']),

            ids=int(proxy_data['id']),
        )

        session.add(item)

    await session.commit()


async def get_user_proxies(tg_id: int, session: AsyncSession) -> list[Proxy]:
    """
    Возвращает список всех прокси, принадлежащих пользователю.

    Поиск осуществляется по Telegram ID пользователя через связь
    между моделями `User` и `Proxy`.

    Parameters
    ----------
    tg_id : int
        Telegram ID пользователя.
    session : AsyncSession
        Асинхронная SQLAlchemy-сессия.

    Returns
    -------
    list[Proxy]
        Список объектов Proxy пользователя.
    """
    result = await session.scalars(
        select(Proxy)
        .join(User)
        .where(User.tg_id == tg_id)
    )

    return list(result)