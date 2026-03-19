"""
Local Agent SDK — drop-in replacement for inferencesh agent API.

Creates agents that use MANBEARPIG for reasoning, with tool execution,
multi-turn conversation, and streaming support — all local.

Usage:
    from sdk import inference, tool, string

    client = inference()

    # Template agent (pre-configured)
    agent = client.agent("litigation-researcher")
    response = agent.send_message("What does MCR 2.003 require?")

    # Ad-hoc agent with tools
    search = tool("search").describe("Search DB").param("q", string("Query")).build()
    agent = client.agent({"system_prompt": "You are a legal assistant.", "tools": [search]})
    response = agent.send_message("Find authority on disqualification")
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class AgentResult:
    """Result from an agent message."""
    text: str
    tool_calls: List[dict] = field(default_factory=list)
    sources: List[dict] = field(default_factory=list)
    confidence: float = 0.0
    elapsed_ms: float = 0.0
    turn_index: int = 0

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "tool_calls": self.tool_calls,
            "sources": self.sources,
            "confidence": self.confidence,
            "elapsed_ms": self.elapsed_ms,
            "turn_index": self.turn_index,
        }


# Pre-built agent templates
_AGENT_TEMPLATES = {
    "litigation-researcher": {
        "system_prompt": (
            "You are a Michigan litigation research assistant for Pigors v. Watson. "
            "Search the litigation database for authority, evidence, and case law. "
            "Always cite MCR/MCL/MRE references. Verify every citation."
        ),
        "tools": ["search_legal_db", "find_authority", "check_citations"],
        "temperature": 0.3,
    },
    "filing-assistant": {
        "system_prompt": (
            "You are a court filing assistant. Help prepare Michigan court filings "
            "by checking readiness, filling placeholders from DB data, verifying "
            "citations, and ensuring MCR compliance. Never fabricate party names or facts."
        ),
        "tools": ["filing_readiness", "deadline_urgency", "evidence_gaps", "check_citations"],
        "temperature": 0.1,
    },
    "evidence-analyst": {
        "system_prompt": (
            "You are an evidence analyst for family law litigation. Map evidence to "
            "legal grounds, identify gaps, build timelines, and score evidence strength. "
            "Use IRAC analysis for complex legal questions."
        ),
        "tools": ["irac_analysis", "evidence_gaps", "build_timeline", "analyze_document"],
        "temperature": 0.2,
    },
    "judicial-analyst": {
        "system_prompt": (
            "You are a judicial conduct analyst specializing in Judge Jenny L. McNeill. "
            "Analyze patterns of ex parte communication, procedural violations, "
            "and bias indicators. Cross-reference with MCR and JTC standards."
        ),
        "tools": ["mcneill_pattern", "find_authority", "multi_jurisdiction"],
        "temperature": 0.2,
    },
    "appellate-strategist": {
        "system_prompt": (
            "You are an appellate strategy specialist for Michigan COA/MSC proceedings. "
            "Analyze issues for appeal, identify MSC original action viability, "
            "and recommend procedural vehicles. Reference MCR 7.2xx rules."
        ),
        "tools": ["multi_jurisdiction", "find_authority", "irac_analysis", "search_legal_db"],
        "temperature": 0.3,
    },
}


class LocalAgent:
    """
    A local agent that processes messages using MANBEARPIG.

    Supports:
    - Multi-turn conversation with context window
    - Tool execution (calls local inference apps)
    - Template and ad-hoc agent creation
    - Streaming responses
    """

    def __init__(self, client, config):
        self._client = client
        self._id = str(uuid.uuid4())[:12]
        self._chat_history: List[dict] = []
        self._turn_index = 0

        if isinstance(config, str):
            # Template agent reference
            template = _AGENT_TEMPLATES.get(config)
            if not template:
                available = list(_AGENT_TEMPLATES.keys())
                raise ValueError(f"Unknown agent template: {config}. Available: {available}")
            self._system_prompt = template["system_prompt"]
            self._tool_names = template.get("tools", [])
            self._tools = self._resolve_tools(self._tool_names)
            self._temperature = template.get("temperature", 0.5)
        elif isinstance(config, dict):
            self._system_prompt = config.get("system_prompt", "You are a helpful assistant.")
            self._tools = config.get("tools", [])
            self._tool_names = [t.name if hasattr(t, "name") else str(t) for t in self._tools]
            self._temperature = config.get("temperature", 0.5)
        else:
            raise ValueError(f"Agent config must be str or dict, got {type(config)}")

    def _resolve_tools(self, tool_names: List[str]) -> list:
        """Resolve tool names to ToolDefinition objects from the litigation library."""
        from sdk.tool_builder import litigation_tools
        lib = {t.name: t for t in litigation_tools()}
        resolved = []
        for name in tool_names:
            if name in lib:
                resolved.append(lib[name])
            else:
                logger.warning(f"Tool '{name}' not found in litigation library")
        return resolved

    def send_message(
        self,
        message: str,
        on_message: Callable = None,
        on_tool_call: Callable = None,
        files: List = None,
    ) -> AgentResult:
        """
        Send a message and get a response.

        The agent will:
        1. Classify the intent of the message
        2. Execute relevant tools if available
        3. Synthesize a response using MANBEARPIG
        4. Maintain conversation context
        """
        start = time.time()
        self._turn_index += 1

        # Add to chat history
        self._chat_history.append({
            "role": "user",
            "content": message,
            "turn": self._turn_index,
            "ts": time.time(),
        })

        model = self._client.model
        if not model:
            return AgentResult(
                text="Error: MANBEARPIG model not loaded.",
                turn_index=self._turn_index,
            )

        # Phase 1: Intent classification
        intent, confidence = model.classify_intent(message)

        # Phase 2: Entity extraction
        entities = model.extract_entities(message)

        # Phase 3: Tool execution
        tool_results = []
        tool_calls = []
        for t in self._tools:
            if self._should_use_tool(t, message, intent, entities):
                call = {"tool": t.name if hasattr(t, "name") else str(t), "args": {"query": message}}
                tool_calls.append(call)

                if on_tool_call and hasattr(t, "name"):
                    on_tool_call(type("ToolCall", (), {
                        "name": t.name,
                        "args": {"query": message},
                        "id": str(uuid.uuid4())[:8],
                        "requires_approval": getattr(t, "requires_approval", False),
                    })())

                result = t.execute({"query": message, "text": message, "topic": message}, self._client)
                if isinstance(result, dict) and "output" in result:
                    result = result["output"]
                tool_results.append({"tool": call["tool"], "result": result})

        # Phase 4: Main query with context
        context_query = message
        if tool_results:
            context_parts = []
            for tr in tool_results:
                if isinstance(tr["result"], dict):
                    summary = tr["result"].get("response", tr["result"].get("synthesis", str(tr["result"])[:500]))
                else:
                    summary = str(tr["result"])[:500]
                context_parts.append(f"[{tr['tool']}]: {summary}")
            context_query = f"{message}\n\nContext from tools:\n" + "\n".join(context_parts)

        response = model.query(context_query)

        # Phase 5: Build sources from tool results
        sources = []
        if tool_results:
            for tr in tool_results:
                res = tr["result"]
                if isinstance(res, dict):
                    # Extract authority sources
                    for key in ("authority", "retrieval", "results"):
                        if key in res and isinstance(res[key], list):
                            for item in res[key][:3]:
                                if isinstance(item, dict):
                                    sources.append({
                                        "tool": tr["tool"],
                                        "source": item.get("rule_number", item.get("title", item.get("label", "unknown"))),
                                        "text": str(item.get("text", item.get("description", "")))[:200],
                                    })

        response_text = response.get("response", "I couldn't generate a response.")

        # Stream callback
        if on_message:
            on_message({"content": response_text})

        # Add to history
        self._chat_history.append({
            "role": "assistant",
            "content": response_text,
            "turn": self._turn_index,
            "ts": time.time(),
            "tools_used": [tc["tool"] for tc in tool_calls],
        })

        elapsed = (time.time() - start) * 1000

        return AgentResult(
            text=response_text,
            tool_calls=tool_calls,
            sources=sources,
            confidence=response.get("confidence", confidence),
            elapsed_ms=elapsed,
            turn_index=self._turn_index,
        )

    def _should_use_tool(self, tool_def, message: str, intent: str, entities: dict) -> bool:
        """Determine if a tool should be used for this message."""
        if not hasattr(tool_def, "name"):
            return False

        name = tool_def.name
        msg_lower = message.lower()

        # Keyword-based tool routing
        routing = {
            "search_legal_db": ["search", "find", "look up", "what", "how", "mcr", "mcl"],
            "find_authority": ["authority", "rule", "statute", "mcr", "mcl", "law", "cite"],
            "check_citations": ["citation", "verify", "check", "cite", "reference"],
            "analyze_document": ["analyze", "review", "assess", "evaluate", "document"],
            "generate_document": ["generate", "draft", "write", "create", "motion", "brief"],
            "build_timeline": ["timeline", "chronolog", "sequence", "history", "event"],
            "irac_analysis": ["irac", "legal analysis", "issue", "rule", "application"],
            "evidence_gaps": ["gap", "missing", "evidence", "need", "lack"],
            "filing_readiness": ["filing", "ready", "readiness", "status", "go/no-go"],
            "deadline_urgency": ["deadline", "urgency", "due", "overdue", "calendar"],
            "mcneill_pattern": ["mcneill", "judge", "judicial", "bias", "misconduct", "pattern"],
            "multi_jurisdiction": ["jurisdiction", "federal", "appellate", "coa", "msc", "jtc"],
        }

        keywords = routing.get(name, [])
        if any(kw in msg_lower for kw in keywords):
            return True

        # Use all tools if intent is unclear and confidence is low
        if intent == "unknown" or (hasattr(tool_def, "name") and name == "search_legal_db"):
            return True

        return False

    def reset(self):
        """Reset conversation history."""
        self._chat_history = []
        self._turn_index = 0

    def get_chat(self) -> List[dict]:
        """Return conversation history."""
        return list(self._chat_history)

    def submit_tool_result(self, call_id: str, result: Any):
        """Submit external tool result (for human-in-the-loop workflows)."""
        self._chat_history.append({
            "role": "tool",
            "call_id": call_id,
            "content": result,
            "ts": time.time(),
        })

    def get_agent_info(self) -> dict:
        """Return agent metadata."""
        return {
            "id": self._id,
            "system_prompt": self._system_prompt[:100] + "...",
            "tools": self._tool_names,
            "temperature": self._temperature,
            "turns": self._turn_index,
            "history_length": len(self._chat_history),
        }


def list_agent_templates() -> List[dict]:
    """List all available pre-built agent templates."""
    return [
        {
            "name": name,
            "system_prompt": cfg["system_prompt"][:100] + "...",
            "tools": cfg.get("tools", []),
            "temperature": cfg.get("temperature", 0.5),
        }
        for name, cfg in _AGENT_TEMPLATES.items()
    ]
