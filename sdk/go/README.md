# AgentHR Go SDK

The official Go SDK for AgentHR - AI-powered resume analysis and candidate ranking system.

## Installation

```bash
go get github.com/agenthr/agenthr-go
```

## Quick Start

```go
package main

import (
    "context"
    "fmt"
    "log"

    "github.com/agenthr/agenthr-go"
)

func main() {
    // Initialize the client
    client := agenthr.NewClient("your-api-key-here", nil)

    // Upload a resume
    resume, err := client.Resumes.Upload(context.Background(), "path/to/resume.pdf", nil)
    if err != nil {
        log.Fatal(err)
    }
    fmt.Printf("Resume uploaded: %s\n", resume.ID)

    // Create a vacancy
    vacancy, err := client.Vacancies.Create(context.Background(), &agenthr.VacancyCreateRequest{
        Title:          "Senior Go Developer",
        Description:    "We are looking for an experienced Go developer...",
        RequiredSkills: []string{"Go", "PostgreSQL", "gRPC"},
    })
    if err != nil {
        log.Fatal(err)
    }
    fmt.Printf("Vacancy created: %s\n", vacancy.ID)

    // Find matching candidates
    matches, err := client.Vacancies.FindMatches(context.Background(), vacancy.ID, nil)
    if err != nil {
        log.Fatal(err)
    }
    for _, match := range matches {
        fmt.Printf("%s: %.1f%%\n", match.Name, match.Score*100)
    }
}
```

## Configuration

The SDK can be configured via environment variables or client options:

```go
import (
    "os"
    "github.com/agenthr/agenthr-go"
)

// Via environment variables
// AGENTHR_API_KEY=your-api-key
// AGENTHR_API_URL=https://api.agenthr.dev
client := agenthr.NewClient("", nil)

// Or with custom configuration
client := agenthr.NewClient(
    "your-api-key-here",
    &agenthr.ClientOptions{
        BaseURL: "https://api.agenthr.dev",
        Timeout: 30 * time.Second,
    },
)
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `APIKey` | `string` | `AGENTHR_API_KEY` env var | Your AgentHR API key |
| `BaseURL` | `string` | `http://localhost:8000` | Base URL of the AgentHR API |
| `Timeout` | `time.Duration` | `30s` | Request timeout |
| `HTTPClient` | `*http.Client` | `&http.Client{}` | Custom HTTP client |

## API Resources

### Resumes

Upload and manage resumes:

```go
// Upload a resume
resume, err := client.Resumes.Upload(context.Background(), "resume.pdf", &agenthr.ResumeUploadOptions{
    VacancyID: "optional-vacancy-id",
})

// List resumes
resumes, err := client.Resumes.List(context.Background(), &agenthr.ResumeListOptions{
    Limit:  50,
    Status: "completed",
})

// Get resume details
resume, err := client.Resumes.Get(context.Background(), resumeID)

// Get parsed data
fmt.Printf("Name: %s\n", resume.ParsedData.Name)
fmt.Printf("Email: %s\n", resume.ParsedData.Email)
fmt.Printf("Skills: %v\n", resume.ParsedData.Skills)
```

### Vacancies

Manage job vacancies:

```go
// Create a vacancy
vacancy, err := client.Vacancies.Create(context.Background(), &agenthr.VacancyCreateRequest{
    Title:          "Senior Go Developer",
    Description:    "Job description here...",
    RequiredSkills: []string{"Go", "gRPC", "SQL"},
    MinExperience:  5,
    Location:       "Remote",
    SalaryMin:      100000,
    SalaryMax:      150000,
})

// List vacancies
vacancies, err := client.Vacancies.List(context.Background(), nil)

// Get vacancy details
vacancy, err := client.Vacancies.Get(context.Background(), vacancyID)

// Find matching candidates
matches, err := client.Vacancies.FindMatches(context.Background(), vacancyID, &agenthr.FindMatchesOptions{
    Limit: 10,
})
```

### Candidates

Manage candidates and their pipeline stages:

