# CI/CD Setup Guide

## GitHub Repository Configuration

To use the Hamming CI Workflow v2 in GitHub Actions, you need to configure the following:

### 1. Repository Secrets (Settings → Secrets and variables → Actions → Secrets)

**Required Secret:**
- `HAMMING_API_KEY` - Your Hamming API key (get from https://app.hamming.ai/settings)

### 2. Repository Variables (Settings → Secrets and variables → Actions → Variables)

**Recommended Variables:**
```
AGENT_ID = your-agent-id-here
TEST_PHONE_NUMBERS = +12345678901,+10987654321
```

### 3. Using in Your Workflow

#### Option A: Use Repository Variables
```yaml
jobs:
  test:
    uses: HammingHQ/hamming-ci-workflow-v2/.github/workflows/hamming_run_test.yml@main
    with:
      agent_id: ${{ vars.AGENT_ID }}
      phone_numbers: ${{ vars.TEST_PHONE_NUMBERS }}
      tag_ids: "smoke-test"
    secrets:
      HAMMING_API_KEY: ${{ secrets.HAMMING_API_KEY }}
```

#### Option B: Hardcode Values
```yaml
jobs:
  test:
    uses: HammingHQ/hamming-ci-workflow-v2/.github/workflows/hamming_run_test.yml@main
    with:
      agent_id: "agent-abc123"
      phone_numbers: "+12345678901,+10987654321"
      tag_ids: "regression"
    secrets:
      HAMMING_API_KEY: ${{ secrets.HAMMING_API_KEY }}
```

#### Option C: Dynamic Values
```yaml
jobs:
  test:
    uses: HammingHQ/hamming-ci-workflow-v2/.github/workflows/hamming_run_test.yml@main
    with:
      agent_id: ${{ github.event.inputs.agent_id }}
      phone_numbers: ${{ github.event.inputs.phone_numbers }}
      test_case_ids: ${{ github.event.inputs.test_cases }}
    secrets:
      HAMMING_API_KEY: ${{ secrets.HAMMING_API_KEY }}
```

## Environment-Specific Configurations

### Production Testing
```yaml
# Repository Variables for Production
PROD_AGENT_ID = prod-agent-123
PROD_PHONE_NUMBERS = +18005551234
PROD_TAGS = production,critical-path
```

### Staging Testing
```yaml
# Repository Variables for Staging
STAGING_AGENT_ID = staging-agent-456
STAGING_PHONE_NUMBERS = +18005555678
STAGING_TAGS = staging,smoke-test
```

### Development Testing
```yaml
# Repository Variables for Development
DEV_AGENT_ID = dev-agent-789
DEV_PHONE_NUMBERS = +18005559999
DEV_TAGS = development,experimental
```

## Example Multi-Environment Workflow

```yaml
name: Multi-Environment Tests

on:
  push:
    branches: [main, staging, develop]

jobs:
  determine-environment:
    runs-on: ubuntu-latest
    outputs:
      agent_id: ${{ steps.set-env.outputs.agent_id }}
      phone_numbers: ${{ steps.set-env.outputs.phone_numbers }}
      tags: ${{ steps.set-env.outputs.tags }}
    steps:
      - id: set-env
        run: |
          if [[ "${{ github.ref }}" == "refs/heads/main" ]]; then
            echo "agent_id=${{ vars.PROD_AGENT_ID }}" >> $GITHUB_OUTPUT
            echo "phone_numbers=${{ vars.PROD_PHONE_NUMBERS }}" >> $GITHUB_OUTPUT
            echo "tags=${{ vars.PROD_TAGS }}" >> $GITHUB_OUTPUT
          elif [[ "${{ github.ref }}" == "refs/heads/staging" ]]; then
            echo "agent_id=${{ vars.STAGING_AGENT_ID }}" >> $GITHUB_OUTPUT
            echo "phone_numbers=${{ vars.STAGING_PHONE_NUMBERS }}" >> $GITHUB_OUTPUT
            echo "tags=${{ vars.STAGING_TAGS }}" >> $GITHUB_OUTPUT
          else
            echo "agent_id=${{ vars.DEV_AGENT_ID }}" >> $GITHUB_OUTPUT
            echo "phone_numbers=${{ vars.DEV_PHONE_NUMBERS }}" >> $GITHUB_OUTPUT
            echo "tags=${{ vars.DEV_TAGS }}" >> $GITHUB_OUTPUT
          fi

  run-tests:
    needs: determine-environment
    uses: ./.github/workflows/hamming_run_test.yml
    with:
      agent_id: ${{ needs.determine-environment.outputs.agent_id }}
      phone_numbers: ${{ needs.determine-environment.outputs.phone_numbers }}
      tag_ids: ${{ needs.determine-environment.outputs.tags }}
    secrets:
      HAMMING_API_KEY: ${{ secrets.HAMMING_API_KEY }}
```

## Security Best Practices

1. **Never hardcode API keys** - Always use GitHub Secrets
2. **Use repository variables** for non-sensitive configuration
3. **Limit secret access** - Only give access to workflows that need it
4. **Rotate API keys regularly** - Update the secret periodically
5. **Use environment protection rules** for production deployments

## GitHub Actions Versions

This workflow uses the latest stable versions of GitHub Actions:
- `actions/checkout@v4`
- `actions/setup-python@v5`
- `actions/upload-artifact@v4`
- `actions/github-script@v7`

## Troubleshooting

### Common Issues

1. **"HAMMING_API_KEY is not set"**
   - Ensure the secret is added to your repository
   - Check the secret name matches exactly

2. **"Must specify either tag_ids or test_case_ids"**
   - Provide one selection method in your workflow
   - Don't provide both at the same time

3. **"Phone number must start with '+'"**
   - Ensure all phone numbers include country code
   - Format: +1234567890 (not 1234567890)

4. **Workflow not found**
   - Ensure you're referencing the correct repository and branch
   - Format: `owner/repo/.github/workflows/file.yml@branch`