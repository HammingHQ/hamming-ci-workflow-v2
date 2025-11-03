import os
from typing import Optional, List


def get_test_run_url(test_run_id: str) -> str:
    """Generate the URL for viewing a test run in the Hamming UI."""
    base_url = os.environ.get("HAMMING_UI_BASE_URL", "https://app.hamming.ai")
    return f"{base_url}/test-runs/{test_run_id}"


def get_test_case_url(test_case_id: str) -> str:
    """Generate the URL for viewing a test case in the Hamming UI."""
    base_url = os.environ.get("HAMMING_UI_BASE_URL", "https://app.hamming.ai")
    return f"{base_url}/test-cases/{test_case_id}"


def parse_comma_separated(value: Optional[str]) -> Optional[List[str]]:
    """Parse a comma-separated string into a list of strings."""
    if not value:
        return None
    return [item.strip() for item in value.split(",") if item.strip()]


def validate_selection_method(tag_ids: Optional[List[str]], test_case_ids: Optional[List[str]]) -> None:
    """Validate that exactly one selection method is provided."""
    if tag_ids and test_case_ids:
        raise ValueError("Cannot specify both tag_ids and test_case_ids. Choose one selection method.")
    if not tag_ids and not test_case_ids:
        raise ValueError("Must specify either tag_ids or test_case_ids for test selection.")


def format_phone_numbers(phone_numbers: List[str]) -> List[str]:
    """Ensure phone numbers are properly formatted."""
    formatted = []
    for number in phone_numbers:
        # Remove any whitespace
        number = number.strip()
        # Ensure it starts with +
        if not number.startswith("+"):
            raise ValueError(f"Phone number must start with '+': {number}")
        formatted.append(number)
    return formatted