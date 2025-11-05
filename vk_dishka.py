from inspect import signature, Parameter
from typing import ParamSpec, TypeVar, Final, Callable, Any, cast

from dishka import AsyncContainer
from dishka.integrations.base import wrap_injection
from vkbottle import BaseMiddleware, Bot
from vkbottle.bot import Message
from vkbottle.dispatch.views.bot import BotMessageView
from vkbottle.tools.mini_types.bot import MessageMin

P = ParamSpec("P")
T = TypeVar("T")
CONTAINER_NAME: Final = "dishka_container"


def inject(func: Callable[P, T]) -> Callable[P, T]:
    sig = signature(func)
    additional_params = []

    if CONTAINER_NAME not in sig.parameters:
        additional_params.append(
            Parameter(
                name=CONTAINER_NAME,
                annotation=AsyncContainer,
                kind=Parameter.KEYWORD_ONLY,
            )
        )

    def container_getter(args: tuple[Any, ...], kwargs: dict[str, Any]) -> AsyncContainer:
        event = args[0]
        container = getattr(event, f"_{CONTAINER_NAME}", None)
        if container is not None:
            # добавляем в kwargs, чтобы wrap_injection не упал на pop
            kwargs[CONTAINER_NAME] = container
            return cast(AsyncContainer, container)
        raise KeyError(
            f"Container '{CONTAINER_NAME}' not found in event. "
            "Ensure ContainerMiddleware placed it in event._dishka_container"
        )

    return wrap_injection(
        func=func,
        is_async=True,
        additional_params=additional_params,
        container_getter=container_getter,
    )


class ContainerMiddleware(BaseMiddleware[Message]):  # type: ignore[misc]
    def __init__(
            self,
            event: MessageMin,
            view: BotMessageView,
            container: AsyncContainer,

    ) -> None:
        super().__init__(event, view)
        self.container = container

    async def pre(self) -> None:
        dishka_container_wrapper = self.container({type(self.event): self.event})
        setattr(self.event, f"_{CONTAINER_NAME}_wrapper", dishka_container_wrapper)
        container_instance = await dishka_container_wrapper.__aenter__()
        setattr(self.event, f"_{CONTAINER_NAME}", container_instance)

    async def post(self) -> None:
        dishka_container_wrapper = getattr(self.event, f"_{CONTAINER_NAME}_wrapper")
        await dishka_container_wrapper.__aexit__(None, None, None)


def provide_dependencies(
        container: AsyncContainer,
) -> type[ContainerMiddleware]:
    class ContainerMiddlewareFinal(ContainerMiddleware):
        def __init__(self, event: MessageMin, view: BotMessageView) -> None:
            super().__init__(
                event,
                view,
                container=container,
            )

    return ContainerMiddlewareFinal


def setup_dishka(
        container: AsyncContainer,
        bot: Bot,
) -> None:
    bot.labeler.message_view.register_middleware(
        provide_dependencies(container)
    )
