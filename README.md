# DLD MCP Server

MCP server for Dubai Land Department property data. Query 1.6M+ real estate transactions directly from AI assistants via the [OfferBrief](https://offerbrief.com) API.

## Features

- **Search properties** by project, building, or community
- **Market pulse** with YoY changes for apartments and villas
- **Trending projects** - most transacted in last 90 days
- **Price movers** - buildings with significant price changes
- **Recent sales** - notable high-value transactions
- **Check deals** - compare prices against market data
- **Analyze listings** - AI-powered listing analysis

## Installation

```bash
# Using uv (recommended)
uv pip install dld-mcp

# Or pip
pip install dld-mcp
```

## Usage with Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "dld": {
      "command": "uvx",
      "args": ["dld-mcp"]
    }
  }
}
```

No configuration needed - the server calls the public OfferBrief API.

## Available Tools

### find_project
Find the best matching project for a query. More forgiving - handles typos, partial names, aliases.

```
find_project("marina gate")  # → JUMEIRAH LIVING MARINA GATE
find_project("jbr")          # → top project in Marsa Dubai
find_project("downtown")     # → top project in Burj Khalifa
```

Returns project name, community, transaction count, and median price/sqm. Use the returned `project` name for `check_deal`.

### search_properties
Search for multiple matching projects/buildings.

```
search_properties("Marina Gate")
search_properties("JBR")
```

### get_market_pulse
Current market overview with YoY changes.

### get_trending_projects
Most transacted projects in last 90 days.

### get_price_movers
Buildings with significant 6-month price changes.

### get_recent_sales
Notable recent transactions (>=1M AED, last 7 days).

### check_deal
Evaluate if a property price is fair.

```
check_deal(project="Marina Gate", area_sqm=120, price=2200000)
```

Returns verdict: `great_deal`, `good_deal`, `fair_price`, `above_market`, or `overpriced`.

### analyze_listing
AI-powered analysis of property listing text.

```
analyze_listing("2BR in Marina Gate, 1200 sqft, asking 2.2M AED...")
```

## Resources

- `dld://market-summary` - Current market snapshot

## Development

```bash
git clone https://github.com/level09/dld-mcp
cd dld-mcp
uv sync
uv run dld-mcp
```

## License

MIT
