# AgentHR TypeScript/JavaScript SDK

The official TypeScript SDK for AgentHR - AI-powered resume analysis and candidate ranking system.

## Installation

```bash
npm install @agenthr/sdk
# or
yarn add @agenthr/sdk
# or
pnpm add @agenthr/sdk
```

## Quick Start

```typescript
import { Client } from '@agenthr/sdk';

// Initialize the client
const client = new Client({ apiKey: 'your-api-key-here' });

// Upload a resume
const resume = await client.resumes.upload('path/to/resume.pdf');
console.log(`Resume uploaded: ${resume.id}`);

// Create a vacancy
const vacancy = await client.vacancies.create({
  title: 'Senior TypeScript Developer',
  description: 'We are looking for an experienced TypeScript developer...',
  requiredSkills: ['TypeScript', 'React', 'Node.js']
});
console.log(`Vacancy created: ${vacancy.id}`);

// Find matching candidates
const matches = await client.vacancies.findMatches(vacancy.id);
for (const match of matches) {
  console.log(`${match.name}: ${(match.score * 100).toFixed(1)}%`);
}

// Close the client when done
await client.close();
```

Or use the SDK with top-level await:

```typescript
import { Client } from '@agenthr/sdk';

const client = new Client({ apiKey: 'your-api-key-here' });

// List vacancies
const vacancies = await client.vacancies.list();
console.log(`Found ${vacancies.length} vacancies`);

await client.close();
```

## Configuration

The SDK can be configured via environment variables or constructor parameters:

```typescript
// Via environment variables
process.env.AGENTHR_API_KEY = 'your-api-key';
process.env.AGENTHR_API_URL = 'https://api.agenthr.dev';

const client = new Client();

// Or via constructor
const client = new Client({
  apiKey: 'your-api-key-here',
  baseUrl: 'https://api.agenthr.dev',
  timeout: 30000
});
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `apiKey` | `string` | `AGENTHR_API_KEY` env var | Your AgentHR API key |
| `baseUrl` | `string` | `http://localhost:8000` | Base URL of the AgentHR API |
| `timeout` | `number` | `30000` | Request timeout in milliseconds |
| `headers` | `Record<string, string>` | `{}` | Additional HTTP headers |

## API Resources

### Resumes

Upload and manage resumes:

```typescript
// Upload a resume
const resume = await client.resumes.upload('resume.pdf', { vacancyId: 'optional-vacancy-id' });

// List resumes
const resumes = await client.resumes.list({ limit: 50, status: 'completed' });

// Get resume details
const resume = await client.resumes.get(resumeId);

// Get parsed data
const parsed = resume.parsedData;
console.log(`Name: ${parsed.name}`);
console.log(`Email: ${parsed.email}`);
console.log(`Skills: ${parsed.skills.join(', ')}`);
```

### Vacancies

Manage job vacancies:

```typescript
// Create a vacancy
const vacancy = await client.vacancies.create({
  title: 'Senior TypeScript Developer',
  description: 'Job description here...',
  requiredSkills: ['TypeScript', 'React', 'SQL'],
  minExperience: 5,
  location: 'Remote',
  salaryMin: 100000,
  salaryMax: 150000
});

// List vacancies
const vacancies = await client.vacancies.list();

// Get vacancy details
const vacancy = await client.vacancies.get(vacancyId);

// Find matching candidates
const matches = await client.vacancies.findMatches(vacancyId, { limit: 10 });
```

### Candidates

Manage candidates and their pipeline stages:

```typescript
// List candidates
const candidates = await client.candidates.list({ vacancyId: 'xxx', stage: 'screening' });

// Get candidate details
const candidate = await client.candidates.get(candidateId);

// Move candidate to next stage
await client.candidates.move(candidateId, {
  stageId: 'interview',
  vacancyId: 'yyy',
  notes: 'Strong technical skills'
});
```

### Ranking

Get AI-powered candidate rankings:

```typescript
// Rank a candidate for a vacancy
const ranking = await client.ranking.rank({
  vacancyId: 'xxx',
  resumeId: 'yyy'
});
console.log(`Score: ${(ranking.score * 100).toFixed(1)}%`);
console.log(`Explanation: ${ranking.explanation}`);
```

### Analytics

Query recruitment analytics:

```typescript
// Get key metrics
const metrics = await client.analytics.getKeyMetrics({
  startDate: '2024-01-01',
  endDate: '2024-12-31'
});
console.log(`Time to Hire: ${metrics.timeToHireDays} days`);

// Get funnel metrics
const funnel = await client.analytics.getFunnel();
for (const stage of funnel.stages) {
  console.log(`${stage.name}: ${stage.count} candidates`);
}
```

### Webhooks

