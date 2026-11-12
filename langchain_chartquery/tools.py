"""ChartQuery tools for LangChain agents."""

from __future__ import annotations

import json
from typing import Any, Literal

from langchain_core.callbacks import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from langchain_core.tools import BaseTool, ToolException
from pydantic import BaseModel, Field, SecretStr

from langchain_chartquery import _client


class _ChartQueryTool(BaseTool):
    """Shared settings and request handling for the ChartQuery tools."""

    handle_tool_error: bool = True
    api_key: SecretStr | None = Field(default=None, description="ChartQuery API key. Defaults to CHARTQUERY_API_KEY.")
    base_url: str = _client.DEFAULT_BASE_URL
    timeout: float = _client.DEFAULT_TIMEOUT

    def _key(self) -> str:
        return _client.resolve_api_key(self.api_key.get_secret_value() if self.api_key else None)

    def _output(self, data: Any) -> Any:
        return data

    def _send(self, method: str, path: str, params: dict[str, Any] | None, body: dict[str, Any] | None) -> Any:
        return _client.request(
            method,
            path,
            params=_client.clean(params) if params else None,
            json=body,
            api_key=self._key(),
            base_url=self.base_url,
            timeout=self.timeout,
        )

    async def _asend(self, method: str, path: str, params: dict[str, Any] | None, body: dict[str, Any] | None) -> Any:
        return await _client.arequest(
            method,
            path,
            params=_client.clean(params) if params else None,
            json=body,
            api_key=self._key(),
            base_url=self.base_url,
            timeout=self.timeout,
        )


class ChartQueryChartInput(BaseModel):
    """Arguments the model can set."""

    chart_config: str = Field(
        default=..., description="The Chart.js config as a JSON object with type, data and optional options."
    )


class ChartQueryChart(_ChartQueryTool):
    """Render a Chart.js chart through ChartQuery and return links to the image.

    Setup:
        .. code-block:: bash

            pip install -U langchain-chartquery
            export CHARTQUERY_API_KEY="your-api-key"
    """

    name: str = "chartquery_chart"
    description: str = 'Render a Chart.js chart with ChartQuery and get public links to the image. Returns JSON with render_url (the image), view_url (a page to open) and expires_in. Input is the Chart.js config as JSON, such as {"type": "bar", "data": {"labels": ["Jan", "Feb"], "datasets": [{"label": "Sales", "data": [12, 19]}]}}.'
    args_schema: type[BaseModel] = ChartQueryChartInput

    def _request(self, chart_config: str) -> tuple[str, str, dict[str, Any] | None, dict[str, Any] | None]:
        try:
            config = json.loads(chart_config) if isinstance(chart_config, str) else chart_config
        except ValueError:
            raise _client.ChartQueryError(
                'chart_config must be valid JSON, such as {"type": "bar", "data": {...}}.'
            ) from None
        if not isinstance(config, dict):
            raise _client.ChartQueryError("chart_config must be a JSON object.")
        return "GET", "/v1/chart", {"query": json.dumps(config, separators=(",", ":")), "share": "true"}, None

    def _run(self, chart_config: str, run_manager: CallbackManagerForToolRun | None = None) -> Any:
        try:
            return self._output(self._send(*self._request(chart_config)))
        except _client.ChartQueryError as exc:
            raise ToolException(str(exc)) from exc

    async def _arun(self, chart_config: str, run_manager: AsyncCallbackManagerForToolRun | None = None) -> Any:
        try:
            return self._output(await self._asend(*self._request(chart_config)))
        except _client.ChartQueryError as exc:
            raise ToolException(str(exc)) from exc


class ChartQueryChartFromPromptInput(BaseModel):
    """Arguments the model can set."""

    prompt: str = Field(default=..., description="What to chart: type, topic, colors, style.")
    data: str | None = Field(
        default=None, description="Optional data as CSV, JSON or text, such as Jan: 12400, Feb: 18900."
    )


