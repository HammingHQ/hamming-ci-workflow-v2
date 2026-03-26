import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.hamming_check_results import check_results  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
