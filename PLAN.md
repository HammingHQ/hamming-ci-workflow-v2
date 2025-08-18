# Hamming CI Workflow v2 - Implementation Plan

## Overview
This repository (`hamming-ci-workflow-v2`) is designed to mirror the structure and functionality of `hamming-ci-workflow` but adapted to use the new REST API endpoints from the signalspace implementation. The new APIs provide enhanced validation, tag support, and better error handling.

## Key Differences from v1 to v2

### v1 - Original Workflow
- **Endpoint**: `/api/rest/voice-agent/{agent_id}/run`
- **Selection**: Uses `dataset_id` to select test cases
- **Validation**: Minimal validation, could create empty test runs
- **Response**: Simple `voice_experiment_id`

### v2 - New Workflow
- **Endpoint**: `/api/rest/test-runs/test-inbound-agent` (for outbound calls)
- **Selection**: Uses either `tagIds` or specific `testConfigurations`
- **Validation**: Comprehensive validation before test run creation
- **Response**: Structured response with `testRunId` and `resultsUrl`
- **Tags**: Full support for tag-based test case selection

## Repository Structure

```
hamming-ci-workflow-v2/
├── hamming_workflow_v2/
│   ├── __init__.py
│   ├── types.py              # Data models for new API
│   ├── utils.py              # Utility functions
│   └── config.py             # Configuration management
├── scripts/
│   ├── hamming_run_test.py              # Create and run test (replaces hamming_run_agent.py)
│   ├── hamming_wait_test_run.py         # Wait for test completion (replaces hamming_wait_voice_experiment.py)
│   └── hamming_check_results.py         # Check test results (replaces hamming_check_scores.py)
├── tests/
│   └── test_workflow.py
├── examples/
│   ├── run_with_tags.py                 # Example using tag selection
│   └── run_with_specific_tests.py       # Example using specific test configurations
├── .env.example
├── requirements.txt
├── README.md
└── PLAN.md (this file)
```

## Workflow Components

### 1. Run Test (`hamming_run_test.py`)
**Purpose**: Create and execute a test run using the new API (replaces `hamming_run_agent.py`)

**Functionality**:
- Validate agent ID and workspace
- Select test cases using tags OR specific test IDs
- Support test case overrides (persona, scenario facts)
- Initiate outbound calls to specified phone numbers
- Return test run ID and results URL

**Key APIs Used**:
- `POST /api/rest/test-runs/test-inbound-agent`
- Validation includes agent, tags, and test case verification

### 2. Wait for Test Run (`hamming_wait_test_run.py`)
**Purpose**: Monitor test run progress and wait for completion (replaces `hamming_wait_voice_experiment.py`)

**Functionality**:
- Poll test run status endpoint
- Track individual call progress
- Handle timeout scenarios
- Log progress updates

**Key APIs Used**:
- `GET /api/rest/test-runs/{testRunId}`
- Status polling with configurable intervals

### 3. Check Results (`hamming_check_results.py`)
**Purpose**: Validate test results and scores (replaces `hamming_check_scores.py`)

**Functionality**:
- Retrieve test run results
- Check scoring function outputs
- Validate call completion status
- Generate pass/fail determination

**Key APIs Used**:
- `GET /api/rest/test-runs/{testRunId}/results`
- Scoring and transcript retrieval

## Data Models (types.py)

### Core Models
```python
from typing import Dict, List, Optional, Union
from pydantic import BaseModel
from enum import Enum

class TestStatus(Enum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    SCORING = "SCORING"
    FINISHED = "FINISHED"
    FAILED = "FAILED"

class PersonaOverride(BaseModel):
    name: Optional[str]
    voice: Optional[str]
    prompt: Optional[str]

class TestConfiguration(BaseModel):
    testCaseId: str
    overrides: Optional[Dict] = None
    scenarioFacts: Optional[Dict[str, any]] = None
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
    status: TestStatus
    message: Optional[str]

class CallResult(BaseModel):
    id: str
    status: str
    phoneNumber: str
    testCaseId: str
    scores: Dict[str, float]
    transcript: Optional[str]
    duration: Optional[int]

class TestRunResults(BaseModel):
    testRunId: str
    status: TestStatus
    calls: List[CallResult]
    summary: Dict[str, any]
```

## Environment Variables

