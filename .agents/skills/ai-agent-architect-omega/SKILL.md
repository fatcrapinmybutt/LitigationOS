---
name: ai-agent-architect-omega
description: "ELITE AI agent architecture — fusion of 20 agent/AI skills. Covers agent design, multi-agent orchestration, agent evaluation, memory systems, tool building, autonomous patterns, parallel dispatch, CrewAI, LangGraph, and AI engineering. Use for ALL agent architecture and orchestration work."
metadata:
  model: opus
  forged_from: 20
  forge_date: 2026-03-12
---

# AI-AGENT-ARCHITECT-OMEGA — Elite Composite Skill

> Forged from 20 individual skills into one supreme composite.
> Sources: ai-agents-architect, agent-orchestration-multi-agent-optimize, agent-orchestration-improve-agent, agent-evaluation, agent-memory-systems, agent-memory-mcp, agent-memory, agent-tool-builder, autonomous-agents, autonomous-agent-patterns, multi-agent-patterns, multi-agent-brainstorming, dispatching-parallel-agents, subagent-driven-development, parallel-agents, agent-manager-skill, ai-engineer, ai-product, crewai, langgraph

## When to Apply

Activate this skill for ANY work related to:
- **Agent Architecture**: agent design patterns, ReAct, tool use, planning, reasoning loops
- **Multi-Agent Orchestration**: coordination, task decomposition, fan-out/fan-in, hierarchy
- **Agent Evaluation**: testing, benchmarking, reliability metrics, behavioral testing
- **Memory Systems**: short-term, long-term, episodic, semantic, vector stores, retrieval
- **Tool Building**: JSON Schema, MCP tools, function calling, error handling, descriptions
- **Autonomous Patterns**: self-healing, goal decomposition, reflection, chain-of-thought
- **Parallel Agent Dispatch**: concurrent execution, dependency graphs, resource management
- **Agent Optimization**: prompt engineering, cost reduction, latency, reliability improvement
- **CrewAI & LangGraph**: framework-specific patterns, agents, tasks, workflows
- **AI Engineering**: RAG, embeddings, LLM integration, production AI patterns

---

## §1. Agent Architecture

> agent design patterns, ReAct, tool use, planning, reasoning loops

### Patterns
*Source: ai-agents-architect*

### ReAct Loop

Reason-Act-Observe cycle for step-by-step execution

```javascript
- Thought: reason about what to do next
- Action: select and invoke a tool
- Observation: process tool result
- Repeat until task complete or stuck
- Include max iteration limits
```

### Plan-and-Execute

Plan first, then execute steps

```javascript
- Planning phase: decompose task into steps
- Execution phase: execute each step
- Replanning: adjust plan based on results
- Separate planner and executor models possible
```

### Tool Registry

Dynamic tool discovery and management

```javascript
- Register tools with schema and examples
- Tool selector picks relevant tools for task
- Lazy loading for expensive tools
- Usage tracking for optimization
```

### Patterns
*Source: autonomous-agents*

### ReAct Agent Loop

Alternating reasoning and action steps

### Plan-Execute Pattern

Separate planning phase from execution

### Reflection Pattern

Self-evaluation and iterative improvement

## §2. Multi-Agent Orchestration

> coordination, task decomposition, fan-out/fan-in, hierarchy

### 3. Agent Coordination Efficiency
*Source: agent-orchestration-multi-agent-optimize*

### Coordination Principles

- Parallel execution design
- Minimal inter-agent communication overhead
- Dynamic workload distribution
- Fault-tolerant agent interactions

### Orchestration Framework

```python
class MultiAgentOrchestrator:
    def __init__(self, agents):
        self.agents = agents
        self.execution_queue = PriorityQueue()
        self.performance_tracker = PerformanceTracker()

    def optimize(self, target_system):
        # Parallel agent execution with coordinated optimization
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(agent.optimize, target_system): agent
                for agent in self.agents
            }

            for future in concurrent.futures.as_completed(futures):
                agent = futures[future]
                result = future.result()
                self.performance_tracker.log(agent, result)
```

