import json
import time
import datetime
from typing import Any, Dict, Optional
from collections import defaultdict

from autopilot_core.db import (
    init_db, create_job, next_job, set_job_status, get_job, log_job,
    update_health, log_tool_run, log_self_heal,
    upsert_file, upsert_artifact, create_run, update_run_status
)

class Orchestrator:
    def __init__(self):
        self.running = False
        self.current_run_id: Optional[str] = None
        init_db()  # Ensure DB is initialized on orchestrator startup
        self.job_retries = defaultdict(int)
        self.max_retries = 3 # Example max retries

        # Map job kinds to handler methods (placeholder for actual agent dispatch)
        self.job_handlers = {
            "DISCOVER_FILES": self._handle_discover_files,
            "PROCESS_FILE": self._handle_process_file,
            "DEEP_ARCHIVE_EXTRACT": self._handle_deep_archive_extract,
            "PDF_CONVERT": self._handle_pdf_convert,
            "OCR_FALLBACK": self._handle_ocr_fallback,
            "SEGMENT_MD": self._handle_segment_md,
            # Add other job kinds as they are implemented
        }

    def start_run(self, config_hash: str):
        """Starts a new run and sets the current_run_id."""
        import json
import time
import datetime
import uuid # Import uuid
from typing import Any, Dict, Optional
from collections import defaultdict

from autopilot_core.db import (
    init_db, create_job, next_job, set_job_status, get_job, log_job,
    update_health, log_tool_run, log_self_heal,
    upsert_file, upsert_artifact, create_run, update_run_status
)

