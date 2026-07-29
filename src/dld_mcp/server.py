"""MCP server for Dubai Land Department property data."""

import logging
from datetime import date
from importlib.metadata import version
from typing import Annotated, Any, Literal

import httpx
from mcp.server import MCPServer
from pydantic import Field, StringConstraints

API_BASE = "https://offerbrief.com/api"
REQUEST_TIMEOUT = 30.0
PACKAGE_VERSION = version("dld-mcp")

logging.getLogger("httpx").setLevel(logging.WARNING)

QueryType = Literal["sales", "rentals"]
PropertyType = Literal["all", "apartment", "villa", "townhouse"]
Bedrooms = Literal["all", "studio", "1", "2", "3", "4", "5+"]
Metric = Literal["stats", "count", "list"]
Area = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2)]
DateParam = Annotated[str, Field(pattern=r"^$|^\d{4}-\d{2}-\d{2}$")]
Limit = Annotated[int, Field(ge=1, le=50)]


class OfferBriefClient:
    def __init__(self, base_url: str = API_BASE, transport: httpx.AsyncBaseTransport | None = None):
        self._base_url = base_url
        self._transport = transport

    async def query(self, params: dict[str, str | int]) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(
                base_url=self._base_url,
                headers={"User-Agent": f"dld-mcp/{PACKAGE_VERSION}"},
                timeout=REQUEST_TIMEOUT,
                transport=self._transport,
            ) as client:
                response = await client.get("/query", params=params)
        except httpx.TimeoutException:
            return {"error": "OfferBrief request timed out", "status": 504}
        except httpx.RequestError:
            return {"error": "OfferBrief is unavailable", "status": 503}

        if response.status_code >= 400:
            return _http_error(response.status_code)

        try:
            payload = response.json()
        except ValueError:
            return {"error": "OfferBrief returned invalid JSON", "status": 502}

        if not isinstance(payload, dict):
            return {"error": "OfferBrief returned an unexpected response", "status": 502}
        return payload


def _http_error(status_code: int) -> dict[str, str | int]:
    if status_code == 400:
        message = "OfferBrief rejected the query"
    elif status_code == 404:
        message = "No matching OfferBrief data was found"
    elif status_code == 429:
        message = "OfferBrief rate limit exceeded"
    elif status_code >= 500:
        message = "OfferBrief upstream error"
    else:
        message = "OfferBrief API error"
    return {"error": message, "status": status_code}


def _parse_date(value: str, field_name: str) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"{field_name} must use YYYY-MM-DD") from error


offerbrief_client = OfferBriefClient()

mcp = MCPServer(
    "dld-mcp",
    title="Dubai Land Department",
    description="Query Dubai property sales transactions and rental contracts.",
    instructions="Use query_dld with an area and optional property, bedroom, date, metric, and limit filters.",
    version=PACKAGE_VERSION,
)


@mcp.tool()
async def query_dld(
    area: Area,
    type: QueryType = "sales",
    property_type: PropertyType = "all",
    bedrooms: Bedrooms = "all",
    date_from: DateParam = "",
    date_to: DateParam = "",
    metric: Metric = "stats",
    limit: Limit = 10,
) -> dict[str, Any]:
    """Query Dubai property sales transactions or rental contracts."""
    start_date = _parse_date(date_from, "date_from")
    end_date = _parse_date(date_to, "date_to")
    if start_date and end_date and start_date > end_date:
        raise ValueError("date_from must not be later than date_to")
    if type == "rentals" and property_type != "all":
        raise ValueError("property_type is only supported for sales queries")

    params: dict[str, str | int] = {
        "area": area,
        "type": type,
        "property_type": property_type,
        "bedrooms": bedrooms,
        "metric": metric,
        "limit": limit,
    }
    if date_from:
        params["date_from"] = date_from
    if date_to:
        params["date_to"] = date_to
    return await offerbrief_client.query(params)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
