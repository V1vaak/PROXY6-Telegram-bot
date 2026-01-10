from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.services.yookassa.payment import create_payment


start = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='👤 Мой профиль', callback_data='profile')],
    [InlineKeyboardButton(text='🔐 Мои прокси', callback_data='my_proxy')],
    [InlineKeyboardButton(text='🛒 Купить прокси', callback_data='buy_proxy'),
     InlineKeyboardButton(text='🔄 Продлить прокси', callback_data='prolong_proxy')],
    [InlineKeyboardButton(text='💬 Поддержка', callback_data='support')]
])

return_on_start = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='⬅️ Назад на главную', callback_data='return_to_start')]
])


contacts = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='GitHub', url='https://github.com/V1vaak'), 
     InlineKeyboardButton(text='YouTube', url='https://www.youtube.com/@novikovyo')],
    [InlineKeyboardButton(text='⬅️ Назад на главную', callback_data='return_to_start')]
])

in_buy_proxy_after_main = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Выбрать прокси', callback_data='selected:buy')],
    [InlineKeyboardButton(text='Корзина🗑️', callback_data='selected:basket')],
    [InlineKeyboardButton(text='⬅️ Назад на главную', callback_data='return_to_start')]
])

select_proxy_version = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='IPv4🟢', callback_data='version:4')],
    [InlineKeyboardButton(text='IPv4 Shared🔵', callback_data='version:3')],  # ipv4_shared
    [InlineKeyboardButton(text='IPv6🟢', callback_data='version:6')],
    [InlineKeyboardButton(text='⬅️ Назад', callback_data='buy_proxy')]
])

select_proxy_type = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='HTTPS', callback_data='type:http')],
    [InlineKeyboardButton(text='SOCKS5', callback_data='type:socks')],
    [InlineKeyboardButton(text='⬅️ Назад', callback_data='return_to_select_proxy_version')]
])

after_added_proxy_at_basket = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🔐 Мои прокси', callback_data='my_proxy')],
    [InlineKeyboardButton(text='Выбрать еще прокси', callback_data='selected:buy')],
    [InlineKeyboardButton(text='В корзину🗑️', callback_data='selected:basket')],
    [InlineKeyboardButton(text='⬅️ Назад на главную', callback_data='return_to_start')]
])

in_basket_if_no_proxy = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Выбрать прокси', callback_data='selected:buy')],
    [InlineKeyboardButton(text='⬅️ На главную', callback_data='return_to_start')]
])

after_buyed_proxy = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🔐 Мои прокси', callback_data='my_proxy')],
    [InlineKeyboardButton(text='⬅️ Назад на главную', callback_data='return_to_start')]
])


def count_and_period(count: int, period: int) -> InlineKeyboardMarkup:
    """
    Клавиатура выбора количества прокси и периода аренды.

    Parameters
    ----------
    count : int
        Текущее количество выбранных прокси.
    period : int
        Текущий период аренды в днях.

    Returns
    -------
    InlineKeyboardMarkup
        Inline-клавиатура управления покупкой прокси.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='➖', callback_data='count:dec'),
            InlineKeyboardButton(text=f'{count} шт.', callback_data='noop'),
            InlineKeyboardButton(text='➕', callback_data='count:inc'),
        ],
        [
            InlineKeyboardButton(text='➖', callback_data='period:dec'),
            InlineKeyboardButton(text=f'{period} дн.', callback_data='noop'),
            InlineKeyboardButton(text='➕', callback_data='period:inc'),
        ],
        [
            InlineKeyboardButton(text='💳 Купить сейчас', callback_data='buy:now'),
        ],
        [
            InlineKeyboardButton(text='🗑️ В корзину', callback_data='buy:add_to_basket'),
        ],
        [
            InlineKeyboardButton(
                text='⬅️ Назад',
                callback_data='return_to_select_country'
            )
        ]
    ])



def pay_now(
    price: int | float,
    pay_url: str | None = None,
    pay_id: str | None = None
) -> tuple[InlineKeyboardMarkup, str, str]:
    """
    Создаёт inline-клавиатуру для оплаты и инициализирует платёж при необходимости.

    Если ссылка на оплату и идентификатор платежа не переданы, функция
    создаёт новый платёж через платёжный сервис и возвращает данные
    для последующей проверки статуса оплаты.

    Parameters
    ----------
    price : int | float
        Сумма платежа в копейках.
    pay_url : str | None, optional
        URL для перехода к оплате. Если не указан, создаётся новый платёж.
    pay_id : str | None, optional
        Идентификатор платежа в платёжной системе. Если не указан,
        создаётся новый платёж.

    Returns
    -------
    tuple[InlineKeyboardMarkup, str, str]
        Кортеж из:
        - inline-клавиатуры с кнопками оплаты,
        - URL для перехода к оплате,
        - идентификатора платежа в платёжной системе.
    """
    if not pay_url or not pay_id:
        pay_url, pay_id = create_payment(price / 100)

    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f'💳 Оплатить {price / 100:.2f} ₽',
                url=pay_url
            )],
            [InlineKeyboardButton(
                text='Я оплатил ✅',
                callback_data='iampayed'
            )],
            [InlineKeyboardButton(
                text='⬅️ Назад',
                callback_data='return_from_pay'
            )]
        ]
    )

    return inline_kb, pay_url, pay_id


def pay_in_basket(
    price: int | float,
    pay_url: str | None = None,
    pay_id: str | None = None
) -> tuple[InlineKeyboardMarkup, str, str]:
    """
    Создаёт inline-клавиатуру для оплаты содержимого корзины.

    Если ссылка на оплату и идентификатор платежа не переданы, функция
    инициализирует новый платёж через платёжный сервис и возвращает
    необходимые данные для последующей проверки статуса оплаты.

    Parameters
    ----------
    price : int | float
        Общая сумма оплаты в копейках.
    pay_url : str | None, optional
        URL для перехода к оплате. Если не указан, создаётся новый платёж.
    pay_id : str | None, optional
        Идентификатор платежа в платёжной системе. Если не указан,
        создаётся новый платёж.

    Returns
    -------
    tuple[InlineKeyboardMarkup, str, str]
        Кортеж из:
        - inline-клавиатуры с кнопками оплаты корзины,
        - URL для перехода к оплате,
        - идентификатора платежа в платёжной системе.
    """
    if not pay_url or not pay_id:
        pay_url, pay_id = create_payment(price / 100)

    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f'💳 Оплатить {price / 100:.2f} ₽',
                url=pay_url
            )],
            [InlineKeyboardButton(
                text='Я оплатил ✅',
                callback_data='iampayed:in_basket'
            )],
            [InlineKeyboardButton(
                text='⬅️ Назад',
                callback_data='return_from_pay_in_basket'
            )]
        ]
    )

    return inline_kb, pay_url, pay_id