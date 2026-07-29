# DLD MCP Server

Local stdio MCP server for querying Dubai property sales transactions and rental contracts through OfferBrief.

The server uses MCP Python SDK v2 and supports the MCP 2026-07-28 protocol.

## Installation

Run the published package directly:

```bash
uvx dld-mcp
```

## Setup

Claude Code:

```bash
claude mcp add dld -- uvx dld-mcp
```

Claude Desktop:

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

Add that entry to `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS.

## Tool

`query_dld` accepts:

| Parameter | Allowed values | Default |
| --- | --- | --- |
| `area` | Area or building name, at least 2 non-whitespace characters | Required |
| `type` | `sales`, `rentals` | `sales` |
| `property_type` | `all`, `apartment`, `villa`, `townhouse` | `all` |
| `bedrooms` | `all`, `studio`, `1`, `2`, `3`, `4`, `5+` | `all` |
| `date_from` | A real date in `YYYY-MM-DD` format | OfferBrief default |
| `date_to` | A real date in `YYYY-MM-DD` format | OfferBrief default |
| `metric` | `stats`, `count`, `list` | `stats` |
| `limit` | Integer from 1 through 50 | `10` |

`property_type` is supported only for sales. `date_from` cannot be later than `date_to`.

Examples:

```text
query_dld(area="Marina")
query_dld(area="Palm", property_type="villa", date_from="2024-01-01", metric="count")
query_dld(area="Downtown", type="rentals", bedrooms="2")
query_dld(area="JBR", metric="list", limit=10)
```

Invalid arguments fail before an API request. OfferBrief HTTP, rate limit, timeout, connection, and malformed response failures return structured errors with a message and status code.

## OfferBrief dependency and privacy

Each tool call sends its query parameters to `https://offerbrief.com/api/query`. No credentials are used. The package does not log query parameters or response bodies.

Results reflect the data available from OfferBrief when the call is made. This package does not claim a refresh schedule or transaction count.

## Development

```bash
git clone https://github.com/level09/dld-mcp
cd dld-mcp
uv sync --group dev
uv run pytest
uv run ruff check
uv build
```

## License

MIT, [OfferBrief](https://offerbrief.com)
