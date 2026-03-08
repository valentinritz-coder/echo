from __future__ import annotations

import os
from typing import Any

import requests

# Prefer API_BASE_URL (Docker Compose); fallback to ECHO_API_URL for local dev
API_BASE_URL = (
    os.getenv("API_BASE_URL") or os.getenv("ECHO_API_URL") or "http://localhost:8000"
).rstrip("/")
API_BASE_PATH = "/api/v1"
TIMEOUT_SECONDS = 20


def _mime_from_image_filename(name: str) -> str:
    """Fallback MIME when UploadedFile.type is missing (e.g. Streamlit)."""
    lower = name.lower()
    if lower.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    if lower.endswith(".png"):
        return "image/png"
    if lower.endswith(".webp"):
        return "image/webp"
    return "image/jpeg"


class ApiClientError(Exception):
    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        error_code: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code


def _parse_error_payload(response: requests.Response) -> tuple[str, str | None]:
    try:
        payload = response.json()
    except ValueError:
        return response.text or "Erreur HTTP", None

    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict):
            message = error.get("message") or "Erreur API"
            code = error.get("code")
            return str(message), str(code) if code else None

        message = payload.get("message") or payload.get("detail")
        if message:
            code = payload.get("error_code")
            return str(message), str(code) if code else None

        if payload.get("error_code"):
            return str(payload.get("error_code")), str(payload.get("error_code"))

    return str(payload), None


class APIClient:
    def __init__(self, access_token: str = "") -> None:
        self.access_token = access_token

    @property
    def _headers(self) -> dict[str, str]:
        if not self.access_token:
            return {}
        return {"Authorization": f"Bearer {self.access_token}"}

    def _handle_response(self, response: requests.Response) -> Any:
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            message, error_code = _parse_error_payload(response)
            raise ApiClientError(
                message, status_code=response.status_code, error_code=error_code
            ) from exc

        if not response.content:
            return None
        try:
            return response.json()
        except ValueError:
            return response.content

    def login(self, email: str, password: str) -> str:
        response = requests.post(
            f"{API_BASE_URL}{API_BASE_PATH}/auth/login",
            json={"email": email.strip(), "password": password},
            timeout=TIMEOUT_SECONDS,
        )
        payload = self._handle_response(response)
        token = payload.get("access_token", "") if isinstance(payload, dict) else ""
        if not token:
            raise ApiClientError("Jeton d'accès absent dans la réponse de login")
        self.access_token = token
        return token

    def get_today_question(self) -> dict[str, Any]:
        response = requests.get(
            f"{API_BASE_URL}{API_BASE_PATH}/questions/today",
            headers=self._headers,
            timeout=TIMEOUT_SECONDS,
        )
        payload = self._handle_response(response)
        return payload if isinstance(payload, dict) else {}

    def create_entry(
        self, question_id: int, text_content: str, audio_file: Any | None
    ) -> dict[str, Any]:
        data = {"question_id": str(question_id)}
        if text_content.strip():
            data["text_content"] = text_content.strip()

        files = None
        if audio_file is not None:
            files = {
                "audio_file": (audio_file.name, audio_file.getvalue(), audio_file.type)
            }

        response = requests.post(
            f"{API_BASE_URL}{API_BASE_PATH}/entries",
            data=data,
            files=files,
            headers=self._headers,
            timeout=TIMEOUT_SECONDS,
        )
        payload = self._handle_response(response)
        return payload if isinstance(payload, dict) else {}

    def upload_image(self, entry_id: str, image_file: Any) -> dict[str, Any]:
        mime = getattr(image_file, "type", None) or _mime_from_image_filename(
            getattr(image_file, "name", "") or ""
        )
        files = {"file": (image_file.name, image_file.getvalue(), mime)}
        response = requests.post(
            f"{API_BASE_URL}{API_BASE_PATH}/entries/{entry_id}/assets",
            files=files,
            headers=self._headers,
            timeout=TIMEOUT_SECONDS,
        )
        payload = self._handle_response(response)
        return payload if isinstance(payload, dict) else {}

    def list_entries(self, limit: int, offset: int) -> list[dict[str, Any]]:
        response = requests.get(
            f"{API_BASE_URL}{API_BASE_PATH}/entries",
            params={"limit": limit, "offset": offset},
            headers=self._headers,
            timeout=TIMEOUT_SECONDS,
        )
        payload = self._handle_response(response)

        if isinstance(payload, dict) and isinstance(payload.get("items"), list):
            return [item for item in payload["items"] if isinstance(item, dict)]
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        return []

    def get_entry(self, entry_id: str) -> dict[str, Any]:
        response = requests.get(
            f"{API_BASE_URL}{API_BASE_PATH}/entries/{entry_id}",
            headers=self._headers,
            timeout=TIMEOUT_SECONDS,
        )
        payload = self._handle_response(response)
        return payload if isinstance(payload, dict) else {}

    def fetch_bytes(self, url: str) -> bytes:
        response = requests.get(url, headers=self._headers, timeout=TIMEOUT_SECONDS)
        payload = self._handle_response(response)
        if isinstance(payload, bytes):
            return payload
        return response.content
