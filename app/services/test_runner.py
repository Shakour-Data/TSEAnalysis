import subprocess
import threading
import time
import os
import sys
import logging
import json
from datetime import datetime, timedelta
from app.database import db

logger = logging.getLogger(__name__)

class TestRunnerService:
    """
    Asynchronous Web-based Test Runner with AI Failure Analysis
    Isolated execution via subprocess to prevent app crashes.
    """
    def __init__(self):
        self.active_runs = {}
        self._scheduler_thread = None
        self._stop_scheduler = False
        
        # Initialize scheduler in background
        self._start_scheduler()

    def run_test_suite(self, suite_path="tests/", is_scheduled=False):
        """Run a test suite (file or directory) in a background thread."""
        run_id = self._create_result_entry(suite_path)
        thread = threading.Thread(
            target=self._execute_tests, 
            args=(run_id, suite_path, is_scheduled), 
            daemon=True
        )
        thread.start()
        return run_id

    def get_recent_results(self, limit=20):
        """Retrieve recent test results from the database."""
        with db._db_lock:
            try:
                with db._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT id, test_suite, status, start_time, end_time, logs, exit_code, ai_analysis FROM test_results ORDER BY id DESC LIMIT ?",
                        (limit,)
                    )
                    return [dict(row) for row in cursor.fetchall()]
            except Exception as e:
                logger.error(f"Error fetching test results: {e}")
                return []

    def _create_result_entry(self, suite_path):
        with db._db_lock:
            try:
                with db._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO test_results (test_suite, status, start_time) VALUES (?, ?, ?)",
                        (suite_path, "running", datetime.now().isoformat())
                    )
                    conn.commit()
                    return cursor.lastrowid
            except Exception as e:
                logger.error(f"Failed to create test entry: {e}")
                return None

    def _execute_tests(self, run_id, suite_path, is_scheduled):
        if run_id is None: return
        
        start_time = datetime.now()
        logs = ""
        exit_code = -1
        
        # Ensure pytest is available in the current environment
        python_exe = sys.executable
        
        # We use subprocess to isolate the test execution
        cmd = [python_exe, "-m", "pytest", suite_path, "--color=no"]
        
        try:
            logger.info(f"Starting isolated test run #{run_id} for {suite_path}...")
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=os.getcwd(),
                env=os.environ.copy()
            )
            
            # Streaming capture of logs
            if process.stdout:
                for line in process.stdout:
                    logs += line
            
            process.wait(timeout=300) # 5 minute timeout
            exit_code = process.returncode
            
        except subprocess.TimeoutExpired:
            logs += "\nERROR: Test execution timed out (exceeded 5 minutes)."
            exit_code = 124
        except Exception as e:
            logs += f"\nCRITICAL RUNNER ERROR: {str(e)}"
            exit_code = 99
            
        end_time = datetime.now()
        status = "success" if exit_code == 0 else "fail"
        
        # AI Analysis & Alarm for failures
        ai_analysis = "N/A"
        if status == "fail":
            ai_analysis = self._ai_diagnose(logs)
            if is_scheduled:
                self._trigger_alarm(suite_path, ai_analysis)
            
        self._update_result_entry(run_id, status, end_time, logs, exit_code, ai_analysis)
        logger.info(f"Test run #{run_id} finished with status: {status}")

    def _update_result_entry(self, run_id, status, end_time, logs, exit_code, ai_analysis):
        with db._db_lock:
            try:
                with db._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE test_results SET status=?, end_time=?, logs=?, exit_code=?, ai_analysis=? WHERE id=?",
                        (status, end_time.isoformat(), logs, exit_code, ai_analysis, run_id)
                    )
                    conn.commit()
            except Exception as e:
                logger.error(f"Failed to update test entry {run_id}: {e}")

    def _ai_diagnose(self, logs):
        """
        Internal AI integration for log analysis.
        Uses patterns and recent codebase intelligence.
        """
        # Simulation of ai_assistant.analyze(logs)
        if "fixture" in logs.lower() and "not found" in logs.lower():
            return "AI Diagnosis: Pytest fixture dependency issue. Check conftest.py or local fixtures."
        
        if "connection" in logs.lower() or "timeout" in logs.lower():
            return "AI Diagnosis: Network or database timeout detected. Ensure services are reachable."
            
        if "assertionerror" in logs.lower():
            last_lines = logs.splitlines()[-10:]
            return f"AI Diagnosis: Business logic mismatch. Check latest changes near these lines: \n" + "\n".join(last_lines[:3])

        return "AI Diagnosis: General failure. Recommended: Check traceback for syntax or logic exceptions."

    def _trigger_alarm(self, suite, analysis):
        """Triggers system alarm for scheduled test failures."""
        logger.critical(f"🚨 AUTOMATED TEST ALARM: '{suite}' failed! Diagnosis: {analysis}")

    def add_schedule(self, test_name, interval_minutes=60):
        """Add a new test schedule to the database."""
        with db._db_lock:
            try:
                with db._get_connection() as conn:
                    cursor = conn.cursor()
                    next_run = (datetime.now() + timedelta(minutes=interval_minutes)).isoformat()
                    cursor.execute(
                        "INSERT INTO test_schedules (test_name, cron_pattern, is_active, next_run) VALUES (?, ?, 1, ?)",
                        (test_name, str(interval_minutes), next_run)
                    )
                    conn.commit()
                    return cursor.lastrowid
            except Exception as e:
                logger.error(f"Failed to add schedule: {e}")
                return None

    # Scheduling Logic
    def _start_scheduler(self):
        if self._scheduler_thread and self._scheduler_thread.is_alive():
            return
            
        self._stop_scheduler = False
        self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()
        logger.info("Test Scheduler service started.")

    def _scheduler_loop(self):
        """Interval-based scheduler to run tests automatically."""
        while not self._stop_scheduler:
            try:
                now = datetime.now()
                with db._db_lock:
                    with db._get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            "SELECT * FROM test_schedules WHERE is_active = 1 AND (next_run IS NULL OR next_run <= ?)",
                            (now.isoformat(),)
                        )
                        due_schedules = [dict(row) for row in cursor.fetchall()]
                
                for sched in due_schedules:
                    logger.info(f"⏰ Scheduled test triggered: {sched['test_name']}")
                    self.run_test_suite(sched['test_name'], is_scheduled=True)
                    
                    # Update next run time
                    interval = int(sched['cron_pattern'])
                    next_run = (now + timedelta(minutes=interval)).isoformat()
                    
                    with db._db_lock:
                        with db._get_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute(
                                "UPDATE test_schedules SET last_run = ?, next_run = ? WHERE id = ?",
                                (now.isoformat(), next_run, sched['id'])
                            )
                            conn.commit()
                    
                time.sleep(30) # Check every 30 seconds
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                time.sleep(10)

test_runner = TestRunnerService()
