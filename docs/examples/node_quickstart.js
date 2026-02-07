#!/usr/bin/env node
/**
 * AgentHR Node.js Quickstart Example
 *
 * This example demonstrates how to:
 * 1. Authenticate with the AgentHR API
 * 2. Upload a resume
 * 3. Create a job vacancy
 * 4. Find matching candidates
 * 5. Move candidates through the hiring pipeline
 *
 * Requirements:
 *   npm install fs axios form-data
 *
 * Usage:
 *   node node_quickstart.js --help
 *   node node_quickstart.js upload-resume --file resume.pdf
 *   node node_quickstart.js create-vacancy --title "Senior Developer"
 *   node node_quickstart.js find-matches --vacancy-id <id>
 */

const fs = require('fs');
const path = require('path');
const axios = require('axios');
const FormData = require('form-data');
const { program } = require('commander');


/**
 * Simple Node.js client for the AgentHR API.
 *
 * This client demonstrates best practices for:
 * - API key authentication
 * - Error handling
 * - Request/response handling
 * - File uploads
 */
class AgentHRClient {
    /**
     * Initialize the AgentHR client.
     *
     * @param {Object} options - Client options
     * @param {string} options.apiKey - AgentHR API key
     * @param {string} options.baseUrl - Base URL of the AgentHR API
     * @param {number} options.timeout - Request timeout in milliseconds
     */
    constructor(options = {}) {
        this.apiKey = options.apiKey || process.env.AGENTHR_API_KEY;
        if (!this.apiKey) {
            throw new Error(
                'API key is required. Set AGENTHR_API_KEY environment variable ' +
                'or pass apiKey parameter.'
            );
        }

        this.baseUrl = options.baseUrl || 'http://localhost:8000';
        this.timeout = options.timeout || 30000;

        // Create axios instance with default configuration
        this.client = axios.create({
            baseURL: this.baseUrl,
            headers: {
                'X-API-Key': this.apiKey,
                'Content-Type': 'application/json',
            },
            timeout: this.timeout,
        });

        // Response interceptor for error handling
        this.client.interceptors.response.use(
            (response) => response,
            (error) => {
                if (error.response) {
                    // API returned an error response
                    const detail = error.response.data?.detail || 'Unknown error';
                    throw new AgentHRAPIError(
                        `API request failed: ${error.response.status} - ${detail}`,
                        error.response.status
                    );
                } else if (error.request) {
                    // Request was made but no response received
                    throw new AgentHRAPIError(`Request failed: ${error.message}`);
                } else {
                    // Error setting up the request
                    throw new AgentHRAPIError(`Error: ${error.message}`);
                }
            }
        );
    }

    /**
     * Verify that the API key is valid.
     *
     * @returns {Promise<Object>} API key details
     */
    async verifyApiKey() {
        const response = await this.client.get('/api/api-keys/me');
        return response.data;
    }

    // ===== Resume Operations =====

    /**
     * Upload a resume file for parsing and analysis.
     *
     * @param {string} filePath - Path to the resume file (PDF, DOCX, or DOC)
     * @param {string} vacancyId - Optional vacancy ID to associate with the resume
     * @returns {Promise<Object>} Uploaded resume details including parsed data
     */
    async uploadResume(filePath, vacancyId = null) {
        if (!fs.existsSync(filePath)) {
            throw new Error(`Resume file not found: ${filePath}`);
        }

        const validExtensions = ['.pdf', '.docx', '.doc'];
        const ext = path.extname(filePath).toLowerCase();
        if (!validExtensions.includes(ext)) {
            throw new Error(
                `Invalid file type: ${ext}. ` +
                `Supported types: ${validExtensions.join(', ')}`
            );
        }

        // Create form data
        const form = new FormData();
        form.append('file', fs.createReadStream(filePath));
        if (vacancyId) {
            form.append('vacancy_id', vacancyId);
        }

        // Make request with form data
        const response = await this.client.post('/api/resumes/upload', form, {
            headers: {
                ...form.getHeaders(),
            },
        });

        return response.data;
    }

    /**
     * List all resumes with optional filtering.
     *
     * @param {Object} options - Query options
     * @param {number} options.limit - Maximum number of results
     * @param {number} options.offset - Pagination offset
     * @param {string} options.status - Filter by status
     * @returns {Promise<Object>} List of resumes with pagination info
     */
    async listResumes(options = {}) {
        const { limit = 50, offset = 0, status } = options;
        const params = { limit, offset };
        if (status) {
            params.status = status;
        }

        const response = await this.client.get('/api/resumes', { params });
        return response.data;
    }

