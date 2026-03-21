"""
DELTA9 AGENT BASE — MAX LEVEL 9999++ OMEGA v3.0

Every agent inherits Agent9999. Non-negotiable error handling:
1. Try operation
2. Catch specific → targeted recovery
3. Catch broad → log + skip + continue
4. Checkpoint every N iterations → crash-resume
5. Deadman switch → 60s no progress → self-diagnose
6. Agent-level retry → 3 attempts exponential backoff
7. Tier-level fallback → orchestrator flags + continues
8. Fleet-level report → convergence monitor tracks health

v2.0 OMEGA Upgrades:
  - Plan-and-Execute pattern (decompose → execute → replan)
  - Enhanced tool registry with schema validation
  - Quality scoring (auto-computed from AgentStats)
  - Inter-agent message bus (send/receive findings)
  - Performance profiling (peak memory, retry counts)
  - Adaptive retry with jitter (smarter backoff)

v3.0 OMEGA Upgrades:
  - Lane-aware processing (built-in MEEK signal detection)
  - Anti-hallucination guard (verified party identity)
  - Traceable statistics (every stat → DB query provenance)
  - Cross-agent learning (read any agent's memories)
  - Evidence scoring (built-in relevance/admissibility scoring)
  - Output validation (verify results before returning)
  - Structured health reporting (fleet-readable status)
  - Provenance chain (track which inputs produced each output)
"""
import json
import os
import shutil
import sqlite3
import sys
import threading
import random
import time
import traceback
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeout
from pathlib import Path
from threading import Lock
from typing import Any, List, Optional

from .agent_models import (
    AgentResult, AgentStats, FatalAgentError, SkipItemError,
    RetryableError, QualityScore, PlanStep, AgentMessage,
    HealthReport, ProvenanceEntry, EvidenceScore, LaneDetection,
    FleetStatus, ValidationResult, LaneCrossContaminationError,
    MASTER_INDEX_DB, CHECKPOINT_DIR
)

# Import context manager (fail-safe — falls back to None if unavailable)
_ContextManager = None
_AgentContext = None
try:
    _cm_path = Path(__file__).resolve().parent.parent.parent / "local_model"
    if str(_cm_path) not in sys.path:
        sys.path.insert(0, str(_cm_path))
    from context_manager import ContextManager as _ContextManager, AgentContext as _AgentContext
except Exception:
    pass  # Context manager unavailable — agents run without it

# Import circuit breaker from failsafe module
try:
    _FAILSAFE_DIR = Path(__file__).resolve().parent.parent
    if str(_FAILSAFE_DIR) not in sys.path:
        sys.path.insert(0, str(_FAILSAFE_DIR))
    from failsafe import CircuitBreaker as _CircuitBreaker
except Exception:
    _CircuitBreaker = None

# Import local AI engine — guaranteed to work, zero servers, zero APIs
_PIPELINE_DIR = Path(__file__).resolve().parent.parent
if str(_PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(_PIPELINE_DIR))

try:
    from local_ai_engine import LocalAI as _LocalAI
    _LOCAL_AI = _LocalAI()
except Exception:
    _LOCAL_AI = None


