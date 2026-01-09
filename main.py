import logging
import asyncio

from aiogram import Bot, Dispatcher

from app.middlewares.db import DataBaseSession

from app.database.engine import start_up_app, create_db, async_session

from app.services.proxy6.engine import on_startup, on_shutdown

from app.handlers.user.base import user_base_router
from app.handlers.user.proxy import user_proxy_router
from app.handlers.user.basket import user_basket_router

from config import BOT_TOKEN


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

dp.include_router(user_base_router)
dp.include_router(user_proxy_router)
dp.include_router(user_basket_router)

dp.startup.register(on_startup)
dp.shutdown.register(on_shutdown)


async def main():
    # await create_db()
    # await start_up_app()
    # await bot.delete_my_commands(scope=types.BotCommandScopeAllPrivateChats())
    dp.update.middleware(DataBaseSession(session_pool=async_session))
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')