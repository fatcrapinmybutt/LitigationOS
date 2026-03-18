---
name: local-agent-sdk
description: "Local agent SDK for litigation AI agents. Tool builder, multi-turn conversation, 5 pre-built templates. Replaces inference.sh agent SDK. Zero network. Triggers: agent, build agent, sdk, tool builder, multi-agent, orchestrate"
---

# Local Agent SDK

Build litigation AI agents locally using MANBEARPIG.

## Pre-Built Templates

| Template | Purpose |
|----------|---------|
| `litigation-researcher` | Legal research + authority search |
| `filing-assistant` | Filing prep + compliance |
| `evidence-analyst` | Evidence mapping + gaps |
| `judicial-analyst` | Judge McNeill conduct analysis |
| `appellate-strategist` | COA/MSC appeal strategy |

## Usage

```python
from sdk import inference

client = inference()
agent = client.agent("litigation-researcher")
r = agent.send_message("What does MCR 2.003 require?")
print(r.text)
```

## Custom Agents

```python
from sdk import inference, app_tool, string

client = inference()
search = app_tool("search", "legal-rag").describe("Research").param("query", string("Query")).build()
agent = client.agent({"system_prompt": "Legal assistant.", "tools": [search]})
r = agent.send_message("Find disqualification authority")
```

## Tool Builder

```python
from sdk.tool_builder import tool, string, number, enum_of, optional, litigation_tools

# Get all 12 pre-built litigation tools
tools = litigation_tools()

# Or build custom
my_tool = tool("custom").describe("Custom").param("q", string("Query")).build()
```

## 19 Local Apps

legal-search, legal-rag, doc-analyzer, doc-generator, authority-search,
citation-check, timeline-build, irac-analysis, evidence-map, gap-detect,
filing-ready, deadline-score, mcneill-pattern, msc-scan, multi-juris,
classify, entities, concepts, status
