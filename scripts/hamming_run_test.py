#!/usr/bin/env python3
import logging
import sys
from typing import Optional, List

# Add parent directory to path for imports
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hamming_sdk import HammingClient
from hamming_sdk.generated_client.models import TestRunsTestInboundAgentRequest
from hamming_workflow_v2.config import Config
from hamming_workflow_v2.utils import (
    parse_comma_separated,
    validate_selection_method,
    format_phone_numbers,
    get_test_run_url
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_test(
    agent_id: str,
    phone_numbers: List[str],
    tag_ids: Optional[List[str]] = None,
    test_case_ids: Optional[List[str]] = None
) -> str:
    """
    Create and run a test using the Hamming SDK.

    Args:
        agent_id: The agent ID to test
        phone_numbers: List of phone numbers to call
        tag_ids: Optional list of tag IDs for test selection
        test_case_ids: Optional list of specific test case IDs

    Returns:
        The test run ID
    """
    # Validate selection method
    validate_selection_method(tag_ids, test_case_ids)

    # Format phone numbers
    phone_numbers = format_phone_numbers(phone_numbers)

    # Build test configurations array
    test_configurations = []
    if tag_ids:
        test_configurations = [{"tagId": tag_id} for tag_id in tag_ids]
        logger.info(f"Running test with tags: {tag_ids}")
    elif test_case_ids:
        test_configurations = [{"testCaseId": test_id} for test_id in test_case_ids]
        logger.info(f"Running test with specific test cases: {test_case_ids}")

    logger.info(f"Creating test run for agent {agent_id}")
    logger.info(f"Phone numbers: {phone_numbers}")

    # Initialize SDK client
    client = HammingClient(api_key=Config.HAMMING_API_KEY)

    try:
        # Build request object for SDK
        request = TestRunsTestInboundAgentRequest(
            agent_id=agent_id,
            phone_numbers=phone_numbers,
            test_configurations=test_configurations
        )

        # Call SDK method to create test run
        response = client.test_runs.test_runs_test_inbound_agent(request)

        # Check if any test cases were found
        if not response.test_case_runs:
            logger.warning("WARNING: No test cases were found for the specified criteria!")
            logger.warning("Check that your agent has test cases with the specified tags or IDs")

        # Log success
        test_run_url = get_test_run_url(response.test_run_id)
        logger.info(f"Test run created successfully")
        logger.info(f"Test Run ID: {response.test_run_id}")
        logger.info(f"Results URL: {response.results_url}")
        logger.info(f"View in UI: {test_run_url}")
        logger.info(f"Test cases queued: {len(response.test_case_runs)}")

        return response.test_run_id

    except Exception as e:
        logger.error(f"Failed to create test run: {e}")
        raise


def main():
    """Main entry point for the script."""
    try:
        # Validate configuration
        Config.validate_required()
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)

    # Parse configuration
    phone_numbers = parse_comma_separated(Config.PHONE_NUMBERS)
    tag_ids = parse_comma_separated(Config.TAG_IDS)
    test_case_ids = parse_comma_separated(Config.TEST_CASE_IDS)

    if not phone_numbers:
        logger.error("No phone numbers provided")
        sys.exit(1)

    try:
        test_run_id = run_test(
            agent_id=Config.AGENT_ID,
            phone_numbers=phone_numbers,
            tag_ids=tag_ids,
            test_case_ids=test_case_ids
        )

        # Output just the test run ID for use in subsequent scripts
        print(test_run_id)

    except Exception as e:
        logger.error(f"Failed to create test run: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
