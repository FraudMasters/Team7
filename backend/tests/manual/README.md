# Manual Verification Tests

This directory contains manual verification scripts for testing API functionality when automated tests cannot run (e.g., in isolated worktree environments).

## API Key Authentication Flow Test

**Script:** `test_api_key_auth_flow.sh`

**Purpose:** Verify that the API key authentication flow works end-to-end, including:
- API key generation
- Authentication with valid API key
- Rejection of invalid API keys
- Handling of requests without API keys

### Prerequisites

1. Backend server must be running:
   ```bash
   cd backend
   source .venv/bin/activate
   uvicorn main:app --reload
   ```

   Or using Docker:
   ```bash
   docker-compose up -d postgres redis backend
   ```

2. Database must be initialized with migrations applied

3. `curl` and `python3` must be available in PATH

### Running the Test

**Default (local development):**
```bash
./test_api_key_auth_flow.sh
```

**Custom base URL:**
```bash
BASE_URL=http://localhost:8001 ./test_api_key_auth_flow.sh
```

### Expected Results

All tests should pass with the following outcomes:

1. **Test 1: Generate API key**
   - HTTP Status: `201 Created`
   - Response includes: `id`, `key`, `key_prefix`, `name`, `scopes`, `rate_limit`, `created_at`, `message`
   - `key` field contains a 64-character hexadecimal string

2. **Test 2: Authenticate with generated API key**
   - HTTP Status: `200 OK`
   - Response includes list of API keys or successful data retrieval
   - Request includes `X-API-Key` header with the generated key

3. **Test 3: Authenticate with invalid API key**
   - HTTP Status: `401 Unauthorized` or `403 Forbidden`
   - Response includes error message indicating invalid or unauthorized API key

4. **Test 4: Request without API key header**
   - HTTP Status: Varies based on endpoint configuration
   - May return `401 Unauthorized` for protected endpoints
   - May return `200 OK` for endpoints that support optional authentication

### Troubleshooting

**Backend not running:**
```
curl: (7) Failed to connect to localhost port 8000: Connection refused
```
→ Start the backend server (see Prerequisites)

**Database not initialized:**
```
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.UndefinedTable) relation "api_keys" does not exist
```
→ Run migrations: `cd backend && alembic upgrade head`

**Python not found:**
```
python3: command not found
```
→ Install Python 3 or use an environment with Python 3 available

### Integration Points Verified

This test verifies the following Phase 1 implementation components:

- ✅ API key generation endpoint (`/api/api-keys/generate`)
- ✅ API key authentication middleware (`APIKeyAuthMiddleware`)
- ✅ API key authentication dependency (`get_api_key`)
- ✅ API routes registration in `main.py`
- ✅ Database models and migrations
- ✅ SHA-256 key hashing
- ✅ Scope validation
- ✅ Rate limit configuration

### Related Subtasks

- **subtask-1-1:** API key authentication middleware
- **subtask-1-2:** API key authentication dependency
- **subtask-1-4:** Middlewares registered in main.py
- **subtask-1-5:** API routes registered in main.py
- **subtask-2-3:** Test API key authentication flow (this test)
