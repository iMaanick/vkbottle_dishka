from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from dishka import make_async_container
from examples.handlers import example_labeler, setup_labelers
from examples.providers import InteractorProvider, StrProvider
from src.vkbottle_dishka.vk_dishka import VkbottleProvider, setup_dishka
from vkbottle.bot import Bot

from tests.common import send_event


@pytest_asyncio.fixture(scope="session")
async def vk_test_app() -> AsyncGenerator[Bot, None]:
    bot = Bot(token="")
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
    _, kwargs = mock_api.messages.send.await_args
    assert kwargs["message"] == "Привет!"


@pytest.mark.asyncio
async def test_req_handler_dependency(vk_test_app: Bot) -> None:
    bot = vk_test_app
    mock_api = await send_event(bot, "req")
    _, kwargs = mock_api.messages.send.await_args
    assert "REQ" in kwargs["message"]


@pytest.mark.asyncio
async def test_app_handler_dependency(vk_test_app: Bot) -> None:
    bot = vk_test_app
    mock_api = await send_event(bot, "app")
    _, kwargs = mock_api.messages.send.await_args
    assert "APP" in kwargs["message"]
