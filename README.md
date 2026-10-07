# DLD MCP Server

MCP server (local stdio or remote HTTP) for querying Dubai property sales transactions and rental contracts through OfferBrief.

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

Remote (no install): add `https://offerbrief.com/mcp` as a custom connector in Claude or ChatGPT, or

```bash
claude mcp add --transport http dld https://offerbrief.com/mcp
```

Self-hosting the HTTP endpoint:

```bash
uvx dld-mcp --http --port 8765 --public-host example.com
```

It listens on 127.0.0.1 (put a TLS reverse proxy in front), is stateless, and rejects Host and Origin headers other than localhost and `--public-host`.

## Tool

`query_dld` accepts:

| Parameter | Allowed values | Default |
| --- | --- | --- |
| `area` | Area or building name, at least 2 non-whitespace characters | Required |
| `type` | `sales`, `rentals` | `sales` |
| `property_type` | `all`, `apartment`, `villa`, `townhouse` | `all` |
| `bedrooms` | `all`, `studio`, `1`, `2`, `3`, `4`, `5`, `5+` | `all` |
| `date_from` | A real date in `YYYY-MM-DD` format | OfferBrief default |
| `date_to` | A real date in `YYYY-MM-DD` format | OfferBrief default |
| `metric` | `stats`, `count`, `list` | `stats` |
| `limit` | Integer from 1 through 50 | `10` |

`bedrooms` is supported only for sales: DLD's current rental feed has no bedroom data. `date_from` cannot be later than `date_to`. The default window is the last 12 months.

Examples:

```text
query_dld(area="Marina")
query_dld(area="Palm", property_type="villa", date_from="2024-01-01", metric="count")
query_dld(area="Downtown", type="rentals", property_type="apartment")
query_dld(area="JBR", metric="list", limit=10)
```

Invalid arguments fail before an API request. OfferBrief's own message is passed through for rejected queries and empty results. HTTP, rate limit, timeout, connection, and malformed response failures set MCP `isError` and return structured errors with a message and status code. Results include both structured content and JSON text for client compatibility. The tool declares read-only, non-destructive, idempotent access to an external data source.

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
