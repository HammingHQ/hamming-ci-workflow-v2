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
    testCaseId: str
    overrides: Optional[Dict[str, Any]] = None
    scenarioFacts: Optional[Dict[str, Any]] = None
    persona: Optional[PersonaOverride] = None


class CreateTestRunRequest(BaseModel):
    agentId: str
    phoneNumbers: List[str]
    # Mutually exclusive selection methods
    tagIds: Optional[List[str]] = None
    testConfigurations: Optional[List[TestConfiguration]] = None


class TestRunResponse(BaseModel):
    testRunId: str
    resultsUrl: str
    status: str
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