from collections.abc import Callable, Iterable
from typing import Any, Final, NewType, ParamSpec, TypeVar

from dishka import AsyncContainer, Provider, Scope, from_context
from dishka.integrations.base import (
    InjectFunc,
    is_dishka_injected,
    wrap_injection,
)
from vkbottle import BaseMiddleware, Bot
from vkbottle.dispatch.views.abc import ABCRawEventView
from vkbottle.dispatch.views.bot import BotMessageView, RawBotEventView
from vkbottle.framework.labeler import ABCLabeler

P = ParamSpec("P")
T = TypeVar("T")
CONTAINER_NAME: Final = "dishka_container"
VkbottleEventData = NewType("VkbottleEventData", object)


def inject(func: Callable[P, T]) -> Callable[P, T]:
    def container_getter(
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> AsyncContainer:
        if args:
            event = args[0]
            if isinstance(event, dict):
                raw_container = event.get(f"_{CONTAINER_NAME}")
                if isinstance(raw_container, AsyncContainer):
                    return raw_container
            event_container = getattr(event, f"_{CONTAINER_NAME}", None)
            if isinstance(event_container, AsyncContainer):
                return event_container

        raise KeyError(CONTAINER_NAME)

    return wrap_injection(
        func=func,
        is_async=True,
        container_getter=container_getter,
    )


class VkbottleProvider(Provider):
    event = from_context(VkbottleEventData, scope=Scope.REQUEST)


class ContainerMiddleware(BaseMiddleware[Any]):
    def __init__(
        self,
        event: Any,
        view: BotMessageView | RawBotEventView,
        container: AsyncContainer,
    ) -> None:
        super().__init__(event, view)
        self.container = container
        self._wrapper: Any = None

    async def pre(self) -> None:
        self._wrapper = self.container(
            {
                VkbottleEventData: self.event,
            },
        )
        sub_container = await self._wrapper.__aenter__()
        if isinstance(self.event, dict):
            self.event[f"_{CONTAINER_NAME}"] = sub_container
        else:
            setattr(self.event, f"_{CONTAINER_NAME}", sub_container)
        self.send({CONTAINER_NAME: sub_container})

    async def post(self) -> None:
        if self._wrapper is not None:
            await self._wrapper.__aexit__(None, None, None)


def patch_raw_event_model_factory(
    raw_event_view: ABCRawEventView[Any, Any],
) -> None:
    original_get_event_model = raw_event_view.get_event_model

    def get_event_model_with_container(
        handler_basement: Any,
        event: dict[str, Any],
    ) -> Any:
        event_model = original_get_event_model(handler_basement, event)
        container = event.get(f"_{CONTAINER_NAME}")
        if isinstance(container, AsyncContainer):
            if isinstance(event_model, dict):
                event_model[f"_{CONTAINER_NAME}"] = container
            else:
                setattr(event_model, f"_{CONTAINER_NAME}", container)
        return event_model

    raw_event_view.get_event_model = get_event_model_with_container  # type: ignore[method-assign]


def provide_dependencies(
    container: AsyncContainer,
) -> type[ContainerMiddleware]:
    class ContainerMiddlewareFinal(ContainerMiddleware):
        def __init__(
            self,
            event: Any,
            view: BotMessageView | RawBotEventView,
        ) -> None:
            super().__init__(event, view, container=container)

    return ContainerMiddlewareFinal


def inject_labeler(  # noqa: C901, PLR0912
    labeler: ABCLabeler,
    inject_func: InjectFunc[P, T] = inject,
) -> None:
    injected_rules: set[int] = set()

    def inject_rule(rule: Any) -> None:
        rule_id = id(rule)
        if rule_id in injected_rules:
            return
        injected_rules.add(rule_id)

        callback = getattr(rule, "check", None)
        if callable(callback) and not is_dishka_injected(callback):
            rule.check = inject_func(callback)

        nested_rules = getattr(rule, "rules", None)
        if isinstance(nested_rules, Iterable):
            for nested_rule in nested_rules:
                inject_rule(nested_rule)

    for handler in labeler.message_view.handlers:
        if not hasattr(handler, "handler"):
            continue
        callback = handler.handler
        if not callable(callback):
            continue
        if not is_dishka_injected(callback):
            handler.handler = inject_func(callback)

        if hasattr(handler, "rules"):
            for rule in handler.rules:
                inject_rule(rule)

    for handlers in labeler.raw_event_view.handlers.values():
        for handler_basement in handlers:
            handler = handler_basement.handler
            if not hasattr(handler, "handler"):
                continue
            callback = handler.handler
            if not callable(callback):
                continue
            if not is_dishka_injected(callback):
                handler.handler = inject_func(callback)

            if hasattr(handler, "rules"):
                for rule in handler.rules:
                    inject_rule(rule)


def setup_dishka(
    container: AsyncContainer,
    bot: Bot,
    *,
    auto_inject: bool = False,
) -> None:
    middleware = provide_dependencies(container)
    bot.labeler.message_view.register_middleware(middleware)
    bot.labeler.raw_event_view.register_middleware(middleware)
    patch_raw_event_model_factory(bot.labeler.raw_event_view)

    if auto_inject is True:
        inject_labeler(bot.labeler, inject_func=inject)