class ChartQueryChartFromPrompt(_ChartQueryTool):
    """Build a chart from a plain-words description through ChartQuery.

    Setup:
        .. code-block:: bash

            pip install -U langchain-chartquery
            export CHARTQUERY_API_KEY="your-api-key"
    """

    name: str = "chartquery_chart_from_prompt"
    description: str = "Describe a chart in plain words, with optional raw data as CSV, JSON or text; ChartQuery's AI builds it and returns public links to the image. Returns JSON with render_url (the image), view_url (a page to open) and expires_in."
    args_schema: type[BaseModel] = ChartQueryChartFromPromptInput

    def _request(
        self, prompt: str, data: str | None = None
    ) -> tuple[str, str, dict[str, Any] | None, dict[str, Any] | None]:
        return (
            "GET",
            "/v1/chart/ai",
            _client.clean({"prompt": _client.required(prompt, "prompt"), "raw_data": data, "share": True}),
            None,
        )

    def _run(self, prompt: str, data: str | None = None, run_manager: CallbackManagerForToolRun | None = None) -> Any:
        try:
            return self._output(self._send(*self._request(prompt, data)))
        except _client.ChartQueryError as exc:
            raise ToolException(str(exc)) from exc

    async def _arun(
        self, prompt: str, data: str | None = None, run_manager: AsyncCallbackManagerForToolRun | None = None
    ) -> Any:
        try:
            return self._output(await self._asend(*self._request(prompt, data)))
        except _client.ChartQueryError as exc:
            raise ToolException(str(exc)) from exc


class ChartQueryDiagramInput(BaseModel):
    """Arguments the model can set."""

    source: str = Field(default=..., description="The diagram source code, such as graph TD; A[Start] --> B[End].")


class ChartQueryDiagram(_ChartQueryTool):
    """Render a diagram from its source through ChartQuery.

    Setup:
        .. code-block:: bash

            pip install -U langchain-chartquery
            export CHARTQUERY_API_KEY="your-api-key"
    """

    name: str = "chartquery_diagram"
    description: str = "Render a diagram from its source code (Mermaid by default, or D2, PlantUML, Graphviz and more) with ChartQuery and get public links to the image. Returns JSON with render_url (the image), view_url (a page to open) and expires_in. Input is the diagram source."
    args_schema: type[BaseModel] = ChartQueryDiagramInput
    language: str = "mermaid"
    """Diagram language: mermaid, d2, plantuml, graphviz, bpmn, dbml and more."""
    image_format: Literal["png", "svg", "jpeg", "pdf"] = "png"
    """Image format."""

    def _request(self, source: str) -> tuple[str, str, dict[str, Any] | None, dict[str, Any] | None]:
        return (
            "GET",
            "/v1/diagram",
            {
                "query": _client.required(source, "source"),
                "type": self.language,
                "format": self.image_format,
                "share": "true",
            },
            None,
        )

    def _run(self, source: str, run_manager: CallbackManagerForToolRun | None = None) -> Any:
        try:
            return self._output(self._send(*self._request(source)))
        except _client.ChartQueryError as exc:
            raise ToolException(str(exc)) from exc

    async def _arun(self, source: str, run_manager: AsyncCallbackManagerForToolRun | None = None) -> Any:
        try:
            return self._output(await self._asend(*self._request(source)))
        except _client.ChartQueryError as exc:
            raise ToolException(str(exc)) from exc


class ChartQueryQRCodeInput(BaseModel):
    """Arguments the model can set."""

    data: str = Field(default=..., description="The text to encode: a URL, mailto:, tel:, a WIFI: string or any text.")


class ChartQueryQRCode(_ChartQueryTool):
    """Generate a QR code through ChartQuery.

    Setup:
        .. code-block:: bash

            pip install -U langchain-chartquery
            export CHARTQUERY_API_KEY="your-api-key"
    """

    name: str = "chartquery_qr_code"
    description: str = "Generate a QR code with ChartQuery for a link, email, phone number, Wi-Fi network or any text, and get public links to the image. Returns JSON with render_url (the image), view_url (a page to open) and expires_in. Input is the text to encode."
    args_schema: type[BaseModel] = ChartQueryQRCodeInput
    size: int = Field(default=300, ge=50, le=2000)
    """Width and height in pixels."""
    image_format: Literal["png", "svg"] = "png"
    """Image format."""

    def _request(self, data: str) -> tuple[str, str, dict[str, Any] | None, dict[str, Any] | None]:
        return (
            "GET",
            "/v1/qrcode",
            {"data": _client.required(data, "data"), "size": self.size, "format": self.image_format, "share": "true"},
            None,
        )

    def _run(self, data: str, run_manager: CallbackManagerForToolRun | None = None) -> Any:
        try:
            return self._output(self._send(*self._request(data)))
        except _client.ChartQueryError as exc:
            raise ToolException(str(exc)) from exc

    async def _arun(self, data: str, run_manager: AsyncCallbackManagerForToolRun | None = None) -> Any:
        try:
            return self._output(await self._asend(*self._request(data)))
        except _client.ChartQueryError as exc:
            raise ToolException(str(exc)) from exc
