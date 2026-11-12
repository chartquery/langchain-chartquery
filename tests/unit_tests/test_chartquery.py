"""Offline tests: every request goes through an httpx.MockTransport."""

from __future__ import annotations

import json
from collections.abc import Callable

import httpx
import pytest

import langchain_chartquery as pkg
from langchain_chartquery import _client

API_KEY = "test-chartquery-key-placeholder"  # pragma: allowlist secret
BASE = "https://api.chartquery.com"
CASES = [
    {
        "cls": "ChartQueryChart",
        "config": {},
        "sample": {"chart_config": '{"type": "bar", "data": {"labels": ["a"]}}'},
        "method": "GET",
        "path": "/v1/chart",
        "params": {"query": '{"type":"bar","data":{"labels":["a"]}}', "share": "true"},
        "body": None,
        "response": {"id": "cq-1", "render_url": "https://api.chartquery.com/v1/chart/render/cq-1"},
        "result": {"id": "cq-1", "render_url": "https://api.chartquery.com/v1/chart/render/cq-1"},
    },
    {
        "cls": "ChartQueryChartFromPrompt",
        "config": {},
        "sample": {"prompt": "Monthly sales", "data": "Jan: 1, Feb: 2"},
        "method": "GET",
        "path": "/v1/chart/ai",
        "params": {"prompt": "Monthly sales", "raw_data": "Jan: 1, Feb: 2", "share": "true"},
        "body": None,
        "response": {"ok": True},
        "result": {"ok": True},
    },
    {
        "cls": "ChartQueryDiagram",
        "config": {"language": "mermaid"},
        "sample": {"source": "graph TD; A-->B"},
        "method": "GET",
        "path": "/v1/diagram",
        "params": {"query": "graph TD; A-->B", "type": "mermaid", "format": "png", "share": "true"},
        "body": None,
        "response": {"ok": True},
        "result": {"ok": True},
    },
    {
        "cls": "ChartQueryQRCode",
        "config": {},
        "sample": {"data": "https://example.com"},
        "method": "GET",
        "path": "/v1/qrcode",
        "params": {"data": "https://example.com", "size": "300", "format": "png", "share": "true"},
        "body": None,
        "response": {"ok": True},
        "result": {"ok": True},
    },
]

Handler = Callable[[httpx.Request], httpx.Response]


@pytest.fixture
def mock_http(monkeypatch: pytest.MonkeyPatch) -> Callable[[Handler], list[httpx.Request]]:
    def install(handler: Handler) -> list[httpx.Request]:
        seen: list[httpx.Request] = []

        def record(request: httpx.Request) -> httpx.Response:
            seen.append(request)
            return handler(request)

        transport = httpx.MockTransport(record)
        real_client, real_async = httpx.Client, httpx.AsyncClient
        monkeypatch.setattr(_client.httpx, "Client", lambda **kw: real_client(transport=transport, **kw))
        monkeypatch.setattr(_client.httpx, "AsyncClient", lambda **kw: real_async(transport=transport, **kw))
        return seen

    return install


def _params(request: httpx.Request) -> dict[str, str]:
    return dict(request.url.params)


def _body(request: httpx.Request) -> object:
    return json.loads(request.content) if request.content else None


@pytest.mark.parametrize("case", CASES, ids=[c["cls"] for c in CASES])
def test_request_and_result(mock_http, case) -> None:
    seen = mock_http(lambda request: httpx.Response(200, json=case["response"]))
    tool = getattr(pkg, case["cls"])(api_key=API_KEY, **case["config"])

    result = tool.invoke(case["sample"])

    request = seen[0]
    assert request.method == case["method"]
    assert request.url.copy_with(query=None) == httpx.URL(BASE + case["path"])
    assert _params(request) == (case["params"] or {})
    assert _body(request) == case["body"]
    assert request.headers["x-api-key"] == API_KEY
    expected = case["result"]
    assert (json.loads(result) if isinstance(result, str) and not isinstance(expected, str) else result) == expected


@pytest.mark.parametrize("case", CASES, ids=[c["cls"] for c in CASES])
async def test_async_matches_sync(mock_http, case) -> None:
    mock_http(lambda request: httpx.Response(200, json=case["response"]))
    tool = getattr(pkg, case["cls"])(api_key=API_KEY, **case["config"])
    result = await tool.ainvoke(case["sample"])
    expected = case["result"]
    assert (json.loads(result) if isinstance(result, str) and not isinstance(expected, str) else result) == expected


@pytest.mark.parametrize(
    ("status", "body", "message"),
    [
        (401, {"error": f"Invalid key {API_KEY}"}, "ChartQuery rejected the API key (HTTP 401): Invalid key ***"),
        (401, {"error": "Rate limit exceeded"}, "ChartQuery rate limit exceeded (HTTP 401): Rate limit exceeded"),
        (402, {"error": {"message": "No credits"}}, "ChartQuery account is out of credits (HTTP 402): No credits"),
        (500, {"error": "Internal Error"}, "ChartQuery API error (HTTP 500): Internal Error"),
    ],
)
def test_errors_reach_the_model_without_the_key(mock_http, status, body, message) -> None:
    mock_http(lambda request: httpx.Response(status, json=body))
    tool = pkg.ChartQueryChart(api_key=API_KEY, **{})
    assert tool.invoke({"chart_config": '{"type": "bar", "data": {"labels": ["a"]}}'}) == message


def test_network_errors(mock_http) -> None:
    def fail(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError(f"failed with {API_KEY}")

    mock_http(fail)
    tool = pkg.ChartQueryChart(api_key=API_KEY, **{})
    assert (
        tool.invoke({"chart_config": '{"type": "bar", "data": {"labels": ["a"]}}'})
        == "Could not reach ChartQuery: failed with ***"
    )


def test_missing_key_sends_no_request(mock_http, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CHARTQUERY_API_KEY", raising=False)
    seen = mock_http(lambda request: httpx.Response(200, json={}))
    result = pkg.ChartQueryChart(**{}).invoke({"chart_config": '{"type": "bar", "data": {"labels": ["a"]}}'})
    assert "CHARTQUERY_API_KEY" in result
    assert seen == []


def test_key_from_the_environment(mock_http, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CHARTQUERY_API_KEY", f" {API_KEY} ")
    seen = mock_http(
        lambda request: httpx.Response(
            200, json={"id": "cq-1", "render_url": "https://api.chartquery.com/v1/chart/render/cq-1"}
        )
    )
    pkg.ChartQueryChart(**{}).invoke({"chart_config": '{"type": "bar", "data": {"labels": ["a"]}}'})
    assert seen[0].headers["x-api-key"] == API_KEY


def test_exports() -> None:
    for name in ["ChartQueryChart", "ChartQueryChartFromPrompt", "ChartQueryDiagram", "ChartQueryQRCode"] + [
        "ChartQueryError"
    ]:
        assert name in pkg.__all__
