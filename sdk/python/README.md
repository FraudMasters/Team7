# AgentHR Python SDK

The official Python SDK for AgentHR - AI-powered resume analysis and candidate ranking system.

## Installation

```bash
pip install agenthr
```

## Quick Start

```python
from agenthr import Client

# Initialize the client
client = Client(api_key="your-api-key-here")

# Upload a resume
resume = client.resumes.upload("path/to/resume.pdf")
print(f"Resume uploaded: {resume.id}")

# Create a vacancy
vacancy = client.vacancies.create(
    title="Senior Python Developer",
    description="We are looking for an experienced Python developer...",
    required_skills=["Python", "FastAPI", "PostgreSQL"]
)
print(f"Vacancy created: {vacancy.id}")

# Find matching candidates
matches = client.vacancies.find_matches(vacancy.id)
for match in matches:
    print(f"{match.name}: {match.score:.1%}")

# Close the client when done
client.close()
```

Or use it as a context manager:

```python
from agenthr import Client

with Client(api_key="your-api-key-here") as client:
    # Your code here
    vacancies = client.vacancies.list()
    print(f"Found {len(vacancies)} vacancies")
```

## Configuration

The SDK can be configured via environment variables or constructor parameters:

```python
import os
from agenthr import Client

# Via environment variables
os.environ["AGENTHR_API_KEY"] = "your-api-key"
os.environ["AGENTHR_API_URL"] = "https://api.agenthr.dev"

client = Client()

# Or via constructor
client = Client(
    api_key="your-api-key-here",
    base_url="https://api.agenthr.dev",
    timeout=30.0
)
```

## API Resources

### Resumes

Upload and manage resumes:

```python
# Upload a resume
resume = client.resumes.upload("resume.pdf", vacancy_id="optional-vacancy-id")

# List resumes
resumes = client.resumes.list(limit=50, status="completed")

# Get resume details
resume = client.resumes.get(resume_id)

# Get parsed data
parsed = resume.parsed_data
print(f"Name: {parsed.name}")
print(f"Email: {parsed.email}")
print(f"Skills: {parsed.skills}")
```

### Vacancies

Manage job vacancies:

```python
# Create a vacancy
vacancy = client.vacancies.create(
    title="Senior Python Developer",
    description="Job description here...",
    required_skills=["Python", "FastAPI", "SQL"],
    min_experience=5,
    location="Remote",
    salary_min=100000,
    salary_max=150000
)

# List vacancies
vacancies = client.vacancies.list()

# Get vacancy details
vacancy = client.vacancies.get(vacancy_id)

# Find matching candidates
matches = client.vacancies.find_matches(vacancy_id, limit=10)
```

### Candidates

Manage candidates and their pipeline stages:

```python
# List candidates
candidates = client.candidates.list(vacancy_id="xxx", stage="screening")

# Get candidate details
candidate = client.candidates.get(candidate_id)

# Move candidate to next stage
client.candidates.move(
    candidate_id="xxx",
    stage_id="interview",
    vacancy_id="yyy",
    notes="Strong technical skills"
)
```

### Ranking

Get AI-powered candidate rankings:

```python
# Rank a candidate for a vacancy
ranking = client.ranking.rank(
    vacancy_id="xxx",
    resume_id="yyy"
)
print(f"Score: {ranking.score:.1%}")
print(f"Explanation: {ranking.explanation}")
```

### Analytics

Query recruitment analytics:

```python
# Get key metrics
metrics = client.analytics.get_key_metrics(
    start_date="2024-01-01",
    end_date="2024-12-31"
)
print(f"Time to Hire: {metrics.time_to_hire_days} days")

# Get funnel metrics
funnel = client.analytics.get_funnel()
for stage in funnel.stages:
    print(f"{stage.name}: {stage.count} candidates")
```

### Webhooks

Manage webhook subscriptions:

```python
# Create a webhook subscription
webhook = client.webhooks.create(
    url="https://your-app.com/webhooks",
    events=["candidate.created", "stage.changed"]
)

# List webhooks
webhooks = client.webhooks.list()

# Get delivery logs
logs = client.webhooks.get_delivery_logs(webhook_id)

# Delete webhook
client.webhooks.delete(webhook_id)
```

### API Keys

Manage API keys (requires admin permissions):

```python
# Generate a new API key
key = client.api_keys.generate(
    name="Production Key",
    scopes=["read:candidates", "write:candidates"],
    rate_limit_per_minute=100
)
print(f"API Key: {key.key}")  # Only shown once!

# List API keys
keys = client.api_keys.list()

# Revoke a key
client.api_keys.revoke(key_id)
```

### Workflows

Manage workflow automations:

```python
# Create a workflow
workflow = client.workflows.create(
    name="Auto-reply to candidates",
    trigger={
        "type": "webhook",
        "event": "candidate.created"
    },
    actions=[
        {
            "type": "send_email",
            "to": "{{candidate.email}}",
            "subject": "Application Received",
            "body": "Thank you for applying..."
        }
    ]
)

# Execute a workflow manually
execution = client.workflows.execute(workflow_id)

# Get execution history
history = client.workflows.get_executions(workflow_id)
```

### Plugins

Manage plugin installations:

```python
# List available plugins
plugins = client.plugins.list(category="integration")

# Install a plugin
installation = client.plugins.install(plugin_id)

# List installed plugins
installed = client.plugins.list_installed()

# Uninstall a plugin
client.plugins.uninstall(installation_id)
```

## Error Handling

The SDK provides detailed error information:

```python
from agenthr import Client
from agenthr.exceptions import (
    APIError,
    AuthenticationError,
    RateLimitError,
    ValidationError
)

try:
    client = Client(api_key="invalid-key")
    client.vacancies.list()
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
except RateLimitError as e:
    print(f"Rate limited: {e.retry_after} seconds until reset")
except ValidationError as e:
    print(f"Validation error: {e.errors}")
except APIError as e:
    print(f"API error: {e}")
```

## Advanced Usage

### Async Client

For async/await support:

```python
import asyncio
from agenthr import AsyncClient

async def main():
    async with AsyncClient(api_key="your-api-key") as client:
        vacancies = await client.vacancies.list()
        print(f"Found {len(vacancies)} vacancies")

asyncio.run(main())
```

### Custom HTTP Configuration

```python
from agenthr import Client
import httpx

# Custom HTTP client with additional configuration
http_client = httpx.Client(
    timeout=60.0,
    proxies={"http://": "http://localhost:8080"},
    verify=False  # Only for testing
)

client = Client(api_key="your-key", http_client=http_client)
```

### Pagination

The SDK handles pagination automatically:

```python
# Iterate through all vacancies
for vacancy in client.vacancies.iter_all():
    print(vacancy.title)

# Or use pages
page = client.vacancies.list(offset=0, limit=50)
while page.items:
    for vacancy in page.items:
        print(vacancy.title)
    page = client.vacancies.list(offset=page.next_offset, limit=50)
```

## Development

Install in development mode:

```bash
git clone https://github.com/agenthr/agenthr
cd agenthr/sdk/python
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

Run linter:

```bash
ruff check agenthr
mypy agenthr
```

## License

MIT License - see LICENSE file for details.

## Support

- Documentation: https://docs.agenthr.dev
- GitHub: https://github.com/agenthr/agenthr
- Issues: https://github.com/agenthr/agenthr/issues
- Email: support@agenthr.dev