class Orchestrator:
    def __init__(self):
        self.running = False
        self.current_run_id: Optional[str] = None
        init_db()  # Ensure DB is initialized on orchestrator startup
        self.job_retries = defaultdict(int)
        self.max_retries = 3 # Example max retries

        # Map job kinds to handler methods (placeholder for actual agent dispatch)
        self.job_handlers = {
            "DISCOVER_FILES": self._handle_discover_files,
            "PROCESS_FILE": self._handle_process_file,
            "DEEP_ARCHIVE_EXTRACT": self._handle_deep_archive_extract,
            "PDF_CONVERT": self._handle_pdf_convert,
            "OCR_FALLBACK": self._handle_ocr_fallback,
            "SEGMENT_MD": self._handle_segment_md,
            # Add other job kinds as they are implemented
        }

    def start_run(self, config_hash: str):
        """Starts a new run and sets the current_run_id."""
        self.current_run_id = f"RUN_{uuid.uuid4()}" # Use uuid for uniqueness
        create_run(self.current_run_id, datetime.datetime.now().isoformat(), config_hash, "running")
        print(f"Orchestrator started a new run: {self.current_run_id}")

    def complete_run(self, status: str, summary: Optional[Dict[str, Any]] = None):
        """Completes the current run with a given status."""
        if self.current_run_id:
            update_run_status(self.current_run_id, datetime.datetime.now().isoformat(), status, json.dumps(summary) if summary else None)
            print(f"Run {self.current_run_id} completed with status: {status}")
            self.current_run_id = None
        else:
            print("No active run to complete.")

    def start(self):
        self.running = True
        print("Orchestrator started. Looking for jobs...")
        while self.running:
            job = next_job()
            if job:
                self._execute_job(job)
            else:
                # print("No jobs in queue. Waiting...") # Avoid excessive output
                time.sleep(0.1) # Small sleep to prevent busy-waiting

    def stop(self):
        self.running = False
        print("Orchestrator stopped.")

    def add_job(self, kind: str, payload: Dict[str, Any]):
        job_id = create_job(kind, payload)
        print(f"Added job {job_id}: {kind}")
        return job_id

    def _execute_job(self, job: Dict[str, Any]):
        job_id = job["id"]
        job_kind = job["kind"]
        job_payload = json.loads(job["payload_json"])

        print(f"Executing job {job_id}: {job_kind} with payload {job_payload}")
        log_job(job_id, "INFO", f"Starting job {job_kind}")
        set_job_status(job_id, "running")

        try:
            handler = self.job_handlers.get(job_kind)
            if handler:
                handler(job_id, job_payload)
            else:
                # If no handler is found, explicitly fail the job and raise an error
                print(f"Unknown job kind: {job_kind}")
                log_job(job_id, "WARNING", f"Unknown job kind: {job_kind}. Marking as failed.")
                set_job_status(job_id, "failed") 
                raise ValueError(f"No handler for job kind: {job_kind}") # Trigger exception for retry/quarantine
            
            set_job_status(job_id, "completed")
            log_job(job_id, "INFO", f"Job {job_kind} completed successfully")
            print(f"Job {job_id} completed.")
            self.job_retries.pop(job_id, None) # Clear retry count on success
        except Exception as e:
            print(f"Job {job_id} failed: {e}")
            failure_type = self._classify_failure(e)
            
            # Retrieve job status safely with explicit connection closing
            job_record = get_job(job_id)
            old_status = job_record["status"] if job_record else "unknown" 

            if self.job_retries[job_id] < self.max_retries:
                self.job_retries[job_id] += 1
                new_status = "retrying"
                set_job_status(job_id, new_status)
                log_self_heal(job_id, failure_type, "Re-queueing job", old_status, new_status, datetime.datetime.now().isoformat(), str(e))
                log_job(job_id, "WARNING", f"Job {job_kind} failed, retrying ({self.job_retries[job_id]}/{self.max_retries}): {e}")
                self.add_job(job_kind, job_payload) # Re-add job to queue for retry
            else:
                new_status = "quarantined"
                set_job_status(job_id, new_status)
                log_self_heal(job_id, failure_type, "Max retries reached, quarantining job", old_status, new_status, datetime.datetime.now().isoformat(), str(e))
                log_job(job_id, "ERROR", f"Job {job_kind} quarantined after {self.max_retries} retries: {e}")
            
            update_health(f"job_{job_id}", "FAILING", last_fail_ts=datetime.datetime.now().isoformat(), last_error=str(e), fail_count=self.job_retries[job_id], remediation_taken_json=json.dumps({"action": "retry" if self.job_retries[job_id] <= self.max_retries else "quarantine"}))

    def _classify_failure(self, e: Exception) -> str:
        """Classifies an exception into a predefined failure type."""
        error_msg = str(e).lower()
        if "timeout" in error_msg:
            return "Timeout"
        if "corrupt" in error_msg or "bad zip" in error_msg:
            return "Corrupt"
        if "not supported" in error_msg:
            return "Unsupported"
        if "memory" in error_msg:
            return "OOM"
        if "permission" in error_msg:
            return "PermissionError"
        if "not found" in error_msg or "no such file" in error_msg:
            return "ToolMissing"
        return "UnknownError"

    # --- Placeholder Agent Handlers ---

    def _handle_discover_files(self, job_id: int, payload: Dict[str, Any]):
        path = payload.get("path")
        print(f"DiscoveryAgent: Simulating file discovery in {path}")
        # Simulate finding some files
        dummy_files = [
            {"file_id": "file1", "abspath": f"{path}/doc1.pdf", "size": 1024, "mtime": int(time.time()), "status": "discovered"},
            {"file_id": "file2", "abspath": f"{path}/archive.zip", "size": 2048, "mtime": int(time.time()), "status": "discovered"},
        ]
        for f in dummy_files:
            upsert_file(f["file_id"], f["abspath"], None, f["size"], f["mtime"], "document", f["status"], self.current_run_id)
            log_job(job_id, "INFO", f"Discovered file: {f['abspath']}")
            self.add_job("PROCESS_FILE", {"file_id": f["file_id"], "path": f["abspath"]})
        
        # Simulate calling an external tool
        log_tool_run(job_id, "simulated_scanner --path " + path, "1.0", "inputs_hash_123", "output_paths_abc", "stdout_log", "stderr_log", "completed", datetime.datetime.now().isoformat(), datetime.datetime.now().isoformat())
        update_health("DiscoveryAgent", "OK", last_ok_ts=datetime.datetime.now().isoformat())


    def _handle_process_file(self, job_id: int, payload: Dict[str, Any]):
        file_id = payload.get("file_id")
        path = payload.get("path")
        print(f"ProcessFileAgent: Simulating processing of {file_id} at {path}")
        log_job(job_id, "INFO", f"Processing file: {file_id}")
        upsert_artifact(f"artifact_{file_id}_raw", file_id, "raw_processing", path, 100, int(time.time()), "processed")
        update_health("ProcessFileAgent", "OK", last_ok_ts=datetime.datetime.now().isoformat())
        # Example: Add next step for PDF convert if it's a PDF
        if path.endswith(".pdf"):
            self.add_job("PDF_CONVERT", {"file_id": file_id, "path": path})

    def _handle_deep_archive_extract(self, job_id: int, payload: Dict[str, Any]):
        file_id = payload.get("file_id")
        path = payload.get("path")
        print(f"ArchiveAgent: Simulating deep archive extraction for {file_id} at {path}")
        log_job(job_id, "INFO", f"Extracting archive: {file_id}")
        # Simulate extraction and finding new files
        new_files = [
            {"file_id": "nested_file_1", "abspath": "extracted/nested_doc.txt", "size": 500, "mtime": int(time.time()), "status": "extracted"},
        ]
        for f in new_files:
            upsert_file(f["file_id"], f["abspath"], f"archive:{file_id}", f["size"], f["mtime"], "text", f["status"], self.current_run_id)
            self.add_job("PROCESS_FILE", {"file_id": f["file_id"], "path": f["abspath"]})
        upsert_artifact(f"artifact_{file_id}_extracted", file_id, "archive_extraction", path, 5000, int(time.time()), "extracted")
        update_health("ArchiveAgent", "OK", last_ok_ts=datetime.datetime.now().isoformat())

    def _handle_pdf_convert(self, job_id: int, payload: Dict[str, Any]):
        file_id = payload.get("file_id")
        path = payload.get("path")
        print(f"ConversionAgent: Simulating PDF conversion for {file_id} at {path}")
        log_job(job_id, "INFO", f"Converting PDF: {file_id}")
        # Simulate conversion output
        converted_path = f"converted/{file_id}.md"
        upsert_artifact(f"artifact_{file_id}_md", file_id, "pdf_conversion", converted_path, 1500, int(time.time()), "converted")
        update_health("ConversionAgent", "OK", last_ok_ts=datetime.datetime.now().isoformat())
        # Add next step for segmentation
        self.add_job("SEGMENT_MD", {"file_id": file_id, "path": converted_path})

    def _handle_ocr_fallback(self, job_id: int, payload: Dict[str, Any]):
        file_id = payload.get("file_id")
        path = payload.get("path")
        print(f"OCRAgent: Simulating OCR fallback for {file_id} at {path}")
        log_job(job_id, "INFO", f"Performing OCR: {file_id}")
        # Simulate OCR output
        ocr_path = f"ocr/{file_id}.txt"
        upsert_artifact(f"artifact_{file_id}_ocr", file_id, "ocr_processing", ocr_path, 800, int(time.time()), "ocr_done")
        update_health("OCRAgent", "OK", last_ok_ts=datetime.datetime.now().isoformat())
        # After OCR, re-attempt conversion or proceed
        self.add_job("PDF_CONVERT", {"file_id": file_id, "path": path, "ocr_applied": True})


    def _handle_segment_md(self, job_id: int, payload: Dict[str, Any]):
        file_id = payload.get("file_id")
        path = payload.get("path")
        print(f"ShardAgent: Simulating markdown segmentation for {file_id} at {path}")
        log_job(job_id, "INFO", f"Segmenting MD: {file_id}")
        # Simulate creating segments
        segment_path = f"segments/{file_id}_part1.md"
        upsert_artifact(f"artifact_{file_id}_segment1", file_id, "segmentation", segment_path, 700, int(time.time()), "segmented")
        update_health("ShardAgent", "OK", last_ok_ts=datetime.datetime.now().isoformat())
        # Finalize processing for this file for now
    
    def close_connections(self):
        """Closes any open connections held by the orchestrator."""
        # In this current setup, db.py manages connections per call.
        # If the Orchestrator itself held a long-lived connection, it would be closed here.
        pass


