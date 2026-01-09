from sqlalchemy.ext.asyncio import AsyncSession

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from app.database.queries.orm_proxy import add_proxies
from app.database.queries.orm_spending import add_spending

from app.services.proxy6.engine import proxy_client
from app.services.proxy6.cache import get_countries

from app.services.yookassa.payment import get_status

from app.utils.constants import (COUNTRY_FLAGS, COUNTRY_NAMES, 
                                PROXY_TYPE_MAP, PROXY_VERSION_MAP)
from app.utils.func_for_handlers import calc_price_proxy6, get_markup_contries

import app.keyboards.keyboards as kb


class BuyProxyFSM(StatesGroup):
    active = State()


user_proxy_router = Router()

# ================= START BUY FLOW =================

@user_proxy_router.callback_query(F.data == 'buy_proxy')
async def buy_proxy_main_page(callback: CallbackQuery):
    await callback.answer()

    await callback.message.edit_text(
        'Выберите действие:',
        reply_markup=kb.in_buy_proxy_after_main
    )

@user_proxy_router.callback_query(F.data == 'prolong_proxy')
async def prolong_proxy(callback: CallbackQuery):
    await callback.answer()

    await callback.message.edit_text(
        'Не реализовал эту функцию',
        reply_markup=kb.return_on_start
    )

