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
    testConfigurations: List[TestConfiguration]  # Array of test case/tag configurations
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


class AssertionResult(BaseModel):
    assertionId: str
    assertionName: str
    status: str  # PASSED, FAILED, ERROR
    reason: Optional[str] = None


class Metrics(BaseModel):
    latencyP50: Optional[float] = None
    latencyP90: Optional[float] = None
    latencyP95: Optional[float] = None
    latencyMax: Optional[float] = None
    userInterruptionCount: Optional[int] = None
    assistantInterruptionCount: Optional[int] = None
    userTalkRatio: Optional[float] = None
    callDuration: Optional[float] = None
    userSpeakingDuration: Optional[float] = None
    assistantSpeakingDuration: Optional[float] = None
    interactivityScore: Optional[float] = None
    assistantTimeToFirstWord: Optional[float] = None


class Transcript(BaseModel):
    messages: Optional[List[Dict[str, Any]]] = None


class CallResult(BaseModel):
    id: str
    testCaseId: str
    status: str  # PASSED, FAILED, PENDING, ERROR
    durationSeconds: Optional[float] = None
    recordingUrl: Optional[str] = None
    transcriptionDataUrl: Optional[str] = None
    transcript: Optional[Transcript] = None
    assertionResults: Optional[List[AssertionResult]] = None
    metrics: Optional[Metrics] = None


class TestRunResults(BaseModel):
    summary: Optional[Dict[str, Any]] = None
    results: List[CallResult]

    # Computed properties for backward compatibility
    @property
    def testRunId(self) -> str:
        return self.summary.get("id", "") if self.summary else ""

    @property
    def status(self) -> str:
        return self.summary.get("status", "") if self.summary else ""

    @property
    def calls(self) -> List[CallResult]:
        """Alias for results for backward compatibility"""
        return self.results


class ErrorResponse(BaseModel):
    message: str
    code: str
    httpStatus: int
    validationErrors: Optional[List[Dict[str, Any]]] = None
    data: Optional[Dict[str, Any]] = None