```bash
# API Configuration
HAMMING_API_KEY=your_api_key
HAMMING_API_BASE_URL=https://app.hamming.ai/api/rest

# Agent Configuration
AGENT_ID=your_agent_id

# Test Selection (use one of these)
TAG_IDS=tag1,tag2,tag3                    # Comma-separated tag IDs
TEST_CASE_IDS=case1,case2,case3           # Comma-separated test case IDs

# Phone Numbers
PHONE_NUMBERS=+1234567890,+0987654321     # Comma-separated phone numbers to call

# Monitoring Configuration  
POLL_INTERVAL_SECONDS=10
TIMEOUT_SECONDS=600
```

## Implementation Timeline

### Phase 1: Core Structure
- [x] Analyze existing hamming-ci-workflow
- [x] Understand new REST API endpoints
- [x] Create implementation plan
- [ ] Set up repository structure

### Phase 2: Type Definitions
- [ ] Create data models matching new API
- [ ] Define request/response types
- [ ] Create configuration management

### Phase 3: Core Scripts
- [ ] Implement hamming_run_test.py
- [ ] Implement hamming_wait_test_run.py  
- [ ] Implement hamming_check_results.py

### Phase 4: Testing & Documentation
- [ ] Create unit tests
- [ ] Write integration tests
- [ ] Complete README with examples
- [ ] Add GitHub Actions workflow

## Key Technical Improvements from v1

### 1. Enhanced Validation
- Pre-validation of agent ID, tags, and test cases
- Prevents creation of empty test runs
- Clear error messages with specific invalid IDs

### 2. Flexible Test Selection
- Support for tag-based selection
- Direct test case selection with overrides
- Persona and scenario fact customization

### 3. Better Error Handling
- Structured error responses with codes
- Validation errors before resource creation
- Specific error identification (e.g., INVALID_TAG_IDS)

### 4. Improved Developer Experience
- Clear API documentation
- Comprehensive test coverage
- Multiple selection methods

## Usage Examples

### Using Tags
```bash
# Run tests for all test cases tagged with "smoke-test"
export TAG_IDS="smoke-test"
export PHONE_NUMBERS="+1234567890,+0987654321"
TEST_RUN_ID=$(python scripts/hamming_run_test.py)

# Wait for completion
python scripts/hamming_wait_test_run.py $TEST_RUN_ID

# Check results
python scripts/hamming_check_results.py $TEST_RUN_ID
```

### Using Specific Test Cases
```bash
# Run specific test cases with overrides
export TEST_CASE_IDS="test-case-1,test-case-2"
export PHONE_NUMBERS="+1234567890"
TEST_RUN_ID=$(python scripts/hamming_run_test.py)

# Monitor and check results
python scripts/hamming_wait_test_run.py $TEST_RUN_ID
python scripts/hamming_check_results.py $TEST_RUN_ID
```

## Success Criteria

1. **Functional Parity**: All core functionality from v1 is maintained
2. **API Compatibility**: Uses new REST API endpoints correctly
3. **Enhanced Features**: Supports tag-based selection and test overrides
4. **Better Validation**: Comprehensive pre-execution validation
5. **Documentation**: Clear examples for both tag and direct selection

## API Endpoint Reference

### Primary Endpoint
**POST** `/api/rest/test-runs/test-inbound-agent`

Creates outbound test runs where the system calls specified phone numbers.

**Request Body:**
```json
{
  "agentId": "agent-123",
  "phoneNumbers": ["+1234567890"],
  "tagIds": ["smoke-test", "regression"]  // OR use testConfigurations below
}
```

OR

```json
{
  "agentId": "agent-123",
  "phoneNumbers": ["+1234567890"],
  "testConfigurations": [
    {
      "testCaseId": "test-case-1",
      "overrides": {
        "scenarioFacts": {"customerName": "John"},
        "persona": {"name": "Support Agent"}
      }
    }
  ]
}
```

**Response:**
```json
{
  "testRunId": "run-123",
  "resultsUrl": "https://app.hamming.ai/test-runs/run-123",
  "status": "CREATED"
}
```

## GitHub Actions Workflows

### 1. Main Workflow (`.github/workflows/hamming_run_test.yml`)

**Purpose**: Reusable workflow for running tests with the new API

