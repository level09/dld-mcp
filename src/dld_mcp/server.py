"""MCP server for Dubai Land Department property data."""

import argparse
import json
import logging
from datetime import date
from importlib.metadata import version
from typing import Annotated, Any, Literal

import httpx
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import CallToolResult, TextContent, ToolAnnotations
from pydantic import Field, StringConstraints

API_BASE = "https://offerbrief.com/api"
REQUEST_TIMEOUT = 30.0
PACKAGE_VERSION = version("dld-mcp")

logging.getLogger("httpx").setLevel(logging.WARNING)

QueryType = Literal["sales", "rentals"]
PropertyType = Literal["all", "apartment", "villa", "townhouse"]
Bedrooms = Literal["all", "studio", "1", "2", "3", "4", "5", "5+"]
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
            return _http_error(response)

        try:
            payload = response.json()
        except ValueError:
            return {"error": "OfferBrief returned invalid JSON", "status": 502}

        if not isinstance(payload, dict):
            return {"error": "OfferBrief returned an unexpected response", "status": 502}
        return payload


def _http_error(response: httpx.Response) -> dict[str, str | int]:
    status_code = response.status_code
    try:
        detail = response.json().get("error")
    except (ValueError, AttributeError):
        detail = None
    if status_code in (400, 404) and isinstance(detail, str) and detail:
        message = detail
    elif status_code == 400:
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
        raise ToolError(f"{field_name} must be a real date in YYYY-MM-DD format") from error


offerbrief_client = OfferBriefClient()

mcp = MCPServer(
    "dld-mcp",
    title="Dubai Land Department",
    description="Query Dubai property sales transactions and rental contracts.",
    instructions="Use query_dld with an area and optional property, bedroom, date, metric, and limit filters.",
    version=PACKAGE_VERSION,
)


@mcp.tool(
    annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True)
)
async def query_dld(
    area: Area,
    type: QueryType = "sales",
    property_type: PropertyType = "all",
    bedrooms: Bedrooms = "all",
    date_from: DateParam = "",
    date_to: DateParam = "",
    metric: Metric = "stats",
    limit: Limit = 10,
) -> Annotated[CallToolResult, dict[str, Any]]:
    """Query Dubai property sales or rentals. Dates default to the last 12 months.

    Bedroom filters are supported only for sales. Prices are in AED and areas in square metres.
    """
    start_date = _parse_date(date_from, "date_from")
    end_date = _parse_date(date_to, "date_to")
    if start_date and end_date and start_date > end_date:
        raise ToolError("date_from must not be later than date_to")
    if type == "rentals" and bedrooms != "all":
        raise ToolError("bedrooms is only supported for sales queries; DLD's current rental feed has no bedroom data")

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
    payload = await offerbrief_client.query(params)
    return CallToolResult(
        content=[TextContent(type="text", text=json.dumps(payload))],
        structured_content=payload,
        is_error="error" in payload,
    )


def main() -> None:
    parser = argparse.ArgumentParser(prog="dld-mcp")
    parser.add_argument("--http", action="store_true", help="Serve streamable HTTP instead of stdio")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--public-host", help="Public hostname allowed in Host and Origin headers")
    args = parser.parse_args()
    if not args.http:
        mcp.run(transport="stdio")
        return
    hosts = ["127.0.0.1", f"127.0.0.1:{args.port}", "localhost", f"localhost:{args.port}"]
    origins = []
    if args.public_host:
        hosts.append(args.public_host)
        origins.append(f"https://{args.public_host}")
    # ponytail: tool calls go through the public API, so all remote users share its per-IP limit
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=args.port,
        stateless_http=True,
        json_response=True,
        transport_security=TransportSecuritySettings(allowed_hosts=hosts, allowed_origins=origins),
    )


if __name__ == "__main__":
    main()
