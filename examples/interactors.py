from dataclasses import dataclass
from typing import NewType

RequestStr = NewType("RequestStr", str)
AppStr = NewType("AppStr", str)


@dataclass(slots=True, frozen=True)
class ReqInteractor:
    text: RequestStr

    async def __call__(
            self,
    ) -> str:
        return f"Привет, {self.text}"


@dataclass(slots=True, frozen=True)
class AppInteractor:
    text: AppStr

    async def __call__(
            self,
    ) -> str:
        return f"Привет, {self.text}"
