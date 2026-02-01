# LLM Provider Integration Testing Guide

This guide explains how to test the Interview Question Generator with different LLM providers (OpenAI, Anthropic, Google, Z.ai).

## Overview

The Interview Question Generator supports 4 LLM providers:
- **OpenAI** (GPT models)
- **Anthropic** (Claude models)
- **Google** (Gemini models)
- **Z.ai** (OpenAI-compatible API)

Each provider has been integrated with proper error handling, response parsing, and JSON format handling.

## Test Files

### 1. Integration Tests (`test_llm_provider_integration.py`)

Formal pytest integration tests that verify each provider works correctly with real API calls.

**Location:** `backend/tests/test_llm_provider_integration.py`

**Features:**
- Tests each provider independently
- Verifies question structure and format
- Compares results across providers
- Skips tests for providers without API keys

**Usage:**
```bash
# Run all integration tests (with all configured providers)
cd backend
pytest tests/test_llm_provider_integration.py -v

# Run specific provider tests
pytest tests/test_llm_provider_integration.py::TestOpenAIIntegration -v
pytest tests/test_llm_provider_integration.py::TestAnthropicIntegration -v
pytest tests/test_llm_provider_integration.py::TestGoogleIntegration -v
pytest tests/test_llm_provider_integration.py::TestZaiIntegration -v

# Run with detailed output
pytest tests/test_llm_provider_integration.py -v -s

# Skip integration tests
pytest tests/test_llm_provider_integration.py -v -m "not integration"
```

### 2. Manual Testing Script (`test_llm_providers.py`)

Standalone Python script for manual testing and verification. Easier to run than pytest and provides more detailed output.

**Location:** `backend/test_llm_providers.py`

**Features:**
- Interactive testing with colored terminal output
- Tests all or specific providers
- Shows question examples and details
- Saves results to JSON file
- Displays timing and performance metrics
- No pytest dependency

**Usage:**
```bash
# Test all configured providers
cd backend
python test_llm_providers.py

# Test specific providers
python test_llm_providers.py --providers openai,anthropic

# Test single provider with verbose output
python test_llm_providers.py --providers openai --verbose

# Save results to JSON file
python test_llm_providers.py --providers all --save llm_test_results.json

# Combine options
python test_llm_providers.py --providers openai,anthropic --verbose --save results.json
```

**Options:**
- `--providers`: Comma-separated list (openai,anthropic,google,zai,all) - Default: all
- `--verbose`: Show detailed question output including rationales and expected answers
- `--save`: Save results to JSON file (creates separate file per provider)

## Prerequisites

### 1. Install Dependencies

Ensure all required packages are installed:

```bash
cd backend
pip install -r requirements.txt
```

Required packages:
- `openai` - For OpenAI and Z.ai providers
- `anthropic` - For Anthropic provider
- `google-generativeai` - For Google provider

### 2. Configure API Keys

Set API keys as environment variables. You can:

**Option A: Set in terminal**
```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_API_KEY="AI..."
export ZAI_API_KEY="zai-..."
```

**Option B: Create `.env` file in backend directory**
```bash
cd backend
cat > .env << EOF
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AI...
ZAI_API_KEY=zai-...
EOF
```

The application will automatically load `.env` file using `python-dotenv`.

**Option C: Use system environment**
Add to your `~/.bashrc` or `~/.zshrc`:
```bash
export OPENAI_API_KEY="sk-..."
```

## Expected Test Results

### OpenAI Provider

**Model:** `gpt-4o-mini` (recommended for testing, cheaper)
**Expected Questions:**
- 4-6 technical questions
- 3-4 behavioral questions
- 2-3 situational questions
- 3-5 skill verification questions
- 2-5 areas to probe
- 2-5 interview tips

**Example Output:**
```
Testing OPENAI Provider
✓ Questions generated in 12.45 seconds

Summary:
  Total Questions: 15
  Technical Questions: 5
  Behavioral Questions: 4
  Situational Questions: 3
  Skill Verification Questions: 3
  Areas to Probe: 4
  Skill Gaps to Address: 2
  Interview Tips: 3
```

### Anthropic Provider

**Model:** `claude-3-5-sonnet-20241022` (recommended for testing)
**Expected Questions:** Similar to OpenAI

**Example Output:**
```
Testing ANTHROPIC Provider
✓ Questions generated in 8.23 seconds

Summary:
  Total Questions: 14
  Technical Questions: 4
  Behavioral Questions: 3
  Situational Questions: 3
  Skill Verification Questions: 4
  ...
```

### Google Provider

**Model:** `gemini-1.5-flash` (recommended for faster testing)
**Expected Questions:** Similar to OpenAI

**Example Output:**
```
Testing GOOGLE Provider
✓ Questions generated in 6.78 seconds

Summary:
  Total Questions: 16
  Technical Questions: 5
  Behavioral Questions: 4
  ...
```

### Z.ai Provider

**Model:** `gpt-4o-mini` (or any OpenAI-compatible model)
**Expected Questions:** Similar to OpenAI

## Verification Checklist

For each provider, verify:

- [ ] API key is configured and accessible
- [ ] Questions are generated successfully
- [ ] All 4 question categories are present:
  - [ ] Technical questions
  - [ ] Behavioral questions
  - [ ] Situational questions
  - [ ] Skill verification questions
