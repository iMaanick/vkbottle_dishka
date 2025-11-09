from typing import Any
from unittest.mock import AsyncMock

from vkbottle import API, Bot
from vkbottle_types.methods.base_category import BaseCategory


async def send_event(bot: Bot, text: str) -> AsyncMock:
    event = make_event(text)

    mock_api = AsyncMock(spec=API)
    mock_api.messages.send = AsyncMock()
    mock_api.messages.get_set_params = BaseCategory.get_set_params
    await bot.router.route(event, mock_api)

    return mock_api


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
                "button_actions": [
                    "text",
                    "vkpay",
                    "open_app",
                    "location",
                    "open_link",
                ],
                "keyboard": True,
                "inline_keyboard": True,
                "carousel": False,
                "lang_id": 0,
            },
        },
        "event_id": "abcd1234efgh5678",
    }
