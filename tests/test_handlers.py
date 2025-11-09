from typing import Any, AsyncGenerator
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from dishka import make_async_container, AsyncContainer
from vkbottle import API
from vkbottle.bot import Bot
from vkbottle_types.methods.base_category import BaseCategory

from handlers import example_labeler, setup_labelers
from providers import StrProvider, InteractorProvider
from vk_dishka import setup_dishka, VkbottleProvider


def make_event(text: str) -> dict[str, Any]:
    return {
        "type": "message_new",
        "group_id": 123456789,
        "object": {
            "message": {
                "date": 1699459200,
                "from_id": 987654321,
                "id": 456,
                "out": 0,
                "peer_id": 987654321,
                "text": text,
                "conversation_message_id": 112,
                "fwd_messages": [],
                "important": False,
                "random_id": 0,
                "attachments": [],
                "is_hidden": False,
                "version": 1,
            },
            "client_info": {
                "button_actions": ["text", "vkpay", "open_app", "location", "open_link"],
                "keyboard": True,
                "inline_keyboard": True,
                "carousel": False,
                "lang_id": 0,
            },
        },
        "event_id": "abcd1234efgh5678",
    }


@pytest_asyncio.fixture(scope="session")
async def vk_test_app() -> AsyncGenerator[tuple[Bot, AsyncContainer], None]:
    bot = Bot(token="test_token")
    container = make_async_container(
        StrProvider(),
        InteractorProvider(),
        VkbottleProvider(),
    )

    setup_labelers(bot, [example_labeler])
    setup_dishka(container, bot)

    yield bot, container
    await container.close()


async def send_event(bot: Bot, text: str) -> AsyncMock:
    event = make_event(text)

    mock_api = AsyncMock(spec=API)
    mock_api.messages.send = AsyncMock()
    mock_api.messages.get_set_params = BaseCategory.get_set_params
    await bot.router.route(event, mock_api)

    return mock_api


@pytest.mark.asyncio
async def test_hi_handler(vk_test_app: tuple[Bot, AsyncContainer]) -> None:
    bot, _ = vk_test_app
    mock_api = await send_event(bot, "привет")

    mock_api.messages.send.assert_awaited_once()
    args, kwargs = mock_api.messages.send.await_args
    assert "Привет!" == kwargs["message"]


@pytest.mark.asyncio
async def test_req_handler_dependency(vk_test_app: tuple[Bot, AsyncContainer]) -> None:
    bot, _ = vk_test_app
    mock_api = await send_event(bot, "req")
    args, kwargs = mock_api.messages.send.await_args
    assert "REQ" in kwargs["message"]


@pytest.mark.asyncio
async def test_app_handler_dependency(vk_test_app: tuple[Bot, AsyncContainer]) -> None:
    bot, _ = vk_test_app
    mock_api = await send_event(bot, "app")
    args, kwargs = mock_api.messages.send.await_args
    assert "APP" in kwargs["message"]