    /**
     * Get detailed information about a resume.
     *
     * @param {string} resumeId - Resume UUID
     * @returns {Promise<Object>} Resume details including parsed data
     */
    async getResume(resumeId) {
        const response = await this.client.get(`/api/resumes/${resumeId}`);
        return response.data;
    }

    // ===== Vacancy Operations =====

    /**
     * Create a new job vacancy.
     *
     * @param {Object} data - Vacancy data
     * @param {string} data.title - Job title
     * @param {string} data.description - Job description
     * @param {string[]} data.requiredSkills - List of required skills
     * @param {number} data.minExperience - Minimum years of experience
     * @param {string} data.location - Job location
     * @param {number} data.salaryMin - Minimum salary
     * @param {number} data.salaryMax - Maximum salary
     * @returns {Promise<Object>} Created vacancy details
     */
    async createVacancy(data) {
        const {
            title,
            description,
            requiredSkills,
            minExperience,
            location,
            salaryMin,
            salaryMax,
        } = data;

        const payload = {
            title,
            description,
            required_skills: requiredSkills,
        };

        // Add optional fields
        if (minExperience !== undefined) {
            payload.min_experience = minExperience;
        }
        if (location) {
            payload.location = location;
        }
        if (salaryMin !== undefined) {
            payload.salary_min = salaryMin;
        }
        if (salaryMax !== undefined) {
            payload.salary_max = salaryMax;
        }

        const response = await this.client.post('/api/vacancies', payload);
        return response.data;
    }

    /**
     * List all job vacancies.
     *
     * @param {Object} options - Query options
     * @param {number} options.limit - Maximum number of results
     * @param {number} options.offset - Pagination offset
     * @returns {Promise<Object>} List of vacancies with pagination info
     */
    async listVacancies(options = {}) {
        const { limit = 50, offset = 0 } = options;
        const response = await this.client.get('/api/vacancies', {
            params: { limit, offset },
        });
        return response.data;
    }

    /**
     * Get detailed information about a vacancy.
     *
     * @param {string} vacancyId - Vacancy UUID
     * @returns {Promise<Object>} Vacancy details
     */
    async getVacancy(vacancyId) {
        const response = await this.client.get(`/api/vacancies/${vacancyId}`);
        return response.data;
    }

    // ===== Candidate Operations =====

    /**
     * List candidates with optional filtering.
     *
     * @param {Object} options - Query options
     * @param {string} options.vacancyId - Filter by vacancy ID
     * @param {string} options.stage - Filter by workflow stage
     * @param {number} options.limit - Maximum number of results
     * @param {number} options.offset - Pagination offset
     * @returns {Promise<Object>} List of candidates with pagination info
     */
    async listCandidates(options = {}) {
        const { vacancyId, stage, limit = 50, offset = 0 } = options;
        const params = { limit, offset };
        if (vacancyId) {
            params.vacancy_id = vacancyId;
        }
        if (stage) {
            params.stage = stage;
        }

        const response = await this.client.get('/api/candidates', { params });
        return response.data;
    }

    /**
     * Move a candidate to a different workflow stage.
     *
     * @param {string} candidateId - Candidate (resume) UUID
     * @param {string} stageId - Target stage ID (e.g., 'screening', 'interview')
     * @param {string} vacancyId - Vacancy UUID
     * @param {string} notes - Optional notes about the move
     * @returns {Promise<Object>} Move operation result
     */
    async moveCandidate(candidateId, stageId, vacancyId, notes = null) {
        const payload = {
            stage_id: stageId,
            vacancy_id: vacancyId,
        };
        if (notes) {
            payload.notes = notes;
        }

        const response = await this.client.put(
            `/api/candidates/${candidateId}/stage`,
            payload
        );
        return response.data;
    }

    // ===== Matching Operations =====

    /**
     * Find candidates matching a vacancy using AI-powered ranking.
     *
     * @param {string} vacancyId - Vacancy UUID
     * @param {number} limit - Maximum number of matches to return
     * @returns {Promise<Object>} List of ranked candidate matches
     */
    async findMatches(vacancyId, limit = 10) {
        const response = await this.client.get(`/api/vacancies/${vacancyId}/matches`, {
            params: { limit },
        });
        return response.data;
    }

