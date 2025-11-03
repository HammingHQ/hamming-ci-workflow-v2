from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel


class TestStatus(Enum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    SCORING = "SCORING"
    SCORING_FAILED = "SCORING_FAILED"
    FINISHED = "FINISHED"
    FAILED = "FAILED"


class PersonaOverride(BaseModel):
    name: Optional[str] = None
    voice: Optional[str] = None
    prompt: Optional[str] = None


class TestConfiguration(BaseModel):
    # Must have either testCaseId OR tagId (mutually exclusive)
    testCaseId: Optional[str] = None
    tagId: Optional[str] = None
    overrides: Optional[Dict[str, Any]] = None
    scenarioFacts: Optional[Dict[str, Any]] = None
    persona: Optional[PersonaOverride] = None


class CreateTestRunRequest(BaseModel):
    agentId: str
    phoneNumbers: List[str]
    configurations: List[TestConfiguration]  # Array of test case/tag configurations
    name: Optional[str] = None
    description: Optional[str] = None
    testRunOverrides: Optional[Dict[str, Any]] = None
    fromNumbers: Optional[List[str]] = None
    useDifferentFromNumbers: Optional[bool] = None
    samplingCount: Optional[int] = None
    assertionSelectionMode: Optional[str] = None
    selectedAssertionIds: Optional[List[str]] = None


class TestRunResponse(BaseModel):
    testRunId: str
    resultsUrl: str
    testCaseRuns: Optional[List[Any]] = []  # Array of test case runs
    status: Optional[str] = None  # Not returned by API on creation
    message: Optional[str] = None


class Score(BaseModel):
    value: float
    details: Optional[Dict[str, Any]] = None


class CallResult(BaseModel):
    id: str
    status: str
    phoneNumber: str
    testCaseId: str
    scores: Dict[str, Score]
    transcript: Optional[str] = None
    duration: Optional[int] = None
    recordingUrl: Optional[str] = None


class TestRunResults(BaseModel):
    testRunId: str
    status: str
    calls: List[CallResult]
    summary: Optional[Dict[str, Any]] = None
    totalCalls: Optional[int] = None
    successfulCalls: Optional[int] = None
    failedCalls: Optional[int] = None


class ErrorResponse(BaseModel):
    message: str
    code: str
    httpStatus: int
    validationErrors: Optional[List[Dict[str, Any]]] = None
    data: Optional[Dict[str, Any]] = None