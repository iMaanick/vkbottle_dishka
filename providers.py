import time
from typing import AsyncGenerator

from dishka import Provider, provide, Scope, provide_all

from interactors import RequestStr, AppStr, ReqInteractor, AppInteractor


class StrProvider(Provider):
    @provide(scope=Scope.REQUEST)
    async def get_req(
            self,
    ) -> AsyncGenerator[RequestStr, None]:
        print("Scope.REQUEST before")
        yield f"REQ {time.time()}"
        print("Scope.REQUEST after")

    @provide(scope=Scope.APP)
    async def get_app(
            self,
    ) -> AsyncGenerator[AppStr, None]:
        print("Scope.APP before")
        yield f"APP {time.time()}"
        print("Scope.APP after")


class InteractorProvider(Provider):
    scope = Scope.REQUEST

    interactors = provide_all(
        ReqInteractor,
        AppInteractor

    )
