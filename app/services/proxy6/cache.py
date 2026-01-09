from time import time
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import PriceCache

from app.services.proxy6.engine import proxy_client


_CACHE_TTL = 600  # 10 минут
_country_cache: dict[int, dict] = {}


async def get_countries(version: int) -> list[str]:
    """
    Возвращает список кодов стран, в которых доступны прокси указанной версии.

    Данные запрашиваются у сервиса Proxy6 и кэшируются в памяти
    на ограниченное время (TTL), чтобы избежать лишних сетевых запросов
    и снизить задержки при повторных вызовах.

    Parameters
    ----------
    version : int
        Версия прокси:
        4 - IPv4,
        3 - IPv4 Shared,
        6 - IPv6.

    Returns
    -------
    list[str]
        Список кодов стран (ISO 3166-1 alpha-2), например:
        ['ru', 'de', 'us', 'fr'].

        В случае ошибки или отсутствия данных возвращается пустой список.
    """
    now = time()

    cache = _country_cache.get(version)
    if cache and now - cache['time'] < _CACHE_TTL:
        return cache['data']

    data = await proxy_client.get_country(version=version)

    if not data:
        return []

    _country_cache[version] = {
        'data': data,
        'time': now
    }

    return data


async def get_price_cache(
    *,
    proxy_version: int,
    count: int,
    period: int,
    session: AsyncSession
) -> PriceCache | None:
    
    result = await session.scalar(
        select(PriceCache).where(
            PriceCache.proxy_version == proxy_version,
            PriceCache.count == count,
            PriceCache.period == period,
        )
    )
    return result


async def save_price_cache(
    *,
    proxy_version: int,
    count: int,
    period: int,
    price_rub: float,
    session: AsyncSession
) -> None:
    
    cache = await get_price_cache(
        proxy_version=proxy_version,
        count=count,
        period=period,
        session=session
    )

    if cache:
        cache.price_rub = price_rub
        cache.updated_at = datetime.utcnow()
    else:
        cache = PriceCache(
            proxy_version=proxy_version,
            count=count,
            period=period,
            price_rub=price_rub
        )
        session.add(cache)

    await session.commit()