from sqlalchemy.ext.asyncio import AsyncSession

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from app.database.queries.orm_user import add_user, get_data_user
from app.database.queries.orm_proxy import get_user_proxies

from app.database.models import User

from app.utils.func_for_handlers import get_profile_text, get_proxy_list_text
from app.utils.texts_for_handlers import start_message

import app.keyboards.keyboards as kb


user_base_router = Router()

@user_base_router.message(CommandStart())
async def start_cmd(message: Message, session: AsyncSession):
    await message.answer(text=start_message, reply_markup=kb.start) 
    
    await add_user(message.from_user, session)


@user_base_router.callback_query(F.data == 'profile')
async def profile(callback: CallbackQuery, session: AsyncSession):
    await callback.answer()
    
    user: User = await get_data_user(callback.from_user.id, session)
    
    text = get_profile_text(user)
    
    await callback.message.edit_text(
        text=text,
        reply_markup=kb.return_on_start,
        parse_mode="HTML"
    )


@user_base_router.callback_query(F.data == 'my_proxy')
async def my_proxy(callback: CallbackQuery, session: AsyncSession):
    await callback.answer()

    proxies = await get_user_proxies(callback.from_user.id, session)

    text = get_proxy_list_text(proxies)

    await callback.message.edit_text(
        text=text,
        reply_markup=kb.return_on_start,
        parse_mode="HTML"
    )
    

@user_base_router.callback_query(F.data == 'support')
async def contacts(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text('Вот мой контакт:\n@novikovyo.\n И другие мои контакты:', 
                                     reply_markup=kb.contacts)


@user_base_router.callback_query(F.data == 'return_to_start')
async def returns(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(text=start_message, reply_markup=kb.start)