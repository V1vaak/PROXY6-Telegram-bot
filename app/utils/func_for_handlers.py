from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.database.models import User, Proxy, Basket

from app.services.proxy6.engine import proxy_client
from app.services.proxy6.client import Proxy6Error
from app.services.proxy6.cache import get_price_cache, save_price_cache

from app.utils.constants import (COUNTRY_NAMES, COUNTRY_FLAGS, 
                                 PROXY_VERSION_MAP, PROXY_TYPE_MAP)


def get_profile_text(user: User) -> str:
    username = f'@{user.username}' if user.username else 'не указан'
    
    return f"""
<b>👤 ПРОФИЛЬ</b>

<b>🆔 ID:</b> <code>{user.tg_id}</code>
<b>👤 Юзернейм:</b> {username}
<b>📛 Имя:</b> {user.first_name or 'не указано'}
<b>📛 Фамилия:</b> {user.last_name or 'не указана'}
<b>📅 Дата регистрации:</b> {user.created_at.strftime('%d.%m.%Y %H:%M')}
<b>⏳ В системе:</b> {(datetime.now() - user.created_at).days} дней
    """


def get_proxy_list_text(proxies: list[Proxy]) -> str:
    """
    Форматирование прокси для отображения пользователю.
    Каждая прокси — отдельный code-блок, чтобы легко копировать на телефоне.
    """
    if not proxies:
        return (
            "<b>🔍 ВАШИ ПРОКСИ</b>\n\n"
            "📭 <i>У вас пока нет добавленных прокси.</i>\n\n"
        )

    header = (
        "<b>🔍 ВАШИ ПРОКСИ</b>\n\n"
        "📌 <b>Формат:</b>\n"
        "<code>IP:ПОРТ:ЛОГИН:ПАРОЛЬ</code>\n\n"
        "<i>Коснитесь строки с прокси, чтобы скопировать</i>\n\n"
    )

    now = datetime.utcnow()
    blocks = []

    for i, proxy in enumerate(proxies, 1):
        remaining = proxy.date_end - now
        days_left = max(remaining.days, 0)

        proxy_type = PROXY_TYPE_MAP.get(proxy.proxy_type, proxy.proxy_type)
        proxy_version = PROXY_VERSION_MAP.get(proxy.proxy_version, proxy.proxy_version)
        country = COUNTRY_NAMES.get(proxy.country, proxy.country.upper())
        flag = COUNTRY_FLAGS.get(proxy.country, '🏴')

        value = f"{proxy.ip}:{proxy.port}:{proxy.login}:{proxy.password}"

        blocks.append(
            f"[{i}] {proxy_type} | {proxy_version}\n"
            f"🌍 Страна: {flag}{country}\n"
            f"⏳ Осталось: {days_left} дн.\n"
            f"<code>{value}</code>"
        )

    return header + '\n\n'.join(blocks)


def get_markup_contries(countries: list[str]) -> InlineKeyboardMarkup:
    """
    Формирует inline-клавиатуру со списком стран для выбора прокси.

    Для каждой страны создаётся кнопка с флагом и названием страны.
    Callback-данные имеют формат: ``country:<code>``.

    В конце клавиатуры добавляется кнопка возврата «Назад».

    Parameters
    ----------
    countries : list[str]
        Список кодов стран в формате ISO 3166-1 alpha-2
        (например: ``["ru", "us", "de"]``).

    Returns
    -------
    InlineKeyboardMarkup
        Inline-клавиатура для отправки или редактирования сообщения
        в Telegram-боте.

    Notes
    -----
    • Флаги стран берутся из словаря ``COUNTRY_FLAGS``  
    • Названия стран формируются через функцию ``get_country_name``  
    • Кнопки автоматически группируются по 3 в ряд
    """
    builder = InlineKeyboardBuilder()

    for code in countries:
        builder.button(
            text=f"{COUNTRY_FLAGS.get(code, '🏴')} {COUNTRY_NAMES.get(code, code.upper())}",
            callback_data=f"country:{code}"
        )

    builder.adjust(3)

    builder.row(
        InlineKeyboardButton(
            text='⬅️ Назад',
            callback_data='return_to_select_proxy_type'
        )
    )

    return builder.as_markup()


@dataclass
class BasketGroup:
    proxy_version: int
    proxy_type: str
    country: str
    count: int
    period: int
    basket_ids: list[int]


def group_basket_items(baskets: list[Basket]) -> list[BasketGroup]:
    grouped = defaultdict(lambda: {
        'count': 0,
        'period': 0,
        'basket_ids': []
    })

    for item in baskets:
        key = (item.proxy_version, item.proxy_type, item.country, item.period)
        grouped[key]['count'] += item.count
        grouped[key]['period'] = item.period
        grouped[key]['basket_ids'].append(item.id)

    result = []
    for (version, ptype, country, period), data in grouped.items():
        result.append(
            BasketGroup(
                proxy_version=version,
                proxy_type=ptype,
                country=country,
                count=data['count'],
                period=period,
                basket_ids=data['basket_ids']
            )
        )

    return result


async def calc_price_proxy6(
    *,
    proxy_version: int,
    count: int,
    period: int,
    session
) -> int:
    """
    Возвращает цену в копейках с кэшированием на 24 часа.
    """

    cache = await get_price_cache(
        proxy_version=proxy_version,
        count=count,
        period=period,
        session=session
    )

    if cache and not cache.is_expired():
        return int(cache.price_rub * 100)

    try:
        price_rub = await proxy_client.get_price(
            count=count,
            period=period,
            version=proxy_version
        )
    except Proxy6Error:
        return 0

    await save_price_cache(
        proxy_version=proxy_version,
        count=count,
        period=period,
        price_rub=float(price_rub),
        session=session
    )

    return int(float(price_rub) * 100)


async def format_basket_proxies(baskets: list[Basket], session: AsyncSession) -> tuple[str, int]:
    if not baskets:
        return '🛒 <b>Ваша корзина пуста.</b>', 0

    groups = group_basket_items(baskets)

    lines = ['🛒 <b>Ваша корзина:</b>\n']
    total_price = 0

    for i, item in enumerate(groups, start=1):
        price = await calc_price_proxy6(
                proxy_version=item.proxy_version,
                count=item.count,
                period=item.period,
                session=session
            )


        total_price += price

        lines.append(
            f"<b>{i}️⃣ {PROXY_VERSION_MAP.get(item.proxy_version)} | "
            f"{PROXY_TYPE_MAP.get(item.proxy_type)} | {COUNTRY_FLAGS.get(item.country)}"
            f"{COUNTRY_NAMES.get(item.country)}</b>\n"
            f"   🔢 Кол-во: <b>{item.count}</b>\n"
            f"   ⏳ Период: <b>{item.period} дней</b>\n"
            f"   💰 Цена: <b>{price / 100:.2f} ₽</b>\n"
        )

    lines.append(
        f"\n<b>Итого:</b> 💳 <b>{total_price / 100:.2f} ₽</b>"
    )

    return "\n".join(lines), total_price