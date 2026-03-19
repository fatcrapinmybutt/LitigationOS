import sqlite3
import time

db_path = r'C:\Users\andre\LitigationOS\litigation_context.db'
conn = sqlite3.connect(db_path, timeout=120)
conn.execute("PRAGMA busy_timeout=60000")
conn.execute("PRAGMA journal_mode=WAL")

# Check existing columns
cursor = conn.execute("PRAGMA table_info(skill_registry)")
columns = [row[1] for row in cursor.fetchall()]
print(f"Existing columns: {columns}")

# Add missing columns
for col, coltype, default in [
    ("category", "TEXT", "'skill'"),
    ("source", "TEXT", "'awesome-copilot-main'"),
    ("install_path", "TEXT", "''"),
    ("description", "TEXT", "''"),
    ("installed_at", "TEXT", "''"),
    ("status", "TEXT", "'active'"),
]:
    if col not in columns:
        try:
            conn.execute(f"ALTER TABLE skill_registry ADD COLUMN {col} {coltype} DEFAULT {default}")
            print(f"  Added column: {col}")
        except Exception as e:
            print(f"  Column {col} already exists or error: {e}")

conn.commit()

now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

# Show what exists
existing = conn.execute("SELECT * FROM skill_registry LIMIT 3").fetchall()
cols_now = [d[0] for d in conn.execute("SELECT * FROM skill_registry LIMIT 1").description]
print(f"Columns now: {cols_now}")
for row in existing:
    print(f"  Sample row: {dict(zip(cols_now, row))}")

# Construct INSERT with correct columns from the table
# First get all column names
col_names = [d[0] for d in conn.execute("SELECT * FROM skill_registry LIMIT 1").description]
print(f"Using columns: {col_names}")