## §3. Agent Evaluation

> testing, benchmarking, reliability metrics, behavioral testing

### Phase 1: Performance Analysis and Baseline Metrics
*Source: agent-orchestration-improve-agent*

Comprehensive analysis of agent performance using context-manager for historical data collection.

### 1.1 Gather Performance Data

```
Use: context-manager
Command: analyze-agent-performance $ARGUMENTS --days 30
```

Collect metrics including:

- Task completion rate (successful vs failed tasks)
- Response accuracy and factual correctness
- Tool usage efficiency (correct tools, call frequency)
- Average response time and token consumption
- User satisfaction indicators (corrections, retries)
- Hallucination incidents and error patterns

### 1.2 User Feedback Pattern Analysis

Identify recurring patterns in user interactions:

- **Correction patterns**: Where users consistently modify outputs
- **Clarification requests**: Common areas of ambiguity
- **Task abandonment**: Points where users give up
- **Follow-up questions**: Indicators of incomplete responses
- **Positive feedback**: Successful patterns to preserve

### 1.3 Failure Mode Classification

Categorize failures by root cause:

- **Instruction misunderstanding**: Role or task confusion
- **Output format errors**: Structure or formatting issues
- **Context loss**: Long conversation degradation
- **Tool misuse**: Incorrect or inefficient tool selection
- **Constraint violations**: Safety or business rule breaches
- **Edge case handling**: Unusual input scenarios

### 1.4 Baseline Performance Report

Generate quantitative baseline metrics:

```
Performance Baseline:
- Task Success Rate: [X%]
- Average Corrections per Task: [Y]
- Tool Call Efficiency: [Z%]
- User Satisfaction Score: [1-10]
- Average Response Latency: [Xms]
- Token Efficiency Ratio: [X:Y]
```

### Phase 3: Testing and Validation
*Source: agent-orchestration-improve-agent*

Comprehensive testing framework with A/B comparison.

### 3.1 Test Suite Development

Create representative test scenarios:

```
Test Categories:
1. Golden path scenarios (common successful cases)
2. Previously failed tasks (regression testing)
3. Edge cases and corner scenarios
4. Stress tests (complex, multi-step tasks)
5. Adversarial inputs (potential breaking points)
6. Cross-domain tasks (combining capabilities)
```

### 3.2 A/B Testing Framework

Compare original vs improved agent:

```
Use: parallel-test-runner
Config:
  - Agent A: Original version
  - Agent B: Improved version
  - Test set: 100 representative tasks
  - Metrics: Success rate, speed, token usage
  - Evaluation: Blind human review + automated scoring
```

Statistical significance testing:

- Minimum sample size: 100 tasks per variant
- Confidence level: 95% (p < 0.05)
- Effect size calculation (Cohen's d)
- Power analysis for future tests

### 3.3 Evaluation Metrics

Comprehensive scoring framework:

**Task-Level Metrics:**

- Completion rate (binary success/failure)
- Correctness score (0-100% accuracy)
- Efficiency score (steps taken vs optimal)
- Tool usage appropriateness
- Response relevance and completeness

**Quality Metrics:**

- Hallucination rate (factual errors per response)
- Consistency score (alignment with previous responses)
- Format compliance (matches specified structure)
- Safety score (constraint adherence)
- User satisfaction prediction

**Performance Metrics:**

- Response latency (time to first token)
- Total generation time
- Token consumption (input + output)
- Cost per task (API usage fees)
- Memory/context efficiency

### 3.4 Human Evaluation Protocol

Structured human review process:

- Blind evaluation (evaluators don't know version)
- Standardized rubric with clear criteria
- Multiple evaluators per sample (inter-rater reliability)
- Qualitative feedback collection
- Preference ranking (A vs B comparison)

### Behavioral Traits
*Source: ai-engineer*

- Prioritizes production reliability and scalability over proof-of-concept implementations
- Implements comprehensive error handling and graceful degradation
- Focuses on cost optimization and efficient resource utilization
- Emphasizes observability and monitoring from day one
- Considers AI safety and responsible AI practices in all implementations
- Uses structured outputs and type safety wherever possible
- Implements thorough testing including adversarial inputs
- Documents AI system behavior and decision-making processes
- Stays current with rapidly evolving AI/ML landscape
- Balances cutting-edge techniques with proven, stable solutions

## §4. Memory Systems

> short-term, long-term, episodic, semantic, vector stores, retrieval

## §5. Tool Building

> JSON Schema, MCP tools, function calling, error handling, descriptions

## §6. Autonomous Patterns

> self-healing, goal decomposition, reflection, chain-of-thought

## §7. Parallel Agent Dispatch

> concurrent execution, dependency graphs, resource management

### 4. Parallel Execution Optimization
*Source: agent-orchestration-multi-agent-optimize*

### Key Strategies

- Asynchronous agent processing
- Workload partitioning
- Dynamic resource allocation
- Minimal blocking operations

### 5. Context Management
*Source: autonomous-agent-patterns*

### 5.1 Context Injection Patterns

````python
class ContextManager:
    """
    Manage context provided to the agent.
    Inspired by Cline's @-mention patterns.
    """

    def __init__(self, workspace: str):
        self.workspace = workspace
        self.context = []

    def add_file(self, path: str) -> None:
        """@file - Add file contents to context"""
        with open(path, 'r') as f:
            content = f.read()

        self.context.append({
            "type": "file",
            "path": path,
            "content": content
        })

    def add_folder(self, path: str, max_files: int = 20) -> None:
        """@folder - Add all files in folder"""
        for root, dirs, files in os.walk(path):
            for file in files[:max_files]:
                file_path = os.path.join(root, file)
                self.add_file(file_path)

    def add_url(self, url: str) -> None:
        """@url - Fetch and add URL content"""
        response = requests.get(url)
        content = html_to_markdown(response.text)

        self.context.append({
            "type": "url",
            "url": url,
            "content": content
        })

    def add_problems(self, diagnostics: list) -> None:
        """@problems - Add IDE diagnostics"""
        self.context.append({
            "type": "diagnostics",
            "problems": diagnostics
        })

    def format_for_prompt(self) -> str:
        """Format all context for LLM prompt"""
        parts = []
        for item in self.context:
            if item["type"] == "file":
                parts.append(f"## File: {item['path']}\n```\n{item['content']}\n```")
            elif item["type"] == "url":
                parts.append(f"## URL: {item['url']}\n{item['content']}")
            elif item["type"] == "diagnostics":
                parts.append(f"## Problems:\n{json.dumps(item['problems'], indent=2)}")

        return "\n\n".join(parts)
````

### 5.2 Checkpoint/Resume

```python
class CheckpointManager:
    """
    Save and restore agent state for long-running tasks.
    """

    def __init__(self, storage_dir: str):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)

    def save_checkpoint(self, session_id: str, state: dict) -> str:
        """Save current agent state"""
        checkpoint = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,

*[...34 more lines]*

### Resources
*Source: autonomous-agent-patterns*

- [Cline](https://github.com/cline/cline)
- [OpenAI Codex](https://github.com/openai/codex)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Anthropic Tool Use](https://docs.anthropic.com/claude/docs/tool-use)

## §8. Agent Optimization

> prompt engineering, cost reduction, latency, reliability improvement

### Role: AI-Powered Multi-Agent Performance Engineering Specialist
*Source: agent-orchestration-multi-agent-optimize*

### Context

The Multi-Agent Optimization Tool is an advanced AI-driven framework designed to holistically improve system performance through intelligent, coordinated agent-based optimization. Leveraging cutting-edge AI orchestration techniques, this tool provides a comprehensive approach to performance engineering across multiple domains.

### Core Capabilities

- Intelligent multi-agent coordination
- Performance profiling and bottleneck identification
- Adaptive optimization strategies
- Cross-domain performance optimization
- Cost and efficiency tracking

### 6. Latency Reduction Techniques
*Source: agent-orchestration-multi-agent-optimize*

### Performance Acceleration

- Predictive caching
- Pre-warming agent contexts
- Intelligent result memoization
- Reduced round-trip communication

### 8. Monitoring and Continuous Improvement
*Source: agent-orchestration-multi-agent-optimize*

### Observability Framework

- Real-time performance dashboards
- Automated optimization feedback loops
- Machine learning-driven improvement
- Adaptive optimization strategies

### Phase 2: Prompt Engineering Improvements
*Source: agent-orchestration-improve-agent*

Apply advanced prompt optimization techniques using prompt-engineer agent.

### 2.1 Chain-of-Thought Enhancement

Implement structured reasoning patterns:

```
Use: prompt-engineer
Technique: chain-of-thought-optimization
```

- Add explicit reasoning steps: "Let's approach this step-by-step..."
- Include self-verification checkpoints: "Before proceeding, verify that..."
- Implement recursive decomposition for complex tasks
- Add reasoning trace visibility for debugging

### 2.2 Few-Shot Example Optimization

Curate high-quality examples from successful interactions:

- **Select diverse examples** covering common use cases
- **Include edge cases** that previously failed
- **Show both positive and negative examples** with explanations
- **Order examples** from simple to complex
- **Annotate examples** with key decision points

Example structure:

```
Good Example:
Input: [User request]
Reasoning: [Step-by-step thought process]
Output: [Successful response]
Why this works: [Key success factors]

Bad Example:
Input: [Similar request]
Output: [Failed response]
Why this fails: [Specific issues]
Correct approach: [Fixed version]
```

### 2.3 Role Definition Refinement

Strengthen agent identity and capabilities:

- **Core purpose**: Clear, single-sentence mission
- **Expertise domains**: Specific knowledge areas
- **Behavioral traits**: Personality and interaction style
- **Tool proficiency**: Available tools and when to use them
- **Constraints**: What the agent should NOT do
- **Success criteria**: How to measure task completion

### 2.4 Constitutional AI Integration

Implement self-correction mechanisms:

```
Constitutional Principles:
1. Verify factual accuracy before responding
2. Self-check for potential biases or harmful content
3. Validate output format matches requirements
4. Ensure response completeness
5. Maintain consistency with previous responses
```

Add critique-and-revise loops:

- Initial response generation
- Self-critique against principles
- Automatic revision if issues detected
- Final validation before output

### 2.5 Output Format Tuning

Optimize response structure:

- **Structured templates** for common tasks
- **Dynamic formatting** based on complexity
- **Progressive disclosure** for detailed information

*[...3 more lines]*

### Continuous Improvement Cycle
*Source: agent-orchestration-improve-agent*

Establish regular improvement cadence:

- **Weekly**: Monitor metrics and collect feedback
- **Monthly**: Analyze patterns and plan improvements
- **Quarterly**: Major version updates with new capabilities
- **Annually**: Strategic review and architecture updates

Remember: Agent optimization is an iterative process. Each cycle builds upon previous learnings, gradually improving performance while maintaining stability and safety.

## §9. CrewAI & LangGraph

> framework-specific patterns, agents, tasks, workflows

### 2. Tool Design Patterns
*Source: autonomous-agent-patterns*

### 2.1 Tool Schema

```python
class Tool:
    """Base class for agent tools"""

    @property
    def schema(self) -> dict:
        """JSON Schema for the tool"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": self._get_parameters(),
                "required": self._get_required()
            }
        }

    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool and return result"""
        raise NotImplementedError

class ReadFileTool(Tool):
    name = "read_file"
    description = "Read the contents of a file from the filesystem"

    def _get_parameters(self):
        return {
            "path": {
                "type": "string",
                "description": "Absolute path to the file"
            },
            "start_line": {
                "type": "integer",
                "description": "Line to start reading from (1-indexed)"
            },
            "end_line": {
                "type": "integer",
                "description": "Line to stop reading at (inclusive)"
            }
        }

    def _get_required(self):
        return ["path"]

    def execute(self, path: str, start_line: int = None, end_line: int = None) -> ToolResult:
        try:
            with open(path, 'r') as f:
                lines = f.readlines()

            if start_line and end_line:
                lines = lines[start_line-1:end_line]

            return ToolResult(
                success=True,
                output="".join(lines)
            )
        except FileNotFoundError:
            return ToolResult(
                success=False,
                error=f"File not found: {path}"
            )
```

### 2.2 Essential Agent Tools

```python
CODING_AGENT_TOOLS = {
    # File operations
    "read_file": "Read file contents",
    "write_file": "Create or overwrite a file",
    "edit_file": "Make targeted edits to a file",
    "list_directory": "List files and folders",
    "search_files": "Search for files by pattern",

    # Code understanding
    "search_code": "Search for code patterns (grep)",
    "get_definition": "Find function/class definition",
    "get_references": "Find all references to a symbol",

*[...74 more lines]*

### 3. Permission & Safety Patterns
*Source: autonomous-agent-patterns*

### 3.1 Permission Levels

```python
class PermissionLevel(Enum):
    # Fully automatic - no user approval needed
    AUTO = "auto"

    # Ask once per session
    ASK_ONCE = "ask_once"

    # Ask every time
    ASK_EACH = "ask_each"

    # Never allow
    NEVER = "never"

PERMISSION_CONFIG = {
    # Low risk - can auto-approve
    "read_file": PermissionLevel.AUTO,
    "list_directory": PermissionLevel.AUTO,
    "search_code": PermissionLevel.AUTO,

    # Medium risk - ask once
    "write_file": PermissionLevel.ASK_ONCE,
    "edit_file": PermissionLevel.ASK_ONCE,

    # High risk - ask each time
    "run_command": PermissionLevel.ASK_EACH,
    "delete_file": PermissionLevel.ASK_EACH,

    # Dangerous - never auto-approve
    "sudo_command": PermissionLevel.NEVER,
    "format_disk": PermissionLevel.NEVER
}
```

### 3.2 Approval UI Pattern

```python
class ApprovalManager:
    def __init__(self, ui, config):
        self.ui = ui
        self.config = config
        self.session_approvals = {}

    def request_approval(self, tool_name: str, args: dict) -> bool:
        level = self.config.get(tool_name, PermissionLevel.ASK_EACH)

        if level == PermissionLevel.AUTO:
            return True

        if level == PermissionLevel.NEVER:
            self.ui.show_error(f"Tool '{tool_name}' is not allowed")
            return False

        if level == PermissionLevel.ASK_ONCE:
            if tool_name in self.session_approvals:
                return self.session_approvals[tool_name]

        # Show approval dialog
        approved = self.ui.show_approval_dialog(
            tool=tool_name,
            args=args,
            risk_level=self._assess_risk(tool_name, args)
        )

        if level == PermissionLevel.ASK_ONCE:
            self.session_approvals[tool_name] = approved

        return approved

    def _assess_risk(self, tool_name: str, args: dict) -> str:
        """Analyze specific call for risk level"""
        if tool_name == "run_command":
            cmd = args.get("command", "")
            if any(danger in cmd for danger in ["rm -rf", "sudo", "chmod"]):
                return "HIGH"
        return "MEDIUM"
```


*[...56 more lines]*

## §10. AI Engineering

> RAG, embeddings, LLM integration, production AI patterns

### Integration
*Source: multi-agent-patterns*

This skill builds on context-fundamentals and context-degradation. It connects to:

- memory-systems - Shared state management across agents
- tool-design - Tool specialization per agent
- context-optimization - Context partitioning strategies
