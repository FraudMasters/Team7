/**
 * AgentHR TypeScript/JavaScript SDK
 *
 * Official TypeScript SDK for AgentHR - AI-powered resume analysis and candidate ranking system.
 *
 * @example
 * ```ts
 * import { Client } from '@agenthr/sdk';
 *
 * const client = new Client({ apiKey: 'your-api-key' });
 * const vacancies = await client.vacancies.list();
 * await client.close();
 * ```
 *
 * @packageDocumentation
 */

export interface ClientConfig {
  /**
   * AgentHR API key.
   * If not provided, reads from AGENTHR_API_KEY environment variable.
   */
  apiKey?: string;

  /**
   * Base URL of the AgentHR API.
   * @default "http://localhost:8000"
   */
  baseUrl?: string;

  /**
   * Request timeout in milliseconds.
   * @default 30000
   */
  timeout?: number;

  /**
   * Additional HTTP headers to include in all requests.
   */
  headers?: Record<string, string>;

  /**
   * Custom fetch function for making HTTP requests.
   * Useful for testing or adding custom request handling.
   */
  fetch?: typeof fetch;
}

/**
 * Main AgentHR API client.
 *
 * This is the main entry point for interacting with the AgentHR API.
 * It provides access to all API resources through nested resource objects.
 *
 * @example
 * ```ts
 * import { Client } from '@agenthr/sdk';
 *
 * const client = new Client({ apiKey: 'your-api-key' });
 * const vacancies = await client.vacancies.list();
 * await client.close();
 * ```
 */
export class Client {
  private readonly apiKey: string;
  private readonly baseUrl: string;
  private readonly timeout: number;
  private readonly headers: Record<string, string>;
  private readonly fetchFn: typeof fetch;
  private readonly resources: Map<string, unknown>;

  constructor(config: ClientConfig = {}) {
    // Get API key from config or environment variable
    this.apiKey =
      config.apiKey ||
      (typeof process !== 'undefined' && process.env?.AGENTHR_API_KEY) ||
      '';

    if (!this.apiKey) {
      throw new Error(
        'API key is required. Set AGENTHR_API_KEY environment variable or pass apiKey parameter.'
      );
    }

    this.baseUrl = (config.baseUrl || 'http://localhost:8000').replace(/\/$/, '');
    this.timeout = config.timeout ?? 30000;
    this.headers = {
      'X-API-Key': this.apiKey,
      'Content-Type': 'application/json',
      ...config.headers,
    };
    this.fetchFn = config.fetch || fetch;
    this.resources = new Map();
  }

  /**
   * Access resume operations.
   */
  get resumes(): ResumesResource {
    if (!this.resources.has('resumes')) {
      this.resources.set('resumes', new ResumesResource(this));
    }
    return this.resources.get('resumes') as ResumesResource;
  }

  /**
   * Access vacancy operations.
   */
  get vacancies(): VacanciesResource {
    if (!this.resources.has('vacancies')) {
      this.resources.set('vacancies', new VacanciesResource(this));
    }
    return this.resources.get('vacancies') as VacanciesResource;
  }

  /**
   * Access candidate operations.
   */
  get candidates(): CandidatesResource {
    if (!this.resources.has('candidates')) {
      this.resources.set('candidates', new CandidatesResource(this));
    }
    return this.resources.get('candidates') as CandidatesResource;
  }

  /**
   * Access ranking operations.
   */
  get ranking(): RankingResource {
    if (!this.resources.has('ranking')) {
      this.resources.set('ranking', new RankingResource(this));
    }
    return this.resources.get('ranking') as RankingResource;
  }

  /**
   * Access analytics operations.
   */
  get analytics(): AnalyticsResource {
    if (!this.resources.has('analytics')) {
      this.resources.set('analytics', new AnalyticsResource(this));
    }
    return this.resources.get('analytics') as AnalyticsResource;
  }

  /**
   * Access webhook operations.
   */
  get webhooks(): WebhooksResource {
    if (!this.resources.has('webhooks')) {
      this.resources.set('webhooks', new WebhooksResource(this));
    }
    return this.resources.get('webhooks') as WebhooksResource;
  }

  /**
   * Access API key operations.
   */
  get apiKeys(): APIKeysResource {
    if (!this.resources.has('apiKeys')) {
      this.resources.set('apiKeys', new APIKeysResource(this));
    }
    return this.resources.get('apiKeys') as APIKeysResource;
  }

  /**
   * Access workflow operations.
   */
  get workflows(): WorkflowsResource {
    if (!this.resources.has('workflows')) {
      this.resources.set('workflows', new WorkflowsResource(this));
    }
    return this.resources.get('workflows') as WorkflowsResource;
  }

