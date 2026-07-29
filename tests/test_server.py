from collections.abc import Callable

import httpx
import pytest
from mcp import Client

from dld_mcp.server import mcp


@pytest.fixture
async def client():
    async with Client(mcp) as connected_client:
        yield connected_client


def json_handler(payload: dict) -> Callable[[httpx.Request], httpx.Response]:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    return handler


async def call(client: Client, **arguments):
    return await client.call_tool("query_dld", {"area": "Marina", **arguments})


@pytest.mark.anyio
async def test_server_discovers_query_dld_with_enum_and_boundary_schema(client):
    tools = (await client.list_tools()).tools

    assert [tool.name for tool in tools] == ["query_dld"]
    schema = tools[0].input_schema
    assert schema["properties"]["type"]["enum"] == ["sales", "rentals"]
    assert schema["properties"]["property_type"]["enum"] == ["all", "apartment", "villa", "townhouse"]
    assert schema["properties"]["bedrooms"]["enum"] == ["all", "studio", "1", "2", "3", "4", "5+"]
    assert schema["properties"]["metric"]["enum"] == ["stats", "count", "list"]
    assert schema["properties"]["limit"]["minimum"] == 1
    assert schema["properties"]["limit"]["maximum"] == 50
    assert schema["properties"]["date_from"]["pattern"] == r"^$|^\d{4}-\d{2}-\d{2}$"
    assert schema["properties"]["date_to"]["pattern"] == r"^$|^\d{4}-\d{2}-\d{2}$"


@pytest.mark.anyio
@pytest.mark.parametrize("area", ["", " ", " M "])
async def test_area_requires_two_non_whitespace_characters(client, area):
    result = await client.call_tool("query_dld", {"area": area})

    assert result.is_error


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("field", "values"),
    [
        ("type", ["sales", "rentals"]),
        ("property_type", ["all", "apartment", "villa", "townhouse"]),
        ("bedrooms", ["all", "studio", "1", "2", "3", "4", "5+"]),
        ("metric", ["stats", "count", "list"]),
    ],
)
async def test_all_documented_enum_values_are_accepted(client, set_http_handler, field, values):
    set_http_handler(json_handler({"ok": True}))

    for value in values:
        arguments = {field: value}
        if field == "property_type" and value != "all":
            arguments["type"] = "sales"
        result = await call(client, **arguments)
        assert not result.is_error, (field, value, result.content)


@pytest.mark.anyio
@pytest.mark.parametrize("field", ["type", "property_type", "bedrooms", "metric"])
async def test_unknown_enum_values_are_rejected_before_http(client, field):
    result = await call(client, **{field: "unknown"})

    assert result.is_error


@pytest.mark.anyio
@pytest.mark.parametrize("date_field", ["date_from", "date_to"])
@pytest.mark.parametrize("value", ["2026/01/01", "2026-13-01", "not-a-date"])
async def test_dates_must_be_real_iso_dates(client, date_field, value):
    result = await call(client, **{date_field: value})

    assert result.is_error


@pytest.mark.anyio
async def test_date_from_cannot_follow_date_to(client):
    result = await call(client, date_from="2026-07-30", date_to="2026-07-29")

    assert result.is_error


@pytest.mark.anyio
@pytest.mark.parametrize(("limit", "valid"), [(0, False), (1, True), (50, True), (51, False)])
async def test_limit_boundaries(client, set_http_handler, limit, valid):
    set_http_handler(json_handler({"ok": True}))

    result = await call(client, limit=limit)

    assert result.is_error is not valid


@pytest.mark.anyio
async def test_rentals_reject_sales_only_property_type(client):
    result = await call(client, type="rentals", property_type="villa")

    assert result.is_error


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("query_type", "metric", "payload"),
    [
        (
            "sales",
            "stats",
            {
                "area": "Dubai Marina",
                "avg_price_per_sqm": 21_000,
                "count": 2,
                "match_type": "community",
                "max_price_per_sqm": 22_000,
                "median_price": 1_500_000,
                "median_price_per_sqm": 21_000,
                "min_price_per_sqm": 20_000,
                "total_volume": 3_100_000,
                "type": "sales",
            },
        ),
        ("sales", "count", {"area": "Dubai Marina", "count": 2, "match_type": "community", "type": "sales"}),
        (
            "sales",
            "list",
            {
                "area": "Dubai Marina",
                "count": 1,
                "match_type": "community",
                "transactions": [
                    {
                        "area_sqm": 75,
                        "community": "Dubai Marina",
                        "date": "2026-07-01",
                        "is_offplan": False,
                        "price": 1_500_000,
                        "price_per_sqm": 20_000,
                        "project": "Example Tower",
                        "rooms": "1 B/R",
                    }
                ],
                "type": "sales",
            },
        ),
        (
            "rentals",
            "stats",
            {
                "area": "Dubai Marina",
                "avg_annual_rent": 125_000,
                "count": 2,
                "match_type": "community",
                "max_annual_rent": 130_000,
                "median_annual_rent": 125_000,
                "min_annual_rent": 120_000,
                "type": "rentals",
            },
        ),
        ("rentals", "count", {"area": "Dubai Marina", "count": 2, "match_type": "community", "type": "rentals"}),
        (
            "rentals",
            "list",
            {
                "area": "Dubai Marina",
                "contracts": [
                    {
                        "annual_rent": 120_000,
                        "area_sqm": 75,
                        "community": "Dubai Marina",
                        "date": "2026-07-01",
                        "project": "Example Tower",
                        "property_type": "Unit",
                    }
                ],
                "count": 1,
                "match_type": "community",
                "type": "rentals",
            },
        ),
    ],
)
async def test_preserves_offerbrief_response_shapes(client, set_http_handler, query_type, metric, payload):
    set_http_handler(json_handler(payload))

    result = await call(client, type=query_type, metric=metric)

    assert not result.is_error
    assert result.structured_content == payload
