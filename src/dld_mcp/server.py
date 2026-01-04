"""MCP server for Dubai Land Department property data via OfferBrief API."""

import httpx
from mcp.server.fastmcp import FastMCP

API_BASE = "https://offerbrief.com/api"

mcp = FastMCP(
    "DLD Property Data",
    instructions="""Dubai Land Department property transaction data.
Query 1.6M+ real estate transactions via OfferBrief API. Search properties,
get market stats, check if prices are fair, and find trending projects.""",
)


def api_get(endpoint: str, params: dict | None = None) -> dict | list:
    """Make GET request to OfferBrief API."""
    with httpx.Client(timeout=30) as client:
        r = client.get(f"{API_BASE}/{endpoint}", params=params)
        r.raise_for_status()
        return r.json()


def api_post(endpoint: str, data: dict) -> dict:
    """Make POST request to OfferBrief API."""
    with httpx.Client(timeout=30) as client:
        r = client.post(f"{API_BASE}/{endpoint}", json=data)
        r.raise_for_status()
        return r.json()


@mcp.tool()
def find_project(query: str) -> dict:
    """Find the best matching project for a query.

    More forgiving than search - returns single best match with stats.
    Supports aliases like JBR, Marina, Downtown, JVC, JLT, Palm.

    Args:
        query: Project name, building, or area (can be partial/fuzzy)

    Returns:
        Best matching project with name, community, transaction count, and median price/sqm.
        Use the returned 'project' name for check_deal.
    """
    if not query or len(query) < 2:
        return {"error": "Query must be at least 2 characters"}

    try:
        return api_get("find-project", {"q": query})
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return e.response.json()
        raise


@mcp.tool()
def search_properties(query: str) -> list[dict]:
    """Search for multiple matching projects/buildings.

    Returns list of matches - use find_project if you just need the best match.
    Supports aliases like JBR, Marina, Downtown, JVC, JLT, Palm.

    Args:
        query: Search term (project name, building, or area)

    Returns:
        List of matching projects with transaction counts
    """
    if not query or len(query) < 2:
        return [{"error": "Query must be at least 2 characters"}]

    results = api_get("search", {"q": query})
    if not results:
        return [{"error": f"No properties found matching '{query}'"}]
    return results


@mcp.tool()
def get_market_pulse() -> dict:
    """Get current Dubai real estate market overview with YoY changes.

    Returns:
        Market metrics including median prices for apartments and villas,
        year-over-year changes, and transaction volume for last 90 days.
    """
    return api_get("market-pulse")


@mcp.tool()
def get_trending_projects() -> list[dict]:
    """Get most transacted projects in the last 90 days.

    Returns:
        List of 8 trending projects with transaction counts and off-plan percentage.
    """
    return api_get("trending")


@mcp.tool()
def get_price_movers() -> list[dict]:
    """Get buildings with significant 6-month price changes.

    Returns balanced mix of ready and off-plan properties with 5-30% price swings.

    Returns:
        List of projects with price change percentage and current median.
    """
    return api_get("price-movers")


@mcp.tool()
def get_recent_sales() -> list[dict]:
    """Get notable recent transactions (>=1M AED, last 7 days).

    Returns:
        List of recent sales with property details and prices.
    """
    return api_get("recent-sales")


@mcp.tool()
def check_deal(project: str, area_sqm: float, price: float, rooms: str | None = None) -> dict:
    """Check if a property price is fair compared to market.

    Args:
        project: Project or building name
        area_sqm: Property size in square meters
        price: Asking price in AED
        rooms: Optional room type (e.g., "2 B/R", "Studio")

    Returns:
        Analysis with verdict: great_deal, good_deal, fair_price, above_market, or overpriced.
    """
    params = {"project": project, "area_sqm": area_sqm, "price": price}
    if rooms:
        params["rooms"] = rooms

    try:
        return api_get("check-deal", params)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {"error": f"Insufficient market data for '{project}'"}
        raise


@mcp.tool()
def analyze_listing(listing_text: str) -> dict:
    """Analyze a property listing using AI.

    Extracts property details from free-form listing text, compares to market data,
    and provides a verdict on whether it's a good deal.

    Args:
        listing_text: Property listing text (from PropertyFinder, Bayut, etc.)

    Returns:
        Extracted details, market comparison, and AI-generated verdict.
    """
    if not listing_text or len(listing_text) < 20:
        return {"error": "Please provide a property listing (at least 20 characters)"}

    try:
        return api_post("analyze-listing", {"text": listing_text})
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 400:
            return e.response.json()
        raise


# Resources
@mcp.resource("dld://market-summary")
def market_summary() -> str:
    """Current Dubai real estate market snapshot."""
    pulse = api_get("market-pulse")

    return f"""Dubai Real Estate Market Summary (as of {pulse['period']})

Transactions (90 days): {pulse['transactions']:,}

Overall Market:
  Median: AED {pulse['overall']['median_psqm']:,}/sqm
  YoY Change: {pulse['overall']['yoy_change']:+.1f}%

Apartments:
  Median: AED {pulse['apartments']['median_psqm']:,}/sqm
  YoY Change: {pulse['apartments']['yoy_change']:+.1f}%

Villas:
  Median: AED {pulse['villas']['median_psqm']:,}/sqm
  YoY Change: {pulse['villas']['yoy_change']:+.1f}%
"""


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
