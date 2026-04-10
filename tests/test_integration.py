from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from typing import Any, ParamSpec, TypeVar
from unittest.mock import Mock

import pytest
from dishka import FromDishka, make_async_container
from dishka.provider import BaseProvider
from vkbottle.bot import Bot, BotLabeler, Message
from vkbottle_types import BaseGroupEvent, GroupEventType, GroupTypes

from vkbottle_dishka import inject, setup_dishka
from .common import (
    APP_DEP_VALUE,
    REQUEST_DEP_VALUE,
    AppDep,
    AppProvider,
    RequestDep,
    make_message_allow_event,
    make_message_deny_event,
    send_event,
    send_raw_event,
)

P = ParamSpec("P")
T = TypeVar("T")


@asynccontextmanager
async def dishka_app(
    handler: Callable[P, T],
    provider: BaseProvider,
    *,
    auto_inject: bool = False,
) -> AsyncGenerator[Bot, None]:
    bot = Bot(token="")
    bot.on.message()(handler if auto_inject else inject(handler))

    container = make_async_container(provider)
    setup_dishka(container=container, bot=bot, auto_inject=auto_inject)

    yield bot
    await container.close()


@asynccontextmanager
async def dishka_raw_app(
    event_type: str | GroupEventType,
    dataclass: type[dict[str, Any] | BaseGroupEvent],
    handler: Callable[P, T],
    provider: BaseProvider,
    *,
    auto_inject: bool = False,
) -> AsyncGenerator[Bot, None]:
    labeler = BotLabeler()
    labeler.raw_event(event_type, dataclass)(
        handler if auto_inject else inject(handler),
    )

    bot = Bot(token="")
    bot.labeler.load(labeler)

    container = make_async_container(provider)
    setup_dishka(container=container, bot=bot, auto_inject=auto_inject)

    yield bot
    await container.close()


async def handle_with_app(
    _: Message,
    a: FromDishka[AppDep],
    mock: FromDishka[Mock],
) -> None:
    mock(a)


async def handle_with_request(
    _: Message,
    a: FromDishka[RequestDep],
    mock: FromDishka[Mock],
) -> None:
    mock(a)


async def raw_handle_with_app(
    _event: dict[str, Any],
    a: FromDishka[AppDep],
    mock: FromDishka[Mock],
) -> None:
    mock(a)


async def raw_handle_with_request(
    _event: dict[str, Any],
    a: FromDishka[RequestDep],
    mock: FromDishka[Mock],
) -> None:
    mock(a)


async def typed_handle_with_app(
    _event: GroupTypes.MessageAllow,
    a: FromDishka[AppDep],
    mock: FromDishka[Mock],
) -> None:
    mock(a)


async def typed_handle_with_request(
    _event: GroupTypes.MessageAllow,
    a: FromDishka[RequestDep],
    mock: FromDishka[Mock],
) -> None:
    mock(a)


@pytest.mark.asyncio
async def test_app_dependency(
    app_provider: AppProvider,
    *,
    auto_inject: bool,
) -> None:
    async with dishka_app(
        handle_with_app,
        app_provider,
        auto_inject=auto_inject,
    ) as bot:
        await send_event(bot, "привет")
        app_provider.mock.assert_called_with(APP_DEP_VALUE)
        app_provider.app_released.assert_not_called()
    app_provider.app_released.assert_called()


@pytest.mark.asyncio
async def test_request_dependency(
    app_provider: AppProvider,
    *,
    auto_inject: bool,
) -> None:
    async with dishka_app(
        handle_with_request,
        app_provider,
        auto_inject=auto_inject,
    ) as bot:
        await send_event(bot, "привет")
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()


@pytest.mark.asyncio
async def test_request_dependency_twice(
    app_provider: AppProvider,
    *,
    auto_inject: bool,
) -> None:
    async with dishka_app(
        handle_with_request,
        app_provider,
        auto_inject=auto_inject,
    ) as bot:
        await send_event(bot, "привет")
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()

        app_provider.mock.reset_mock()
        app_provider.request_released.reset_mock()

        await send_event(bot, "ещё раз")
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()


@pytest.mark.asyncio
async def test_raw_message_deny_app_dependency(
    app_provider: AppProvider,
    *,
    auto_inject: bool,
) -> None:
    async with dishka_raw_app(
        "message_deny",
        dict,
        raw_handle_with_app,
        app_provider,
        auto_inject=auto_inject,
    ) as bot:
        await send_raw_event(bot, make_message_deny_event())
        app_provider.mock.assert_called_with(APP_DEP_VALUE)
        app_provider.app_released.assert_not_called()
    app_provider.app_released.assert_called()


@pytest.mark.asyncio
async def test_raw_message_deny_request_dependency(
    app_provider: AppProvider,
    *,
    auto_inject: bool,
) -> None:
    async with dishka_raw_app(
        "message_deny",
        dict,
        raw_handle_with_request,
        app_provider,
        auto_inject=auto_inject,
    ) as bot:
        await send_raw_event(bot, make_message_deny_event())
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()


@pytest.mark.asyncio
async def test_raw_message_deny_request_dependency_twice(
    app_provider: AppProvider,
    *,
    auto_inject: bool,
) -> None:
    async with dishka_raw_app(
        "message_deny",
        dict,
        raw_handle_with_request,
        app_provider,
        auto_inject=auto_inject,
    ) as bot:
        await send_raw_event(bot, make_message_deny_event())
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()

        app_provider.mock.reset_mock()
        app_provider.request_released.reset_mock()

        await send_raw_event(bot, make_message_deny_event())
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()


@pytest.mark.asyncio
async def test_raw_message_allow_app_dependency(
    app_provider: AppProvider,
    *,
    auto_inject: bool,
) -> None:
    async with dishka_raw_app(
        GroupEventType.MESSAGE_ALLOW,
        GroupTypes.MessageAllow,
        typed_handle_with_app,
        app_provider,
        auto_inject=auto_inject,
    ) as bot:
        await send_raw_event(bot, make_message_allow_event())
        app_provider.mock.assert_called_with(APP_DEP_VALUE)
        app_provider.app_released.assert_not_called()
    app_provider.app_released.assert_called()


@pytest.mark.asyncio
async def test_raw_message_allow_request_dependency(
    app_provider: AppProvider,
    *,
    auto_inject: bool,
) -> None:
    async with dishka_raw_app(
        GroupEventType.MESSAGE_ALLOW,
        GroupTypes.MessageAllow,
        typed_handle_with_request,
        app_provider,
        auto_inject=auto_inject,
    ) as bot:
        await send_raw_event(bot, make_message_allow_event())
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()


@pytest.mark.asyncio
async def test_raw_message_allow_request_dependency_twice(
    app_provider: AppProvider,
    *,
    auto_inject: bool,
) -> None:
    async with dishka_raw_app(
        GroupEventType.MESSAGE_ALLOW,
        GroupTypes.MessageAllow,
        typed_handle_with_request,
        app_provider,
        auto_inject=auto_inject,
    ) as bot:
        await send_raw_event(bot, make_message_allow_event())
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()

        app_provider.mock.reset_mock()
        app_provider.request_released.reset_mock()

        await send_raw_event(bot, make_message_allow_event())
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()
