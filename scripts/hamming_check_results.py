#!/usr/bin/env python3
import json
import sys
import logging

# Add parent directory to path for imports
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_results(
    results_dict: dict,
    min_test_pass_rate: float = 1.0,
    min_assertion_pass_rate: float = 1.0
) -> bool:
    """
    Check test run results with separate thresholds.

    Args:
        results_dict: The test run results as a dictionary
        min_test_pass_rate: Minimum test case pass rate (0.0-1.0, default: 1.0 = 100%)
        min_assertion_pass_rate: Minimum assertion pass rate (0.0-1.0, default: 1.0 = 100%)

    Returns:
        True if all thresholds pass, False otherwise
    """
    summary = results_dict.get("summary", {})
    results = results_dict.get("results", [])

    all_checks_passed = True

    # Check 1: Overall test run status
    status = summary.get("status", "UNKNOWN")
    if status not in ["COMPLETED", "FINISHED"]:
        logger.error(f"✗ Test run did not complete successfully. Status: {status}")
        return False

    total_tests = len(results)
    if total_tests == 0:
        logger.error("✗ No test cases found in results")
        return False

    # Check 2: Test case pass rate
    passed_tests = sum(1 for r in results if r.get("status") == "PASSED")
    test_pass_rate = passed_tests / total_tests

    logger.info(f"\n{'='*60}")
    logger.info(f"TEST CASE PASS RATE:")
    logger.info(f"  Passed: {passed_tests}/{total_tests} ({test_pass_rate:.1%})")
    logger.info(f"  Threshold: {min_test_pass_rate:.1%}")

    if test_pass_rate >= min_test_pass_rate:
        logger.info(f"  ✓ PASS: Test pass rate meets threshold")
    else:
        logger.error(f"  ✗ FAIL: Test pass rate below threshold")
        all_checks_passed = False

    # Check 3: Assertion pass rate (across all test cases)
    total_assertions = 0
    passed_assertions = 0

    for result in results:
        assertion_results = result.get("assertionResults", [])
        for assertion in assertion_results:
            total_assertions += 1
            if assertion.get("status") == "PASSED":
                passed_assertions += 1

    if total_assertions > 0:
        assertion_pass_rate = passed_assertions / total_assertions

        logger.info(f"\n{'='*60}")
        logger.info(f"ASSERTION PASS RATE:")
        logger.info(f"  Passed: {passed_assertions}/{total_assertions} ({assertion_pass_rate:.1%})")
        logger.info(f"  Threshold: {min_assertion_pass_rate:.1%}")

        if assertion_pass_rate >= min_assertion_pass_rate:
            logger.info(f"  ✓ PASS: Assertion pass rate meets threshold")
        else:
            logger.error(f"  ✗ FAIL: Assertion pass rate below threshold")
            all_checks_passed = False
    else:
        logger.info(f"\nNo assertions found to check")

    # Log detailed test case results
    logger.info(f"\n{'='*60}")
    logger.info(f"DETAILED TEST RESULTS:")
    for result in results:
        test_id = result.get("id", "unknown")
        test_case_id = result.get("testCaseId", "unknown")
        test_status = result.get("status", "UNKNOWN")

        if test_status == "PASSED":
            logger.info(f"  ✓ {test_id} (testCase: {test_case_id}): PASSED")
        else:
            logger.error(f"  ✗ {test_id} (testCase: {test_case_id}): {test_status}")

            # Show failed assertions
            assertion_results = result.get("assertionResults", [])
            for assertion in assertion_results:
                if assertion.get("status") == "FAILED":
                    logger.error(f"      └─ {assertion.get('assertionName')}: {assertion.get('reason')}")

    logger.info(f"{'='*60}\n")

    # Final result
    if all_checks_passed:
        logger.info("✓ All checks PASSED")
        return True
    else:
        logger.error("✗ Some checks FAILED")
        return False


def main():
    """Main entry point for the script."""
    # Check if input is provided via stdin or as argument
    if len(sys.argv) > 1:
        logger.error("Direct test run ID not yet implemented. Please pipe results from hamming_wait_test_run.py")
        sys.exit(1)
    else:
        # Read results from stdin (piped from hamming_wait_test_run.py)
        try:
            results_dict = json.load(sys.stdin)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse input JSON: {e}")
            sys.exit(1)

    # Get thresholds from environment (all should be 0.0 to 1.0)
    min_test_pass_rate = float(os.environ.get("MIN_TEST_PASS_RATE", "1.0"))  # Default: 100%
    min_assertion_pass_rate = float(os.environ.get("MIN_ASSERTION_PASS_RATE", "1.0"))  # Default: 100%

    # Check results
    if check_results(results_dict, min_test_pass_rate, min_assertion_pass_rate):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
