"""LangChain standard unit tests for every tool."""

from langchain_tests.unit_tests import ToolsUnitTests

import langchain_chartquery as pkg

KEY = "test-chartquery-key-placeholder"  # pragma: allowlist secret


class TestChartQueryChartStandard(ToolsUnitTests):
    @property
    def tool_constructor(self) -> type:
        return pkg.ChartQueryChart

    @property
    def tool_constructor_params(self) -> dict:
        return {"api_key": KEY, **{}}

    @property
    def tool_invoke_params_example(self) -> dict:
        return {"chart_config": '{"type": "bar", "data": {"labels": ["a"]}}'}


class TestChartQueryChartFromPromptStandard(ToolsUnitTests):
    @property
    def tool_constructor(self) -> type:
        return pkg.ChartQueryChartFromPrompt

    @property
    def tool_constructor_params(self) -> dict:
        return {"api_key": KEY, **{}}

    @property
    def tool_invoke_params_example(self) -> dict:
        return {"prompt": "Monthly sales", "data": "Jan: 1, Feb: 2"}


class TestChartQueryDiagramStandard(ToolsUnitTests):
    @property
    def tool_constructor(self) -> type:
        return pkg.ChartQueryDiagram

    @property
    def tool_constructor_params(self) -> dict:
        return {"api_key": KEY, **{"language": "mermaid"}}

    @property
    def tool_invoke_params_example(self) -> dict:
        return {"source": "graph TD; A-->B"}


class TestChartQueryQRCodeStandard(ToolsUnitTests):
    @property
    def tool_constructor(self) -> type:
        return pkg.ChartQueryQRCode

    @property
    def tool_constructor_params(self) -> dict:
        return {"api_key": KEY, **{}}

    @property
    def tool_invoke_params_example(self) -> dict:
        return {"data": "https://example.com"}
