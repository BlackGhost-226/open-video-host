from asyncio import Condition
from typing import Generic, TypeVar

T = TypeVar("T")


class AsyncList(Generic[T]):
    def __init__(self):
        self._items: list[T] = []
        self._condition = Condition()

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self):
        return iter(self._items)

    def __getitem__(self, index):
        return self._items[index]

    async def put(self, item: T):
        async with self._condition:
            self._items.append(item)
            self._condition.notify()

    async def get(self) -> T:
        async with self._condition:
            await self._condition.wait_for(self._items.__len__)
            return self._items.pop()

    def append(self, item: T):
        self._items.append(item)

    def pop(self, index: int = -1) -> T:
        return self._items.pop(index)
