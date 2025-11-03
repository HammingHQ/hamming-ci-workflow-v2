# Hamming CI Workflow v2

A GitHub Actions workflow for running Hamming voice agent tests in CI/CD pipelines. This is the successor to hamming-ci-workflow, using the new REST API endpoints with enhanced validation and tag support.

## Features

- 🏷️ **Tag-based test selection** - Run tests by tags or specific test case IDs
- 📞 **Multiple phone numbers** - Test with multiple phone numbers in parallel
- ✅ **Enhanced validation** - Pre-execution validation prevents empty test runs
- 📊 **Detailed results** - Get comprehensive test results with scores and transcripts
- 🔄 **GitHub Actions integration** - Reusable workflows for easy CI/CD setup
- 🚦 **PR comments** - Automatic test results posted to pull requests
- 🐍 **Official Python SDK** - Uses Hamming's official Python SDK for type safety and reliability

## Quick Start

### Using in Your Repository

1. **Create a workflow file** in your repo (`.github/workflows/voice-tests.yml`):

```yaml
name: Voice Tests

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    uses: HammingHQ/hamming-ci-workflow-v2/.github/workflows/hamming_run_test.yml@main
    with:
      agent_id: ${{ vars.AGENT_ID }}
      phone_numbers: ${{ vars.PHONE_NUMBERS }}
      tag_ids: ${{ vars.TEST_TAGS }}
    secrets:
      HAMMING_API_KEY: ${{ secrets.HAMMING_API_KEY }}
```

2. **Configure repository secrets and variables**:
   - Go to Settings → Secrets and variables → Actions
   - Add secret: `HAMMING_API_KEY`
   - Add variables: `AGENT_ID`, `PHONE_NUMBERS`, `TEST_TAGS`

3. **Push to trigger tests** - Tests will run automatically on push/PR

## Configuration

### Repository Secrets
- `HAMMING_API_KEY` - Your Hamming API key (required)

### Repository Variables

#### For General Tests
- `AGENT_ID` - The agent ID to test
- `PHONE_NUMBERS` - Comma-separated phone numbers (e.g., `+15551234567,+15559876543`)
- `TEST_TAGS` - Comma-separated tag IDs for test selection

#### For Smoke Tests
- `SMOKE_TEST_AGENT_ID` - Agent ID for smoke tests
- `SMOKE_TEST_PHONE_NUMBERS` - Phone numbers for smoke tests
- `SMOKE_TEST_TAGS` - Tags for smoke test selection

## Workflow Inputs

The reusable workflow accepts these inputs:

| Input | Required | Description | Example |
|-------|----------|-------------|---------|
| `agent_id` | Yes | Agent ID to test | `agent-123` |
| `phone_numbers` | Yes | Comma-separated phone numbers | `+15551234567` |
| `tag_ids` | No* | Comma-separated tag IDs | `cmc220l4i00zsgn0gvqkvpvxh` |
| `test_case_ids` | No* | Comma-separated test case IDs | `case-1,case-2` |
| `timeout_seconds` | No | Max wait time (default: 900) | `1200` |
| `min_score_threshold` | No | Minimum passing score (default: 0.0) | `0.7` |

\* Either `tag_ids` OR `test_case_ids` must be provided (not both)

## Usage Examples

### Basic Test with Tags

```yaml
jobs:
  test:
    uses: HammingHQ/hamming-ci-workflow-v2/.github/workflows/hamming_run_test.yml@main
    with:
      agent_id: "agent-123"
      phone_numbers: "+15551234567"
      tag_ids: "regression,critical"
    secrets:
      HAMMING_API_KEY: ${{ secrets.HAMMING_API_KEY }}
```

### Test Specific Test Cases

```yaml
jobs:
  test:
    uses: HammingHQ/hamming-ci-workflow-v2/.github/workflows/hamming_run_test.yml@main
    with:
      agent_id: "agent-123"
      phone_numbers: "+15551234567,+15559876543"
      test_case_ids: "test-case-1,test-case-2"
      min_score_threshold: "0.8"
    secrets:
      HAMMING_API_KEY: ${{ secrets.HAMMING_API_KEY }}
```

### Smoke Tests on Schedule

