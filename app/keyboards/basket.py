from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.utils.func_for_handlers import BasketGroup


def basket_keyboard(groups: list[BasketGroup]) -> InlineKeyboardMarkup:
    """
    Создаёт inline-клавиатуру для управления корзиной пользователя.

    Для каждой группы элементов корзины добавляется кнопка удаления,
    передающая в callback_data идентификаторы всех связанных записей корзины.
    Также добавляются кнопки для перехода к оплате и возврата назад.

    Parameters
    ----------
    groups : list[BasketGroup]
        Список сгруппированных элементов корзины пользователя.
        Каждый объект `BasketGroup` должен содержать список идентификаторов
        элементов корзины (`basket_ids`), относящихся к одной группе.

    Returns
    -------
    InlineKeyboardMarkup
        Inline-клавиатура для отображения корзины и управления её содержимым
        в Telegram-боте.
    """
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
            callback_data='basket:pay'
        ),
        InlineKeyboardButton(
            text='⬅️ Назад',
            callback_data='buy_proxy'
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)