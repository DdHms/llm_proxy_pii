import json
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src import constants
from src.proxy import app

client = TestClient(app)


def test_dashboard_added_exclusion_scrubs_gemini_request_and_logs_redaction_count():
    name = "Jane Example"
    constants.DEFAULT_EXCLUSIONS = []

    add_response = client.post("/api/exclusions", json={"phrase": name})
    assert add_response.status_code == 200
    assert name in client.get("/api/config").json()["exclusions"]

    async def mock_stream_iterator():
        yield b'{"ok": true}'

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "application/json"}
    mock_response.aiter_bytes = MagicMock(return_value=mock_stream_iterator())

    with patch("src.constants.async_client.send", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = mock_response
        response = client.post(
            "/v1beta/models/gemini-pro:generateContent",
            json={"contents": [{"parts": [{"text": f"My name is {name}."}]}]},
        )

    assert response.status_code == 200
    forwarded = json.loads(mock_send.call_args[0][0].content)
    forwarded_text = forwarded["contents"][0]["parts"][0]["text"]
    assert name not in forwarded_text
    assert "<EXCLUSION_1>" in forwarded_text

    latest_log = client.get("/api/logs").json()[0]
    assert latest_log["redaction_count"] == 1
    assert name not in latest_log["req_after"]
