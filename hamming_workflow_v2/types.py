from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel


class TestStatus(Enum):
    """Test run status values."""
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    SCORING = "SCORING"
    SCORING_FAILED = "SCORING_FAILED"
    COMPLETED = "COMPLETED"
    FINISHED = "FINISHED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"


class TestCaseStatus(Enum):
    """Individual test case status values."""
    PASSED = "PASSED"
    FAILED = "FAILED"
    PENDING = "PENDING"
    ERROR = "ERROR"


class AssertionStatus(Enum):
    """Assertion status values."""
    PASSED = "PASSED"
    FAILED = "FAILED"
    ERROR = "ERROR"


class PersonaOverride(BaseModel):
    """Persona override configuration."""
    name: Optional[str] = None
    voice: Optional[str] = None
    prompt: Optional[str] = None


class TestConfiguration(BaseModel):
    """Configuration for a single test case or tag."""
    tagId: Optional[str] = None
    testCaseId: Optional[str] = None
    overrides: Optional[Dict[str, Any]] = None
    scenarioFacts: Optional[Dict[str, Any]] = None
    persona: Optional[PersonaOverride] = None


class CreateTestRunRequest(BaseModel):
    """Request body for creating a test run."""
    agentId: str
    phoneNumbers: List[str]
    testConfigurations: List[TestConfiguration]


class TestRunResponse(BaseModel):
    """Response from creating a test run."""
    testRunId: str
    resultsUrl: str
    testCaseRuns: Optional[List[Any]] = []
    status: Optional[str] = None
    message: Optional[str] = None


class AssertionResult(BaseModel):
    """Result of a single assertion."""
    assertionId: str
    assertionName: str
    status: str  # PASSED, FAILED, ERROR
    reason: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class AssertionsSummary(BaseModel):
    """Summary of assertions for a test case."""
    overallScore: Optional[float] = None
    categories: Optional[List[str]] = None


class TestCaseMetrics(BaseModel):
    """Metrics for a test case run."""
    latencyP50: Optional[float] = None
    latencyP90: Optional[float] = None
    interruptionCount: Optional[int] = None
    interactivityScore: Optional[float] = None


class TestCaseResult(BaseModel):
    """Result of a single test case run."""
    id: str
    testCaseId: str
    status: str  # PASSED, FAILED, PENDING, ERROR
    phoneNumber: Optional[str] = None
    assertions: Optional[AssertionsSummary] = None
    assertionResults: Optional[List[AssertionResult]] = []
    metrics: Optional[TestCaseMetrics] = None
    transcript: Optional[str] = None
    duration: Optional[int] = None
    recordingUrl: Optional[str] = None


class AssertionCategory(BaseModel):
    """Assertion category details."""
    name: str
    score: Optional[float] = None
    status: Optional[str] = None  # passed, failed
    stats: Optional[Dict[str, Any]] = None
    assertionIds: Optional[List[str]] = None


class TestRunAssertionsSummary(BaseModel):
    """Summary of assertions at test run level."""
    overallScore: Optional[float] = None
    categories: Optional[List[AssertionCategory]] = None


class TestRunSummary(BaseModel):
    """Summary of a test run."""
    id: str
    status: str
    stats: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Any]] = None
    assertions: Optional[TestRunAssertionsSummary] = None
    topIssues: Optional[List[Dict[str, Any]]] = None


class TestRunResults(BaseModel):
    """Complete test run results."""
    summary: TestRunSummary
    results: List[TestCaseResult]
    resultsUrl: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response from the API."""
    message: str
    code: Optional[str] = None
    httpStatus: Optional[int] = None
    validationErrors: Optional[List[Dict[str, Any]]] = None
    data: Optional[Dict[str, Any]] = None
