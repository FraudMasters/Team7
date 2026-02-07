# AgentHR Java SDK

The official Java SDK for AgentHR - AI-powered resume analysis and candidate ranking system.

## Installation

Add the dependency to your `pom.xml`:

```xml
<dependency>
    <groupId>dev.agenthr</groupId>
    <artifactId>agenthr-sdk</artifactId>
    <version>0.1.0</version>
</dependency>
```

Or for Gradle:

```groovy
implementation 'dev.agenthr:agenthr-sdk:0.1.0'
```

## Quick Start

```java
import dev.agenthr.Client;

// Initialize the client
Client client = new Client("your-api-key-here");

// Upload a resume
Resume resume = client.resumes().upload("path/to/resume.pdf");
System.out.println("Resume uploaded: " + resume.getId());

// Create a vacancy
Vacancy vacancy = client.vacancies().create(
    "Senior Java Developer",
    "We are looking for an experienced Java developer...",
    List.of("Java", "Spring", "PostgreSQL")
);
System.out.println("Vacancy created: " + vacancy.getId());

// Find matching candidates
List<CandidateMatch> matches = client.vacancies().findMatches(vacancy.getId(), 10);
for (CandidateMatch match : matches) {
    System.out.println(match.getName() + ": " + match.getScore());
}

// Close the client when done
client.close();
```

Or use try-with-resources:

```java
import dev.agenthr.Client;

try (Client client = new Client("your-api-key-here")) {
    List<Vacancy> vacancies = client.vacancies().list();
    System.out.println("Found " + vacancies.size() + " vacancies");
}
```

## Configuration

The SDK can be configured via environment variables or constructor parameters:

```java
import dev.agenthr.Client;

// Via environment variables
// AGENTHR_API_KEY=your-api-key
// AGENTHR_API_URL=https://api.agenthr.dev
Client client = new Client();

// Or via constructor
Client client = new Client(
    "your-api-key-here",
    "https://api.agenthr.dev",
    Duration.ofSeconds(30)
);
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `apiKey` | `String` | `AGENTHR_API_KEY` env var | Your AgentHR API key |
| `baseUrl` | `String` | `http://localhost:8000` | Base URL of the AgentHR API |
| `timeout` | `Duration` | `30 seconds` | Request timeout |

## API Resources

### Resumes

Upload and manage resumes:

```java
// Upload a resume
Resume resume = client.resumes().upload("resume.pdf", "optional-vacancy-id");

// List resumes
List<Resume> resumes = client.resumes().list(50, "completed");

// Get resume details
Resume resume = client.resumes().get(resumeId);

// Get parsed data
ParsedData parsed = resume.getParsedData();
System.out.println("Name: " + parsed.getName());
System.out.println("Email: " + parsed.getEmail());
System.out.println("Skills: " + parsed.getSkills());
```

### Vacancies

Manage job vacancies:

```java
// Create a vacancy
Vacancy vacancy = client.vacancies().create(
    "Senior Java Developer",
    "Job description here...",
    List.of("Java", "Spring", "SQL"),
    5,  // minExperience
    "Remote",
    100000,  // salaryMin
    150000   // salaryMax
);

// List vacancies
List<Vacancy> vacancies = client.vacancies().list();

// Get vacancy details
Vacancy vacancy = client.vacancies().get(vacancyId);

// Find matching candidates
List<CandidateMatch> matches = client.vacancies().findMatches(vacancyId, 10);
```

### Candidates

Manage candidates and their pipeline stages:

```java
// List candidates
List<Candidate> candidates = client.candidates().list("xxx", "screening");

// Get candidate details
Candidate candidate = client.candidates().get(candidateId);

// Move candidate to next stage
client.candidates().move(
    candidateId,
    "interview",
    "yyy",  // vacancyId
    "Strong technical skills"
);
```

### Ranking

Get AI-powered candidate rankings:

```java
// Rank a candidate for a vacancy
Ranking ranking = client.ranking().rank("xxx", "yyy");
System.out.println("Score: " + ranking.getScore());
System.out.println("Explanation: " + ranking.getExplanation());
```

### Analytics

Query recruitment analytics:

```java
// Get key metrics
KeyMetrics metrics = client.analytics().getKeyMetrics(
    LocalDate.of(2024, 1, 1),
    LocalDate.of(2024, 12, 31)
);
System.out.println("Time to Hire: " + metrics.getTimeToHireDays() + " days");

// Get funnel metrics
FunnelMetrics funnel = client.analytics().getFunnel();
for (StageMetrics stage : funnel.getStages()) {
    System.out.println(stage.getName() + ": " + stage.getCount() + " candidates");
}
```

### Webhooks

Manage webhook subscriptions:

```java
// Create a webhook subscription
Webhook webhook = client.webhooks().create(
    "https://your-app.com/webhooks",
    List.of("candidate.created", "stage.changed")
);

// List webhooks
List<Webhook> webhooks = client.webhooks().list();

// Get delivery logs
List<DeliveryLog> logs = client.webhooks().getDeliveryLogs(webhookId);

// Delete webhook
client.webhooks().delete(webhookId);
```

### API Keys

