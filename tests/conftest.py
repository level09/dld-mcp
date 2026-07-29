import httpx
import pytest

from dld_mcp.server import offerbrief_client


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def set_http_handler(monkeypatch):
    def set_handler(handler):
        monkeypatch.setattr(offerbrief_client, "_transport", httpx.MockTransport(handler))

    return set_handler
