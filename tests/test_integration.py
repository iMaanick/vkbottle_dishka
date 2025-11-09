from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from typing import ParamSpec, TypeVar
from unittest.mock import Mock

import pytest
from dishka import FromDishka, make_async_container
from dishka.provider import BaseProvider
from src.vkbottle_dishka.vk_dishka import inject, setup_dishka
from vkbottle.bot import Bot, Message

from .common import (
    APP_DEP_VALUE,
    REQUEST_DEP_VALUE,
    AppDep,
    AppProvider,
    RequestDep,
    send_event,
)

P = ParamSpec("P")
T = TypeVar("T")


@asynccontextmanager
async def dishka_app(
        handler: Callable[P, T],
        provider: BaseProvider,
) -> AsyncGenerator[Bot, None]:
    bot = Bot(token="")
    bot.on.message()(inject(handler))

    container = make_async_container(provider)
    setup_dishka(container=container, bot=bot)

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


@pytest.mark.asyncio
async def test_app_dependency(app_provider: AppProvider) -> None:
    async with dishka_app(handle_with_app, app_provider) as bot:
        await send_event(bot, "привет")
        app_provider.mock.assert_called_with(APP_DEP_VALUE)
        app_provider.app_released.assert_not_called()
    app_provider.app_released.assert_called()


@pytest.mark.asyncio
async def test_request_dependency(app_provider: AppProvider) -> None:
    async with dishka_app(handle_with_request, app_provider) as bot:
        await send_event(bot, "привет")
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()


@pytest.mark.asyncio
async def test_request_dependency_twice(app_provider: AppProvider) -> None:
    async with dishka_app(handle_with_request, app_provider) as bot:
        await send_event(bot, "привет")
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()

        app_provider.mock.reset_mock()
        app_provider.request_released.reset_mock()

        await send_event(bot, "ещё раз")
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()
