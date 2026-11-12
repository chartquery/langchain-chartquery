# langchain-chartquery

[LangChain](https://www.langchain.com) integration for [ChartQuery](https://www.chartquery.com): turn data into charts, descriptions into diagrams, and text into QR codes, as image links.

## Installation

```bash
pip install -U langchain-chartquery
export CHARTQUERY_API_KEY="your-api-key"
```

Get an API key at [app.chartquery.com](https://app.chartquery.com).

## Tools

| Class | Tool name | What it does |
| --- | --- | --- |
| `ChartQueryChart` | `chartquery_chart` | Render a Chart.js chart through ChartQuery and return links to the image. |
| `ChartQueryChartFromPrompt` | `chartquery_chart_from_prompt` | Build a chart from a plain-words description through ChartQuery. |
| `ChartQueryDiagram` | `chartquery_diagram` | Render a diagram from its source through ChartQuery. |
| `ChartQueryQRCode` | `chartquery_qr_code` | Generate a QR code through ChartQuery. |

Each tool takes `api_key` (defaults to `CHARTQUERY_API_KEY`), `base_url` and `timeout`, plus the settings shown in its docstring. Errors (invalid key, no credits, rate limit, timeout) come back to the model as a `ToolException` message, without the API key. Every tool has an async version.

```python
from langchain_chartquery import ChartQueryChart

tool = ChartQueryChart()
print(tool.invoke({"chart_config": '{"type": "bar", "data": {"labels": ["a"]}}'}))
```

### In an agent

```python
from langchain.agents import create_agent
from langchain_chartquery import ChartQueryChart, ChartQueryChartFromPrompt, ChartQueryDiagram

agent = create_agent("openai:gpt-4.1-mini", tools=[ChartQueryChart(), ChartQueryChartFromPrompt(), ChartQueryDiagram()])
result = agent.invoke({"messages": [{"role": "user", "content": "..."}]})
```

## Development

```bash
pip install -e ".[test]"
pytest tests/unit_tests
```

## License

MIT
