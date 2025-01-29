import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import TOKEN

from app.handlers import common

from aiogram.filters import CommandStart

from aiogram.types import Message

import multiprocessing as mp


from app.handlers import adduser, allusers

from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from aiogram import Dispatcher, types

class SomeMiddleware(BaseMiddleware):
    def __init__(self, allowed_users):
        super().__init__()
        self.allowed_users = allowed_users

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.chat.id
        if user_id not in self.allowed_users:
            return 0
            # raise CancelHandler()  # Остановка дальнейшей обработки
        result = await handler(event, data)
        return result



async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )

    dp = Dispatcher(storage=MemoryStorage())
    bot = Bot(TOKEN)

    allowed_users = [348691698, 540862463, 925216062]

    background_tasks = set()

    import bckg
    asyncio.create_task(bckg.newreports(bot))

    common.router.message.middleware(SomeMiddleware(allowed_users))
    adduser.router.message.middleware(SomeMiddleware(allowed_users))
    allusers.router.message.middleware(SomeMiddleware(allowed_users))

    dp.include_router(common.router)
    dp.include_router(adduser.router)
    dp.include_router(allusers.router)

    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())