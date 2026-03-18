---
name: context-memory-omega
description: "ELITE context & memory management — fusion of 15 context/memory skills. Covers context window optimization, compression, degradation, fundamentals, session memory, agent memory, persistent memory, retrieval, and conversation continuity."
metadata:
  model: opus
  forged_from: 15
  forge_date: 2026-03-12
---

# CONTEXT-MEMORY-OMEGA — Elite Composite Skill

> Forged from 15 individual skills into one supreme composite.
> Sources: context-window-management, context-manager, context-management-context-save, context-management-context-restore, context-driven-development, context-optimization, context-compression, context-degradation, context-fundamentals, conversation-memory, agent-memory, agent-memory-mcp, agent-memory-systems, memory-systems, memory-safety-patterns

## When to Apply

Activate this skill for ANY work related to:
- **Context Window Management**: token budgeting, priority ranking, sliding windows
- **Context Compression**: summarization, key extraction, lossy/lossless strategies
- **Context Degradation**: graceful degradation, fallback chains, recovery
- **Session Memory**: save/restore, checkpointing, conversation continuity
- **Agent Memory Systems**: short-term, long-term, episodic, semantic memory
- **Persistent Memory**: MCP memory, vector stores, retrieval-augmented memory
- **Memory Safety**: memory leaks, cleanup, lifecycle management, Rust-inspired patterns
- **Context-Driven Development**: using context effectively for code generation/review

---

## §1. Context Window Management

> token budgeting, priority ranking, sliding windows

## §2. Context Compression

> summarization, key extraction, lossy/lossless strategies

### Context Extraction Strategies
*Source: context-management-context-save*

### 1. Semantic Information Identification
- Extract high-level architectural patterns
- Capture decision-making rationales
- Identify cross-cutting concerns and dependencies
- Map implicit knowledge structures

### 2. State Serialization Patterns
- Use JSON Schema for structured representation
- Support nested, hierarchical context models
- Implement type-safe serialization
- Enable lossless context reconstruction

### 3. Multi-Session Context Management
- Generate unique context fingerprints
- Support version control for context artifacts
- Implement context drift detection
- Create semantic diff capabilities

### 4. Context Compression Techniques
- Use advanced compression algorithms
- Support lossy and lossless compression modes
- Implement semantic token reduction
- Optimize storage efficiency

### 5. Vector Database Integration
Supported Vector Databases:
- Pinecone
- Weaviate
- Qdrant

Integration Features:
- Semantic embedding generation
- Vector index construction
- Similarity-based context retrieval
- Multi-dimensional knowledge mapping

### 6. Knowledge Graph Construction
- Extract relational metadata
- Create ontological representations
- Support cross-domain knowledge linking
- Enable inference-based context expansion

### 7. Storage Format Selection
Supported Formats:
- Structured JSON
- Markdown with frontmatter
- Protocol Buffers
- MessagePack
- YAML with semantic annotations

## §3. Context Degradation

> graceful degradation, fallback chains, recovery

## §4. Session Memory

> save/restore, checkpointing, conversation continuity

## §5. Agent Memory Systems

> short-term, long-term, episodic, semantic memory

## §6. Persistent Memory

> MCP memory, vector stores, retrieval-augmented memory

## §7. Memory Safety

> memory leaks, cleanup, lifecycle management, Rust-inspired patterns

### Patterns by Language
*Source: memory-safety-patterns*

### Pattern 1: RAII in C++

```cpp
// RAII: Resource Acquisition Is Initialization
// Resource lifetime tied to object lifetime

#include <memory>
#include <fstream>
#include <mutex>

// File handle with RAII
class FileHandle {
public:
    explicit FileHandle(const std::string& path)
        : file_(path) {
        if (!file_.is_open()) {
            throw std::runtime_error("Failed to open file");
        }
    }

    // Destructor automatically closes file
    ~FileHandle() = default; // fstream closes in its destructor

    // Delete copy (prevent double-close)
    FileHandle(const FileHandle&) = delete;
    FileHandle& operator=(const FileHandle&) = delete;

    // Allow move
    FileHandle(FileHandle&&) = default;
    FileHandle& operator=(FileHandle&&) = default;

    void write(const std::string& data) {
        file_ << data;
    }

private:
    std::fstream file_;
};

// Lock guard (RAII for mutexes)
class Database {
public:
    void update(const std::string& key, const std::string& value) {
        std::lock_guard<std::mutex> lock(mutex_); // Released on scope exit
        data_[key] = value;
    }

    std::string get(const std::string& key) {
        std::shared_lock<std::shared_mutex> lock(shared_mutex_);
        return data_[key];
    }

private:
    std::mutex mutex_;
    std::shared_mutex shared_mutex_;
    std::map<std::string, std::string> data_;
};

// Transaction with rollback (RAII)
template<typename T>
class Transaction {
public:
    explicit Transaction(T& target)
        : target_(target), backup_(target), committed_(false) {}

    ~Transaction() {
        if (!committed_) {
            target_ = backup_; // Rollback
        }
    }

    void commit() { committed_ = true; }

    T& get() { return target_; }

private:
    T& target_;
    T backup_;
    bool committed_;
};

*[...445 more lines]*

### Context Lifecycle
*Source: context-driven-development*

1. **Creation**: Initial setup via `/conductor:setup`
2. **Validation**: Verify before each track
3. **Evolution**: Update as project grows
4. **Synchronization**: Keep artifacts aligned
5. **Archival**: Document historical decisions

### Common Anti-Patterns
*Source: context-driven-development*

Avoid these context management mistakes:

### Stale Context

Problem: Context documents become outdated and misleading.
Solution: Update context as part of each track's completion process.

### Context Sprawl

Problem: Information scattered across multiple locations.
Solution: Use the defined artifact structure; resist creating new document types.

### Implicit Context

Problem: Relying on knowledge not captured in artifacts.
Solution: If you reference something repeatedly, add it to the appropriate artifact.

### Context Hoarding

Problem: One person maintains context without team input.
Solution: Review context artifacts in pull requests; make updates collaborative.

### Over-Specification

Problem: Context becomes so detailed it's impossible to maintain.
Solution: Keep artifacts focused on decisions that affect AI behavior and team alignment.

## §8. Context-Driven Development

> using context effectively for code generation/review