```yaml
name: Scheduled Smoke Tests

on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours

jobs:
  smoke:
    uses: HammingHQ/hamming-ci-workflow-v2/.github/workflows/hamming_run_test.yml@main
    with:
      agent_id: ${{ vars.SMOKE_TEST_AGENT_ID }}
      phone_numbers: ${{ vars.SMOKE_TEST_PHONE_NUMBERS }}
      tag_ids: ${{ vars.SMOKE_TEST_TAGS }}
    secrets:
      HAMMING_API_KEY: ${{ secrets.HAMMING_API_KEY }}
```

### Manual Trigger with Inputs

```yaml
name: Manual Test

on:
  workflow_dispatch:
    inputs:
      tags:
        description: 'Tags to test'
        required: true
        default: 'smoke-test'

jobs:
  test:
    uses: HammingHQ/hamming-ci-workflow-v2/.github/workflows/hamming_run_test.yml@main
    with:
      agent_id: ${{ vars.AGENT_ID }}
      phone_numbers: ${{ vars.PHONE_NUMBERS }}
      tag_ids: ${{ github.event.inputs.tags }}
    secrets:
      HAMMING_API_KEY: ${{ secrets.HAMMING_API_KEY }}
```

## Local Development

### Setup

1. Clone the repository:
```bash
git clone https://github.com/HammingHQ/hamming-ci-workflow-v2.git
cd hamming-ci-workflow-v2
```

2. Set your Hamming API key (required for SDK installation):
```bash
export HAMMING_API_KEY=sk-***
```

3. Install dependencies:
```bash
pip install -r requirements.txt
# Install Hamming Python SDK (requires API key)
pip install "https://app.hamming.ai/api/sdk/python/hamming_sdk-0.1.22-py3-none-any.whl?key=$HAMMING_API_KEY"
```

4. Copy and configure environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

**Note**: The Hamming SDK requires your API key during installation. The SDK is not available on PyPI and must be installed directly from the Hamming API URL.

### Running Scripts Locally

```bash
# Run a test with tags
export AGENT_ID="your-agent-id"
export PHONE_NUMBERS="+15551234567"
export TAG_IDS="smoke-test"
python scripts/hamming_run_test.py

# Wait for completion (outputs test run ID)
python scripts/hamming_wait_test_run.py <test-run-id>

# Check results (pipe from wait script)
python scripts/hamming_wait_test_run.py <test-run-id> | python scripts/hamming_check_results.py
```

## API Endpoints Used

This workflow uses the following Hamming API endpoints:

- `POST /api/rest/test-runs/test-inbound-agent` - Create test run with configurations array
- `GET /api/rest/test-runs/{id}/status` - Check test run status
- `GET /api/rest/test-runs/{id}/results` - Get test results

### API Request Format

The workflow sends requests in this format:
```json
{
  "agentId": "your-agent-id",
  "phoneNumbers": ["+15551234567"],
  "testConfigurations": [
    {"tagId": "your-tag-id"}  // or {"testCaseId": "test-case-id"}
  ]
}
```

**Note:** The API documentation examples show `configurations`, but the actual API expects `testConfigurations`.

## Troubleshooting

### No test cases found
If you see "WARNING: No test cases were found for the specified criteria":
- Verify your agent has test cases with the specified tags
- Check tag IDs are correct (case-sensitive)
- Try using specific test case IDs instead of tags

### Authentication errors
- Ensure `HAMMING_API_KEY` is set correctly as a repository secret
- Verify the API key has appropriate permissions

### Phone number errors
- Phone numbers must include country code with `+` (e.g., `+15551234567`)
- Multiple numbers should be comma-separated
- Remove any trailing commas

### Workflow not appearing
For manual workflows (`workflow_dispatch`):
- The workflow must be on the default branch to appear in Actions UI
- Check Settings → General → Default branch

## Migration from v1

Key differences from hamming-ci-workflow v1:

| Feature | v1 | v2 |
|---------|----|----|
| Test Selection | `dataset_id` | `testConfigurations` array with `tagId` or `testCaseId` |
| Phone Numbers | Single `to_number` | Multiple `phone_numbers` array |
| API Endpoint | `/voice-agent/{id}/run` | `/test-runs/test-inbound-agent` |
| Request Format | Flat parameters | Structured `testConfigurations` array |
| Validation | Minimal | Comprehensive pre-execution |
| Response | `experiment_id` | Full `testRunId` and results |

## Contributing

See [PLAN.md](PLAN.md) for architecture details and [CI_CD_SETUP.md](CI_CD_SETUP.md) for CI/CD configuration guide.

## License

[Add your license here]