if __name__ == "__main__":
    orchestrator = Orchestrator()
    orchestrator.start_run(config_hash="test_config_123")

    # Example usage:
    orchestrator.add_job("DISCOVER_FILES", {"path": "H:\\inputs"})
    orchestrator.add_job("DEEP_ARCHIVE_EXTRACT", {"file_id": "archive1", "path": "H:\\inputs\\archive.zip"})
    orchestrator.add_job("PDF_CONVERT", {"file_id": "pdf_doc_id", "path": "H:\\inputs\\scanned.pdf"})
    # Example of a job that might fail and retry
    # orchestrator.add_job("PROCESS_FILE", {"file_id": "failing_file", "path": "non_existent.txt"})
    
    try:
        orchestrator.start()
    except KeyboardInterrupt:
        print("\nOrchestrator interrupted by user.")
    finally:
        # Check if there's an active run before trying to complete it
        if orchestrator.current_run_id:
            orchestrator.complete_run("interrupted")
        orchestrator.stop()
        orchestrator.close_connections()
        create_run(self.current_run_id, datetime.datetime.now().isoformat(), config_hash, "running")
        print(f"Orchestrator started a new run: {self.current_run_id}")

    def complete_run(self, status: str, summary: Optional[Dict[str, Any]] = None):
        """Completes the current run with a given status."""
        if self.current_run_id:
            update_run_status(self.current_run_id, datetime.datetime.now().isoformat(), status, json.dumps(summary) if summary else None)
            print(f"Run {self.current_run_id} completed with status: {status}")
            self.current_run_id = None
        else:
            print("No active run to complete.")

    def start(self):
        self.running = True
        print("Orchestrator started. Looking for jobs...")
        while self.running:
            job = next_job()
            if job:
                self._execute_job(job)
            else:
                # print("No jobs in queue. Waiting...") # Avoid excessive output
                time.sleep(1) # Wait a bit before checking again

    def stop(self):
        self.running = False
        print("Orchestrator stopped.")

    def add_job(self, kind: str, payload: Dict[str, Any]):
        job_id = create_job(kind, payload)
        print(f"Added job {job_id}: {kind}")
        return job_id

    def _execute_job(self, job: Dict[str, Any]):
        job_id = job["id"]
        job_kind = job["kind"]
        job_payload = json.loads(job["payload_json"])

        print(f"Executing job {job_id}: {job_kind} with payload {job_payload}")
        log_job(job_id, "INFO", f"Starting job {job_kind}")
        set_job_status(job_id, "running")

        try:
            handler = self.job_handlers.get(job_kind)
            if handler:
                handler(job_id, job_payload)
            else:
                print(f"Unknown job kind: {job_kind}")
                log_job(job_id, "WARNING", f"Unknown job kind: {job_kind}")
                set_job_status(job_id, "failed") # Mark as failed if no handler
            
            set_job_status(job_id, "completed")
            log_job(job_id, "INFO", f"Job {job_kind} completed successfully")
            print(f"Job {job_id} completed.")
            self.job_retries.pop(job_id, None) # Clear retry count on success
        except Exception as e:
            print(f"Job {job_id} failed: {e}")
            failure_type = self._classify_failure(e)
            old_status = get_job(job_id)("status") # Get current status before remediation

            if self.job_retries[job_id] < self.max_retries:
                self.job_retries[job_id] += 1
                new_status = "retrying"
                set_job_status(job_id, new_status)
                log_self_heal(job_id, failure_type, "Re-queueing job", old_status, new_status, datetime.datetime.now().isoformat(), str(e))
                log_job(job_id, "WARNING", f"Job {job_kind} failed, retrying ({self.job_retries[job_id]}/{self.max_retries}): {e}")
                self.add_job(job_kind, job_payload) # Re-add job to queue for retry
            else:
                new_status = "quarantined"
                set_job_status(job_id, new_status)
                log_self_heal(job_id, failure_type, "Max retries reached, quarantining job", old_status, new_status, datetime.datetime.now().isoformat(), str(e))
                log_job(job_id, "ERROR", f"Job {job_kind} quarantined after {self.max_retries} retries: {e}")
            
            update_health(f"job_{job_id}", "FAILING", last_fail_ts=datetime.datetime.now().isoformat(), last_error=str(e), fail_count=self.job_retries[job_id], remediation_taken_json=json.dumps({"action": "retry" if self.job_retries[job_id] <= self.max_retries else "quarantine"}))


    def _classify_failure(self, e: Exception) -> str:
        """Classifies an exception into a predefined failure type."""
        error_msg = str(e).lower()
        if "timeout" in error_msg:
            return "Timeout"
        if "corrupt" in error_msg or "bad zip" in error_msg:
            return "Corrupt"
        if "not supported" in error_msg:
            return "Unsupported"
        if "memory" in error_msg:
            return "OOM"
        if "permission" in error_msg:
            return "PermissionError"
        if "not found" in error_msg or "no such file" in error_msg:
            return "ToolMissing"
        return "UnknownError"

    # --- Placeholder Agent Handlers ---

    def _handle_discover_files(self, job_id: int, payload: Dict[str, Any]):
        path = payload.get("path")
        print(f"DiscoveryAgent: Simulating file discovery in {path}")
        # Simulate finding some files
        dummy_files = [
            {"file_id": "file1", "abspath": f"{path}/doc1.pdf", "size": 1024, "mtime": int(time.time()), "status": "discovered"},
            {"file_id": "file2", "abspath": f"{path}/archive.zip", "size": 2048, "mtime": int(time.time()), "status": "discovered"},
        ]
        for f in dummy_files:
            upsert_file(f["file_id"], f["abspath"], None, f["size"], f["mtime"], "document", f["status"], self.current_run_id)
            log_job(job_id, "INFO", f"Discovered file: {f['abspath']}")
            self.add_job("PROCESS_FILE", {"file_id": f["file_id"], "path": f["abspath"]})
        
        # Simulate calling an external tool
        log_tool_run(job_id, "simulated_scanner --path " + path, "1.0", "inputs_hash_123", "output_paths_abc", "stdout_log", "stderr_log", "completed", datetime.datetime.now().isoformat(), datetime.datetime.now().isoformat())
        update_health("DiscoveryAgent", "OK", last_ok_ts=datetime.datetime.now().isoformat())


    def _handle_process_file(self, job_id: int, payload: Dict[str, Any]):
        file_id = payload.get("file_id")
        path = payload.get("path")
        print(f"ProcessFileAgent: Simulating processing of {file_id} at {path}")
        log_job(job_id, "INFO", f"Processing file: {file_id}")
        upsert_artifact(f"artifact_{file_id}_raw", file_id, "raw_processing", path, 100, int(time.time()), "processed")
        update_health("ProcessFileAgent", "OK", last_ok_ts=datetime.datetime.now().isoformat())
        # Example: Add next step for PDF convert if it's a PDF
        if path.endswith(".pdf"):
            self.add_job("PDF_CONVERT", {"file_id": file_id, "path": path})

    def _handle_deep_archive_extract(self, job_id: int, payload: Dict[str, Any]):
        file_id = payload.get("file_id")
        path = payload.get("path")
        print(f"ArchiveAgent: Simulating deep archive extraction for {file_id} at {path}")
        log_job(job_id, "INFO", f"Extracting archive: {file_id}")
        # Simulate extraction and finding new files
        new_files = [
            {"file_id": "nested_file_1", "abspath": "extracted/nested_doc.txt", "size": 500, "mtime": int(time.time()), "status": "extracted"},
        ]
        for f in new_files:
            upsert_file(f["file_id"], f["abspath"], f"archive:{file_id}", f["size"], f["mtime"], "text", f["status"], self.current_run_id)
            self.add_job("PROCESS_FILE", {"file_id": f["file_id"], "path": f["abspath"]})
        upsert_artifact(f"artifact_{file_id}_extracted", file_id, "archive_extraction", path, 5000, int(time.time()), "extracted")
        update_health("ArchiveAgent", "OK", last_ok_ts=datetime.datetime.now().isoformat())

    def _handle_pdf_convert(self, job_id: int, payload: Dict[str, Any]):
        file_id = payload.get("file_id")
        path = payload.get("path")
        print(f"ConversionAgent: Simulating PDF conversion for {file_id} at {path}")
        log_job(job_id, "INFO", f"Converting PDF: {file_id}")
        # Simulate conversion output
        converted_path = f"converted/{file_id}.md"
        upsert_artifact(f"artifact_{file_id}_md", file_id, "pdf_conversion", converted_path, 1500, int(time.time()), "converted")
        update_health("ConversionAgent", "OK", last_ok_ts=datetime.datetime.now().isoformat())
        # Add next step for segmentation
        self.add_job("SEGMENT_MD", {"file_id": file_id, "path": converted_path})

    def _handle_ocr_fallback(self, job_id: int, payload: Dict[str, Any]):
        file_id = payload.get("file_id")
        path = payload.get("path")
        print(f"OCRAgent: Simulating OCR fallback for {file_id} at {path}")
        log_job(job_id, "INFO", f"Performing OCR: {file_id}")
        # Simulate OCR output
        ocr_path = f"ocr/{file_id}.txt"
        upsert_artifact(f"artifact_{file_id}_ocr", file_id, "ocr_processing", ocr_path, 800, int(time.time()), "ocr_done")
        update_health("OCRAgent", "OK", last_ok_ts=datetime.datetime.now().isoformat())
        # After OCR, re-attempt conversion or proceed
        self.add_job("PDF_CONVERT", {"file_id": file_id, "path": path, "ocr_applied": True})


    def _handle_segment_md(self, job_id: int, payload: Dict[str, Any]):
        file_id = payload.get("file_id")
        path = payload.get("path")
        print(f"ShardAgent: Simulating markdown segmentation for {file_id} at {path}")
        log_job(job_id, "INFO", f"Segmenting MD: {file_id}")
        # Simulate creating segments
        segment_path = f"segments/{file_id}_part1.md"
        upsert_artifact(f"artifact_{file_id}_segment1", file_id, "segmentation", segment_path, 700, int(time.time()), "segmented")
        update_health("ShardAgent", "OK", last_ok_ts=datetime.datetime.now().isoformat())
        # Finalize processing for this file for now

if __name__ == "__main__":
    orchestrator = Orchestrator()
    orchestrator.start_run(config_hash="test_config_123")

    # Example usage:
    orchestrator.add_job("DISCOVER_FILES", {"path": "H:\\inputs"})
    orchestrator.add_job("DEEP_ARCHIVE_EXTRACT", {"file_id": "archive1", "path": "H:\\inputs\\archive.zip"})
    orchestrator.add_job("PDF_CONVERT", {"file_id": "pdf_doc_id", "path": "H:\\inputs\\scanned.pdf"})
    # Example of a job that might fail and retry
    # orchestrator.add_job("PROCESS_FILE", {"file_id": "failing_file", "path": "non_existent.txt"})
    
    try:
        orchestrator.start()
    except KeyboardInterrupt:
        print("\nOrchestrator interrupted by user.")
    finally:
        # Check if there's an active run before trying to complete it
        if orchestrator.current_run_id:
            orchestrator.complete_run("interrupted")
        orchestrator.stop()