- [ ] Questions have proper structure:
  - [ ] id field present
  - [ ] text field is non-empty
  - [ ] difficulty field is valid (beginner/intermediate/advanced)
  - [ ] skills field is a list
  - [ ] rationale field is present
  - [ ] expected_answers field is a list
  - [ ] follow_up_suggestions field is a list
- [ ] Questions are relevant to:
  - [ ] Job requirements (Python, Django, FastAPI, etc.)
  - [ ] Candidate's experience
  - [ ] Skill gaps identified
- [ ] Additional fields are present:
  - [ ] areas_to_probe list
  - [ ] skill_gaps_to_address list
  - [ ] interview_tips list
- [ ] Metadata is correct:
  - [ ] provider field matches provider name
  - [ ] model field is correct
  - [ ] generated_at timestamp is present

## Common Issues and Solutions

### Issue: "API key not configured"

**Solution:** Set the API key environment variable:
```bash
export OPENAI_API_KEY="your-key-here"
```

### Issue: "Package not installed"

**Solution:** Install the required package:
```bash
pip install openai anthropic google-generativeai
```

### Issue: "Invalid JSON response"

**Solution:** This usually means the LLM didn't return valid JSON. Check:
- API key has sufficient credits
- Model name is correct
- Network connection is stable

### Issue: "Rate limit exceeded"

**Solution:** Wait a few minutes and try again, or use a different model/provider for testing.

### Issue: "Questions are empty"

**Solution:** Check that:
- Resume text is not empty
- Job description is not empty
- Required skills list is not empty
- API key is valid

## Sample Output (Verbose Mode)

When running with `--verbose` flag, you'll see detailed output:

```
Testing OPENAI Provider

ℹ Initializing OPENAI generator with model: gpt-4o-mini
ℹ Generating interview questions...
ℹ This may take 10-30 seconds depending on the provider...
✓ Questions generated in 12.45 seconds

GENERATION SUCCESSFUL
================================================================================

Summary:
  Total Questions: 15
  Technical Questions: 5
  Behavioral Questions: 4
  Situational Questions: 3
  Skill Verification Questions: 3
  Areas to Probe: 4
  Skill Gaps to Address: 2
  Interview Tips: 3
  Generation Time: 12.45 seconds

TECHNICAL QUESTIONS (5)
────────────────────────────────────────────────────────────────────────────────

Q1: Explain how you would design a RESTful API using FastAPI for a high-traffic application...
  Difficulty: advanced | Skills: FastAPI, REST APIs, Python, Architecture

  ID: tech_1
  Rationale: This question tests the candidate's ability to design scalable APIs...
  Expected Answers: Discussion of async/await, database connection pooling, caching...
  Follow-ups: How would you handle authentication? What about rate limiting?

Q2: Describe your experience with Django ORM and how you've optimized database queries...
  Difficulty: intermediate | Skills: Django, PostgreSQL, Optimization
  ...

BEHAVIORAL QUESTIONS (4)
────────────────────────────────────────────────────────────────────────────────

Q1: Tell me about a time you had to mentor a junior developer...
  Difficulty: intermediate | Skills: Leadership, Communication
  ...

AREAS TO PROBE:
  • Verify 5 years of Python development experience
  • Deep dive into FastAPI vs Django decision-making
  • Assess actual Kubernetes experience vs Docker knowledge
  • Verify team leadership scope and achievements

SKILL GAPS TO ADDRESS:
  • Kubernetes experience (candidate lists it but needs verification)
  • Team leadership depth (needs examples of mentoring difficult situations)

INTERVIEW TIPS:
  • Ask for specific examples of architectural decisions
  • Probe into the "40% performance improvement" claim
  • Verify hands-on vs theoretical Kubernetes knowledge
  • Assess coaching style and leadership approach

✓ Results saved to: llm_test_results_openai.json
✓ OPENAI provider test PASSED
```

## Performance Benchmarks

Typical generation times (may vary):

| Provider | Model | Avg Time | Cost (per 1K tokens) |
|----------|-------|----------|----------------------|
| OpenAI   | gpt-4o-mini | 10-15s | $0.00015 |
| Anthropic | claude-3-5-sonnet | 8-12s | $0.0003 |
| Google   | gemini-1.5-flash | 6-10s | $0.000075 |
| Z.ai     | gpt-4o-mini | 10-15s | Varies |

## Continuous Integration

To add LLM provider testing to CI/CD:

**Important:** Do NOT add real API keys to CI/CD. These tests should:
1. Run in local environments only
2. Use mocked responses in CI/CD
3. Be skipped with `pytest -m "not integration"` in CI

**Example GitLab CI:**
```yaml
test:llm:
  stage: test
  script:
    - pytest tests/test_llm_provider_integration.py -v -m "not integration"
  only:
    - merge_requests
    - main
```

## Support

For issues or questions:
1. Check the error message carefully
2. Verify API keys are set correctly
3. Check network connectivity
4. Review the code in `backend/analyzers/interview_question_generator.py`
5. Run unit tests: `pytest tests/test_interview_question_generator.py -v`

## Next Steps

After successful LLM provider testing:
1. Run full API endpoint tests: `pytest tests/api/test_interview_prep.py -v`
2. Run end-to-end workflow test: `./verify-e2e.sh`
3. Verify frontend integration: Navigate to http://localhost:5173/interview-prep/{id}
4. Test with real resume and vacancy data