Manage API keys (requires admin permissions):

```java
// Generate a new API key
APIKey key = client.apiKeys().generate(
    "Production Key",
    List.of("read:candidates", "write:candidates"),
    100  // rateLimitPerMinute
);
System.out.println("API Key: " + key.getKey()); // Only shown once!

// List API keys
List<APIKey> keys = client.apiKeys().list();

// Revoke a key
client.apiKeys().revoke(keyId);
```

### Workflows

Manage workflow automations:

```java
// Create a workflow
Workflow workflow = client.workflows().create(
    "Auto-reply to candidates",
    new TriggerConfig("webhook", "candidate.created"),
    List.of(
        new ActionConfig(
            "send_email",
            Map.of(
                "to", "{{candidate.email}}",
                "subject", "Application Received",
                "body", "Thank you for applying..."
            )
        )
    )
);

// Execute a workflow manually
WorkflowExecution execution = client.workflows().execute(workflowId);

// Get execution history
List<WorkflowExecution> history = client.workflows().getExecutions(workflowId);
```

### Plugins

Manage plugin installations:

```java
// List available plugins
List<Plugin> plugins = client.plugins().list("integration");

// Install a plugin
PluginInstallation installation = client.plugins().install(pluginId);

// List installed plugins
List<PluginInstallation> installed = client.plugins().listInstalled();

// Uninstall a plugin
client.plugins().uninstall(installationId);
```

## Error Handling

The SDK provides detailed error information:

```java
import dev.agenthr.Client;
import dev.agenthr.exceptions.*;

try {
    Client client = new Client("invalid-key");
    client.vacancies().list();
} catch (AuthenticationException e) {
    System.err.println("Authentication failed: " + e.getMessage());
} catch (RateLimitException e) {
    System.err.println("Rate limited: " + e.getRetryAfterSeconds() + " seconds until reset");
} catch (ValidationException e) {
    System.err.println("Validation error: " + e.getErrors());
} catch (APIException e) {
    System.err.println("API error: " + e.getMessage());
}
```

## Advanced Usage

### Custom HTTP Client

```java
import dev.agenthr.Client;
import java.net.http.HttpClient;
import java.time.Duration;

// Custom HTTP client with additional configuration
HttpClient httpClient = HttpClient.newBuilder()
    .connectTimeout(Duration.ofSeconds(10))
    .version(HttpClient.Version.HTTP_2)
    .build();

Client client = new Client("your-key", "https://api.agenthr.dev", httpClient);
```

### Pagination

The SDK handles pagination automatically:

```java
// Iterate through all vacancies
for (Vacancy vacancy : client.vacancies().iterAll()) {
    System.out.println(vacancy.getTitle());
}

// Or use pages
Page<Vacancy> page = client.vacancies().listPage(0, 50);
while (page.getItems().size() > 0) {
    for (Vacancy vacancy : page.getItems()) {
        System.out.println(vacancy.getTitle());
    }
    page = client.vacancies().listPage(page.getNextOffset(), 50);
}
```

### Async Operations

For asynchronous operations:

```java
import dev.agenthr.AsyncClient;
import java.util.concurrent.CompletableFuture;

AsyncClient client = new AsyncClient("your-api-key");

CompletableFuture<List<Vacancy>> future = client.vacancies().listAsync();
future.thenAccept(vacancies -> {
    System.out.println("Found " + vacancies.size() + " vacancies");
}).exceptionally(throwable -> {
    System.err.println("Error: " + throwable.getMessage());
    return null;
});
```

## Package Structure

The SDK follows standard Java package conventions:

```
dev.agenthr
├── Client.java              # Main synchronous client
├── AsyncClient.java         # Asynchronous client
├── exceptions               # Exception classes
│   ├── APIException.java
│   ├── AuthenticationException.java
│   ├── RateLimitException.java
│   └── ValidationException.java
├── models                   # Data models
│   ├── Resume.java
│   ├── Vacancy.java
│   ├── Candidate.java
│   └── ...
└── resources                # API resource clients
    ├── Resumes.java
    ├── Vacancies.java
    ├── Candidates.java
    ├── Ranking.java
    ├── Analytics.java
    ├── Webhooks.java
    ├── ApiKeys.java
    ├── Workflows.java
    └── Plugins.java
```

## Dependencies

The Java SDK has minimal dependencies:

- **Java 11+** - Minimum Java version
- **Java HTTP Client** (java.net.http) - Built-in HTTP client (Java 11+)
- **Jackson** (com.fasterxml.jackson.core) - JSON serialization/deserialization
- **SLF4J** (org.slf4j) - Logging facade

## Development

Build from source:

```bash
git clone https://github.com/agenthr/agenthr
cd agenthr/sdk/java
mvn clean install
```

Run tests:

```bash
mvn test
```

Run tests with coverage:

```bash
mvn test jacoco:report
```

Build JAR:

```bash
mvn package
```

## License

MIT License - see LICENSE file for details.

## Support

- Documentation: https://docs.agenthr.dev
- GitHub: https://github.com/agenthr/agenthr
- Issues: https://github.com/agenthr/agenthr/issues
- Email: support@agenthr.dev
