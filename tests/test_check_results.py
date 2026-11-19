import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hamming_workflow_v2.types import TestRunResults  # noqa: E402
from scripts.hamming_check_results import check_results, count_passed_tests  # noqa: E402


def build_results(*, case_results, failed_count=0, assertion_score=100.0):
    return {
        "summary": {
            "id": "run-123",
            "status": "COMPLETED",
            "stats": {
                "total": len(case_results),
                "completed": len(case_results),
                "cancelled": 0,
                "failed": failed_count,
                "pending": 0,
            },
            "assertions": {
                "overallScore": assertion_score,
                "categories": [
                    {
                        "name": "General",
                        "score": assertion_score,
                        "status": "passed" if assertion_score >= 100.0 else "failed",
                        "stats": {
                            "total": 1,
                            "passed": 1 if assertion_score >= 100.0 else 0,
                            "failed": 0 if assertion_score >= 100.0 else 1,
                            "pending": 0,
                            "skipped": 0,
                        },
                        "assertionIds": ["a-1"],
                    }
                ],
            },
        },
        "results": case_results,
    }


class CheckResultsTests(unittest.TestCase):
    def test_separates_cancelled_runs_from_completed_passes(self):
        results_dict = build_results(
            case_results=[
                {
                    "id": "case-1",
                    "testCaseId": "case-1",
                    "status": "COMPLETED",
                    "assertionResults": [],
                },
                {
                    "id": "case-2",
                    "testCaseId": "case-2",
                    "status": "CANCELLED",
                    "assertionResults": [],
                },
            ],
            failed_count=0,
            assertion_score=100.0,
        )
        results = TestRunResults(**results_dict)

        self.assertEqual(count_passed_tests(results.summary, results.results), 1)

        self.assertTrue(
            check_results(
                results_dict,
                min_test_pass_rate=0.5,
                min_assertion_pass_rate=1.0,
            )
        )

    def test_treats_manual_end_cancelled_rows_as_completed_cases(self):
        results = build_results(
            case_results=[
                {
                    "id": "case-1",
                    "testCaseId": "case-1",
                    "status": "CANCELLED",
                    "manuallyEndedBy": "user-123",
                    "assertionResults": [],
                }
            ],
            failed_count=0,
            assertion_score=100.0,
        )

        self.assertTrue(
            check_results(
                results,
                min_test_pass_rate=1.0,
                min_assertion_pass_rate=1.0,
            )
        )

    def test_uses_summary_failed_count_with_completed_statuses(self):
        results = build_results(
            case_results=[
                {
                    "id": "case-1",
                    "testCaseId": "case-1",
                    "status": "COMPLETED",
                    "assertionResults": [],
                },
                {
                    "id": "case-2",
                    "testCaseId": "case-2",
                    "status": "COMPLETED",
                    "assertionResults": [],
                },
            ],
            failed_count=1,
            assertion_score=100.0,
        )

        self.assertFalse(
            check_results(
                results,
                min_test_pass_rate=1.0,
                min_assertion_pass_rate=1.0,
            )
        )

    def test_keeps_behavioral_assertions_separate_from_test_pass_rate(self):
        results = build_results(
            case_results=[
                {
                    "id": "case-1",
                    "testCaseId": "case-1",
                    "status": "COMPLETED",
                    "assertionResults": [
                        {
                            "assertionId": "a-1",
                            "assertionName": "Behavioral warning",
                            "status": "FAILED",
                            "reason": "Did not match tone guidance",
                        }
                    ],
                }
            ],
            failed_count=0,
            assertion_score=50.0,
        )

        self.assertTrue(
            check_results(
                results,
                min_test_pass_rate=1.0,
                min_assertion_pass_rate=0.5,
            )
        )

    def test_converts_assertion_score_from_percent_to_ratio(self):
        results = build_results(
            case_results=[
                {
                    "id": "case-1",
                    "testCaseId": "case-1",
                    "status": "COMPLETED",
                    "assertionResults": [],
                }
            ],
            failed_count=0,
            assertion_score=50.0,
        )

        self.assertFalse(
            check_results(
                results,
                min_test_pass_rate=1.0,
                min_assertion_pass_rate=0.75,
            )
        )

    def test_error_runs_do_not_count_as_passed_cases(self):
        results_dict = build_results(
            case_results=[
                {
                    "id": "case-1",
                    "testCaseId": "case-1",
                    "status": "COMPLETED",
                    "assertionResults": [],
                },
                {
                    "id": "case-2",
                    "testCaseId": "case-2",
                    "status": "ERROR",
                    "assertionResults": [],
                },
            ],
            failed_count=0,
            assertion_score=100.0,
        )
        results = TestRunResults(**results_dict)

        self.assertEqual(count_passed_tests(results.summary, results.results), 1)
        self.assertFalse(
            check_results(
                results_dict,
                min_test_pass_rate=1.0,
                min_assertion_pass_rate=1.0,
            )
        )

    def test_legacy_passed_statuses_still_work(self):
        results = build_results(
            case_results=[
                {
                    "id": "case-1",
                    "testCaseId": "case-1",
                    "status": "PASSED",
                    "assertionResults": [],
                }
            ],
            failed_count=0,
            assertion_score=100.0,
        )

        self.assertTrue(
            check_results(
                results,
                min_test_pass_rate=1.0,
                min_assertion_pass_rate=1.0,
            )
        )

    def test_writes_counts_for_the_pr_comment(self):
        results = build_results(
            case_results=[
                {"id": "case-1", "testCaseId": "case-1", "status": "COMPLETED"},
                {"id": "case-2", "testCaseId": "case-2", "status": "COMPLETED"},
                {"id": "case-3", "testCaseId": "case-3", "status": "ERROR"},
            ],
            failed_count=1,
            assertion_score=75.0,
        )

        with tempfile.TemporaryDirectory() as tmp:
            output_path = os.path.join(tmp, "github_output")
            with mock.patch.dict(os.environ, {"GITHUB_OUTPUT": output_path}):
                self.assertFalse(check_results(results))
            with open(output_path) as f:
                outputs = dict(line.split("=", 1) for line in f.read().splitlines())

        self.assertEqual(
            outputs,
            {"passed_tests": "1", "total_tests": "3", "assertion_score": "75.0%"},
        )


if __name__ == "__main__":
    unittest.main()
