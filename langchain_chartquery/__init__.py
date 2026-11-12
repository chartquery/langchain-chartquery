"""LangChain integration for ChartQuery."""

from importlib import metadata

from langchain_chartquery._client import ChartQueryError
from langchain_chartquery.tools import (
    ChartQueryChart,
    ChartQueryChartFromPrompt,
    ChartQueryChartFromPromptInput,
    ChartQueryChartInput,
    ChartQueryDiagram,
    ChartQueryDiagramInput,
    ChartQueryQRCode,
    ChartQueryQRCodeInput,
)

try:
    __version__ = metadata.version(__package__)
except metadata.PackageNotFoundError:
    __version__ = ""

__all__ = [
    "ChartQueryChart",
    "ChartQueryChartFromPrompt",
    "ChartQueryChartFromPromptInput",
    "ChartQueryChartInput",
    "ChartQueryDiagram",
    "ChartQueryDiagramInput",
    "ChartQueryError",
    "ChartQueryQRCode",
    "ChartQueryQRCodeInput",
    "__version__",
]
