"""
Local Tool Builder — drop-in replacement for inferencesh tool builder API.

Provides the same fluent API for defining tools with typed parameters,
but tools execute locally against MANBEARPIG instead of cloud services.

Usage:
    from sdk.tool_builder import tool, app_tool, string, number, enum_of

    search = (
        tool("legal_search")
        .describe("Search Michigan legal database")
        .param("query", string("Legal search query"))
        .param("limit", number("Max results"))
        .build()
    )
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union


# ── Parameter Type Factories ───────────────────────────────────────

@dataclass
class ParamSchema:
    """JSON Schema-compatible parameter definition."""
    type: str
    description: str = ""
    enum: Optional[List[str]] = None
    items: Optional["ParamSchema"] = None
    properties: Optional[Dict[str, "ParamSchema"]] = None
    required: Optional[List[str]] = None
    default: Any = None
    is_optional: bool = False

    def to_json_schema(self) -> dict:
        schema: dict = {"type": self.type, "description": self.description}
        if self.enum:
            schema["enum"] = self.enum
        if self.items:
            schema["items"] = self.items.to_json_schema()
        if self.properties:
            schema["properties"] = {k: v.to_json_schema() for k, v in self.properties.items()}
            if self.required:
                schema["required"] = self.required
        if self.default is not None:
            schema["default"] = self.default
        return schema


def string(description: str = "") -> ParamSchema:
    """String parameter type."""
    return ParamSchema(type="string", description=description)


def number(description: str = "") -> ParamSchema:
    """Number (float) parameter type."""
    return ParamSchema(type="number", description=description)


def integer(description: str = "") -> ParamSchema:
    """Integer parameter type."""
    return ParamSchema(type="integer", description=description)


def boolean(description: str = "") -> ParamSchema:
    """Boolean parameter type."""
    return ParamSchema(type="boolean", description=description)


def enum_of(values: List[str], description: str = "") -> ParamSchema:
    """Enumerated string parameter."""
    return ParamSchema(type="string", description=description, enum=values)


def array(item_type: ParamSchema, description: str = "") -> ParamSchema:
    """Array parameter with typed items."""
    return ParamSchema(type="array", description=description, items=item_type)


def obj(properties: Dict[str, ParamSchema], description: str = "") -> ParamSchema:
    """Object parameter with named properties."""
    required = [k for k, v in properties.items() if not v.is_optional]
    return ParamSchema(
        type="object",
        description=description,
        properties=properties,
        required=required if required else None,
    )


def optional(param: ParamSchema) -> ParamSchema:
    """Mark a parameter as optional."""
    param.is_optional = True
    return param


# ── Tool Definitions ───────────────────────────────────────────────

@dataclass
class ToolDefinition:
    """A fully-built tool definition ready for agent use."""
    name: str
    description: str = ""
    display_name: str = ""
    parameters: Dict[str, ParamSchema] = field(default_factory=dict)
    required_params: List[str] = field(default_factory=list)
    tool_type: str = "client"  # client | app | agent | webhook
    app_ref: Optional[str] = None
    agent_ref: Optional[str] = None
    webhook_url: Optional[str] = None
    setup_config: Optional[dict] = None
    input_defaults: Optional[dict] = None
    requires_approval: bool = False
    handler: Optional[Callable] = None

    def to_json_schema(self) -> dict:
        """Export as JSON Schema for agent consumption."""
        props = {name: p.to_json_schema() for name, p in self.parameters.items()}
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": props,
                "required": self.required_params,
            },
            "tool_type": self.tool_type,
        }

    def execute(self, args: dict, client=None) -> Any:
        """Execute the tool with given arguments."""
        if self.handler:
            return self.handler(**args)

        if self.tool_type == "app" and client:
            merged_input = dict(self.input_defaults or {})
            merged_input.update(args)
            return client.run({
                "app": self.app_ref,
                "input": merged_input,
                "setup": self.setup_config,
            })

        return {"error": f"No handler for tool '{self.name}'", "args": args}


# ── Fluent Builders ────────────────────────────────────────────────

class _ToolBuilder:
    """Fluent builder for client tools (execute in your code)."""

    def __init__(self, name: str):
        self._def = ToolDefinition(name=name, tool_type="client")

    def describe(self, desc: str) -> "_ToolBuilder":
        self._def.description = desc
        return self

    def display(self, name: str) -> "_ToolBuilder":
        self._def.display_name = name
        return self

    def param(self, name: str, schema: ParamSchema) -> "_ToolBuilder":
        self._def.parameters[name] = schema
        if not schema.is_optional:
            self._def.required_params.append(name)
        return self

    def handler(self, fn: Callable) -> "_ToolBuilder":
        self._def.handler = fn
        return self

    def require_approval(self) -> "_ToolBuilder":
        self._def.requires_approval = True
        return self

    def build(self) -> ToolDefinition:
        return self._def


class _AppToolBuilder:
    """Fluent builder for app tools (call local apps via inference client)."""

    def __init__(self, name: str, app_ref: str):
        self._def = ToolDefinition(name=name, tool_type="app", app_ref=app_ref)

    def describe(self, desc: str) -> "_AppToolBuilder":
        self._def.description = desc
        return self

    def param(self, name: str, schema: ParamSchema) -> "_AppToolBuilder":
        self._def.parameters[name] = schema
        if not schema.is_optional:
            self._def.required_params.append(name)
        return self

    def setup(self, config: dict) -> "_AppToolBuilder":
        self._def.setup_config = config
        return self

    def input(self, defaults: dict) -> "_AppToolBuilder":
        self._def.input_defaults = defaults
        return self

    def require_approval(self) -> "_AppToolBuilder":
        self._def.requires_approval = True
        return self

    def build(self) -> ToolDefinition:
        return self._def


class _AgentToolBuilder:
    """Fluent builder for agent tools (delegate to sub-agents)."""

    def __init__(self, name: str, agent_ref: str):
        self._def = ToolDefinition(name=name, tool_type="agent", agent_ref=agent_ref)

    def describe(self, desc: str) -> "_AgentToolBuilder":
        self._def.description = desc
        return self

    def param(self, name: str, schema: ParamSchema) -> "_AgentToolBuilder":
        self._def.parameters[name] = schema
        if not schema.is_optional:
            self._def.required_params.append(name)
        return self

    def build(self) -> ToolDefinition:
        return self._def


class _WebhookToolBuilder:
    """Fluent builder for webhook tools (call local or external endpoints)."""

    def __init__(self, name: str, url: str):
        self._def = ToolDefinition(name=name, tool_type="webhook", webhook_url=url)
        self._secret_key: Optional[str] = None

    def describe(self, desc: str) -> "_WebhookToolBuilder":
        self._def.description = desc
        return self

    def secret(self, key: str) -> "_WebhookToolBuilder":
        self._secret_key = key
        return self

    def param(self, name: str, schema: ParamSchema) -> "_WebhookToolBuilder":
        self._def.parameters[name] = schema
        if not schema.is_optional:
            self._def.required_params.append(name)
        return self

    def build(self) -> ToolDefinition:
        return self._def


class _InternalToolsBuilder:
    """Configure built-in capabilities (memory, search, code exec)."""

    def __init__(self):
        self._config = {}

    def plan(self) -> "_InternalToolsBuilder":
        self._config["plan"] = True
        return self

    def memory(self) -> "_InternalToolsBuilder":
        self._config["memory"] = True
        return self

    def web_search(self, enabled: bool = True) -> "_InternalToolsBuilder":
        self._config["web_search"] = enabled
        return self

    def code_execution(self, enabled: bool = True) -> "_InternalToolsBuilder":
        self._config["code_execution"] = enabled
        return self

    def image_generation(self, config: dict) -> "_InternalToolsBuilder":
        self._config["image_generation"] = config
        return self

    def build(self) -> dict:
        return self._config


# ── Factory Functions ──────────────────────────────────────────────

def tool(name: str) -> _ToolBuilder:
    """Create a client tool (runs in your code)."""
    return _ToolBuilder(name)


def app_tool(name: str, app_ref: str) -> _AppToolBuilder:
    """Create an app tool (calls a local inference app)."""
    return _AppToolBuilder(name, app_ref)


def agent_tool(name: str, agent_ref: str) -> _AgentToolBuilder:
    """Create an agent tool (delegates to a sub-agent)."""
    return _AgentToolBuilder(name, agent_ref)


def webhook_tool(name: str, url: str) -> _WebhookToolBuilder:
    """Create a webhook tool (calls an endpoint)."""
    return _WebhookToolBuilder(name, url)


def internal_tools() -> _InternalToolsBuilder:
    """Configure built-in agent capabilities."""
    return _InternalToolsBuilder()


# ── Pre-built Litigation Tool Library ──────────────────────────────

def litigation_tools() -> List[ToolDefinition]:
    """Return a curated set of pre-built litigation tools for agents."""
    return [
        (
            app_tool("search_legal_db", "legal-search")
            .describe("Search the 694-table Michigan litigation database using TF-IDF + FTS5")
            .param("query", string("Natural language legal search query"))
            .build()
        ),
        (
            app_tool("find_authority", "authority-search")
            .describe("Find MCR, MCL, case law, and statute authority for a legal topic")
            .param("topic", string("Legal topic to research"))
            .param("limit", optional(integer("Max results (default 10)")))
            .build()
        ),
        (
            app_tool("check_citations", "citation-check")
            .describe("Verify all legal citations in a document against the database")
            .param("text", string("Document text containing citations to verify"))
            .build()
        ),
        (
            app_tool("analyze_document", "doc-analyzer")
            .describe("Analyze a legal document for citations, claims, and weaknesses")
            .param("text", string("Full text of the legal document"))
            .build()
        ),
        (
            app_tool("generate_document", "doc-generator")
            .describe("Generate a court-ready legal document from templates + DB authority")
            .param("doc_type", enum_of(["motion", "brief", "affidavit", "response", "complaint"], "Type of document"))
            .param("params", optional(obj({}, "Additional generation parameters")))
            .build()
        ),
        (
            app_tool("build_timeline", "timeline-build")
            .describe("Build chronological case timeline from evidence + docket events")
            .param("case_id", optional(string("Filter to specific case ID")))
            .build()
        ),
        (
            app_tool("irac_analysis", "irac-analysis")
            .describe("Perform structured IRAC legal reasoning with authority chain")
            .param("issue", string("Legal issue to analyze"))
            .param("facts", optional(array(string("Fact"), "Relevant facts")))
            .build()
        ),
        (
            app_tool("evidence_gaps", "gap-detect")
            .describe("Detect evidence gaps for a filing vehicle")
            .param("vehicle_name", optional(string("Specific filing vehicle name")))
            .build()
        ),
        (
            app_tool("filing_readiness", "filing-ready")
            .describe("Get filing readiness scores and recommended next actions for all vehicles")
            .build()
        ),
        (
            app_tool("deadline_urgency", "deadline-score")
            .describe("Score all deadlines by urgency with color-coded alerts")
            .param("days_threshold", optional(integer("Days ahead to check (default 30)")))
            .build()
        ),
        (
            app_tool("mcneill_pattern", "mcneill-pattern")
            .describe("Deep analysis of Judge McNeill's pattern of conduct violations")
            .build()
        ),
        (
            app_tool("multi_jurisdiction", "multi-juris")
            .describe("Query across MI Circuit, COA, MSC, Federal, and JTC jurisdictions")
            .param("topic", string("Legal topic to research across jurisdictions"))
            .param("jurisdictions", optional(array(string("Jurisdiction"), "Specific jurisdictions")))
            .build()
        ),
    ]
