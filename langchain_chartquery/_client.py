"""HTTP client for the ChartQuery API (https://www.chartquery.com)."""

from __future__ import annotations

import os
from typing import Any

import httpx

DEFAULT_BASE_URL = "https://api.chartquery.com"
DEFAULT_TIMEOUT = 120.0
USER_AGENT = "langchain-chartquery"
ENV = "CHARTQUERY_API_KEY"

_ERROR_DETAIL_LIMIT = 300


class ChartQueryError(Exception):
    """A ChartQuery request failed. The message never contains the API key."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


def resolve_api_key(value: str | None) -> str:
    """Return ``value`` or ``CHARTQUERY_API_KEY``, stripped. Raises if neither is set."""
    key = (value or os.environ.get(ENV) or "").strip()
    if not key:
        raise ChartQueryError(f"Set {ENV} or pass api_key. Get a key at https://app.chartquery.com")
    return key


def required(value: Any, name: str) -> str:
    """Return ``value`` stripped, or raise if it is empty."""
    text = str(value or "").strip()
    if not text:
        raise ChartQueryError(f"{name} is empty.")
    return text


def clean(values: dict[str, Any]) -> dict[str, Any]:
    """Drop unset values; send booleans as true/false."""
    out: dict[str, Any] = {}
    for key, value in values.items():
        if value is None or value == "":
            continue
        out[key] = ("true" if value else "false") if isinstance(value, bool) else value
    return out


def _redact(text: str, api_key: str) -> str:
    return text.replace(api_key, "***") if api_key else text


def _error(response: httpx.Response, api_key: str) -> ChartQueryError:
    detail = ""
    try:
        body = response.json()
    except ValueError:
        detail = response.text.strip()
    else:
        if isinstance(body, dict):
            error = body.get("error") or body.get("message") or ""
            if isinstance(error, dict):
                error = error.get("message") or ""
            detail = str(error)
    detail = _redact(detail, api_key)[:_ERROR_DETAIL_LIMIT]
    status = response.status_code
    # ChartQuery answers a rate limit with HTTP 401 and a "Rate limit exceeded" message.
    if status == 429 or (status == 401 and "rate limit" in detail.lower()):
        label = "ChartQuery rate limit exceeded"
    elif status == 401:
        label = "ChartQuery rejected the API key"
    elif status == 402:
        label = "ChartQuery account is out of credits"
    else:
        label = "ChartQuery API error"
    return ChartQueryError(f"{label} (HTTP {status})" + (f": {detail}" if detail else ""), status)


def _headers(api_key: str) -> dict[str, str]:
    headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
    headers["x-api-key"] = api_key
    return headers


def _decode(response: httpx.Response, api_key: str) -> Any:
    if not response.is_success:
        raise _error(response, api_key)
    try:
        return response.json()
    except ValueError as exc:
        raise ChartQueryError("ChartQuery returned a response that is not JSON.") from exc


def request(
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    json: dict[str, Any] | None = None,
    api_key: str,
    base_url: str = DEFAULT_BASE_URL,
    timeout: float = DEFAULT_TIMEOUT,
) -> Any:
    """Call ``path`` and return the decoded JSON body."""
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.request(
                method, f"{base_url.rstrip('/')}{path}", params=params, json=json, headers=_headers(api_key)
            )
    except httpx.TimeoutException as exc:
        raise ChartQueryError(f"ChartQuery did not answer within {timeout:g} seconds.") from exc
    except httpx.HTTPError as exc:
        raise ChartQueryError(f"Could not reach ChartQuery: {_redact(str(exc), api_key)}") from exc
    return _decode(response, api_key)


async def arequest(
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    json: dict[str, Any] | None = None,
    api_key: str,
    base_url: str = DEFAULT_BASE_URL,
    timeout: float = DEFAULT_TIMEOUT,
) -> Any:
    """Async version of :func:`request`."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.request(
                method, f"{base_url.rstrip('/')}{path}", params=params, json=json, headers=_headers(api_key)
            )
    except httpx.TimeoutException as exc:
        raise ChartQueryError(f"ChartQuery did not answer within {timeout:g} seconds.") from exc
    except httpx.HTTPError as exc:
        raise ChartQueryError(f"Could not reach ChartQuery: {_redact(str(exc), api_key)}") from exc
    return _decode(response, api_key)
