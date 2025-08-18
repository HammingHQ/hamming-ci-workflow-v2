#!/usr/bin/env python3
import json
import sys
import logging
from typing import Optional

# Add parent directory to path for imports
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hamming_workflow_v2.types import TestRunResults

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_results(results: TestRunResults, min_score_threshold: float = 0.0) -> bool:
    """
    Check test run results and determine if they pass.
    
    Args:
        results: The test run results to check
        min_score_threshold: Minimum score threshold for passing (default: 0.0)
    
    Returns:
        True if all checks pass, False otherwise
    """
    all_passed = True
    
    # Check overall status
    if results.status != "FINISHED":
        logger.error(f"Test run did not complete successfully. Status: {results.status}")
        all_passed = False
    
    # Check each call
    for call in results.calls:
        call_passed = True
        
        # Check call status
        if call.status != "ended":
            logger.error(f"Call {call.id} has status '{call.status}', expected 'ended'")
            call_passed = False
            all_passed = False
        
        # Check scores
        for score_name, score in call.scores.items():
            if score.value <= min_score_threshold:
                logger.error(
                    f"Call {call.id} failed score '{score_name}': {score.value} "
                    f"(threshold: {min_score_threshold})"
                )
                call_passed = False
                all_passed = False
            else:
                logger.info(f"Call {call.id} passed score '{score_name}': {score.value}")
        
        if call_passed:
            logger.info(f"Call {call.id} to {call.phoneNumber} PASSED all checks")
        else:
            logger.error(f"Call {call.id} to {call.phoneNumber} FAILED")
    
    # Log summary
    if results.summary:
        logger.info(f"Test Summary: {json.dumps(results.summary, indent=2)}")
    
    # Log final result
    total_calls = len(results.calls)
    if all_passed:
        logger.info(f"✓ All {total_calls} calls passed successfully")
    else:
        failed_calls = sum(1 for call in results.calls if call.status != "ended" or 
                          any(score.value <= min_score_threshold for score in call.scores.values()))
        logger.error(f"✗ {failed_calls}/{total_calls} calls failed")
    
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
            input_data = json.load(sys.stdin)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse input JSON: {e}")
            sys.exit(1)
    
    # Parse results
    try:
        results = TestRunResults(**input_data)
    except Exception as e:
        logger.error(f"Failed to parse test results: {e}")
        sys.exit(1)
    
    # Get threshold from environment or use default
    min_score_threshold = float(os.environ.get("MIN_SCORE_THRESHOLD", "0.0"))
    
    # Check results
    if check_results(results, min_score_threshold):
        logger.info("All checks passed successfully ✓")
        sys.exit(0)
    else:
        logger.error("Some checks failed ✗")
        sys.exit(1)


if __name__ == "__main__":
    main()