    /**
     * Get AI-powered ranking score for a candidate against a vacancy.
     *
     * @param {string} vacancyId - Vacancy UUID
     * @param {string} resumeId - Resume UUID
     * @returns {Promise<Object>} Ranking results with score and explanation
     */
    async rankCandidate(vacancyId, resumeId) {
        const response = await this.client.post('/api/ranking/rank', null, {
            params: {
                vacancy_id: vacancyId,
                resume_id: resumeId,
            },
        });
        return response.data;
    }

    // ===== Analytics Operations =====

    /**
     * Get key recruitment metrics.
     *
     * @param {Object} options - Query options
     * @param {string} options.startDate - Start date (ISO 8601 format)
     * @param {string} options.endDate - End date (ISO 8601 format)
     * @returns {Promise<Object>} Key metrics including time-to-hire, conversion rates
     */
    async getKeyMetrics(options = {}) {
        const { startDate, endDate } = options;
        const params = {};
        if (startDate) {
            params.start_date = startDate;
        }
        if (endDate) {
            params.end_date = endDate;
        }

        const response = await this.client.get('/api/analytics/key-metrics', { params });
        return response.data;
    }

    /**
     * Close the client connection.
     */
    close() {
        // axios instances don't need explicit closing in Node.js
    }
}


/**
 * Exception raised for API errors.
 */
class AgentHRAPIError extends Error {
    constructor(message, statusCode = null) {
        super(message);
        this.name = 'AgentHRAPIError';
        this.statusCode = statusCode;
    }
}


// ===== CLI Interface =====