```go
// List candidates
candidates, err := client.Candidates.List(context.Background(), &agenthr.CandidateListOptions{
    VacancyID: "xxx",
    Stage:     "screening",
})

// Get candidate details
candidate, err := client.Candidates.Get(context.Background(), candidateID)

// Move candidate to next stage
err := client.Candidates.Move(context.Background(), candidateID, &agenthr.MoveCandidateRequest{
    StageID:   "interview",
    VacancyID: "yyy",
    Notes:     "Strong technical skills",
})
```

### Ranking

Get AI-powered candidate rankings:

```go
// Rank a candidate for a vacancy
ranking, err := client.Ranking.Rank(context.Background(), &agenthr.RankingRequest{
    VacancyID: "xxx",
    ResumeID:  "yyy",
})
fmt.Printf("Score: %.1f%%\n", ranking.Score*100)
fmt.Printf("Explanation: %s\n", ranking.Explanation)
```

### Analytics

Query recruitment analytics:

```go
import "time"

// Get key metrics
start := time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC)
end := time.Date(2024, 12, 31, 23, 59, 59, 0, time.UTC)

metrics, err := client.Analytics.GetKeyMetrics(context.Background(), &agenthr.KeyMetricsOptions{
    StartDate: &start,
    EndDate:   &end,
})
fmt.Printf("Time to Hire: %d days\n", metrics.TimeToHireDays)

// Get funnel metrics
funnel, err := client.Analytics.GetFunnel(context.Background(), nil)
for _, stage := range funnel.Stages {
    fmt.Printf("%s: %d candidates\n", stage.Name, stage.Count)
}
```

### Webhooks

Manage webhook subscriptions:

```go
// Create a webhook subscription
webhook, err := client.Webhooks.Create(context.Background(), &agenthr.WebhookCreateRequest{
    URL:    "https://your-app.com/webhooks",
    Events: []string{"candidate.created", "stage.changed"},
})

// List webhooks
webhooks, err := client.Webhooks.List(context.Background(), nil)

// Get delivery logs
logs, err := client.Webhooks.GetDeliveryLogs(context.Background(), webhookID, nil)

// Delete webhook
err := client.Webhooks.Delete(context.Background(), webhookID)
```

### API Keys

Manage API keys (requires admin permissions):

```go
// Generate a new API key
key, err := client.APIKeys.Generate(context.Background(), &agenthr.APIKeyGenerateRequest{
    Name:               "Production Key",
    Scopes:             []string{"read:candidates", "write:candidates"},
    RateLimitPerMinute: 100,
})
fmt.Printf("API Key: %s\n", key.Key) // Only shown once!

// List API keys
keys, err := client.APIKeys.List(context.Background(), nil)

// Revoke a key
err := client.APIKeys.Revoke(context.Background(), keyID)
```

### Workflows

Manage workflow automations:

```go
// Create a workflow
workflow, err := client.Workflows.Create(context.Background(), &agenthr.WorkflowCreateRequest{
    Name: "Auto-reply to candidates",
    Trigger: &agenthr.TriggerConfig{
        Type:  "webhook",
        Event: "candidate.created",
    },
    Actions: []agenthr.ActionConfig{
        {
            Type: "send_email",
            Config: map[string]interface{}{
                "to":      "{{candidate.email}}",
                "subject": "Application Received",
                "body":    "Thank you for applying...",
            },
        },
    },
})

// Execute a workflow manually
execution, err := client.Workflows.Execute(context.Background(), workflowID, nil)

// Get execution history
history, err := client.Workflows.GetExecutions(context.Background(), workflowID, nil)
```

### Plugins

Manage plugin installations:

```go
// List available plugins
plugins, err := client.Plugins.List(context.Background(), &agenthr.PluginListOptions{
    Category: "integration",
})

// Install a plugin
installation, err := client.Plugins.Install(context.Background(), pluginID, nil)

// List installed plugins
installed, err := client.Plugins.ListInstalled(context.Background(), nil)

// Uninstall a plugin
err := client.Plugins.Uninstall(context.Background(), installationID)
```

## Error Handling

The SDK provides detailed error information:

