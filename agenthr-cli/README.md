# AgentHR CLI

Command-line interface for AgentHR - AI-powered resume analysis and candidate ranking system.

## Installation

```bash
pip install agenthr-cli
```

## Configuration

The CLI requires an API key to authenticate with the AgentHR backend. Set the `AGENTHR_API_KEY` environment variable:

```bash
export AGENTHR_API_KEY="your-api-key-here"
```

Or configure the API base URL:

```bash
export AGENTHR_API_URL="http://localhost:8000"
```

## Usage

### Resume Commands

Upload and manage resumes:

```bash
# Upload a resume file
agenthr resume upload path/to/resume.pdf

# List all resumes
agenthr resume list

# Get resume details
agenthr resume get <resume_id>

# Search resumes
agenthr resume search "python developer"
```

### Vacancy Commands

Manage job vacancies:

```bash
# Create a new vacancy
agenthr vacancy create --title "Senior Python Developer" --description "Job description..."

# List all vacancies
agenthr vacancy list

# Get vacancy details
agenthr vacancy get <vacancy_id>

# Update a vacancy
agenthr vacancy update <vacancy_id> --title "New Title"
```

### Candidate Commands

Manage candidates:

```bash
# List candidates for a vacancy
agenthr candidate list --vacancy <vacancy_id>

# Get candidate details
agenthr candidate get <candidate_id>

# Move candidate to a different stage
agenthr candidate move <candidate_id> --stage "interview"

# Rank candidates for a vacancy
agenthr candidate rank --vacancy <vacancy_id>
```

### Analytics Commands

Query analytics data:

```bash
# Get analytics overview
agenthr analytics overview

# Get candidate statistics
agenthr analytics candidates

# Get vacancy statistics
agenthr analytics vacancies
```

### Configuration

Manage CLI configuration:

```bash
# Show current configuration
agenthr config show

# Set API key
agenthr config set api-key YOUR_KEY

# Set API URL
agenthr config set api-url http://localhost:8000
```

## Development

Install in development mode:

```bash
cd agenthr-cli
pip install -e .
```

Run tests:

```bash
pytest tests/
```

## License

MIT License - see LICENSE file for details.
