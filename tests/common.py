from collections.abc import Iterable
from typing import Any, NewType
from unittest.mock import AsyncMock, Mock

from dishka import Provider, Scope, from_context, provide
from dishka.entities.depends_marker import FromDishka
from vkbottle import API, Bot
from vkbottle_types.methods.base_category import BaseCategory

ContextDep = NewType("ContextDep", str)
UserDep = NewType("UserDep", str)
StepDep = NewType("StepDep", str)

AppDep = NewType("AppDep", str)
APP_DEP_VALUE = AppDep("APP")

RequestDep = NewType("RequestDep", str)
REQUEST_DEP_VALUE = RequestDep("REQUEST")

WebSocketDep = NewType("WebSocketDep", str)
WS_DEP_VALUE = WebSocketDep("WS")

AppMock = NewType("AppMock", Mock)


class AppProvider(Provider):
    context = from_context(provides=ContextDep, scope=Scope.REQUEST)

    def __init__(self) -> None:
        super().__init__()
        self.app_released = Mock()
        self.request_released = Mock()
        self.websocket_released = Mock()
        self.db_session_released = Mock()
        self.mock = Mock()
        self.app_mock = AppMock(Mock())

    @provide(scope=Scope.APP)
    def app(self) -> Iterable[AppDep]:
        yield APP_DEP_VALUE
        self.app_released()

    @provide(scope=Scope.REQUEST)
    def request(self) -> Iterable[RequestDep]:
        yield REQUEST_DEP_VALUE
        self.request_released()

    @provide(scope=Scope.REQUEST)
    def websocket(self) -> Iterable[WebSocketDep]:
        yield WS_DEP_VALUE
        self.websocket_released()

    @provide(scope=Scope.REQUEST)
    def user(self, context: FromDishka[ContextDep]) -> Iterable[UserDep]:
        yield UserDep(f"user_id.from_context({context})")
        self.db_session_released()

    @provide(scope=Scope.REQUEST)
    def get_mock(self) -> Mock:
        return self.mock

    @provide(scope=Scope.APP)
    def get_app_mock(self) -> AppMock:
        return self.app_mock

    @provide(scope=Scope.STEP)
    def step(self, request: FromDishka[RequestDep]) -> StepDep:
        return StepDep(f"step for {request}")


class WebSocketAppProvider(Provider):
    def __init__(self) -> None:
        super().__init__()
        self.app_released = Mock()
        self.request_released = Mock()
        self.websocket_released = Mock()
        self.mock = Mock()

    @provide(scope=Scope.APP)
    def app(self) -> Iterable[AppDep]:
        yield APP_DEP_VALUE
        self.app_released()

    @provide(scope=Scope.SESSION)
    def request(self) -> Iterable[RequestDep]:
        yield REQUEST_DEP_VALUE
        self.request_released()

    @provide(scope=Scope.SESSION)
    def websocket(self) -> Iterable[WebSocketDep]:
        yield WS_DEP_VALUE
        self.websocket_released()

    @provide(scope=Scope.SESSION)
    def get_mock(self) -> Mock:
        return self.mock


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
