import os
import sys
from unittest.mock import patch

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src import constants
from src.proxy import app, start_fastapi

client = TestClient(app)


def test_start_fastapi_binds_to_configured_host_and_port(capsys):
    original_host = constants.HOST
    original_port = constants.PORT
    original_token = constants.DASHBOARD_TOKEN
    constants.HOST = "127.0.0.1"
    constants.PORT = 18080
    constants.DASHBOARD_TOKEN = ""

    try:
        with patch("uvicorn.run") as run:
            start_fastapi()

        run.assert_called_once_with(app, host="127.0.0.1", port=18080, log_level="info")
        captured = capsys.readouterr()
        assert "Proxy endpoint: http://localhost:18080" in captured.out
        assert "Dashboard: http://localhost:18080/dashboard" in captured.out
    finally:
        constants.HOST = original_host
        constants.PORT = original_port
        constants.DASHBOARD_TOKEN = original_token


def test_start_fastapi_warns_when_exposed_without_dashboard_token(capsys):
    original_host = constants.HOST
    original_port = constants.PORT
    original_token = constants.DASHBOARD_TOKEN
    constants.HOST = "0.0.0.0"
    constants.PORT = 8080
    constants.DASHBOARD_TOKEN = ""

    try:
        with patch("uvicorn.run"):
            start_fastapi()

        captured = capsys.readouterr()
        assert "listening on all interfaces without DASHBOARD_TOKEN" in captured.out
    finally:
        constants.HOST = original_host
        constants.PORT = original_port
        constants.DASHBOARD_TOKEN = original_token


def test_internal_api_allows_access_when_dashboard_token_unset():
    original_token = constants.DASHBOARD_TOKEN
    constants.DASHBOARD_TOKEN = ""

    try:
        response = client.get("/api/config")
        assert response.status_code == 200
    finally:
        constants.DASHBOARD_TOKEN = original_token


def test_internal_api_requires_bearer_token_when_configured():
    original_token = constants.DASHBOARD_TOKEN
    constants.DASHBOARD_TOKEN = "secret-token"

    try:
        assert client.get("/api/config").status_code == 401
        assert client.get("/api/config", headers={"Authorization": "Bearer wrong"}).status_code == 401

        response = client.get("/api/config", headers={"Authorization": "Bearer secret-token"})
        assert response.status_code == 200
    finally:
        constants.DASHBOARD_TOKEN = original_token


def test_dashboard_query_token_sets_cookie_for_internal_api_access():
    original_token = constants.DASHBOARD_TOKEN
    constants.DASHBOARD_TOKEN = "secret-token"
    isolated_client = TestClient(app)

    try:
        dashboard_response = isolated_client.get("/dashboard?token=secret-token")
        assert dashboard_response.status_code == 200
        assert isolated_client.cookies.get("dashboard_token") == "secret-token"

        config_response = isolated_client.get("/api/config")
        assert config_response.status_code == 200
    finally:
        constants.DASHBOARD_TOKEN = original_token