@user_proxy_router.callback_query(F.data.in_({'selected:buy', 'return_to_select_proxy_version'}))
async def select_proxy_version(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(BuyProxyFSM.active)

    await callback.message.edit_text(
        'Выберите версию прокси:',
        reply_markup=kb.select_proxy_version
    )

# ================= SELECT VERSION =================

@user_proxy_router.callback_query(F.data.startswith('version:'))
async def set_proxy_version(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    version = int(callback.data.split(':')[1])
    await state.update_data(proxy_version=version)

    await callback.message.edit_text(
        'Выберите тип прокси:',
        reply_markup=kb.select_proxy_type
    )


# ================= SELECT TYPE =================

@user_proxy_router.callback_query(F.data.startswith('type:'))
async def set_proxy_type(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    proxy_type = callback.data.split(':')[1]
    await state.update_data(proxy_type=proxy_type)

    data = await state.get_data()
    countries = await get_countries(version=data['proxy_version'])

    await callback.message.edit_text(
        '<b>🌍 ВЫБЕРИТЕ СТРАНУ:</b>',
        reply_markup=get_markup_contries(countries),
        parse_mode='HTML'
    )

# ================= SELECT COUNTRY =================

@user_proxy_router.callback_query(F.data.startswith('country:'))
async def set_country(callback: CallbackQuery, state: FSMContext):
    await callback.answer(
    "❗ По правилам Proxy6 минимальный период аренды прокси — 3 дня.\n\n"
    "Пожалуйста, выберите срок не менее 3 дней.",
    show_alert=True)

    country = callback.data.split(':')[1]

    await state.update_data(
        country=country,
        count=1,
        period=3
    )

    await callback.message.edit_text(
        'Выберите количество и период:',
        reply_markup=kb.count_and_period(count=1, period=3)
    )

# ================= CHANGE COUNT =================

@user_proxy_router.callback_query(F.data.startswith('count:'))
async def change_count(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    data = await state.get_data()
    count = data.get('count', 1)
    period = data.get('period', 3)

    if callback.data == 'count:inc':
        count += 1
    elif callback.data == 'count:dec' and count > 1:
        count -= 1

    await state.update_data(count=count)

    await callback.message.edit_reply_markup(
        reply_markup=kb.count_and_period(count=count, period=period)
    )

# ================= CHANGE PERIOD =================

@user_proxy_router.callback_query(F.data.startswith('period:'))
async def change_period(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    data = await state.get_data()
    count = data.get('count', 1)
    period = data.get('period', 3)

    if callback.data == 'period:inc':
        period += 1
    elif callback.data == 'period:dec' and period > 3:
        period -= 1

    await state.update_data(period=period)

    await callback.message.edit_reply_markup(
        reply_markup=kb.count_and_period(count=count, period=period)
    )

# ================= BACK TO =================

@user_proxy_router.callback_query(F.data == 'return_to_select_proxy_version')
async def back_to_version(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        'Выберите версию прокси:',
        reply_markup=kb.select_proxy_version
    )


@user_proxy_router.callback_query(F.data == 'return_to_select_proxy_type')
async def back_to_type(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        'Выберите тип прокси:',
        reply_markup=kb.select_proxy_type
    )

@user_proxy_router.callback_query(F.data == 'return_to_select_country')
async def back_to_country(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    data = await state.get_data()
    countries = await get_countries(version=data['proxy_version'])

    await callback.message.edit_text(
        '<b>🌍 ВЫБЕРИТЕ СТРАНУ:</b>',
        reply_markup=get_markup_contries(countries),
        parse_mode='HTML'
    )

@user_proxy_router.callback_query(F.data == 'return_from_pay')
async def return_from_pay(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text(
        'Выберите количество и период:'
    )
    await change_count(callback, state)


# ================= BUY =================

@user_proxy_router.callback_query(F.data == 'buy:now')
async def selected_buy(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await callback.answer()

    data = await state.get_data()

    if data:
            price = await calc_price_proxy6(
                proxy_version=data['proxy_version'],
                count=1,
                period=data['period'],
                session=session
            )

            keyboard, payment_url, payment_id = kb.pay_now(price)

            text = (
                f"<b>{PROXY_VERSION_MAP.get(data['proxy_version'])} | "
                f"{PROXY_TYPE_MAP.get(data['proxy_type'])} | "
                f"{COUNTRY_FLAGS.get(data['country'])} {COUNTRY_NAMES.get(data['country'])}</b>\n"
                f"⏳ Срок действия: <b>{data['period']} дней</b>\n"
                f"💰 Стоимость: <b>{price / 100:.2f} ₽</b>"
            )

            await callback.message.edit_text(
                text,
                parse_mode='HTML', 
                reply_markup=keyboard
            )
            await state.update_data(payment_url=payment_url, payment_id=payment_id)

    else:
        await callback.message.edit_text(
            'Данные не выбраны!\nВыберите, пожалуйста, прокси заново.',
            reply_markup=kb.in_buy_proxy_after_main
        )


@user_proxy_router.callback_query(F.data == 'iampayed')
async def iampayed(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await callback.answer()

    data = await state.get_data()

    if data:
        
        if get_status(data['payment_id']) == 'succeeded':
            
            await callback.message.edit_text(
                '⏳ <b>Прокси покупаются...</b>\n\n'
                'Пожалуйста, подождите, это может занять несколько секунд.',
                parse_mode='HTML')
            
            try:
                proxy_data = await proxy_client.buy(
                                            count=data['count'],
                                            period=data['period'],
                                            country=data['country'],
                                            version=data['proxy_version'],
                                            type=data['proxy_type']
                                            )
                
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
                
                await callback.message.edit_text(
                    '✅ Прокси успешно куплены',
                    reply_markup=kb.after_added_proxy_at_basket
                )
            except Exception as e:
                await callback.message.edit_text(
                    f"❌ <b>Ошибка: {e} при покупке прокси</b>\n\n"
                    "Попробуйте позже или обратитесь в поддержку.",
                    reply_markup=kb.return_on_start,
                    parse_mode="HTML"
                )
            await state.clear()    
        else:
            price = await calc_price_proxy6(
                proxy_version=data['proxy_version'],
                count=1,
                period=data['period'],
                session=session
            )
            keyboard, payment_url, payment_id = kb.pay(price, 
                                                       data['payment_url'], 
                                                       data['payment_id']
                                                      )

            await callback.message.edit_text(
                "❌ <b>Вы не оплатили</b>\n\n"
                "Попробуйте еще раз.",
                reply_markup=keyboard,
                parse_mode="HTML"
            )            

    else:
        await callback.message.edit_text(
            'Данные не выбраны!\nВыберите, пожалуйста, прокси заново.',
            reply_markup=kb.in_buy_proxy_after_main
        )



@user_proxy_router.callback_query(F.data == 'buy:now')
async def add_to_basket(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await callback.answer()

    data = await state.get_data()

    if data:
        await callback.message.edit_text(
            '⏳ <b>Прокси покупаются...</b>\n\n'
            'Пожалуйста, подождите, это может занять несколько секунд.',
            parse_mode='HTML')
        
        try:
            proxy_data = await proxy_client.buy(
                                        count=data['count'],
                                        period=data['period'],
                                        country=data['country'],
                                        version=data['proxy_version'],
                                        type=data['proxy_type']
                                        )
            
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
            
            await callback.message.edit_text(
                '✅ Прокси успешно куплены',
                reply_markup=kb.after_added_proxy_at_basket
            )
        except Exception as e:
            await callback.message.edit_text(
                "❌ <b>Ошибка при покупке прокси</b>\n\n"
                "Попробуйте позже или обратитесь в поддержку.",
                reply_markup=kb.return_on_start,
                parse_mode='HTML'
            )

    else:
        await callback.message.edit_text(
            'Данные не выбраны!\nВыберите, пожалуйста, прокси заново.',
            reply_markup=kb.in_buy_proxy_after_main
        )

    await state.clear()