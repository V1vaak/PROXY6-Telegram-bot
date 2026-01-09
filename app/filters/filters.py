from aiogram.filters import BaseFilter, Filter
from aiogram.types import Message


class IsAdmin(BaseFilter):
    def __init__(self, admin_ids: list[int]) -> None:
        self.admin_ids = admin_ids

    async def __call__(self, message: Message):
        return message.from_user.id in self.admin_ids