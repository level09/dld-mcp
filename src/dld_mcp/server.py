"""MCP server for Dubai Land Department property data."""

import httpx
from mcp.server.fastmcp import FastMCP

API_BASE = "https://offerbrief.com/api"

mcp = FastMCP(
    "Dubai Land Department",
    instructions="""Query Dubai property data: 1.6M+ DLD sales transactions and 9.5M+ Ejari rental contracts.
Use query_dld with filters for area, property type, bedrooms, dates, etc.
Supports fuzzy search and aliases (Marina, JBR, Downtown, Palm, JVC, JLT).""",
)


@mcp.tool()
def query_dld(
    area: str,
    type: str = "sales",
    property_type: str = "all",
    bedrooms: str = "all",
    date_from: str = "",
    date_to: str = "",
    metric: str = "stats",
    limit: int = 10,
) -> dict:
    """Query Dubai property data - sales transactions or rental contracts.

    Args:
        area: Location to search (e.g., "Marina", "JBR", "Downtown", "Palm Jumeirah", or building name)
        type: "sales" for DLD transactions, "rentals" for Ejari contracts
        property_type: "all", "apartment", "villa", or "townhouse" (sales only)
        bedrooms: "all", "studio", "1", "2", "3", "4", "5+"
        date_from: Start date YYYY-MM-DD (default: last 12 months for sales, 24 for rentals)
        date_to: End date YYYY-MM-DD (default: today)
        metric: "stats" (aggregated statistics), "count" (just count), "list" (individual records)
        limit: Max records for list mode (1-50, default 10)

    Returns:
        For stats: median/avg/min/max prices, transaction count, total volume
        For count: just the count of matching records
        For list: individual transaction/contract records

    Examples:
        - "How many villas sold in Palm Jumeirah in 2024?"
          query_dld(area="Palm", property_type="villa", date_from="2024-01-01", metric="count")

        - "Average rent for 2BR in Marina"
          query_dld(area="Marina", type="rentals", bedrooms="2")

        - "Recent sales in Downtown"
          query_dld(area="Downtown", metric="list", limit=10)

        - "Compare JBR vs Marina prices"
          Call twice with different areas
    """
    if not area or len(area) < 2:
        return {"error": "area must be at least 2 characters"}

    params = {
        "area": area,
        "type": type,
        "property_type": property_type,
        "bedrooms": bedrooms,
        "metric": metric,
        "limit": min(max(1, limit), 50),
    }
    if date_from:
        params["date_from"] = date_from
    if date_to:
        params["date_to"] = date_to

    try:
        with httpx.Client(timeout=30) as client:
            r = client.get(f"{API_BASE}/query", params=params)
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return e.response.json()
        return {"error": f"API error: {e.response.status_code}"}


def main():
    mcp.run()


if __name__ == "__main__":
    main()
