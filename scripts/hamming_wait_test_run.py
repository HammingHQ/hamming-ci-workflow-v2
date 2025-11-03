#!/usr/bin/env python3
import time
import logging
import sys
import json

# Add parent directory to path for imports
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hamming_sdk import HammingClient
from hamming_workflow_v2.config import Config
from hamming_workflow_v2.utils import get_test_run_url

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def wait_for_test_run(test_run_id: str, timeout_seconds: int = None):
    """
    Wait for a test run to complete and return the results.

    Args:
        test_run_id: The test run ID to monitor
        timeout_seconds: Maximum time to wait (defaults to Config.TIMEOUT_SECONDS)

    Returns:
        The test run results object from SDK
    """
    if timeout_seconds is None:
        timeout_seconds = Config.TIMEOUT_SECONDS

    # Initialize SDK client
    client = HammingClient(api_key=Config.HAMMING_API_KEY)

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
            return {
                "summary": {"id": test_run_id, "status": "TIMEOUT", "error": "Timeout waiting for test completion"},
                "results": []
            }

        try:
            # Get test run status using SDK
            status_response = client.test_runs.test_runs_get_test_run_status(
                test_run_id=test_run_id
            )

            current_status = status_response.status

            # Log status changes
            if current_status != last_status:
                logger.info(f"Test run status: {current_status}")
                last_status = current_status

            # Check if test is complete
            if current_status in ["COMPLETED", "FAILED", "CANCELED"]:
                logger.info(f"Test run completed with status: {current_status}")

                # Get full results using SDK
                results = client.test_runs.test_runs_get_test_run_results(
                    test_run_id=test_run_id
                )

                return results

            # Still running, log progress if available
            if current_status == "RUNNING":
                # Try to get current results to show progress
                try:
                    results = client.test_runs.test_runs_get_test_run_results(
                        test_run_id=test_run_id
                    )
                    if results.results:
                        status_counts = {}
                        for run in results.results:
                            run_status = run.status
                            status_counts[run_status] = status_counts.get(run_status, 0) + 1
                        logger.info(f"Progress: {len(results.results)} test cases - {status_counts}")
                except Exception as e:
                    logger.debug(f"Could not fetch progress: {e}")

        except Exception as e:
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

        # Convert SDK response to dict for JSON output
        if hasattr(results, 'model_dump'):
            results_dict = results.model_dump()
        elif hasattr(results, 'dict'):
            results_dict = results.dict()
        else:
            results_dict = results

        # Output results as JSON for downstream processing
        print(json.dumps(results_dict, indent=2, default=str))

        # Exit with appropriate code - "COMPLETED" is the success status
        status = results_dict.get("summary", {}).get("status", "")
        if status in ["COMPLETED", "FINISHED"]:
            sys.exit(0)
        else:
            logger.error(f"Test run failed with status: {status}")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Error waiting for test run: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
