from typing import AsyncGenerator

import pytest
import pytest_asyncio
from dishka import make_async_container
from vkbottle.bot import Bot

from handlers import example_labeler, setup_labelers
from providers import StrProvider, InteractorProvider
from tests.common import send_event
from vk_dishka import setup_dishka, VkbottleProvider


@pytest_asyncio.fixture(scope="session")
async def vk_test_app() -> AsyncGenerator[Bot, None]:
    bot = Bot(token="test_token")
    container = make_async_container(
        StrProvider(),
        InteractorProvider(),
        VkbottleProvider(),
    )

    setup_labelers(bot, [example_labeler])
    setup_dishka(container, bot)

    yield bot
    await container.close()


@pytest.mark.asyncio
async def test_hi_handler(vk_test_app: Bot) -> None:
    bot = vk_test_app
    mock_api = await send_event(bot, "привет")

    mock_api.messages.send.assert_awaited_once()
    args, kwargs = mock_api.messages.send.await_args
    assert "Привет!" == kwargs["message"]


@pytest.mark.asyncio
async def test_req_handler_dependency(vk_test_app: Bot) -> None:
    bot = vk_test_app
    mock_api = await send_event(bot, "req")
    args, kwargs = mock_api.messages.send.await_args
    assert "REQ" in kwargs["message"]


@pytest.mark.asyncio
async def test_app_handler_dependency(vk_test_app: Bot) -> None:
    bot = vk_test_app
    mock_api = await send_event(bot, "app")
    args, kwargs = mock_api.messages.send.await_args
    assert "APP" in kwargs["message"]
