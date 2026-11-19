#!/usr/bin/env python3
import json
import sys
import logging
from typing import Optional

# Add parent directory to path for imports
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hamming_workflow_v2.types import TestRunResults, TestCaseStatus
from hamming_workflow_v2.utils import get_test_run_url

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RAW_COMPLETED_TEST_CASE_STATUSES = {
    TestCaseStatus.COMPLETED.value,
    TestCaseStatus.PASSED.value,
}
RAW_ERROR_TEST_CASE_STATUSES = {
    TestCaseStatus.ERROR.value,
}


def write_github_outputs(**values):
    """Pass counts to later workflow steps, such as the PR comment."""
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return
    with open(output_path, "a") as f:
        for key, value in values.items():
            f.write(f"{key}={value}\n")


def get_failed_test_case_count(summary) -> Optional[int]:
    """Return the API's failed test-case count when summary stats are present."""
    stats = summary.stats or {}
    failed = stats.get("failed")

    if isinstance(failed, int) and failed >= 0:
        return failed

    return None


def is_completed_compatibility_row(result) -> bool:
    """Historical manual-end rows can persist as CANCELLED while still classifying from assertions."""
    return (
        result.status in {TestCaseStatus.CANCELLED.value, TestCaseStatus.CANCELED.value}
        and result.manuallyEndedBy is not None
    )


def count_passed_tests(summary, results) -> int:
    """
    Count passed test cases without collapsing test pass rate into assertion pass rate.

    The REST payload returns raw lifecycle statuses such as COMPLETED and CANCELLED.
    Current summary stats already split true cancellations from outcome failures,
    while ERROR remains a completed terminal state that should not count as passed.
    """
    completed_tests = sum(
        1
        for result in results
        if result.status in RAW_COMPLETED_TEST_CASE_STATUSES
        or is_completed_compatibility_row(result)
    )
    failed_test_cases = get_failed_test_case_count(summary)

    if failed_test_cases is not None:
        passed_tests = max(
            0,
            completed_tests - failed_test_cases,
        )
        return passed_tests

    if completed_tests > 0:
        logger.warning(
            "API returned completed case statuses without summary.stats.failed; "
            "treating raw completed cases as passed for compatibility."
        )
        return completed_tests

    return 0


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
    # Parse with Pydantic model for type safety
    try:
        results_obj = TestRunResults(**results_dict)
    except Exception as e:
        logger.error(f"Failed to parse test results: {e}")
        return False

    summary = results_obj.summary
    results = results_obj.results

    all_checks_passed = True

    # Log test run URL for reference
    test_run_url = get_test_run_url(summary.id)
    logger.info(f"Test Run URL: {test_run_url}")

    # Check 1: Overall test run status
    if summary.status not in ["COMPLETED", "FINISHED"]:
        logger.error(f"✗ Test run did not complete successfully. Status: {summary.status}")
        return False

    total_tests = len(results)
    if total_tests == 0:
        logger.error("✗ No test cases found in results")
        return False

    # Check 2: Test case pass rate
    passed_tests = count_passed_tests(summary, results)
    test_pass_rate = passed_tests / total_tests
    write_github_outputs(passed_tests=passed_tests, total_tests=total_tests)

    logger.info(f"\n{'='*60}")
    logger.info(f"TEST CASE PASS RATE:")
    logger.info(f"  Passed: {passed_tests}/{total_tests} ({test_pass_rate:.1%})")
    logger.info(f"  Threshold: {min_test_pass_rate:.1%}")

    if test_pass_rate >= min_test_pass_rate:
        logger.info(f"  ✓ PASS: Test pass rate meets threshold")
    else:
        logger.error(f"  ✗ FAIL: Test pass rate below threshold")
        all_checks_passed = False

    # Check 3: Assertion pass rate (using summary.assertions.overallScore)
    if summary.assertions and summary.assertions.overallScore is not None:
        # Check if assertions are actually configured
        categories = summary.assertions.categories or []
        overall_score = summary.assertions.overallScore

        # If overallScore is 0 and no categories, assertions are not configured
        if overall_score == 0.0 and len(categories) == 0:
            logger.info(f"\n{'='*60}")
            logger.info(f"ASSERTION PASS RATE:")
            logger.info(f"  No assertions configured for these test cases")
            logger.info(f"  ✓ SKIP: Assertion check skipped")
        else:
            # Convert to 0.0-1.0 scale (API returns 0-100)
            assertion_score = overall_score / 100.0
            write_github_outputs(assertion_score=f"{assertion_score:.1%}")

            logger.info(f"\n{'='*60}")
            logger.info(f"ASSERTION PASS RATE:")
            logger.info(f"  Overall Score: {assertion_score:.1%}")
            logger.info(f"  Threshold: {min_assertion_pass_rate:.1%}")

            if assertion_score >= min_assertion_pass_rate:
                logger.info(f"  ✓ PASS: Assertion pass rate meets threshold")
            else:
                logger.error(f"  ✗ FAIL: Assertion pass rate below threshold")
                all_checks_passed = False
    else:
        logger.info(f"\n{'='*60}")
        logger.info(f"ASSERTION PASS RATE:")
        logger.info(f"  No assertions configured for these test cases")
        logger.info(f"  ✓ SKIP: Assertion check skipped")

    # Log non-completed raw failures directly from the payload.
    raw_failed_results = [
        r
        for r in results
        if r.status not in RAW_COMPLETED_TEST_CASE_STATUSES
        and not is_completed_compatibility_row(r)
    ]
    if raw_failed_results:
        logger.info(f"\n{'='*60}")
        logger.info(f"FAILED TEST CASES ({len(raw_failed_results)}):")
        for result in raw_failed_results:
            logger.error(f"  ✗ {result.testCaseId}: {result.status}")

    error_test_cases = sum(
        1 for result in results if result.status in RAW_ERROR_TEST_CASE_STATUSES
    )
    failed_test_cases = get_failed_test_case_count(summary)
    if failed_test_cases:
        completed_outcome_failures = max(
            0,
            failed_test_cases,
        )

        if completed_outcome_failures:
            logger.info(
                "  Outcome-failed completed test cases (derived from summary stats): "
                f"{completed_outcome_failures}"
            )
            logger.info(
                "  Use the Test Run URL above to inspect which completed cases "
                "failed their expected outcome."
            )
    if error_test_cases:
        logger.info(f"  Error test cases (raw ERROR status): {error_test_cases}")

    # Final summary
    logger.info(f"{'='*60}\n")
    if all_checks_passed:
        logger.info("✓ All checks PASSED")
    else:
        logger.error("✗ Some checks FAILED")

    return all_checks_passed


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
