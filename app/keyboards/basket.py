from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.utils.func_for_handlers import BasketGroup


def basket_keyboard(groups: list[BasketGroup]) -> InlineKeyboardMarkup:
    keyboard = []

    for i, group in enumerate(groups, start=1):
        ids = ','.join(map(str, group.basket_ids))
        keyboard.append([
            InlineKeyboardButton(
                text=f'❌ Удалить {i}',
                callback_data=f'basket:delete:{ids}'
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            text='💳 Купить',
            callback_data='basket:pay'),
        InlineKeyboardButton(
            text='⬅️ Назад',
            callback_data='buy_proxy')
        ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)