# Try inserting with available columns
skills_data = [
    {"name": "SQL Code Review", "category": "skill", "source": "awesome-copilot-main",
     "install_path": ".copilot/skills/sql-code-review", "description": "Security, performance, and maintainability analysis for SQL queries",
     "status": "active"},
    {"name": "SQL Optimization", "category": "skill", "source": "awesome-copilot-main",
     "install_path": ".copilot/skills/sql-optimization", "description": "Query tuning, indexing strategies, and performance analysis",
     "status": "active"},
    {"name": "Create Specification", "category": "skill", "source": "awesome-copilot-main",
     "install_path": ".copilot/skills/create-specification", "description": "AI-ready specification files with structured formatting",
     "status": "active"},
    {"name": "Documentation Writer", "category": "skill", "source": "awesome-copilot-main",
     "install_path": ".copilot/skills/documentation-writer", "description": "Diataxis framework expert for technical documentation",
     "status": "active"},
    {"name": "Review and Refactor", "category": "skill", "source": "awesome-copilot-main",
     "install_path": ".copilot/skills/review-and-refactor", "description": "Code review against coding guidelines and best practices",
     "status": "active"},
    {"name": "Refactor", "category": "skill", "source": "awesome-copilot-main",
     "install_path": ".copilot/skills/refactor", "description": "Surgical refactoring with code smells and design patterns",
     "status": "active"},
    {"name": "Refactor Plan", "category": "skill", "source": "awesome-copilot-main",
     "install_path": ".copilot/skills/refactor-plan", "description": "Multi-file refactoring sequencing and rollback strategy",
     "status": "active"},
    {"name": "Context Map", "category": "skill", "source": "awesome-copilot-main",
     "install_path": ".copilot/skills/context-map", "description": "Pre-implementation context mapping of files and dependencies",
     "status": "active"},
    {"name": "Remember", "category": "skill", "source": "awesome-copilot-main",
     "install_path": ".copilot/skills/remember", "description": "Domain-organized memory persistence for lessons learned",
     "status": "active"},
    {"name": "Python MCP Server Generator", "category": "skill", "source": "awesome-copilot-main",
     "install_path": ".copilot/skills/python-mcp-server-generator", "description": "Complete MCP server generation in Python",
     "status": "active"},
    {"name": "Conventional Commit", "category": "skill", "source": "awesome-copilot-main",
     "install_path": ".copilot/skills/conventional-commit", "description": "Standardized commit message generation workflow",
     "status": "active"},
    {"name": "Breakdown Plan", "category": "skill", "source": "awesome-copilot-main",
     "install_path": ".copilot/skills/breakdown-plan", "description": "GitHub project planning with Epic to Feature to Story hierarchy",
     "status": "active"},
    {"name": "Create Implementation Plan", "category": "skill", "source": "awesome-copilot-main",
     "install_path": ".copilot/skills/create-implementation-plan", "description": "Deterministic AI-executable implementation plans",
     "status": "active"},
    {"name": "Product Requirements Document", "category": "skill", "source": "awesome-copilot-main",
     "install_path": ".copilot/skills/prd", "description": "PRD creation with discovery phase",
     "status": "active"},
    {"name": "Create ADR", "category": "skill", "source": "awesome-copilot-main",
     "install_path": ".copilot/skills/create-architectural-decision-record", "description": "Architectural Decision Record documentation",
     "status": "active"},
    {"name": "Create README", "category": "skill", "source": "awesome-copilot-main",
     "install_path": ".copilot/skills/create-readme", "description": "Project README generation with modern documentation patterns",
     "status": "active"},
    {"name": "Code Exemplars Blueprint", "category": "skill", "source": "awesome-copilot-main",
     "install_path": ".copilot/skills/code-exemplars-blueprint-generator", "description": "Identifies high-quality code patterns across tech stacks",
     "status": "active"},
    {"name": "Governance Audit Hook", "category": "hook", "source": "awesome-copilot-main",
     "install_path": ".copilot/hooks/governance-audit", "description": "Real-time threat detection for Copilot prompts",
     "status": "active"},
    {"name": "Session Logger Hook", "category": "hook", "source": "awesome-copilot-main",
     "install_path": ".copilot/hooks/session-logger", "description": "Logs all Copilot session activity in JSON format",
     "status": "active"},
    {"name": "Critical Thinking Agent", "category": "agent", "source": "awesome-copilot-main",
     "install_path": ".copilot/agents/critical-thinking.agent.md", "description": "Challenges assumptions and encourages critical thinking",
     "status": "active"},
    {"name": "Devils Advocate Agent", "category": "agent", "source": "awesome-copilot-main",
     "install_path": ".copilot/agents/devils-advocate.agent.md", "description": "Stress-tests ideas by finding flaws, risks, edge cases",
     "status": "active"},
    {"name": "Debug Agent", "category": "agent", "source": "awesome-copilot-main",
     "install_path": ".copilot/agents/debug.agent.md", "description": "Systematic debugging: Assessment, Investigation, Resolution, QA",
     "status": "active"},
    {"name": "Plan Agent", "category": "agent", "source": "awesome-copilot-main",
     "install_path": ".copilot/agents/plan.agent.md", "description": "Strategic planning focusing on analysis before implementation",
     "status": "active"},
    {"name": "Planner Agent", "category": "agent", "source": "awesome-copilot-main",
     "install_path": ".copilot/agents/planner.agent.md", "description": "Implementation planning for features or refactoring",
     "status": "active"},
    {"name": "Research Technical Spike", "category": "agent", "source": "awesome-copilot-main",
     "install_path": ".copilot/agents/research-technical-spike.agent.md", "description": "Exhaustive technical research with continuous documentation",
     "status": "active"},
    {"name": "Security Reviewer Agent", "category": "agent", "source": "awesome-copilot-main",
     "install_path": ".copilot/agents/se-security-reviewer.agent.md", "description": "OWASP Top 10 and LLM security review, Zero Trust",
     "status": "active"},
    {"name": "Technical Writer Agent", "category": "agent", "source": "awesome-copilot-main",
     "install_path": ".copilot/agents/se-technical-writer.agent.md", "description": "Creates developer documentation, blogs, tutorials",
     "status": "active"},
    {"name": "Repo Architect Agent", "category": "agent", "source": "awesome-copilot-main",
     "install_path": ".copilot/agents/repo-architect.agent.md", "description": "Scaffolds agentic project structures with 3-layer model",
     "status": "active"},
    {"name": "Context Architect Agent", "category": "agent", "source": "awesome-copilot-main",
     "install_path": ".copilot/agents/context-architect.agent.md", "description": "Plans multi-file changes by identifying context and dependencies",
     "status": "active"},
    {"name": "Principal SW Engineer", "category": "agent", "source": "awesome-copilot-main",
     "install_path": ".copilot/agents/principal-software-engineer.agent.md", "description": "Expert guidance on engineering excellence and SOLID principles",
     "status": "active"},
    {"name": "MS SQL DBA Agent", "category": "agent", "source": "awesome-copilot-main",
     "install_path": ".copilot/agents/ms-sql-dba.agent.md", "description": "MS SQL Server management, T-SQL optimization, security",
     "status": "active"},
    {"name": "Janitor Agent", "category": "agent", "source": "awesome-copilot-main",
     "install_path": ".copilot/agents/janitor.agent.md", "description": "Tech debt elimination through deletion and simplification",
     "status": "active"},
    {"name": "Upcoming Deadlines MCP Tool", "category": "mcp_tool", "source": "custom",
     "install_path": "00_SYSTEM/mcp_server/litigation_context_mcp/server.py", "description": "Query upcoming court deadlines with urgency indicators",
     "status": "active"},
    {"name": "Filing Search MCP Tool", "category": "mcp_tool", "source": "custom",
     "install_path": "00_SYSTEM/mcp_server/litigation_context_mcp/server.py", "description": "Search filings by case, court, type, or keyword",
     "status": "active"},
    {"name": "Evidence Lookup MCP Tool", "category": "mcp_tool", "source": "custom",
     "install_path": "00_SYSTEM/mcp_server/litigation_context_mcp/server.py", "description": "Search evidence by keyword and date range",
     "status": "active"},
]

inserted = 0
skipped = 0
for s in skills_data:
    try:
        # Use INSERT OR REPLACE to handle existing rows
        conn.execute(
            """INSERT OR REPLACE INTO skill_registry (name, category, source, install_path, description, installed_at, status)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (s["name"], s.get("category", "skill"), s.get("source", "awesome-copilot-main"),
             s.get("install_path", ""), s.get("description", ""), now, s.get("status", "active"))
        )
        inserted += 1
    except Exception as e:
        print(f"Error inserting {s['name']}: {e}")
        skipped += 1

conn.commit()

# Verify
count = conn.execute("SELECT COUNT(*) FROM skill_registry").fetchone()[0]
print(f"\nInserted/updated: {inserted}, Errors: {skipped}")
print(f"Total skills in registry: {count}")

# Show all
rows = conn.execute("SELECT name, category, status FROM skill_registry ORDER BY category, name").fetchall()
for r in rows:
    print(f"  [{r[1]}] {r[0]} ({r[2]})")

conn.close()
print("\nDONE")