```yaml
name: Hamming Run Test

on:
  workflow_call:
    inputs:
      agent_id:
        required: true
        type: string
      phone_numbers:
        required: true
        type: string
        description: "Comma-separated phone numbers"
      # Mutually exclusive selection methods
      tag_ids:
        required: false
        type: string
        description: "Comma-separated tag IDs (use this OR test_case_ids)"
      test_case_ids:
        required: false
        type: string
        description: "Comma-separated test case IDs (use this OR tag_ids)"
      # Optional parameters
      timeout_seconds:
        required: false
        type: string
        default: "600"
    secrets:
      HAMMING_API_KEY:
        required: true

jobs:
  run-test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
        with:
          repository: HammingHQ/hamming-ci-workflow-v2

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.x'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run Hamming test
        id: run_test
        env:
          HAMMING_API_KEY: ${{ secrets.HAMMING_API_KEY }}
          AGENT_ID: ${{ inputs.agent_id }}
          PHONE_NUMBERS: ${{ inputs.phone_numbers }}
          TAG_IDS: ${{ inputs.tag_ids }}
          TEST_CASE_IDS: ${{ inputs.test_case_ids }}
        run: | 
          output=$(python scripts/hamming_run_test.py)
          echo "test_run_id=$output" >> $GITHUB_OUTPUT

      - name: Wait for test to complete
        id: wait_for_test
        env:
          HAMMING_API_KEY: ${{ secrets.HAMMING_API_KEY }}
          TIMEOUT_SECONDS: ${{ inputs.timeout_seconds }}
        run: |
          python scripts/hamming_wait_test_run.py ${{ steps.run_test.outputs.test_run_id }}

      - name: Check test results
        env:
          HAMMING_API_KEY: ${{ secrets.HAMMING_API_KEY }}
        run: |
          python scripts/hamming_check_results.py ${{ steps.run_test.outputs.test_run_id }}
```

### 2. Example Caller Workflows

#### Smoke Test Workflow (`.github/workflows/smoke-test.yml`)
```yaml
name: Smoke Test

on:
  push:
    branches: [main]
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours

jobs:
  smoke-test:
    uses: HammingHQ/hamming-ci-workflow-v2/.github/workflows/hamming_run_test.yml@main
    with:
      agent_id: "your-agent-id"
      phone_numbers: "+1234567890"
      tag_ids: "smoke-test"
    secrets:
      HAMMING_API_KEY: ${{ secrets.HAMMING_API_KEY }}
```

#### Regression Test Workflow (`.github/workflows/regression-test.yml`)
```yaml
name: Regression Test

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  regression-test:
    uses: HammingHQ/hamming-ci-workflow-v2/.github/workflows/hamming_run_test.yml@main
    with:
      agent_id: "your-agent-id"  
      phone_numbers: "+1234567890,+0987654321"
      tag_ids: "regression,pr-test"
      timeout_seconds: "900"
    secrets:
      HAMMING_API_KEY: ${{ secrets.HAMMING_API_KEY }}
```

#### Specific Test Cases Workflow (`.github/workflows/specific-tests.yml`)
```yaml
name: Specific Tests

on:
  workflow_dispatch:
    inputs:
      test_cases:
        description: 'Test case IDs to run'
        required: true
        default: 'test-case-1,test-case-2'

jobs:
  specific-tests:
    uses: HammingHQ/hamming-ci-workflow-v2/.github/workflows/hamming_run_test.yml@main
    with:
      agent_id: "your-agent-id"
      phone_numbers: "+1234567890"
      test_case_ids: ${{ github.event.inputs.test_cases }}
    secrets:
      HAMMING_API_KEY: ${{ secrets.HAMMING_API_KEY }}
```

## Key Differences in Workflows (v1 vs v2)

### v1 Workflow
- Single selection method: `dataset_id`
- Single phone number: `to_number`
- Returns: `experiment_id`

### v2 Workflow
- Multiple selection methods: `tag_ids` OR `test_case_ids`
- Multiple phone numbers: `phone_numbers` (comma-separated)
- Returns: `test_run_id`
- Enhanced validation and error handling
- Support for test case overrides (in scripts)

## Next Steps

1. Review and approve this plan
2. Create the repository structure
3. Implement type definitions
4. Build core scripts iteratively
5. Create GitHub Actions workflows
6. Test with real API endpoints
7. Document and release