import time
from typing import AsyncGenerator

from dishka import Provider, provide, Scope, provide_all
from vkbottle.tools.mini_types.bot import MessageMin

from interactors import RequestStr, AppStr, ReqInteractor, AppInteractor
from vkbottle_dishka.vk_dishka import VkbottleEventData


class StrProvider(Provider):
    @provide(scope=Scope.REQUEST)
    async def get_req(
        self,
        event: VkbottleEventData,
    ) -> AsyncGenerator[RequestStr, None]:
        print("Scope.REQUEST before")
        if isinstance(event, MessageMin):
            yield RequestStr(f"REQ {time.time()} msg_id: {event.id}")
        else:
            yield RequestStr(f"REQ {time.time()} msg_id: {42}")

        print("Scope.REQUEST after")

    @provide(scope=Scope.APP)
    async def get_app(
        self,
    ) -> AsyncGenerator[AppStr, None]:
        print("Scope.APP before")
        yield AppStr(f"APP {time.time()}")
        print("Scope.APP after")


class InteractorProvider(Provider):
    scope = Scope.REQUEST

    interactors = provide_all(ReqInteractor, AppInteractor)