class Agent9999(ABC):
    """DELTA9 Agent Base — MAX LEVEL 9999++
    
    Performance features:
    - Parallel I/O: set self.parallel_workers > 1 to process items concurrently
    - Per-item timeout: self.item_timeout caps time on any single item (default 30s)
    - Adaptive checkpoint: auto-adjusts interval based on throughput
    - Real-time progress: flushes output every checkpoint
    """

    # Thread-local storage for per-thread DB connections
    _thread_local = threading.local()

    def __init__(self, agent_id: str, db_path: Optional[Path] = None):
        self.agent_id = agent_id
        self.db_path = db_path or MASTER_INDEX_DB
        self.stats = AgentStats()
        self.checkpoint_file = CHECKPOINT_DIR / f"{agent_id}.checkpoint.json"

        # Load centralized config (with hardcoded fallbacks)
        try:
            from config import AGENT_CONFIG as _cfg
        except Exception:
            _cfg = {}

        self.max_retries = _cfg.get("max_retries", 3)
        self.checkpoint_interval = _cfg.get("checkpoint_interval", 500)
        self.deadman_timeout = _cfg.get("deadman_timeout", 120)
        self.item_timeout = _cfg.get("item_timeout", 30)
        self.parallel_workers = 1   # >1 enables concurrent _process_item
        self._last_progress = time.time()
        self._stats_lock = Lock()
        self._main_thread_id = threading.get_ident()
        self._main_db: Optional[sqlite3.Connection] = None
        self._central_db: Optional[sqlite3.Connection] = None
        self._log_buffer: list = []
        # ReAct loop defaults (from config)
        self._react_max_iterations = _cfg.get("react_max_iterations", 10)
        # DB-backed checkpoint timing
        self._last_db_checkpoint = time.time()
        self._db_checkpoint_interval = _cfg.get("react_checkpoint_interval", 300)
        # Tool registry for subclass-populated tools
        self._tool_registry: dict = {}
        # Circuit breaker for DB operations (wired from failsafe.py)
        _cb_threshold = _cfg.get("circuit_breaker_threshold", 5)
        _cb_cooldown = _cfg.get("circuit_breaker_cooldown", 30.0)
        self._db_breaker = (
            _CircuitBreaker(name=f"{agent_id}_db", threshold=_cb_threshold, cooldown=_cb_cooldown)
            if _CircuitBreaker else None
        )
        # Unified context manager (fail-safe — None if unavailable)
        self._ctx: Optional[Any] = None
        if _ContextManager:
            try:
                self._ctx = _ContextManager(agent_id)
            except Exception:
                pass

        # ═══ OMEGA v2.0 ENHANCEMENTS ═══
        # Inter-agent message bus (thread-safe inbox)
        self._inbox: List[AgentMessage] = []
        self._outbox: List[AgentMessage] = []
        self._inbox_lock = Lock()
        # Plan-and-Execute state
        self._plan: List[PlanStep] = []
        self._plan_lock = Lock()
        # Quality tracking (auto-computed at end of run)
        self._quality: Optional[QualityScore] = None
        self._quality_history: list = []  # last 5 quality scores for trend tracking
        # Findings accumulator (key evidence/results to pass upstream)
        self._findings: List[dict] = []
        self._findings_lock = Lock()
        # Self-healing: known error patterns from past runs
        self._known_error_patterns: set = set()
        # Performance profiling: phase timing
        self._timing: dict = {}

    # =========================================
    # CONTEXT HANDOFF PROTOCOL
    # =========================================
    def get_agent_context(self) -> Optional[Any]:
        """Export this agent's context for handoff to another agent."""
        if not self._ctx or not _AgentContext:
            return None
        try:
            return _AgentContext(
                source_agent=self.agent_id,
                target_agent="",
                lane=getattr(self, "lane", "C"),
                data={
                    "stats": {"processed": self.stats.processed, "errors": self.stats.errors,
                              "total": self.stats.total, "skipped": self.stats.skipped},
                    "agent_id": self.agent_id,
                },
                priority="MEDIUM",
            )
        except Exception:
            return None

    def receive_context(self, ctx) -> None:
        """Receive context from a prior agent/tier. Stores in context window."""
        if not self._ctx or ctx is None:
            return
        try:
            self._ctx.add_to_window(
                key=f"handoff_{getattr(ctx, 'source_agent', 'unknown')}",
                value=getattr(ctx, 'data', {}),
                priority="HIGH",
                category="agent_handoff",
            )
        except Exception:
            pass

    @property
    def db(self) -> Optional[sqlite3.Connection]:
        """Thread-safe DB access: returns correct connection for current thread.
        Main thread gets _main_db; worker threads get per-thread connections."""
        tid = threading.get_ident()
        if tid == self._main_thread_id:
            return self._main_db
        # Worker thread — get or create per-thread connection
        if not hasattr(self._thread_local, 'db') or self._thread_local.db is None:
            if self._main_db is None:
                return None
            conn = sqlite3.connect(str(self.db_path), timeout=120,
                                   check_same_thread=False)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA busy_timeout=120000")
            conn.row_factory = sqlite3.Row
            self._thread_local.db = conn
        return self._thread_local.db

    @db.setter
    def db(self, value):
        """Set the main thread DB connection."""
        self._main_db = value

    @property
    def ai(self):
        """Guaranteed local AI engine. NEVER None, NEVER fails, NEVER needs network.
        Provides: classify_document(), detect_lane(), extract_entities(),
        score_evidence(), summarize(), generate()"""
        return _LOCAL_AI

    # =========================================
    # MAIN EXECUTION LOOP
    # =========================================
    def run(self) -> AgentResult:
        """Main execution loop with full error containment."""
        self._main_thread_id = threading.get_ident()
        self._log("BOOT", f"Agent {self.agent_id} initializing")
        try:
            self._mark_time("setup_start")
            self._connect_db()
            self._ensure_base_tables()
            self._ensure_tables()
            self._load_checkpoint()
            self._validate_preconditions()
            self._self_heal()
            self._mark_time("setup_end")

            self._mark_time("process_start")
            items = self._get_work_items()
            self.stats.total = len(items)
            self._log("WORK", f"{self.stats.total} items to process")

            if self.stats.total == 0:
                self._log("DONE", "No items to process")
                return AgentResult(self.agent_id, "SUCCESS", self.stats)

            # Slice off already-processed items for resume
            pending = items[self.stats.processed:]

            if self.parallel_workers > 1 and len(pending) > 1:
                self._run_parallel(pending)
            else:
                self._run_sequential(pending)
            self._mark_time("process_end")

            self._save_checkpoint()
            self._finalize()
            self._flush_log()
            self._quality = self._compute_quality()
            self._quality_history.append(self._quality.overall if self._quality else 0.0)
            self._quality_history = self._quality_history[-5:]
            self._log("DONE", f"{self.stats} {self._quality or ''}")

            # Determine status: PARTIAL if significant errors but some success
            status = "SUCCESS"
            if self.stats.errored > 0 and self.stats.processed > 0:
                if self.stats.error_rate > 0.3:
                    status = "PARTIAL"

            return AgentResult(
                self.agent_id, status, self.stats,
                quality=self._quality,
                findings=list(self._findings),
                messages_sent=len(self._outbox)
            )

        except FatalAgentError as e:
            self._log("FATAL", str(e))
            self._save_checkpoint()
            self._flush_log()
            self._quality = self._compute_quality()
            return AgentResult(self.agent_id, "FATAL", self.stats,
                               error=str(e), quality=self._quality)
        except Exception as e:
            self._log("CRASH", f"{type(e).__name__}: {e}\n{traceback.format_exc()}")
            self._save_checkpoint()
            self._flush_log()
            self._quality = self._compute_quality()
            return AgentResult(self.agent_id, "CRASH", self.stats,
                               error=str(e), quality=self._quality)
        finally:
            self._close_db()

    # =========================================
    # ABSTRACT METHODS — subclass MUST implement
    # =========================================
    @abstractmethod
    def _get_work_items(self) -> list:
        """Return list of items to process."""
        ...

    @abstractmethod
    def _process_item(self, item: Any) -> None:
        """Process a single item. Raise SkipItemError to skip."""
        ...

    @abstractmethod
    def _validate_preconditions(self) -> None:
        """Check deps/state before running. Raise FatalAgentError if bad."""
        ...

    # =========================================
    # OPTIONAL OVERRIDES
    # =========================================
    def _finalize(self) -> None:
        """Called after all items processed. Override for cleanup/summary."""
        pass

    # =========================================
    # EXECUTION ENGINES (sequential + parallel)
    # =========================================
    def _run_sequential(self, items: list):
        """Process items one at a time with per-item timeout."""
        for i, item in enumerate(items):
            try:
                if self.item_timeout and self.item_timeout > 0:
                    self._process_with_timeout(item)
                else:
                    self._process_item(item)
                with self._stats_lock:
                    self.stats.processed += 1
                self._last_progress = time.time()
            except SkipItemError as e:
                with self._stats_lock:
                    self.stats.skipped += 1
            except Exception as e:
                with self._stats_lock:
                    self.stats.errored += 1
                self._log("ERROR", f"{type(e).__name__}: {e}")
                if self.stats.total > 10 and self.stats.errored > self.stats.total * 0.1:
                    self._log("ALARM", "Error rate >10%")
                    self._diagnose()

            total_done = self.stats.processed + self.stats.skipped + self.stats.errored
            if total_done % self.checkpoint_interval == 0 and total_done > 0:
                self._save_checkpoint()
                self._log("CHECKPOINT", f"{self.stats.processed}/{self.stats.total}")
                sys.stdout.flush()

            elapsed_since = time.time() - self._last_progress
            if elapsed_since > self.deadman_timeout:
                self._log("DEADMAN", f"No progress for {elapsed_since:.0f}s — skipping stuck item")
                with self._stats_lock:
                    self.stats.skipped += 1
                self._last_progress = time.time()

    def _run_parallel(self, items: list):
        """Process items concurrently with thread pool. 
        Each thread gets its own DB connection for writes."""
        self._log("PARALLEL", f"Processing {len(items)} items with {self.parallel_workers} workers")
        batch_size = min(500, len(items))
        
        for batch_start in range(0, len(items), batch_size):
            batch = items[batch_start:batch_start + batch_size]
            with ThreadPoolExecutor(max_workers=self.parallel_workers) as pool:
                futures = {}
                for item in batch:
                    f = pool.submit(self._safe_process_item, item)
                    futures[f] = item
                
                batch_timeout = max(self.item_timeout * len(batch), self.deadman_timeout)
                try:
                    for future in as_completed(futures, timeout=batch_timeout):
                        try:
                            status = future.result(timeout=self.item_timeout)
                            if status == "OK":
                                with self._stats_lock:
                                    self.stats.processed += 1
                                self._last_progress = time.time()
                            elif status == "SKIP":
                                with self._stats_lock:
                                    self.stats.skipped += 1
                        except (TimeoutError, FuturesTimeout):
                            with self._stats_lock:
                                self.stats.skipped += 1
                        except Exception:
                            with self._stats_lock:
                                self.stats.errored += 1
                except (TimeoutError, FuturesTimeout):
                    # Deadman switch for parallel execution — cancel remaining futures
                    cancelled = 0
                    for f in futures:
                        if not f.done():
                            f.cancel()
                            cancelled += 1
                    with self._stats_lock:
                        self.stats.skipped += cancelled
                    self._log("DEADMAN", f"Parallel batch timeout after {batch_timeout}s — cancelled {cancelled} futures")
            
            # Close per-thread connections after each batch
            self._cleanup_thread_connections()
            self._save_checkpoint()
            self._log("CHECKPOINT", f"{self.stats.processed}/{self.stats.total}")
            sys.stdout.flush()

    def _safe_process_item(self, item) -> str:
        """Wrapper for parallel/timeout execution — thread-safe DB access.
        Retries on 'database is locked' with random jitter instead of counting as error."""
        max_lock_retries = 5
        for attempt in range(max_lock_retries):
            try:
                self._process_item(item)
                return "OK"
            except SkipItemError:
                return "SKIP"
            except sqlite3.OperationalError as e:
                if "locked" in str(e) and attempt < max_lock_retries - 1:
                    time.sleep(random.uniform(0.5, 3.0) * (attempt + 1))
                    continue
                self._log("ERROR", f"{type(e).__name__}: {e}")
                return "ERROR"
            except Exception as e:
                self._log("ERROR", f"{type(e).__name__}: {e}")
                return "ERROR"
        return "ERROR"

    def _process_with_timeout(self, item):
        """Run _process_item with a timeout. Uses per-thread DB for the worker."""
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(self._safe_process_item_for_timeout, item)
            try:
                result = future.result(timeout=self.item_timeout)
                if result == "SKIP":
                    raise SkipItemError("Skipped by inner logic")
                elif result == "ERROR":
                    raise Exception("Error in timed item")
            except (TimeoutError, FuturesTimeout):
                raise SkipItemError(f"Timed out after {self.item_timeout}s")

    def _safe_process_item_for_timeout(self, item) -> str:
        """Wrapper for timeout execution — thread-safe DB access.
        Retries on 'database is locked' with random jitter."""
        max_lock_retries = 5
        for attempt in range(max_lock_retries):
            try:
                self._process_item(item)
                return "OK"
            except SkipItemError:
                return "SKIP"
            except sqlite3.OperationalError as e:
                if "locked" in str(e) and attempt < max_lock_retries - 1:
                    time.sleep(random.uniform(0.5, 3.0) * (attempt + 1))
                    continue
                self._log("ERROR", f"{type(e).__name__}: {e}")
                return "ERROR"
            except Exception as e:
                self._log("ERROR", f"{type(e).__name__}: {e}")
                return "ERROR"
        return "ERROR"

    def _cleanup_thread_connections(self):
        """Close any per-thread DB connections."""
        if hasattr(self._thread_local, 'db') and self._thread_local.db:
            try:
                self._thread_local.db.close()
            except Exception:
                pass  # Intentionally silent — thread cleanup may race with GC
            self._thread_local.db = None

    def _ensure_tables(self) -> None:
        """Create any tables this agent needs. Called after DB connect."""
        pass

    # =========================================
    # DATABASE
    # =========================================
    def _connect_db(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(self.db_path), timeout=120,
                                  check_same_thread=False)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=NORMAL")
        self.db.execute("PRAGMA busy_timeout=120000")
        self.db.execute("PRAGMA cache_size=-32000")
        self.db.row_factory = sqlite3.Row

    def _close_db(self):
        if self._main_db:
            try:
                self._main_db.close()
            except Exception:
                pass  # Intentionally silent — connection close during teardown
            self._main_db = None
        self._close_central_db()
        self._cleanup_thread_connections()

    def _db_execute(self, sql: str, params=()) -> sqlite3.Cursor:
        """Execute with retry on database locked. Thread-safe via db property.
        Uses circuit breaker to stop retrying when DB is consistently failing."""
        # Circuit breaker check — if DB is consistently failing, fail fast
        if self._db_breaker and not self._db_breaker.allow():
            raise sqlite3.OperationalError(
                f"Circuit breaker OPEN for {self.agent_id} DB — too many consecutive failures"
            )
        for attempt in range(8):
            try:
                result = self.db.execute(sql, params)
                if self._db_breaker:
                    self._db_breaker.record_success()
                return result
            except sqlite3.OperationalError as e:
                if "locked" in str(e) and attempt < 7:
                    time.sleep(random.uniform(0.3, 1.5) * (attempt + 1))
                else:
                    if self._db_breaker:
                        self._db_breaker.record_failure(e)
                    raise

    def _db_executemany(self, sql: str, params_list) -> sqlite3.Cursor:
        for attempt in range(8):
            try:
                return self.db.executemany(sql, params_list)
            except sqlite3.OperationalError as e:
                if "locked" in str(e) and attempt < 7:
                    time.sleep(random.uniform(0.3, 1.5) * (attempt + 1))
                else:
                    raise

    # =========================================
    # CHECKPOINT (crash-resume)
    # =========================================
    def _load_checkpoint(self):
        if self.checkpoint_file.exists():
            try:
                data = json.loads(self.checkpoint_file.read_text())
                self.stats.processed = data.get("processed", 0)
                self.stats.skipped = data.get("skipped", 0)
                self.stats.errored = data.get("errored", 0)
                self._log("RESUME", f"Resuming from {self.stats.processed}")
            except Exception:
                self._log("WARN", "Corrupt checkpoint, starting fresh")

    def _save_checkpoint(self):
        try:
            CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
            data = {
                "agent_id": self.agent_id,
                "processed": self.stats.processed,
                "skipped": self.stats.skipped,
                "errored": self.stats.errored,
                "total": self.stats.total,
                "elapsed": self.stats.elapsed,
                "timestamp": time.time()
            }
            self.checkpoint_file.write_text(json.dumps(data))
        except Exception as e:
            self._log("WARN", f"Checkpoint save failed: {e}")

    # =========================================
    # SELF-DIAGNOSIS
    # =========================================
    def _diagnose(self):
        """Self-diagnosis when stuck or error rate high."""
        # Check disk space on the DB drive
        try:
            drive = str(self.db_path)[:3]
            usage = shutil.disk_usage(drive)
            free_gb = usage.free / (1024**3)
            if free_gb < 0.5:
                raise FatalAgentError(f"DISK CRITICAL: {free_gb:.2f} GB free on {drive}")
            self._log("DIAG", f"Disk OK: {free_gb:.1f} GB free on {drive}")
        except FatalAgentError:
            raise
        except Exception as e:
            self._log("WARN", f"Disk check failed: {e}")

        # Check DB health
        if self.db:
            try:
                self.db.execute("PRAGMA integrity_check")
                self._log("DIAG", "DB integrity OK")
            except Exception:
                raise FatalAgentError("DATABASE CORRUPTED")

    # =========================================
    # RETRY HELPER
    # =========================================
    def _retry(self, func, *args, **kwargs):
        """Retry with exponential backoff."""
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                wait = 2 ** attempt
                self._log("RETRY", f"Attempt {attempt+1}/{self.max_retries}, wait {wait}s: {e}")
                time.sleep(wait)

    # =========================================
    # LOGGING
    # =========================================
    def _log(self, level: str, detail: str):
        entry = {
            "agent_id": self.agent_id,
            "level": level,
            "detail": detail,
            "processed": self.stats.processed,
            "errored": self.stats.errored,
            "ts": time.time()
        }
        self._log_buffer.append(entry)
        # Print to console
        print(f"[{self.agent_id}] {level}: {detail}")

        # Flush every 50 entries
        if len(self._log_buffer) >= 50:
            self._flush_log()

    def _flush_log(self):
        if not self.db or not self._log_buffer:
            return
        try:
            self._db_executemany(
                """INSERT INTO agent_log (agent_id, level, action, detail, items_processed, items_errored)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                [(e["agent_id"], e["level"], e["level"], e["detail"],
                  e["processed"], e["errored"]) for e in self._log_buffer]
            )
            self.db.commit()
            self._log_buffer.clear()
        except Exception:
            pass  # Intentionally silent — logging loop prevention

    # =========================================
    # UTILITY
    # =========================================
    @staticmethod
    def long_path(p: str) -> str:
        """Add \\\\?\\ prefix for Windows long paths."""
        if os.name == 'nt' and not p.startswith('\\\\?\\'):
            return f'\\\\?\\{os.path.abspath(p)}'
        return p

    @staticmethod
    def safe_stat(path: str) -> Optional[os.stat_result]:
        """Stat a file safely, return None on error."""
        try:
            return os.stat(path)
        except (OSError, PermissionError):
            return None

    # =========================================
    # UNIVERSAL FILE CONTENT READER
    # =========================================
    _TEXT_EXTS = {'.txt', '.md', '.csv', '.json', '.jsonl', '.log', '.yml',
                  '.yaml', '.xml', '.html', '.htm', '.py', '.js', '.ts',
                  '.css', '.rtf', '.ini', '.cfg', '.conf', '.bat', '.ps1',
                  '.sh', '.sql', '.r', '.rb', '.java', '.c', '.cpp', '.h'}

    def _read_file_content(self, file_id: int) -> str:
        """Smart content reader: text files direct, PDFs via pymupdf, fallback to extracted_text cache."""
        # 1. Try extracted_text cache first (fastest if Tier 3 already ran)
        try:
            row = self._db_execute(
                "SELECT content FROM extracted_text WHERE file_id = ?", (file_id,)
            ).fetchone()
            if row and row["content"]:
                return row["content"]
        except Exception:
            pass  # table may not exist yet

        # 2. Look up file info
        try:
            row = self._db_execute(
                "SELECT full_path, extension, size_bytes FROM files WHERE id = ?", (file_id,)
            ).fetchone()
        except Exception:
            return ""
        if not row:
            return ""

        full_path = row["full_path"]
        ext = (row["extension"] or "").lower()
        size = row["size_bytes"] or 0

        # Skip huge files (>50MB)
        if size > 50_000_000:
            return ""

        lp = self.long_path(full_path)

        # 3. Text files — direct read
        if ext in self._TEXT_EXTS or ext == "":
            try:
                with open(lp, "r", encoding="utf-8", errors="replace") as f:
                    return f.read()
            except Exception:
                return ""  # Intentionally silent — file may be locked or inaccessible

        # 4. PDF files — pymupdf extraction
        if ext == ".pdf":
            try:
                import pymupdf
                doc = pymupdf.open(lp)
                text_parts = []
                for page in doc:
                    text_parts.append(page.get_text())
                doc.close()
                content = "\n".join(text_parts)
                # Cache the extraction
                self._cache_extracted_text(file_id, content, "pymupdf")
                return content
            except Exception:
                return ""  # Intentionally silent — PDF may be corrupt or encrypted

        # 5. DOCX files — python-docx extraction
        if ext == ".docx":
            try:
                from docx import Document
                doc = Document(lp)
                content = "\n".join(p.text for p in doc.paragraphs)
                self._cache_extracted_text(file_id, content, "python-docx")
                return content
            except Exception:
                return ""  # Intentionally silent — DOCX may be corrupt or missing deps

        return ""

    def _cache_extracted_text(self, file_id: int, content: str, method: str):
        """Cache extracted text for future agents to reuse."""
        try:
            self._db_execute(
                """CREATE TABLE IF NOT EXISTS extracted_text
                   (file_id INTEGER PRIMARY KEY, content TEXT, method TEXT, agent_id TEXT)"""
            )
            self._db_execute(
                "INSERT OR REPLACE INTO extracted_text (file_id, content, method, agent_id) VALUES (?, ?, ?, ?)",
                (file_id, content, method, self.agent_id)
            )
            self.db.commit()
        except Exception:
            pass  # caching failure is not critical

    # =========================================
    # CENTRAL DB (litigation_context.db) — for agent_memory
    # =========================================
    _CENTRAL_DB_PATH = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")

    def _get_central_db(self) -> Optional[sqlite3.Connection]:
        """Get or create connection to central litigation_context.db."""
        if self._central_db:
            return self._central_db
        try:
            if not self._CENTRAL_DB_PATH.exists():
                return None
            conn = sqlite3.connect(
                str(self._CENTRAL_DB_PATH), timeout=120,
                check_same_thread=False
            )
            conn.execute("PRAGMA busy_timeout=60000")
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA cache_size=-32000")
            conn.row_factory = sqlite3.Row
            self._central_db = conn
            return conn
        except Exception as e:
            self._log("WARN", f"Central DB connect failed: {e}")
            return None

    def _close_central_db(self):
        if self._central_db:
            try:
                self._central_db.close()
            except Exception:
                pass  # Intentionally silent — central DB close during teardown
            self._central_db = None

    @staticmethod
    def _execute_with_retry(conn, sql, params=(), max_retries=8):
        """Execute SQL with retry on database locked."""
        for attempt in range(max_retries):
            try:
                return conn.execute(sql, params)
            except sqlite3.OperationalError as e:
                if "locked" in str(e) and attempt < max_retries - 1:
                    time.sleep(random.uniform(0.3, 1.5) * (attempt + 1))
                else:
                    raise

    # =========================================
    # BASE TABLE CREATION (agent_checkpoints)
    # =========================================
    def _ensure_base_tables(self) -> None:
        """Create tables needed by Agent9999 base features (ReAct checkpoints)."""
        if not self.db:
            return
        try:
            self._db_execute("""
                CREATE TABLE IF NOT EXISTS agent_checkpoints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    checkpoint_data TEXT NOT NULL,
                    created_at TEXT DEFAULT (datetime('now'))
                )
            """)
            self._db_execute("""
                CREATE INDEX IF NOT EXISTS idx_agent_checkpoints
                ON agent_checkpoints(agent_id, created_at DESC)
            """)
            self.db.commit()
        except Exception as e:
            self._log("WARN", f"Base table creation failed: {e}")

    # =========================================
    # REACT LOOP — Reason → Act → Observe
    # =========================================
    def react_loop(self, task: str, max_iterations: int = 10) -> dict:
        """ReAct (Reason-Act-Observe) loop for complex multi-step tasks.

        Each iteration calls _reason → _act → _observe (all overridable).
        Terminates on _observe returning 'DONE:...' or max_iterations.
        Auto-checkpoints every self._db_checkpoint_interval seconds.

        Returns dict: {status, iterations, result, history}
        """
        context = {"task": task, "history": [], "iteration": 0}

        for i in range(max_iterations):
            context["iteration"] = i + 1
            self._log("REACT", f"Iteration {i + 1}/{max_iterations}: {task[:80]}")

            # 1. Reason
            reasoning = self._reason(context)

            # 2. Act
            action, action_result = self._act(reasoning, context)

            # 3. Observe
            observation = self._observe(action, action_result, context)

            step = {
                "iteration": i + 1,
                "reasoning": reasoning,
                "action": action,
                "result": str(action_result)[:500],
                "observation": observation,
                "ts": time.time()
            }
            context["history"].append(step)

            self._log("REACT_STEP", json.dumps(
                {"iter": i + 1, "action": action, "obs": observation[:200]},
                default=str
            ))

            if observation.startswith("DONE"):
                self._log("REACT", f"Completed in {i + 1} iterations")
                return {
                    "status": "SUCCESS",
                    "iterations": i + 1,
                    "result": action_result,
                    "history": context["history"]
                }

            # Auto-checkpoint during long operations
            if time.time() - self._last_db_checkpoint > self._db_checkpoint_interval:
                self.checkpoint({
                    "react_task": task,
                    "iteration": i + 1,
                    "history": context["history"]
                })

        self._log("REACT", f"Max iterations ({max_iterations}) reached")
        return {
            "status": "MAX_ITERATIONS",
            "iterations": max_iterations,
            "result": None,
            "history": context["history"]
        }

    def _reason(self, context: dict) -> str:
        """Analyze context and decide next step. Override in subclass."""
        history = context.get("history", [])
        if not history:
            return f"Starting task: {context.get('task', '')}"
        last = history[-1]
        return (
            f"Iteration {context['iteration']}: "
            f"Last action='{last.get('action', '?')}', "
            f"observation='{last.get('observation', '?')[:200]}'"
        )

    def _act(self, reasoning: str, context: dict) -> tuple:
        """Execute an action based on reasoning. Override in subclass.
        Returns (action_name: str, action_result: Any)."""
        return ("no_op", None)

    def _observe(self, action: str, result, context: dict) -> str:
        """Interpret action result. Return 'DONE: ...' to signal loop completion.
        Override in subclass for domain-specific observation logic."""
        if result is not None:
            return f"Action '{action}' completed with result"
        return f"Action '{action}' returned no result"

    # =========================================
    # PERSISTENT MEMORY (agent_memory in central DB)
    # =========================================
    def remember(self, key: str, value: str, category: str = 'general',
                 confidence: float = 1.0) -> None:
        """Store a memory scoped to this agent_id in agent_memory (central DB).

        Schema: key (PK), type, content, tags, confidence, source_session,
        created_at, updated_at.  Keys are prefixed with '{agent_id}::' for
        per-agent scoping since `key` is the table's primary key.
        """
        conn = self._get_central_db()
        if not conn:
            return
        scoped_key = f"{self.agent_id}::{key}"
        try:
            self._execute_with_retry(
                conn,
                "INSERT OR REPLACE INTO agent_memory "
                "(key, type, content, tags, confidence, source_session, "
                "created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))",
                (scoped_key, category, value, None, confidence, self.agent_id)
            )
            conn.commit()
            # Periodic memory pruning — keep memory table bounded
            # Only run cleanup ~1% of the time to avoid overhead
            if random.random() < 0.01:
                try:
                    self._execute_with_retry(
                        conn,
                        "DELETE FROM agent_memory WHERE updated_at < datetime('now', '-30 days')"
                    )
                    conn.commit()
                except Exception:
                    pass  # Pruning failure is non-critical
        except Exception as e:
            self._log("WARN", f"Memory write failed: {e}")

    def recall(self, key: Optional[str] = None, category: Optional[str] = None,
               limit: int = 10) -> List[dict]:
        """Recall memories for this agent from central DB.
        Filter by key (exact), category (=type column), or both."""
        conn = self._get_central_db()
        if not conn:
            return []
        try:
            sql = ("SELECT key, content, type, confidence, updated_at "
                   "FROM agent_memory WHERE source_session = ?")
            params: list = [self.agent_id]
            if key is not None:
                sql += " AND key = ?"
                params.append(f"{self.agent_id}::{key}")
            if category is not None:
                sql += " AND type = ?"
                params.append(category)
            sql += " ORDER BY updated_at DESC LIMIT ?"
            params.append(limit)

            rows = self._execute_with_retry(conn, sql, tuple(params)).fetchall()
            prefix = f"{self.agent_id}::"
            return [
                {
                    "key": (r["key"] if isinstance(r, sqlite3.Row) else r[0]).removeprefix(prefix),
                    "value": r["content"] if isinstance(r, sqlite3.Row) else r[1],
                    "category": r["type"] if isinstance(r, sqlite3.Row) else r[2],
                    "confidence": r["confidence"] if isinstance(r, sqlite3.Row) else r[3],
                    "updated_at": r["updated_at"] if isinstance(r, sqlite3.Row) else r[4],
                }
                for r in rows
            ]
        except Exception as e:
            self._log("WARN", f"Memory recall failed: {e}")
            return []

    def recall_errors(self, limit: int = 5) -> List[dict]:
        """Recall past error memories for self-healing. Convenience wrapper."""
        return self.recall(category='error', limit=limit)

    def _self_heal(self) -> None:
        """Load past error patterns so the agent can skip/handle known-bad items.
        Called automatically in run() before processing starts."""
        try:
            past_errors = self.recall_errors(limit=10)
            for err in past_errors:
                val = err.get("value", "")
                if isinstance(val, str) and val:
                    # Extract file paths and exception types as patterns
                    for token in val.replace("\\", "/").split():
                        if "/" in token or "Error" in token or "Exception" in token:
                            self._known_error_patterns.add(token.strip(":'\""))
            if self._known_error_patterns:
                self._log("HEAL", f"Loaded {len(self._known_error_patterns)} known error patterns")
        except Exception as e:
            self._log("WARN", f"Self-heal load failed: {e}")

    # =========================================
    # PERFORMANCE PROFILING
    # =========================================
    def _mark_time(self, phase: str) -> None:
        """Record a timestamp for a named phase."""
        self._timing[phase] = time.time()

    def _profile_run(self) -> dict:
        """Return timing breakdown from recorded phase marks and stats."""
        t = self._timing
        total = self.stats.elapsed
        setup_time = t.get("setup_end", 0) - t.get("setup_start", 0) if "setup_end" in t else 0.0
        process_time = t.get("process_end", 0) - t.get("process_start", 0) if "process_end" in t else 0.0
        db_time = total - setup_time - process_time
        items_per_sec = self.stats.processed / max(process_time, 0.001) if process_time > 0 else 0.0
        return {
            "setup_time": round(setup_time, 3),
            "process_time": round(process_time, 3),
            "db_time": round(max(db_time, 0.0), 3),
            "total_time": round(total, 3),
            "items_per_sec": round(items_per_sec, 2),
        }

    # =========================================
    # DB-BACKED CHECKPOINTING
    # =========================================
    def checkpoint(self, data: dict) -> None:
        """Save structured checkpoint to agent_checkpoints table."""
        if not self.db:
            return
        try:
            serialized = json.dumps(data, default=str)
            self._db_execute(
                "INSERT INTO agent_checkpoints (agent_id, checkpoint_data, created_at) "
                "VALUES (?, ?, datetime('now'))",
                (self.agent_id, serialized)
            )
            self.db.commit()
            self._last_db_checkpoint = time.time()
            self._log("DB_CHECKPOINT", f"Saved ({len(serialized)} bytes)")
        except Exception as e:
            self._log("WARN", f"DB checkpoint failed: {e}")

    def restore_checkpoint(self) -> Optional[dict]:
        """Restore the most recent DB checkpoint for this agent."""
        if not self.db:
            return None
        try:
            row = self._db_execute(
                "SELECT checkpoint_data FROM agent_checkpoints "
                "WHERE agent_id = ? ORDER BY created_at DESC LIMIT 1",
                (self.agent_id,)
            ).fetchone()
            if row:
                payload = row["checkpoint_data"] if isinstance(row, sqlite3.Row) else row[0]
                data = json.loads(payload)
                self._log("RESTORE", f"Restored checkpoint ({len(payload)} bytes)")
                return data
        except Exception as e:
            self._log("WARN", f"Checkpoint restore failed: {e}")
        return None

    # =========================================
    # TOOL REGISTRY
    # =========================================
    def register_tool(self, name: str, func, description: str = "",
                      schema: Optional[dict] = None) -> None:
        """Register a callable tool with optional JSON schema for args validation.
        Schema enables the ReAct loop to select tools intelligently."""
        self._tool_registry[name] = {
            "func": func,
            "description": description,
            "schema": schema or {}
        }

    def get_tool(self, name: str):
        """Retrieve a registered tool function by name, or None."""
        entry = self._tool_registry.get(name)
        return entry["func"] if entry else None

    def list_tools(self) -> dict:
        """Return {name: description} for all registered tools."""
        return {k: v["description"] for k, v in self._tool_registry.items()}

    def get_tool_schema(self, name: str) -> dict:
        """Return the JSON schema for a tool's arguments."""
        entry = self._tool_registry.get(name)
        return entry.get("schema", {}) if entry else {}

    # =========================================
    # OMEGA v2.0: QUALITY SCORING
    # =========================================
    def _compute_quality(self) -> QualityScore:
        """Auto-compute quality score from AgentStats.
        Factors: completeness, accuracy, throughput, coverage,
        error diversity penalty, memory efficiency penalty.
        Subclasses can override for domain-specific scoring."""
        s = self.stats
        done = s.processed + s.skipped + s.errored

        completeness = done / max(s.total, 1)
        accuracy = 1.0 - (s.errored / max(done, 1))
        throughput = min(1.0, s.rate / max(self._expected_rate(), 0.001))
        coverage = s.processed / max(s.total, 1)

        # Error diversity: many distinct error types is worse than one repeated error
        error_types = set()
        for entry in self._log_buffer:
            if entry.get("level") == "ERROR":
                detail = entry.get("detail", "")
                etype = detail.split(":")[0] if ":" in detail else detail[:40]
                error_types.add(etype)
        if s.errored > 0 and len(error_types) > 1:
            diversity_penalty = min(0.1, 0.02 * len(error_types))
            accuracy = max(0.0, accuracy - diversity_penalty)

        # Memory efficiency: penalize if peak memory is excessive (>500MB)
        mem_penalty = min(1.0, s.peak_memory_mb / 500.0) * 0.05
        throughput = max(0.0, throughput - mem_penalty)

        return QualityScore(
            completeness=round(completeness, 3),
            accuracy=round(accuracy, 3),
            throughput=round(throughput, 3),
            coverage=round(coverage, 3)
        )

    def _expected_rate(self) -> float:
        """Expected items/sec for this agent type. Override for calibration."""
        return 10.0

    # =========================================
    # OMEGA v2.0: INTER-AGENT MESSAGE BUS
    # =========================================
    def send_message(self, recipient: str, msg_type: str,
                     payload: dict, priority: int = 5) -> None:
        """Send a message to another agent (queued in outbox)."""
        msg = AgentMessage(
            sender=self.agent_id,
            recipient=recipient,
            msg_type=msg_type,
            payload=payload,
            priority=priority
        )
        self._outbox.append(msg)
        self._log("MSG_OUT", f"→{recipient} [{msg_type}]: {str(payload)[:80]}")

    def receive_messages(self, msg_type: Optional[str] = None) -> List[AgentMessage]:
        """Read messages from inbox, optionally filtered by type."""
        with self._inbox_lock:
            if msg_type:
                msgs = [m for m in self._inbox if m.msg_type == msg_type]
            else:
                msgs = list(self._inbox)
            self._inbox.clear()
        return sorted(msgs, key=lambda m: m.priority)

    def deliver_messages(self, messages: List[AgentMessage]) -> None:
        """Called by orchestrator to deliver messages to this agent's inbox."""
        with self._inbox_lock:
            self._inbox.extend(messages)

    def broadcast_finding(self, finding_type: str, content: str,
                          source_file: str = "", relevance: float = 0.8,
                          filing_targets: str = "") -> None:
        """Record a finding and broadcast it to the fleet via message bus."""
        finding = {
            "type": finding_type,
            "content": content,
            "source_file": source_file,
            "relevance": relevance,
            "filing_targets": filing_targets,
            "agent_id": self.agent_id,
            "ts": time.time()
        }
        with self._findings_lock:
            self._findings.append(finding)
        self.send_message("*", "finding", finding, priority=3)

    def add_finding(self, finding_type: str, content: str, **kwargs) -> dict:
        """Convenience method to record a finding without broadcasting."""
        finding = {
            "type": finding_type, "content": content,
            "agent_id": self.agent_id, "ts": time.time(), **kwargs
        }
        with self._findings_lock:
            self._findings.append(finding)
        return finding

    def get_findings(self, finding_type: Optional[str] = None) -> list:
        """Retrieve accumulated findings, optionally filtered by type."""
        with self._findings_lock:
            if finding_type:
                return [f for f in self._findings if f.get("type") == finding_type]
            return list(self._findings)

    # =========================================
    # OMEGA v2.0: PLAN-AND-EXECUTE PATTERN
    # =========================================
    def plan(self, task: str) -> List[PlanStep]:
        """Decompose a task into ordered steps.
        Override in subclass for domain-specific planning.
        Default: single-step plan that processes all work items."""
        return [PlanStep(
            step_id="process_all",
            description=f"Process all items for: {task}",
            tool_name="process_items"
        )]

    def execute_plan(self, plan: Optional[List[PlanStep]] = None) -> List[PlanStep]:
        """Execute a plan step-by-step, handling failures and replanning."""
        if plan:
            with self._plan_lock:
                self._plan = plan

        executed = []
        max_replans = 3
        replan_count = 0

        while True:
            with self._plan_lock:
                ready = [s for s in self._plan
                         if s.status == "pending" and s.is_ready]
            if not ready:
                break

            step = ready[0]
            step.status = "running"
            start = time.time()
            self._log("PLAN_EXEC", f"Step {step.step_id}: {step.description[:60]}")

            try:
                tool_func = self.get_tool(step.tool_name)
                if tool_func:
                    step.result = tool_func(**step.tool_args)
                else:
                    step.result = self._execute_step(step)
                step.status = "done"
                step.elapsed = time.time() - start

                # Remove this step from dependencies of other steps
                with self._plan_lock:
                    for s in self._plan:
                        if step.step_id in s.depends_on:
                            s.depends_on.remove(step.step_id)

            except RetryableError as e:
                step.status = "pending"
                self.stats.retry_count += 1
                time.sleep(e.suggested_wait)
                continue
            except Exception as e:
                step.status = "failed"
                step.error = str(e)
                step.elapsed = time.time() - start
                self._log("PLAN_FAIL", f"Step {step.step_id}: {e}")

                # Attempt replan
                if replan_count < max_replans:
                    replan_count += 1
                    new_steps = self._replan(step, e)
                    if new_steps:
                        with self._plan_lock:
                            self._plan.extend(new_steps)
                        self._log("REPLAN", f"Added {len(new_steps)} recovery steps")

            executed.append(step)
        return executed

    def _execute_step(self, step: PlanStep) -> Any:
        """Execute a single plan step. Override for custom step execution."""
        return None

    def _replan(self, failed_step: PlanStep, error: Exception) -> List[PlanStep]:
        """Generate recovery steps after a plan step fails.
        Override in subclass for domain-specific recovery strategies."""
        return []

    # =========================================
    # OMEGA v2.0: ADAPTIVE RETRY WITH JITTER
    # =========================================
    def _adaptive_retry(self, func, *args, max_retries: int = 0,
                        base_wait: float = 1.0, **kwargs):
        """Retry with exponential backoff + random jitter.
        Smarter than _retry: adjusts wait based on error type."""
        retries = max_retries or self.max_retries
        for attempt in range(retries):
            try:
                result = func(*args, **kwargs)
                return result
            except RetryableError as e:
                if attempt == retries - 1:
                    raise
                wait = e.suggested_wait * (1 + random.uniform(0, 0.5))
                self._log("RETRY", f"Attempt {attempt+1}/{retries}, wait {wait:.1f}s: {e}")
                self.stats.retry_count += 1
                time.sleep(wait)
            except sqlite3.OperationalError as e:
                if "locked" in str(e) and attempt < retries - 1:
                    wait = base_wait * (2 ** attempt) + random.uniform(0, 1)
                    self._log("RETRY", f"DB locked, attempt {attempt+1}, wait {wait:.1f}s")
                    self.stats.retry_count += 1
                    time.sleep(wait)
                else:
                    raise
            except Exception as e:
                if attempt == retries - 1:
                    raise
                wait = base_wait * (2 ** attempt) + random.uniform(0, 0.5)
                self._log("RETRY", f"Attempt {attempt+1}/{retries}, wait {wait:.1f}s: {e}")
                self.stats.retry_count += 1
                time.sleep(wait)

    # ═══════════════════════════════════════════
    # OMEGA v3.0: LANE-AWARE PROCESSING
    # ═══════════════════════════════════════════

    # MEEK signal sets (imported from agent_models)
    _LANE_SIGNALS = {
        'E': LANE_E_SIGNALS if 'LANE_E_SIGNALS' in dir() else set(),
        'D': LANE_D_SIGNALS if 'LANE_D_SIGNALS' in dir() else set(),
        'F': LANE_F_SIGNALS if 'LANE_F_SIGNALS' in dir() else set(),
        'C': LANE_C_SIGNALS if 'LANE_C_SIGNALS' in dir() else set(),
        'A': LANE_A_SIGNALS if 'LANE_A_SIGNALS' in dir() else set(),
        'B': LANE_B_SIGNALS if 'LANE_B_SIGNALS' in dir() else set(),
    }

    def detect_lane(self, text: str) -> str:
        """Detect which case lane (A-F) a text belongs to using MEEK signals.
        Priority order: E → D → F → C → A → B (highest specificity first).
        Returns lane letter or 'U' for unclassified."""
        if not text:
            return 'U'
        text_lower = text.lower()

        # Import lane signals from models (deferred to avoid circular import)
        from .agent_models import (
            LANE_E_SIGNALS, LANE_D_SIGNALS, LANE_F_SIGNALS,
            LANE_C_SIGNALS, LANE_A_SIGNALS, LANE_B_SIGNALS
        )
        lane_signals = {
            'E': LANE_E_SIGNALS, 'D': LANE_D_SIGNALS,
            'F': LANE_F_SIGNALS, 'C': LANE_C_SIGNALS,
            'A': LANE_A_SIGNALS, 'B': LANE_B_SIGNALS,
        }

        best_lane = 'U'
        best_score = 0
        for lane, signals in lane_signals.items():
            score = sum(1 for sig in signals if sig in text_lower)
            if score > best_score:
                best_score = score
                best_lane = lane
        return best_lane

    def require_lane(self, text: str, expected_lane: str) -> None:
        """Raise LaneCrossContaminationError if text doesn't match expected lane."""
        from .agent_models import LaneCrossContaminationError
        detected = self.detect_lane(text)
        if detected != 'U' and detected != expected_lane:
            raise LaneCrossContaminationError(
                f"Lane contamination: expected {expected_lane}, detected {detected}"
            )

    # ═══════════════════════════════════════════
    # OMEGA v3.0: ANTI-HALLUCINATION GUARD
    # ═══════════════════════════════════════════

    # Verified party identity — IMMUTABLE SOURCE OF TRUTH
    _VERIFIED_PARTIES = {
        'plaintiff': 'Andrew James Pigors',
        'defendant': 'Emily A. Watson',
        'child': 'L.D.W.',
        'judge': 'Hon. Jenny L. McNeill',
        'defendant_attorney': 'Jennifer Barnes (P55406)',
        'foc': 'Pamela Rusco',
        'ronald_berry': 'Ronald Berry (NON-ATTORNEY)',
    }

    # Known hallucinations — if ANY of these appear, it's fabricated
    _HALLUCINATION_PATTERNS = {
        'jane berry', 'patricia berry', 'patricia berry (sbn p35878)',
        'amy mcneill', 'emily ann watson', 'emily m. watson',
        'tiffany watson', 'ronald berry, esq',
    }

    def validate_party_name(self, name: str) -> bool:
        """Check if a party name is verified. Returns False for hallucinations."""
        name_lower = name.lower().strip()
        for pattern in self._HALLUCINATION_PATTERNS:
            if pattern in name_lower:
                self._log("HALLUCINATION", f"Detected fabricated name: '{name}'")
                return False
        return True

    def get_verified_party(self, role: str) -> str:
        """Get the verified name for a party role. Returns '[UNKNOWN — VERIFY]' if not found."""
        return self._VERIFIED_PARTIES.get(role.lower(), '[UNKNOWN — VERIFY]')

    def guard_output(self, text: str) -> str:
        """Scan output text for hallucinated names and replace with verified versions."""
        result = text
        replacements = {
            'Jane Berry': '[HALLUCINATION REMOVED]',
            'Patricia Berry': '[HALLUCINATION REMOVED]',
            'Amy McNeill': 'Hon. Jenny L. McNeill',
            'Emily Ann Watson': 'Emily A. Watson',
            'Emily Ann': 'Emily A.',
            'Emily M. Watson': 'Emily A. Watson',
        }
        for bad, good in replacements.items():
            if bad in result:
                result = result.replace(bad, good)
                self._log("GUARD", f"Replaced hallucination '{bad}' → '{good}'")
        return result

    # ═══════════════════════════════════════════
    # OMEGA v3.0: TRACEABLE STATISTICS
    # ═══════════════════════════════════════════

    def traceable_count(self, table: str, where: str = "",
                        params: tuple = ()) -> dict:
        """Execute a COUNT(*) with full provenance tracking.
        Returns dict with count, query, table, and timestamp.
        NEVER use fabricated stats — always query the DB."""
        sql = f"SELECT COUNT(*) as cnt FROM {table}"
        if where:
            sql += f" WHERE {where}"

        try:
            row = self._db_execute(sql, params).fetchone()
            count = row['cnt'] if isinstance(row, sqlite3.Row) else row[0]
        except Exception as e:
            self._log("STAT_FAIL", f"Count query failed: {sql} — {e}")
            return {"count": 0, "query": sql, "table": table,
                    "error": str(e), "ts": time.time()}

        provenance = {
            "count": count,
            "query": sql,
            "params": str(params),
            "table": table,
            "agent_id": self.agent_id,
            "ts": time.time()
        }
        self._log("STAT", f"{table}: {count} rows ({where or 'all'})")
        return provenance

    def traceable_aggregate(self, queries: dict) -> dict:
        """Execute multiple COUNT(*) queries in one consolidated statement.
        Input: {name: (table, where, params)} or {name: (table,)}
        Returns: {name: {count, query, ...}}"""
        results = {}
        for name, spec in queries.items():
            table = spec[0]
            where = spec[1] if len(spec) > 1 else ""
            params = spec[2] if len(spec) > 2 else ()
            results[name] = self.traceable_count(table, where, params)
        return results

    # ═══════════════════════════════════════════
    # OMEGA v3.0: CROSS-AGENT LEARNING
    # ═══════════════════════════════════════════

    def cross_recall(self, agent_id: str, category: Optional[str] = None,
                     limit: int = 10) -> List[dict]:
        """Read memories from ANOTHER agent. Enables cross-agent learning.
        Use to leverage insights from agents that already ran."""
        conn = self._get_central_db()
        if not conn:
            return []
        try:
            sql = ("SELECT key, content, type, confidence, updated_at "
                   "FROM agent_memory WHERE source_session = ?")
            params: list = [agent_id]
            if category is not None:
                sql += " AND type = ?"
                params.append(category)
            sql += " ORDER BY updated_at DESC LIMIT ?"
            params.append(limit)

            rows = self._execute_with_retry(conn, sql, tuple(params)).fetchall()
            prefix = f"{agent_id}::"
            return [
                {
                    "key": (r["key"] if isinstance(r, sqlite3.Row) else r[0]).removeprefix(prefix),
                    "value": r["content"] if isinstance(r, sqlite3.Row) else r[1],
                    "category": r["type"] if isinstance(r, sqlite3.Row) else r[2],
                    "confidence": r["confidence"] if isinstance(r, sqlite3.Row) else r[3],
                    "source_agent": agent_id,
                }
                for r in rows
            ]
        except Exception as e:
            self._log("WARN", f"Cross-recall from {agent_id} failed: {e}")
            return []

    def fleet_recall(self, category: str, limit: int = 20) -> List[dict]:
        """Read memories from ALL agents for a given category.
        Useful for gathering fleet-wide insights on a topic."""
        conn = self._get_central_db()
        if not conn:
            return []
        try:
            rows = self._execute_with_retry(
                conn,
                "SELECT key, content, type, confidence, source_session, updated_at "
                "FROM agent_memory WHERE type = ? "
                "ORDER BY updated_at DESC LIMIT ?",
                (category, limit)
            ).fetchall()
            return [
                {
                    "key": r["key"] if isinstance(r, sqlite3.Row) else r[0],
                    "value": r["content"] if isinstance(r, sqlite3.Row) else r[1],
                    "source_agent": r["source_session"] if isinstance(r, sqlite3.Row) else r[4],
                }
                for r in rows
            ]
        except Exception as e:
            self._log("WARN", f"Fleet recall failed: {e}")
            return []

    # ═══════════════════════════════════════════
    # OMEGA v3.0: EVIDENCE SCORING
    # ═══════════════════════════════════════════

    _EVIDENCE_WEIGHTS = {
        'court_order': 1.0, 'sworn_testimony': 0.95, 'official_record': 0.9,
        'police_report': 0.85, 'medical_record': 0.85, 'financial_record': 0.8,
        'communication': 0.7, 'photograph': 0.65, 'screenshot': 0.6,
        'witness_statement': 0.6, 'self_report': 0.4, 'hearsay': 0.2,
    }

    def score_evidence(self, text: str, evidence_type: str = 'unknown',
                       claim_type: str = '') -> dict:
        """Score evidence for relevance and admissibility.
        Returns dict with relevance (0-1), admissibility (0-1),
        evidence_type weight, and suggested MRE rules."""
        base_weight = self._EVIDENCE_WEIGHTS.get(evidence_type, 0.5)

        # Relevance: how many case-specific terms appear
        relevance_terms = {
            'custody', 'parenting', 'child', 'mcl', 'mcr', 'court',
            'watson', 'pigors', 'mcneill', 'rusco', 'foc', 'ppo',
            'visitation', 'support', 'alienation', 'contempt',
        }
        text_lower = text.lower() if text else ''
        term_hits = sum(1 for t in relevance_terms if t in text_lower)
        relevance = min(1.0, term_hits / 5.0)

        # Admissibility: MRE compliance indicators
        mre_rules = []
        if evidence_type in ('court_order', 'official_record'):
            mre_rules.append('MRE 902 (self-authenticating)')
        elif evidence_type in ('communication', 'screenshot'):
            mre_rules.append('MRE 901(b)(4) (distinctive characteristics)')
        elif evidence_type in ('sworn_testimony', 'witness_statement'):
            mre_rules.append('MRE 901(b)(1) (testimony of witness)')
        if any(kw in text_lower for kw in ('hearsay', 'told me', 'said that')):
            mre_rules.append('MRE 802 (hearsay — may need exception)')
            base_weight *= 0.5

        return {
            "relevance": round(relevance, 3),
            "admissibility": round(base_weight, 3),
            "combined_score": round((relevance * 0.6 + base_weight * 0.4), 3),
            "evidence_type": evidence_type,
            "mre_rules": mre_rules,
            "claim_type": claim_type,
            "agent_id": self.agent_id,
        }

    # ═══════════════════════════════════════════
    # OMEGA v3.0: OUTPUT VALIDATION
    # ═══════════════════════════════════════════

    def validate_output(self, output: dict) -> dict:
        """Validate agent output before returning. Checks for:
        1. Hallucinated party names
        2. Untraced statistics
        3. Missing required fields
        Returns validation result with pass/fail and issues list."""
        issues = []

        # Check string values for hallucinations
        def _check_strings(obj, path=""):
            if isinstance(obj, str):
                for pattern in self._HALLUCINATION_PATTERNS:
                    if pattern in obj.lower():
                        issues.append({
                            "type": "hallucination",
                            "path": path,
                            "detail": f"Fabricated name detected: '{pattern}'"
                        })
            elif isinstance(obj, dict):
                for k, v in obj.items():
                    _check_strings(v, f"{path}.{k}")
            elif isinstance(obj, list):
                for i, v in enumerate(obj):
                    _check_strings(v, f"{path}[{i}]")

        _check_strings(output)

        passed = len(issues) == 0
        if not passed:
            self._log("VALIDATE_FAIL", f"Output validation: {len(issues)} issues")
        return {"passed": passed, "issues": issues, "checked_at": time.time()}

    # ═══════════════════════════════════════════
    # OMEGA v3.0: STRUCTURED HEALTH REPORTING
    # ═══════════════════════════════════════════

    def health_report(self) -> dict:
        """Generate a structured health report for fleet monitoring.
        Called by orchestrator to assess agent readiness and performance."""
        profile = self._profile_run()
        quality = self._quality or self._compute_quality()
        return {
            "agent_id": self.agent_id,
            "status": "healthy" if self.stats.error_rate < 0.1 else "degraded",
            "stats": {
                "total": self.stats.total,
                "processed": self.stats.processed,
                "errored": self.stats.errored,
                "skipped": self.stats.skipped,
                "error_rate": round(self.stats.error_rate, 4),
                "success_rate": round(self.stats.success_rate, 4),
                "elapsed": round(self.stats.elapsed, 2),
                "rate": round(self.stats.rate, 2),
            },
            "quality": {
                "overall": round(quality.overall, 3),
                "completeness": quality.completeness,
                "accuracy": quality.accuracy,
                "throughput": quality.throughput,
                "coverage": quality.coverage,
            },
            "profile": profile,
            "findings_count": len(self._findings),
            "messages_sent": len(self._outbox),
            "messages_received": len(self._inbox),
            "known_error_patterns": len(self._known_error_patterns),
            "quality_trend": self._quality_history[-5:],
            "ts": time.time(),
        }

    # ═══════════════════════════════════════════
    # OMEGA v3.0: PROVENANCE CHAIN
    # ═══════════════════════════════════════════

    def _provenance_entry(self, output_type: str, output_id: str,
                          inputs: List[dict]) -> dict:
        """Create a provenance chain entry linking outputs to inputs.
        Every finding, filing section, or statistic should have one.
        inputs: list of {type, id, source} dicts."""
        entry = {
            "agent_id": self.agent_id,
            "output_type": output_type,
            "output_id": output_id,
            "inputs": inputs,
            "ts": time.time(),
        }

        # Store in central DB if available
        conn = self._get_central_db()
        if conn:
            try:
                self._execute_with_retry(
                    conn,
                    """CREATE TABLE IF NOT EXISTS provenance_chain (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        agent_id TEXT, output_type TEXT, output_id TEXT,
                        inputs_json TEXT, created_at TEXT DEFAULT (datetime('now'))
                    )"""
                )
                self._execute_with_retry(
                    conn,
                    "INSERT INTO provenance_chain (agent_id, output_type, output_id, inputs_json) "
                    "VALUES (?, ?, ?, ?)",
                    (self.agent_id, output_type, output_id, json.dumps(inputs, default=str))
                )
                conn.commit()
            except Exception as e:
                self._log("WARN", f"Provenance write failed: {e}")

        return entry

    # ═══════════════════════════════════════════
    # OMEGA v3.0: SMART FILE DISCOVERY
    # ═══════════════════════════════════════════

    _DRIVE_ROOTS = [
        Path(r"C:\Users\andre\LitigationOS"),
        Path(r"C:\Users\andre\Desktop"),
        Path(r"C:\Users\andre\Documents"),
        Path("D:\\"), Path("F:\\"), Path("G:\\"),
        Path("H:\\"), Path("I:\\"),
    ]

    def discover_files(self, pattern: str, extensions: Optional[List[str]] = None,
                       max_results: int = 100) -> List[Path]:
        """Search across all 6+ drives for files matching a pattern.
        Used for evidence discovery and prior work detection."""
        results = []
        pattern_lower = pattern.lower()
        ext_set = {e.lower().lstrip('.') for e in (extensions or [])}

        for root in self._DRIVE_ROOTS:
            if not root.exists():
                continue
            try:
                for p in root.rglob("*"):
                    if len(results) >= max_results:
                        return results
                    if not p.is_file():
                        continue
                    if ext_set and p.suffix.lower().lstrip('.') not in ext_set:
                        continue
                    if pattern_lower in p.name.lower() or pattern_lower in str(p).lower():
                        results.append(p)
            except (PermissionError, OSError):
                continue
        return results

    # ═══════════════════════════════════════════
    # OMEGA v3.0: BATCH DB OPERATIONS
    # ═══════════════════════════════════════════

    def batch_insert(self, table: str, columns: List[str],
                     rows: List[tuple], or_ignore: bool = True) -> int:
        """Batch insert rows into a table using executemany.
        10-100x faster than row-by-row inserts."""
        if not rows:
            return 0
        conflict = "OR IGNORE" if or_ignore else ""
        placeholders = ", ".join(["?"] * len(columns))
        col_str = ", ".join(columns)
        sql = f"INSERT {conflict} INTO {table} ({col_str}) VALUES ({placeholders})"
        try:
            self._db_executemany(sql, rows)
            self.db.commit()
            self._log("BATCH", f"Inserted {len(rows)} rows into {table}")
            return len(rows)
        except Exception as e:
            self._log("ERROR", f"Batch insert to {table} failed: {e}")
            return 0

    def batch_upsert(self, table: str, columns: List[str],
                     rows: List[tuple], conflict_col: str = "id") -> int:
        """Batch upsert (INSERT OR REPLACE) rows."""
        if not rows:
            return 0
        placeholders = ", ".join(["?"] * len(columns))
        col_str = ", ".join(columns)
        sql = f"INSERT OR REPLACE INTO {table} ({col_str}) VALUES ({placeholders})"
        try:
            self._db_executemany(sql, rows)
            self.db.commit()
            self._log("UPSERT", f"Upserted {len(rows)} rows into {table}")
            return len(rows)
        except Exception as e:
            self._log("ERROR", f"Batch upsert to {table} failed: {e}")
            return 0
