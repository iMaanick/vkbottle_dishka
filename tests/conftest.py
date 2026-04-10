import pytest
from dishka import (
    AsyncContainer,
    Container,
    make_async_container,
    make_container,
)

from .common import AppProvider, WebSocketAppProvider


@pytest.fixture
def app_provider() -> AppProvider:
    return AppProvider()


@pytest.fixture
def ws_app_provider() -> WebSocketAppProvider:
    return WebSocketAppProvider()


@pytest.fixture
def async_container(app_provider: AppProvider) -> AsyncContainer:
    return make_async_container(app_provider)


@pytest.fixture
def container(app_provider: AppProvider) -> Container:
    return make_container(app_provider)

@pytest.fixture(params=[False, True], ids=["manual_inject", "auto_inject"])
def auto_inject(request: pytest.FixtureRequest) -> bool:
    return request.param  # type: ignore[no-any-return]
