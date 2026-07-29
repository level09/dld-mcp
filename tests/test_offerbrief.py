import logging

import httpx
import pytest
from mcp import Client

from dld_mcp.server import mcp


@pytest.fixture
async def client():
    async with Client(mcp) as connected_client:
        yield connected_client


async def call(client: Client):
    return await client.call_tool("query_dld", {"area": "Marina"})


@pytest.mark.anyio
async def test_request_uses_query_route_parameters_and_user_agent(client, set_http_handler):
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["request"] = request
        return httpx.Response(200, json={"count": 1})

    set_http_handler(handler)

    result = await call(client)

    assert not result.is_error
    request = captured["request"]
    assert str(request.url).startswith("https://offerbrief.com/api/query?")
    assert request.url.params["area"] == "Marina"
    assert request.url.params["type"] == "sales"
    assert request.url.params["metric"] == "stats"
    assert request.headers["user-agent"].startswith("dld-mcp/")


@pytest.mark.anyio
async def test_query_parameters_are_not_logged(client, set_http_handler, caplog):
    set_http_handler(lambda request: httpx.Response(200, json={"count": 1}))
    caplog.set_level(logging.INFO)

    await call(client)

    assert "Marina" not in caplog.text


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("status_code", "message"),
    [
        (400, "OfferBrief rejected the query"),
        (404, "No matching OfferBrief data was found"),
        (429, "OfferBrief rate limit exceeded"),
        (500, "OfferBrief upstream error"),
    ],
)
async def test_http_failures_return_stable_errors(client, set_http_handler, status_code, message):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, json={"private": "must not be returned"})

    set_http_handler(handler)

    result = await call(client)

    assert not result.is_error
    assert result.structured_content == {"error": message, "status": status_code}


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("exception", "expected"),
    [
        (httpx.ReadTimeout("slow"), {"error": "OfferBrief request timed out", "status": 504}),
        (httpx.ConnectError("offline"), {"error": "OfferBrief is unavailable", "status": 503}),
    ],
)
async def test_network_failures_return_stable_errors(client, set_http_handler, exception, expected):
    def handler(request: httpx.Request) -> httpx.Response:
        raise exception

    set_http_handler(handler)

    result = await call(client)

    assert not result.is_error
    assert result.structured_content == expected


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("response", "message"),
    [
        (httpx.Response(200, text="<html>not json</html>"), "OfferBrief returned invalid JSON"),
        (httpx.Response(200, json=["unexpected"]), "OfferBrief returned an unexpected response"),
    ],
)
async def test_malformed_responses_return_stable_errors(client, set_http_handler, response, message):
    def handler(request: httpx.Request) -> httpx.Response:
        return response

    set_http_handler(handler)

    result = await call(client)

    assert not result.is_error
    assert result.structured_content == {"error": message, "status": 502}