```go
import (
    "errors"
    "github.com/agenthr/agenthr-go"
)

client := agenthr.NewClient("invalid-key", nil)

_, err := client.Vacancies.List(context.Background(), nil)
if err != nil {
    var authErr *agenthr.AuthenticationError
    var rateErr *agenthr.RateLimitError
    var validationErr *agenthr.ValidationError
    var apiErr *agenthr.APIError

    if errors.As(err, &authErr) {
        fmt.Printf("Authentication failed: %v\n", authErr)
    } else if errors.As(err, &rateErr) {
        fmt.Printf("Rate limited: %d seconds until reset\n", rateErr.RetryAfter)
    } else if errors.As(err, &validationErr) {
        fmt.Printf("Validation error: %v\n", validationErr.Errors)
    } else if errors.As(err, &apiErr) {
        fmt.Printf("API error: %v\n", apiErr)
    } else {
        fmt.Printf("Unknown error: %v\n", err)
    }
}
```

## Advanced Usage

### Custom HTTP Client

```go
import (
    "net/http"
    "time"
    "github.com/agenthr/agenthr-go"
)

// Custom HTTP client with additional configuration
httpClient := &http.Client{
    Timeout: 60 * time.Second,
    Transport: &http.Transport{
        MaxIdleConns:        100,
        MaxIdleConnsPerHost: 100,
        IdleConnTimeout:     90 * time.Second,
    },
}

client := agenthr.NewClient("your-key", &agenthr.ClientOptions{
    HTTPClient: httpClient,
})
```

### Pagination

The SDK handles pagination automatically:

```go
// Iterate through all vacancies
page := 0
limit := 50
for {
    vacancies, err := client.Vacancies.List(context.Background(), &agenthr.VacancyListOptions{
        Offset: page * limit,
        Limit:  limit,
    })
    if err != nil {
        log.Fatal(err)
    }

    if len(vacancies) == 0 {
        break
    }

    for _, vacancy := range vacancies {
        fmt.Println(vacancy.Title)
    }

    page++
}
```

### Context with Timeout

```go
import (
    "context"
    "time"
)

// Context with per-request timeout
ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
defer cancel()

vacancies, err := client.Vacancies.List(ctx, nil)
if err != nil {
    // Handle timeout or other errors
    log.Fatal(err)
}
```

### Request/Response Logging

```go
import (
    "log"
    "net/http"
    "os"
)

// Create a custom HTTP client with logging
loggingClient := &http.Client{
    Transport: loggingRoundTripper{
        http.DefaultTransport,
    },
}

client := agenthr.NewClient("your-key", &agenthr.ClientOptions{
    HTTPClient: loggingClient,
})

type loggingRoundTripper struct {
    http.RoundTripper
}

func (lrt loggingRoundTripper) RoundTrip(req *http.Request) (*http.Response, error) {
    log.Printf("Request: %s %s\n", req.Method, req.URL)
    resp, err := lrt.RoundTripper.RoundTrip(req)
    if err != nil {
        return nil, err
    }
    log.Printf("Response: %d %s\n", resp.StatusCode, resp.Status)
    return resp, nil
}
```

## Module Structure

The Go SDK follows standard Go module conventions:

```
github.com/agenthr/agenthr-go
├── agenthr.go              # Main client and types
├── client.go               # Client implementation
├── errors.go               # Error types
├── options.go              # Client and request options
└── resources               # API resource clients
    ├── resumes.go
    ├── vacancies.go
    ├── candidates.go
    ├── ranking.go
    ├── analytics.go
    ├── webhooks.go
    ├── api_keys.go
    ├── workflows.go
    └── plugins.go
```

## Dependencies

The Go SDK has minimal external dependencies:

- **Go 1.21+** - Minimum Go version
- **net/http** - Standard library HTTP client
- **encoding/json** - Standard library JSON encoding

## Development

Clone the repository:

```bash
git clone https://github.com/agenthr/agenthr
cd agenthr/sdk/go
```

Run tests:

```bash
go test ./...
```

Run tests with coverage:

```bash
go test -cover ./...
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out
```

Run linter:

```bash
go vet ./...
golangci-lint run
```

Format code:

```bash
go fmt ./...
gofmt -s -w .
```

Build:

```bash
go build ./...
```

## License

MIT License - see LICENSE file for details.

## Support

- Documentation: https://docs.agenthr.dev
- GitHub: https://github.com/agenthr/agenthr
- Issues: https://github.com/agenthr/agenthr/issues
- Email: support@agenthr.dev
