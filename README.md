# DLD MCP Server

MCP server for Dubai real estate data. Query 1.6M+ DLD sales transactions and 9.5M+ Ejari rental contracts.

## Installation

```bash
uvx dld-mcp
```

## Setup

**Claude Code:**
```bash
claude mcp add dld -- uvx dld-mcp
```

**Claude Desktop** - add to `~/Library/Application Support/Claude/claude_desktop_config.json`:
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

## Tool: query_dld

One flexible tool to query all Dubai property data.

### Parameters

| Parameter | Values | Default |
|-----------|--------|---------|
| area | Area name or building (fuzzy search) | required |
| type | `sales`, `rentals` | sales |
| property_type | `all`, `apartment`, `villa`, `townhouse` | all |
| bedrooms | `all`, `studio`, `1`, `2`, `3`, `4`, `5+` | all |
| date_from | YYYY-MM-DD | 12 months ago |
| date_to | YYYY-MM-DD | today |
| metric | `stats`, `count`, `list` | stats |
| limit | 1-50 (for list mode) | 10 |

### Examples

```
"What's the median price in Marina?"
→ query_dld(area="Marina")

"How many villas sold in Palm Jumeirah in 2024?"
→ query_dld(area="Palm", property_type="villa", date_from="2024-01-01", metric="count")

"Average rent for 2BR in Downtown"
→ query_dld(area="Downtown", type="rentals", bedrooms="2")

"Show me recent sales in JBR"
→ query_dld(area="JBR", metric="list", limit=10)

"Compare Business Bay vs Marina apartment prices"
→ Two calls with different areas
```

### Supported Aliases

Marina, JBR, Downtown, Palm, JVC, JLT, Business Bay, Sports City, Motor City, Silicon Oasis, Arabian Ranches, Discovery Gardens, International City, Creek Harbour, City Walk, Town Square, DAMAC Hills

## Development

```bash
git clone https://github.com/level09/dld-mcp
cd dld-mcp
uv sync
uv run dld-mcp
```

## License

MIT - [OfferBrief](https://offerbrief.com)
