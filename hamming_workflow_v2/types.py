"""
Type definitions for Hamming CI Workflow v2.

Note: Most types are now provided by the hamming_sdk package.
This file is kept for backward compatibility and custom types if needed.
"""

from enum import Enum


class TestStatus(Enum):
    """Test run status values."""
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    SCORING = "SCORING"
    SCORING_FAILED = "SCORING_FAILED"
    FINISHED = "FINISHED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"