async function main() {
    program
        .name('node_quickstart.js')
        .description('AgentHR Node.js Quickstart Example')
        .option('--api-key <key>', 'AgentHR API key (defaults to AGENTHR_API_KEY env var)')
        .option('--base-url <url>', 'Base URL of the AgentHR API', 'http://localhost:8000');

    // Verify command
    program.command('verify')
        .description('Verify API key')
        .action(async (options) => {
            try {
                const client = new AgentHRClient(program.opts());
                const result = await client.verifyApiKey();
                console.log('API Key verified successfully!');
                console.log(`Key: ${result.key_prefix || 'N/A'}***`);
                client.close();
            } catch (error) {
                console.error(`Error: ${error.message}`);
                process.exit(1);
            }
        });

    // Upload resume command
    program.command('upload-resume')
        .description('Upload a resume file')
        .requiredOption('--file <path>', 'Path to resume file')
        .option('--vacancy-id <id>', 'Optional vacancy ID')
        .action(async (options) => {
            try {
                const client = new AgentHRClient(program.opts());
                const result = await client.uploadResume(
                    options.file,
                    options.vacancyId
                );
                console.log('Resume uploaded successfully!');
                console.log(`ID: ${result.id}`);
                console.log(`Filename: ${result.filename}`);
                if (result.parsed_data) {
                    const data = result.parsed_data;
                    console.log(`Name: ${data.name || 'N/A'}`);
                    console.log(`Email: ${data.email || 'N/A'}`);
                    console.log(`Skills: ${data.skills ? data.skills.join(', ') : 'N/A'}`);
                }
                client.close();
            } catch (error) {
                console.error(`Error: ${error.message}`);
                process.exit(1);
            }
        });

    // List resumes command
    program.command('list-resumes')
        .description('List all resumes')
        .option('--limit <number>', 'Max results', '50')
        .option('--status <status>', 'Filter by status')
        .action(async (options) => {
            try {
                const client = new AgentHRClient(program.opts());
                const result = await client.listResumes({
                    limit: parseInt(options.limit),
                    status: options.status,
                });
                const resumes = result.items || [];
                console.log(`\nTotal resumes: ${result.total || 0}\n`);
                for (const resume of resumes) {
                    console.log(`  ${resume.id.substring(0, 8)}... | ${resume.filename} | ${resume.status || 'N/A'}`);
                }
                client.close();
            } catch (error) {
                console.error(`Error: ${error.message}`);
                process.exit(1);
            }
        });

    // Create vacancy command
    program.command('create-vacancy')
        .description('Create a job vacancy')
        .requiredOption('--title <title>', 'Job title')
        .requiredOption('--skills <skills>', 'Comma-separated required skills')
        .requiredOption('--description <text>', 'Job description')
        .option('--location <location>', 'Job location')
        .option('--min-experience <years>', 'Minimum years of experience', parseInt)
        .action(async (options) => {
            try {
                const client = new AgentHRClient(program.opts());
                const skills = options.skills.split(',').map(s => s.trim());
                const result = await client.createVacancy({
                    title: options.title,
                    description: options.description,
                    requiredSkills: skills,
                    location: options.location,
                    minExperience: options.minExperience,
                });
                console.log('Vacancy created successfully!');
                console.log(`ID: ${result.id}`);
                console.log(`Title: ${result.title}`);
                client.close();
            } catch (error) {
                console.error(`Error: ${error.message}`);
                process.exit(1);
            }
        });

    // List vacancies command
    program.command('list-vacancies')
        .description('List all vacancies')
        .option('--limit <number>', 'Max results', '50')
        .action(async (options) => {
            try {
                const client = new AgentHRClient(program.opts());
                const result = await client.listVacancies({
                    limit: parseInt(options.limit),
                });
                const vacancies = result.items || [];
                console.log(`\nTotal vacancies: ${result.total || 0}\n`);
                for (const vacancy of vacancies) {
                    const skills = (vacancy.required_skills || []).slice(0, 3);
                    let skillsStr = skills.join(', ');
                    if ((vacancy.required_skills || []).length > 3) {
                        skillsStr += '...';
                    }
                    console.log(`  ${vacancy.id.substring(0, 8)}... | ${vacancy.title} | ${skillsStr}`);
                }
                client.close();
            } catch (error) {
                console.error(`Error: ${error.message}`);
                process.exit(1);
            }
        });

    // Find matches command
    program.command('find-matches')
        .description('Find candidates matching a vacancy')
        .requiredOption('--vacancy-id <id>', 'Vacancy UUID')
        .option('--limit <number>', 'Max results', '10')
        .action(async (options) => {
            try {
                const client = new AgentHRClient(program.opts());
                const result = await client.findMatches(
                    options.vacancyId,
                    parseInt(options.limit)
                );
                const matches = result.matches || [];
                console.log(`\nFound ${matches.length} matches:\n`);
                for (const match of matches) {
                    console.log(`  Score: ${(match.score || 0).toFixed(1)}%`);
                    console.log(`  Name: ${match.name || 'N/A'}`);
                    const skills = (match.skills || []).slice(0, 5);
                    console.log(`  Skills: ${skills.join(', ')}`);
                    console.log();
                }
                client.close();
            } catch (error) {
                console.error(`Error: ${error.message}`);
                process.exit(1);
            }
        });

    // Move candidate command
    program.command('move-candidate')
        .description('Move candidate to a new stage')
        .requiredOption('--candidate-id <id>', 'Candidate UUID')
        .requiredOption('--stage <stage>', 'Target stage ID')
        .requiredOption('--vacancy-id <id>', 'Vacancy UUID')
        .option('--notes <text>', 'Optional notes')
        .action(async (options) => {
            try {
                const client = new AgentHRClient(program.opts());
                const result = await client.moveCandidate(
                    options.candidateId,
                    options.stage,
                    options.vacancyId,
                    options.notes
                );
                console.log('Candidate moved successfully!');
                console.log(`Previous stage: ${result.previous_stage || 'N/A'}`);
                console.log(`New stage: ${result.new_stage || 'N/A'}`);
                client.close();
            } catch (error) {
                console.error(`Error: ${error.message}`);
                process.exit(1);
            }
        });

    // Metrics command
    program.command('metrics')
        .description('Get key recruitment metrics')
        .action(async (options) => {
            try {
                const client = new AgentHRClient(program.opts());
                const result = await client.getKeyMetrics();
                console.log('Key Recruitment Metrics:');
                console.log(`  Time to Hire: ${result.time_to_hire_days || 'N/A'} days`);
                console.log(`  Resumes Processed: ${result.resumes_processed || 0}`);
                console.log(`  Match Rate: ${((result.match_rate || 0) * 100).toFixed(1)}%`);
                client.close();
            } catch (error) {
                console.error(`Error: ${error.message}`);
                process.exit(1);
            }
        });

    await program.parseAsync(process.argv);
}


if (require.main === module) {
    main().catch(error => {
        console.error('Fatal error:', error);
        process.exit(1);
    });
}


module.exports = { AgentHRClient, AgentHRAPIError };
