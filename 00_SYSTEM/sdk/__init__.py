"""
LitigationOS Local SDK — inference.sh API emulation over MANBEARPIG.

Provides the same developer ergonomics as the inference.sh Python SDK
(tool builder, agent orchestration, RAG pipelines, sessions) but routes
ALL computation through the local MANBEARPIG inference engine + FTS5.
Zero network. Zero API keys. Zero cost.

Usage:
    from sdk import inference, tool, string, number
    client = inference()
    result = client.run({"app": "legal-search", "input": {"query": "MCR 2.003"}})
"""

from sdk.inference_local import inference, async_inference
from sdk.tool_builder import (
    tool, app_tool, agent_tool, webhook_tool, internal_tools,
    string, number, integer, boolean, enum_of, array, obj, optional,
)
from sdk.agent_sdk import LocalAgent, AgentResult
from sdk.rag_pipeline import RAGPipeline, SearchResult

__version__ = "1.0.0"
__all__ = [
    "inference", "async_inference",
    "tool", "app_tool", "agent_tool", "webhook_tool", "internal_tools",
    "string", "number", "integer", "boolean", "enum_of", "array", "obj", "optional",
    "LocalAgent", "AgentResult",
    "RAGPipeline", "SearchResult",
]
