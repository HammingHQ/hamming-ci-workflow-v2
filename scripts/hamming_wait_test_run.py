#!/usr/bin/env python3
import requests
import time
import logging
import sys
import json

# Add parent directory to path for imports
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hamming_workflow_v2.config import Config
from hamming_workflow_v2.types import TestStatus, TestRunResults
from hamming_workflow_v2.utils import get_test_run_url

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def wait_for_test_run(test_run_id: str, timeout_seconds: int = None) -> TestRunResults:
    """
    Wait for a test run to complete and return the results.
    
    Args:
        test_run_id: The test run ID to monitor
        timeout_seconds: Maximum time to wait (defaults to Config.TIMEOUT_SECONDS)
    
    Returns:
        The test run results
    """
    if timeout_seconds is None:
        timeout_seconds = Config.TIMEOUT_SECONDS
    
    url = f"{Config.HAMMING_API_BASE_URL}/test-runs/{test_run_id}"
    headers = Config.get_headers()
    
    start_time = time.time()
    test_run_url = get_test_run_url(test_run_id)
    
    logger.info(f"Waiting for test run to complete: {test_run_id}")
    logger.info(f"View in UI: {test_run_url}")
    logger.info(f"Timeout: {timeout_seconds} seconds")
    
    last_status = None
    
    while True:
        # Check timeout
        elapsed = time.time() - start_time
        if elapsed > timeout_seconds:
            logger.error(f"Test run timed out after {timeout_seconds} seconds")
            return TestRunResults(
                testRunId=test_run_id,
                status="TIMEOUT",
                calls=[],
                summary={"error": "Timeout waiting for test completion"}
            )
        
        try:
            # Get test run status
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            current_status = data.get("status", "UNKNOWN")
            
            # Log status changes
            if current_status != last_status:
                logger.info(f"Test run status: {current_status}")
                last_status = current_status
            
            # Check if test is complete
            if current_status in [
                TestStatus.FINISHED.value,
                TestStatus.FAILED.value,
                TestStatus.SCORING_FAILED.value
            ]:
                logger.info(f"Test run completed with status: {current_status}")
                
                # Get full results
                results_url = f"{url}/results"
                results_response = requests.get(results_url, headers=headers)
                results_response.raise_for_status()
                results_data = results_response.json()
                
                return TestRunResults(**results_data)
            
            # Still running, log progress if available
            if current_status == TestStatus.RUNNING.value:
                completed_calls = data.get("completedCalls", 0)
                total_calls = data.get("totalCalls", 0)
                if total_calls > 0:
                    progress = f" ({completed_calls}/{total_calls} calls completed)"
                    if completed_calls != data.get("lastLoggedCalls", 0):
                        logger.info(f"Progress: {progress}")
                        data["lastLoggedCalls"] = completed_calls
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error checking test run status: {e}")
        
        # Wait before next poll
        time.sleep(Config.POLL_INTERVAL_SECONDS)


def main():
    """Main entry point for the script."""
    if len(sys.argv) < 2:
        logger.error("Usage: python hamming_wait_test_run.py <test_run_id>")
        sys.exit(1)
    
    test_run_id = sys.argv[1]
    
    # Get timeout from environment or use default
    timeout_seconds = Config.TIMEOUT_SECONDS
    if len(sys.argv) > 2:
        try:
            timeout_seconds = int(sys.argv[2])
        except ValueError:
            logger.warning(f"Invalid timeout value: {sys.argv[2]}, using default: {timeout_seconds}")
    
    # Ensure API key is set
    if not Config.HAMMING_API_KEY:
        logger.error("HAMMING_API_KEY is not set")
        sys.exit(1)
    
    try:
        results = wait_for_test_run(test_run_id, timeout_seconds)
        
        # Output results as JSON for downstream processing
        print(results.model_dump_json(indent=2))
        
        # Exit with appropriate code
        if results.status in [TestStatus.FINISHED.value, "FINISHED"]:
            sys.exit(0)
        else:
            logger.error(f"Test run failed with status: {results.status}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error waiting for test run: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()