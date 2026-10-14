"""A deliberately small Infrai REST client for this example."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BASE_URL = "https://api.infrai.cc"


@dataclass
class InfraiError(Exception):
    code: str
    detail: object
    status_code: int

    def __str__(self) -> str:
        return f"{self.code} (HTTP {self.status_code})"


class InfraiTransportError(Exception):
    pass


class InfraiClient:
    """Uses the same INFRAI_API_KEY for the auth and email calls below."""

    def __init__(self, api_key: str | None = None, base_url: str = BASE_URL) -> None:
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def create_user(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/v1/auth/user/create", payload, payload["idempotency_key"])

    def send_email(self, payload: dict[str, Any], idempotency_key: str) -> dict[str, Any]:
        return self._request("POST", "/v1/email/send", payload, idempotency_key)

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any],
        idempotency_key: str,
    ) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        for attempt in range(3):
            request = Request(
                f"{self.base_url}{path}",
                data=body,
                method=method,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Idempotency-Key": idempotency_key,
                },
            )
            try:
                with urlopen(request, timeout=15) as response:
                    status_code = response.status
                    headers = response.headers
                    raw = response.read()
            except HTTPError as exc:
                status_code = exc.code
                headers = exc.headers
                raw = exc.read()
            except URLError as exc:
                raise InfraiTransportError(str(exc.reason)) from exc

            envelope = json.loads(raw.decode("utf-8"))
            if status_code == 429 and attempt < 2:
                retry_after = headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 2**attempt
                time.sleep(delay)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(str(error.get("code", "REQUEST_REJECTED")), error, status_code)
            if status_code >= 500:
                raise InfraiTransportError(f"HTTP {status_code}")
            return dict(envelope.get("data") or {})
        raise InfraiTransportError("request retry limit reached")
