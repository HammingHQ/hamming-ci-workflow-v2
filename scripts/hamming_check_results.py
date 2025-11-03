#!/usr/bin/env python3
import json
import sys
import logging

# Add parent directory to path for imports
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_results(results_dict: dict, min_score_threshold: float = 0.0) -> bool:
    """
    Check test run results and determine if they pass.

    Args:
        results_dict: The test run results as a dictionary
        min_score_threshold: Minimum score threshold for passing (default: 0.0)

    Returns:
        True if all checks pass, False otherwise
    """
    all_passed = True

    # Get summary and results
    summary = results_dict.get("summary", {})
    results = results_dict.get("results", [])

    # Check overall status
    status = summary.get("status", "UNKNOWN")
    if status not in ["COMPLETED", "FINISHED"]:
        logger.error(f"Test run did not complete successfully. Status: {status}")
        all_passed = False

    # Check each test case result
    for call in results:
        call_passed = True
        call_id = call.get("id", "unknown")
        test_case_id = call.get("testCaseId", "unknown")
        call_status = call.get("status", "UNKNOWN")

        # Check test case status (PASSED/FAILED/PENDING/ERROR)
        if call_status not in ["PASSED"]:
            logger.error(f"Test case {call_id} (testCaseId: {test_case_id}) has status '{call_status}'")
            call_passed = False
            all_passed = False

        # Check assertions
        assertion_results = call.get("assertionResults", [])
        if assertion_results:
            for assertion in assertion_results:
                assertion_id = assertion.get("assertionId", "unknown")
                assertion_name = assertion.get("assertionName", "unknown")
                assertion_status = assertion.get("status", "UNKNOWN")
                reason = assertion.get("reason")

                if assertion_status == "FAILED":
                    logger.error(
                        f"Test case {call_id} failed assertion '{assertion_name}': {reason}"
                    )
                    call_passed = False
                    all_passed = False
                elif assertion_status == "PASSED":
                    logger.info(f"Test case {call_id} passed assertion '{assertion_name}'")
                elif assertion_status == "ERROR":
                    logger.error(f"Test case {call_id} error in assertion '{assertion_name}': {reason}")
                    call_passed = False
                    all_passed = False

        # Log interactivity score if available
        metrics = call.get("metrics", {})
        if metrics and "interactivityScore" in metrics:
            logger.info(f"Test case {call_id} interactivity score: {metrics['interactivityScore']}")

        if call_passed:
            logger.info(f"Test case {call_id} (testCaseId: {test_case_id}) PASSED all checks")
        else:
            logger.error(f"Test case {call_id} (testCaseId: {test_case_id}) FAILED")

    # Log summary
    if summary:
        logger.info(f"Test Summary: {json.dumps(summary, indent=2)}")

    # Log final result
    total_calls = len(results)
    if all_passed:
        logger.info(f"✓ All {total_calls} test cases passed successfully")
    else:
        failed_calls = sum(1 for call in results if call.get("status") != "PASSED")
        logger.error(f"✗ {failed_calls}/{total_calls} test cases failed")

    return all_passed


def main():
    """Main entry point for the script."""
    # Check if input is provided via stdin or as argument
    if len(sys.argv) > 1:
        # Test run ID provided as argument - fetch results first
        logger.error("Direct test run ID not yet implemented. Please pipe results from hamming_wait_test_run.py")
        sys.exit(1)
    else:
        # Read results from stdin (piped from hamming_wait_test_run.py)
        try:
            results_dict = json.load(sys.stdin)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse input JSON: {e}")
            sys.exit(1)

    # Get threshold from environment or use default
    min_score_threshold = float(os.environ.get("MIN_SCORE_THRESHOLD", "0.0"))

    # Check results
    if check_results(results_dict, min_score_threshold):
        logger.info("All checks passed successfully ✓")
        sys.exit(0)
    else:
        logger.error("Some checks failed ✗")
        sys.exit(1)


if __name__ == "__main__":
    main()