  /**
   * Access plugin operations.
   */
  get plugins(): PluginsResource {
    if (!this.resources.has('plugins')) {
      this.resources.set('plugins', new PluginsResource(this));
    }
    return this.resources.get('plugins') as PluginsResource;
  }

  /**
   * Make an HTTP request to the API.
   * @internal
   */
  async request<T>(
    path: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${path}`;
    const controller = new AbortController();

    // Set up timeout
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await this.fetchFn(url, {
        ...options,
        headers: {
          ...this.headers,
          ...options.headers,
        },
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        await this.handleError(response);
      }

      // Handle empty responses (e.g., 204 No Content)
      const contentType = response.headers.get('content-type');
      if (!contentType || contentType === 'application/json') {
        return response.json().catch(() => ({} as T));
      }

      return (await response.json()) as T;
    } catch (error) {
      clearTimeout(timeoutId);

      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          throw new APIError('Request timeout', 0, 'timeout');
        }
        throw error;
      }

      throw new APIError('Unknown error', 0, 'unknown_error');
    }
  }

  /**
   * Handle API error responses.
   * @internal
   */
  private async handleError(response: Response): Promise<never> {
    const status = response.status;
    let message = 'API request failed';
    let code = 'unknown_error';
    let errors: string[] | undefined;

    try {
      const data = await response.json();
      message = data.detail || data.message || message;
      code = data.code || code;
      errors = data.errors;
    } catch {
      // Ignore JSON parsing errors
    }

    if (status === 401 || status === 403) {
      throw new AuthenticationError(message, status);
    }

    if (status === 429) {
      const retryAfter = response.headers.get('Retry-After');
      throw new RateLimitError(message, status, retryAfter ? parseInt(retryAfter, 10) : undefined);
    }

    if (status === 422 && errors) {
      throw new ValidationError(message, status, errors);
    }

    throw new APIError(message, status, code);
  }

  /**
   * Close the client and release resources.
   */
  async close(): Promise<void> {
    // No-op for now, but kept for future resource cleanup
  }
}

// ============================================================================
// Resource Classes (Stubs)
// ============================================================================

/**
 * Base resource class.
 * @internal
 */
abstract class BaseResource {
  constructor(protected readonly client: Client) {}
}

/**
 * Resume resource for managing resumes.
 */
export class ResumesResource extends BaseResource {
  /**
   * Upload a resume file.
   * @stub
   */
  async upload(filePath: string, options?: { vacancyId?: string }): Promise<Resume> {
    throw new NotImplementedError('resumes.upload');
  }

  /**
   * Upload a resume from a buffer.
   * @stub
   */
  async uploadFromBuffer(buffer: ArrayBuffer, filename: string): Promise<Resume> {
    throw new NotImplementedError('resumes.uploadFromBuffer');
  }

  /**
   * List resumes with optional filtering.
   * @stub
   */
  async list(options?: { limit?: number; status?: string }): Promise<Resume[]> {
    throw new NotImplementedError('resumes.list');
  }

  /**
   * Get a resume by ID.
   * @stub
   */
  async get(resumeId: string): Promise<Resume> {
    throw new NotImplementedError('resumes.get');
  }
}

/**
 * Vacancy resource for managing job vacancies.
 */
export class VacanciesResource extends BaseResource {
  /**
   * Create a new vacancy.
   * @stub
   */
  async create(data: VacancyCreate): Promise<Vacancy> {
    throw new NotImplementedError('vacancies.create');
  }

  /**
   * List vacancies.
   * @stub
   */
  async list(options?: { limit?: number; offset?: number }): Promise<Vacancy[]> {
    throw new NotImplementedError('vacancies.list');
  }

  /**
   * Get a vacancy by ID.
   * @stub
   */
  async get(vacancyId: string): Promise<Vacancy> {
    throw new NotImplementedError('vacancies.get');
  }

  /**
   * Find matching candidates for a vacancy.
   * @stub
   */
  async findMatches(vacancyId: string, options?: { limit?: number }): Promise<Match[]> {
    throw new NotImplementedError('vacancies.findMatches');
  }

  /**
   * Iterate through all vacancies.
   * @stub
   */
  async *iterAll(): AsyncIterableIterator<Vacancy> {
    throw new NotImplementedError('vacancies.iterAll');
  }
}

/**
 * Candidate resource for managing candidates.
 */
export class CandidatesResource extends BaseResource {
  /**
   * List candidates with optional filtering.
   * @stub
   */
  async list(options?: { vacancyId?: string; stage?: string }): Promise<Candidate[]> {
    throw new NotImplementedError('candidates.list');
  }

  /**
   * Get a candidate by ID.
   * @stub
   */
  async get(candidateId: string): Promise<Candidate> {
    throw new NotImplementedError('candidates.get');
  }

  /**
   * Move a candidate to a different stage.
   * @stub
   */
  async move(candidateId: string, options: MoveCandidateOptions): Promise<void> {
    throw new NotImplementedError('candidates.move');
  }
}

/**
 * Ranking resource for AI-powered candidate ranking.
 */
export class RankingResource extends BaseResource {
  /**
   * Rank a candidate for a vacancy.
   * @stub
   */
  async rank(options: RankOptions): Promise<Ranking> {
    throw new NotImplementedError('ranking.rank');
  }
}

/**
 * Analytics resource for recruitment analytics.
 */
export class AnalyticsResource extends BaseResource {
  /**
   * Get key recruitment metrics.
   * @stub
   */
  async getKeyMetrics(options?: { startDate?: string; endDate?: string }): Promise<KeyMetrics> {
    throw new NotImplementedError('analytics.getKeyMetrics');
  }

  /**
   * Get hiring funnel metrics.
   * @stub
   */
  async getFunnel(): Promise<Funnel> {
    throw new NotImplementedError('analytics.getFunnel');
  }
}

/**
 * Webhooks resource for managing webhook subscriptions.
 */
export class WebhooksResource extends BaseResource {
  /**
   * Create a webhook subscription.
   * @stub
   */
  async create(data: WebhookCreate): Promise<Webhook> {
    throw new NotImplementedError('webhooks.create');
  }

  /**
   * List webhook subscriptions.
   * @stub
   */
  async list(): Promise<Webhook[]> {
    throw new NotImplementedError('webhooks.list');
  }

  /**
   * Get delivery logs for a webhook.
   * @stub
   */
  async getDeliveryLogs(webhookId: string): Promise<WebhookDeliveryLog[]> {
    throw new NotImplementedError('webhooks.getDeliveryLogs');
  }

  /**
   * Delete a webhook subscription.
   * @stub
   */
  async delete(webhookId: string): Promise<void> {
    throw new NotImplementedError('webhooks.delete');
  }
}

/**
 * API Keys resource for managing API keys.
 */
export class APIKeysResource extends BaseResource {
  /**
   * Generate a new API key.
   * @stub
   */
  async generate(data: APIKeyGenerate): Promise<APIKey> {
    throw new NotImplementedError('apiKeys.generate');
  }

  /**
   * List API keys.
   * @stub
   */
  async list(): Promise<APIKey[]> {
    throw new NotImplementedError('apiKeys.list');
  }

  /**
   * Revoke an API key.
   * @stub
   */
  async revoke(keyId: string): Promise<void> {
    throw new NotImplementedError('apiKeys.revoke');
  }
}

/**
 * Workflows resource for managing workflow automations.
 */
export class WorkflowsResource extends BaseResource {
  /**
   * Create a workflow.
   * @stub
   */
  async create(data: WorkflowCreate): Promise<Workflow> {
    throw new NotImplementedError('workflows.create');
  }

  /**
   * Execute a workflow manually.
   * @stub
   */
  async execute(workflowId: string): Promise<WorkflowExecution> {
    throw new NotImplementedError('workflows.execute');
  }

  /**
   * Get workflow execution history.
   * @stub
   */
  async getExecutions(workflowId: string): Promise<WorkflowExecution[]> {
    throw new NotImplementedError('workflows.getExecutions');
  }
}

/**
 * Plugins resource for managing plugin installations.
 */
export class PluginsResource extends BaseResource {
  /**
   * List available plugins.
   * @stub
   */
  async list(options?: { category?: string }): Promise<Plugin[]> {
    throw new NotImplementedError('plugins.list');
  }

  /**
   * Install a plugin.
   * @stub
   */
  async install(pluginId: string): Promise<PluginInstallation> {
    throw new NotImplementedError('plugins.install');
  }

  /**
   * List installed plugins.
   * @stub
   */
  async listInstalled(): Promise<PluginInstallation[]> {
    throw new NotImplementedError('plugins.listInstalled');
  }

  /**
   * Uninstall a plugin.
   * @stub
   */
  async uninstall(installationId: string): Promise<void> {
    throw new NotImplementedError('plugins.uninstall');
  }
}

// ============================================================================
// Type Definitions
// ============================================================================

/**
 * Resume data model.
 */
export interface Resume {
  id: string;
  status: string;
  uploadedAt: string;
  parsedData?: ResumeParsedData;
}

/**
 * Parsed resume data.
 */
export interface ResumeParsedData {
  name: string;
  email: string;
  phone?: string;
  skills: string[];
  experience?: number;
}

/**
 * Vacancy data model.
 */
export interface Vacancy {
  id: string;
  title: string;
  description: string;
  requiredSkills: string[];
  minExperience?: number;
  location?: string;
  salaryMin?: number;
  salaryMax?: number;
  createdAt: string;
}

/**
 * Vacancy creation data.
 */
export interface VacancyCreate {
  title: string;
  description: string;
  requiredSkills: string[];
  minExperience?: number;
  location?: string;
  salaryMin?: number;
  salaryMax?: number;
}

/**
 * Candidate data model.
 */
export interface Candidate {
  id: string;
  name: string;
  email: string;
  stage: string;
  vacancyId: string;
}

/**
 * Options for moving a candidate.
 */
export interface MoveCandidateOptions {
  stageId: string;
  vacancyId: string;
  notes?: string;
}

/**
 * Candidate match result.
 */
export interface Match {
  id: string;
  name: string;
  score: number;
  explanation?: string;
}

/**
 * Ranking result.
 */
export interface Ranking {
  vacancyId: string;
  resumeId: string;
  score: number;
  explanation: string;
}

/**
 * Options for ranking a candidate.
 */
export interface RankOptions {
  vacancyId: string;
  resumeId: string;
}

/**
 * Key recruitment metrics.
 */
export interface KeyMetrics {
  timeToHireDays: number;
  resumesProcessed: number;
  matchRate: number;
}

/**
 * Hiring funnel data.
 */
export interface Funnel {
  stages: Array<{
    name: string;
    count: number;
    conversionRate: number;
  }>;
}

/**
 * Webhook data model.
 */
export interface Webhook {
  id: string;
  url: string;
  events: string[];
  active: boolean;
  createdAt: string;
}

/**
 * Webhook creation data.
 */
export interface WebhookCreate {
  url: string;
  events: string[];
  secret?: string;
}

/**
 * Webhook delivery log.
 */
export interface WebhookDeliveryLog {
  id: string;
  eventId: string;
  statusCode: number;
  deliveredAt: string;
  success: boolean;
}

/**
 * API key data model.
 */
export interface APIKey {
  id: string;
  key: string;
  name: string;
  scopes: string[];
  createdAt: string;
}

/**
 * API key generation data.
 */
export interface APIKeyGenerate {
  name: string;
  scopes: string[];
  rateLimitPerMinute?: number;
}

/**
 * Workflow data model.
 */
export interface Workflow {
  id: string;
  name: string;
  trigger: WorkflowTrigger;
  actions: WorkflowAction[];
  active: boolean;
  createdAt: string;
}

/**
 * Workflow creation data.
 */
export interface WorkflowCreate {
  name: string;
  trigger: WorkflowTrigger;
  actions: WorkflowAction[];
}

/**
 * Workflow trigger.
 */
export interface WorkflowTrigger {
  type: 'webhook' | 'schedule' | 'manual';
  event?: string;
  cronExpression?: string;
}

/**
 * Workflow action.
 */
export interface WorkflowAction {
  type: string;
  [key: string]: unknown;
}

/**
 * Workflow execution.
 */
export interface WorkflowExecution {
  id: string;
  workflowId: string;
  status: string;
  startedAt: string;
  completedAt?: string;
}

/**
 * Plugin data model.
 */
export interface Plugin {
  id: string;
  name: string;
  description: string;
  version: string;
  category: string;
  author: string;
}

/**
 * Plugin installation.
 */
export interface PluginInstallation {
  id: string;
  pluginId: string;
  enabled: boolean;
  installedAt: string;
}

// ============================================================================
// Error Classes
// ============================================================================

/**
 * Base error class for all AgentHR API errors.
 */
export class APIError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly code: string
  ) {
    super(message);
    this.name = 'APIError';
  }
}

/**
 * Authentication error (401, 403).
 */
export class AuthenticationError extends APIError {
  constructor(message: string, status: number) {
    super(message, status, 'authentication_failed');
    this.name = 'AuthenticationError';
  }
}

/**
 * Rate limit error (429).
 */
export class RateLimitError extends APIError {
  constructor(
    message: string,
    status: number,
    public readonly retryAfter?: number
  ) {
    super(message, status, 'rate_limited');
    this.name = 'RateLimitError';
  }
}

/**
 * Validation error (422).
 */
export class ValidationError extends APIError {
  constructor(
    message: string,
    status: number,
    public readonly errors: string[]
  ) {
    super(message, status, 'validation_failed');
    this.name = 'ValidationError';
  }
}

/**
 * Error thrown when a method is not implemented.
 */
export class NotImplementedError extends Error {
  constructor(method: string) {
    super(`Method "${method}" is not implemented yet.`);
    this.name = 'NotImplementedError';
  }
}

// ============================================================================
// Exports
// ============================================================================
