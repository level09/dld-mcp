from mcp.server.transport_security import TransportSecuritySettings
from starlette.testclient import TestClient

from dld_mcp.server import mcp

INITIALIZE = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "t", "version": "1"}},
}
HEADERS = {"Accept": "application/json, text/event-stream"}


def test_http_serves_public_host_and_rejects_others():
    app = mcp.streamable_http_app(
        stateless_http=True,
        json_response=True,
        transport_security=TransportSecuritySettings(
            allowed_hosts=["offerbrief.com"], allowed_origins=["https://offerbrief.com"]
        ),
    )
    with TestClient(app, base_url="https://offerbrief.com") as client:
        ok = client.post("/mcp", json=INITIALIZE, headers=HEADERS)
        assert ok.status_code == 200
        assert ok.json()["result"]["serverInfo"]["name"] == "dld-mcp"

        forged = client.post("/mcp", json=INITIALIZE, headers={**HEADERS, "Host": "evil.example"})
        assert forged.status_code == 421
