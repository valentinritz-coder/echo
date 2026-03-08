"""
Tests ciblés pour le module client API web-static (issue #90).
Vérifie la présence et le contrat du module : base URL, fetch avec token, 401.
"""
from pathlib import Path

import pytest

# Repo root depuis services/api/tests -> api -> services -> repo
REPO_ROOT = Path(__file__).resolve().parents[3]
WEB_STATIC_API_JS = REPO_ROOT / "apps" / "web-static" / "api.js"


@pytest.fixture
def api_js_content():
    if not WEB_STATIC_API_JS.exists():
        pytest.skip("apps/web-static/api.js non trouvé (hors repo echo?)")
    return WEB_STATIC_API_JS.read_text(encoding="utf-8")


def test_web_static_api_js_exists():
    """Le module client API web-static doit exister."""
    assert WEB_STATIC_API_JS.exists(), f"Fichier attendu: {WEB_STATIC_API_JS}"


def test_web_static_api_client_exposes_base_url(api_js_content):
    """Le module doit exposer une façon d'obtenir la base URL de l'API."""
    assert "getApiBaseUrl" in api_js_content


def test_web_static_api_client_exposes_token_handling(api_js_content):
    """Le module doit exposer getter/setter pour le token."""
    assert "getAccessToken" in api_js_content
    assert "setAccessToken" in api_js_content


def test_web_static_api_client_fetch_with_authorization(api_js_content):
    """Le module doit faire des fetch avec Authorization Bearer."""
    assert "apiFetch" in api_js_content
    assert "Authorization" in api_js_content
    assert "Bearer" in api_js_content


def test_web_static_api_client_handles_401(api_js_content):
    """Le module doit gérer explicitement le statut 401."""
    assert "401" in api_js_content


def test_web_static_api_client_exposes_echo_api_global(api_js_content):
    """Le module doit attacher l'API au global window.echoApi."""
    assert "echoApi" in api_js_content