Manage webhook subscriptions:

```typescript
// Create a webhook subscription
const webhook = await client.webhooks.create({
  url: 'https://your-app.com/webhooks',
  events: ['candidate.created', 'stage.changed']
});

// List webhooks
const webhooks = await client.webhooks.list();

// Get delivery logs
const logs = await client.webhooks.getDeliveryLogs(webhookId);

// Delete webhook
await client.webhooks.delete(webhookId);
```

### API Keys

Manage API keys (requires admin permissions):

```typescript
// Generate a new API key
const key = await client.apiKeys.generate({
  name: 'Production Key',
  scopes: ['read:candidates', 'write:candidates'],
  rateLimitPerMinute: 100
});
console.log(`API Key: ${key.key}`); // Only shown once!

// List API keys
const keys = await client.apiKeys.list();

// Revoke a key
await client.apiKeys.revoke(keyId);
```

### Workflows

Manage workflow automations:

```typescript
// Create a workflow
const workflow = await client.workflows.create({
  name: 'Auto-reply to candidates',
  trigger: {
    type: 'webhook',
    event: 'candidate.created'
  },
  actions: [
    {
      type: 'send_email',
      to: '{{candidate.email}}',
      subject: 'Application Received',
      body: 'Thank you for applying...'
    }
  ]
});

// Execute a workflow manually
const execution = await client.workflows.execute(workflowId);

// Get execution history
const history = await client.workflows.getExecutions(workflowId);
```

### Plugins

Manage plugin installations:

```typescript
// List available plugins
const plugins = await client.plugins.list({ category: 'integration' });

// Install a plugin
const installation = await client.plugins.install(pluginId);

// List installed plugins
const installed = await client.plugins.listInstalled();

// Uninstall a plugin
await client.plugins.uninstall(installationId);
```

## Error Handling

The SDK provides detailed error information:

```typescript
import {
  Client,
  APIError,
  AuthenticationError,
  RateLimitError,
  ValidationError
} from '@agenthr/sdk';

const client = new Client({ apiKey: 'invalid-key' });

try {
  await client.vacancies.list();
} catch (error) {
  if (error instanceof AuthenticationError) {
    console.error(`Authentication failed: ${error.message}`);
  } else if (error instanceof RateLimitError) {
    console.error(`Rate limited: ${error.retryAfter} seconds until reset`);
  } else if (error instanceof ValidationError) {
    console.error(`Validation error: ${error.errors.join(', ')}`);
  } else if (error instanceof APIError) {
    console.error(`API error: ${error.message}`);
  }
}
```

## Advanced Usage

### Custom HTTP Configuration

```typescript
import { Client } from '@agenthr/sdk';

// Custom fetch function
const customFetch = async (url: RequestInfo, init?: RequestInit) => {
  // Add custom logic
  return fetch(url, init);
};

const client = new Client({
  apiKey: 'your-key',
  fetch: customFetch
});
```

### Pagination

The SDK handles pagination automatically:

```typescript
// Iterate through all vacancies
for await (const vacancy of client.vacancies.iterAll()) {
  console.log(vacancy.title);
}

// Or use pages
let page = await client.vacancies.list({ offset: 0, limit: 50 });
while (page.items.length > 0) {
  for (const vacancy of page.items) {
    console.log(vacancy.title);
  }
  page = await client.vacancies.list({ offset: page.nextOffset, limit: 50 });
}
```

### Working with Buffers

```typescript
import { readFileSync } from 'fs';
import { Client } from '@agenthr/sdk';

const client = new Client({ apiKey: 'your-api-key' });

// Upload resume from buffer
const resumeBuffer = readFileSync('resume.pdf');
const resume = await client.resumes.uploadFromBuffer(resumeBuffer, 'resume.pdf');
```

## TypeScript Support

This SDK is written in TypeScript and provides full type definitions:

```typescript
import { Client, Vacancy, Resume, Candidate } from '@agenthr/sdk';

const client = new Client({ apiKey: 'your-api-key' });

// Full type safety
const vacancy: Vacancy = await client.vacancies.get(vacancyId);
const resumes: Resume[] = await client.resumes.list();
const candidate: Candidate = await client.candidates.get(candidateId);
```

## Development

Install in development mode:

```bash
git clone https://github.com/agenthr/agenthr
cd agenthr/sdk/typescript
npm install
npm run build
```

Run tests:

```bash
npm test
```

Run linter:

```bash
npm run lint
```

Build the project:

```bash
npm run build
```

## License

MIT License - see LICENSE file for details.

## Support

- Documentation: https://docs.agenthr.dev
- GitHub: https://github.com/agenthr/agenthr
- Issues: https://github.com/agenthr/agenthr/issues
- Email: support@agenthr.dev
