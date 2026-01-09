import asyncio

from aiogram import F, Router
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Basket

from app.database.queries.orm_basket import (
                                             add_data_proxies_to_basket,
                                             delete_user_basket,
                                             get_user_basket_proxies,
                                             delete_basket_items
                                            )
from app.database.queries.orm_spending import add_spending
from app.database.queries.orm_proxy import add_proxies

from app.services.proxy6.client import Proxy6Error
from app.services.proxy6.engine import proxy_client

from app.services.yookassa.payment import get_status
from app.utils.func_for_handlers import format_basket_proxies, group_basket_items

from app.keyboards.basket import basket_keyboard, BasketGroup

import app.keyboards.keyboards as kb


user_basket_router = Router()


@user_basket_router.callback_query(F.data == "selected:basket")
async def show_basket(callback: CallbackQuery, session: AsyncSession):
    await callback.answer()

    baskets: list[Basket] = await get_user_basket_proxies(callback.from_user.id, session)

    text, _ = await format_basket_proxies(baskets, session)


    if baskets:
        groups: list[BasketGroup] = group_basket_items(baskets)
        await callback.message.edit_text(
                            text=text, 
                            parse_mode='HTML',
                            reply_markup=basket_keyboard(groups)
                        )
    else:
        await callback.message.edit_text(
                            text=text, 
                            parse_mode='HTML',
                            reply_markup=kb.in_basket_if_no_proxy
                        )    


@user_basket_router.callback_query(F.data == 'buy:add_to_basket')
async def add_to_basket(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await callback.answer()

    data = await state.get_data()

    await add_data_proxies_to_basket(
        tg_id=callback.from_user.id,
        data=data,
        session=session
    )

    await state.clear()

    await callback.message.edit_text(
        '✅ Прокси добавлены в корзину',
        reply_markup=kb.after_added_proxy_at_basket
    )


@user_basket_router.callback_query(F.data.startswith("basket:delete:"))
async def delete_basket(callback: CallbackQuery, session: AsyncSession):
    ids = list(map(int, callback.data.split(":")[2].split(",")))
    await delete_basket_items(ids, session)

    await callback.answer("Позиция удалена")
    await show_basket(callback, session)


@user_basket_router.callback_query(F.data == 'basket:pay')
async def pay_basket(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await callback.answer()

    baskets = await get_user_basket_proxies(
                        callback.from_user.id,
                        session
                    )

    text, total_price = await format_basket_proxies(baskets, session)

    keyboard, payment_url, payment_id = kb.pay_in_basket(total_price)

    await state.update_data(price=total_price, payment_url=payment_url, payment_id=payment_id)


    await callback.message.edit_text(
                            text=text, 
                            parse_mode='HTML',
                            reply_markup=keyboard
                        )
    

@user_basket_router.callback_query(F.data == 'iampayed:in_basket')
async def iampayed_in_basket(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await callback.answer()

    data = await state.get_data()

    if get_status(data['payment_id']) == 'succeeded':

        await callback.message.edit_text(
            '⏳ <b>Прокси покупаются...</b>\n\n'
            'Пожалуйста, подождите, это может занять несколько секунд.',
            parse_mode='HTML'
        )

        baskets = await get_user_basket_proxies(
                            callback.from_user.id,
                            session
                        )

        for item in baskets:
            try:
                proxy_data = await proxy_client.buy(
                    count=item.count,
                    period=item.period,
                    country=item.country,
                    version=item.proxy_version,
                    type=item.proxy_type
                )

            except asyncio.TimeoutError:
                await callback.message.edit_text(
                    f'❌ <b>Таймаут при покупке прокси {item.country}</b>\n\n'
                    'Сервис Proxy6 временно не отвечает.\n'
                    'Попробуйте позже.',
                    reply_markup=kb.return_on_start,
                    parse_mode='HTML'
                )
                return

            except Proxy6Error as e:
                await callback.message.edit_text(
                    f'❌ <b>Ошибка при покупке прокси {item.country}:</b>\n\n'
                    f'{e}',
                    reply_markup=kb.return_on_start,
                    parse_mode='HTML'
                )
                return


            await add_proxies(
                tg_id=callback.from_user.id,
                data=proxy_data,
                session=session
            )

            await add_spending(
                tg_id=callback.from_user.id,
                data=proxy_data,
                session=session
            )

            # защита от 429
            await asyncio.sleep(0.5)

        await callback.message.edit_text(
            '✅ Прокси успешно куплены',
            reply_markup=kb.after_buyed_proxy
        )

        await delete_user_basket(callback.from_user.id, session)
        
        await state.clear()

    else:

        keyboard, pay_url, pay_id = kb.pay_in_basket(data['price'], 
                                                     data['payment_url'], 
                                                     data['payment_id']
                                                     )
        await callback.message.edit_text(
            '❌ <b>Вы не оплатили</b>\n\n'
            'Попробуйте еще раз.',
            reply_markup=keyboard,
            parse_mode='HTML'
        )

# ==============================BACK TO============================================================

@user_basket_router.callback_query(F.data == 'return_from_pay_in_basket')
async def return_from_pay_in_basket(callback: CallbackQuery, 
                                    state: FSMContext, 
                                    session: AsyncSession):
    await callback.answer()

    await show_basket(callback, session)
    await state.clear()