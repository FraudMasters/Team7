# API Migration Guide

AgentHR Backend - API Versioning and Migration Strategy

---

## Table of Contents

1. [API Versioning Strategy](#api-versioning-strategy)
2. [Versioning Principles](#versioning-principles)
3. [Current API Version](#current-api-version)
4. [Migration Path](#migration-path)
5. [Breaking Changes](#breaking-changes)
6. [Deprecation Policy](#deprecation-policy)
7. [Version Compatibility](#version-compatibility)
8. [Backward Compatibility](#backward-compatibility)
9. [Testing and Validation](#testing-and-validation)
10. [Migration Examples](#migration-examples)
11. [Best Practices](#best-practices)
12. [Quick Reference](#quick-reference)

---

## API Versioning Strategy

### Version Identification

Version identification is the method clients use to specify which API version they want to consume. AgentHR supports multiple versioning approaches, with **URL path versioning** as the primary method.

#### URL Versioning (Primary Method)

AgentHR uses **URL path versioning** for API version control:

```
http://localhost:8000/api/v1/resumes/
http://localhost:8000/api/v2/resumes/
```

**Implementation Example:**

```python
from fastapi import APIRouter

# v1 router
router_v1 = APIRouter(prefix="/api/v1", tags=["Resumes v1"])

@router_v1.post("/resumes/upload")
async def upload_resume_v1(file: UploadFile):
    """v1 implementation with basic validation"""
    # v1 logic here
    pass

# v2 router
router_v2 = APIRouter(prefix="/api/v2", tags=["Resumes v2"])

@router_v2.post("/resumes/upload")
async def upload_resume_v2(file: UploadFile):
    """v2 implementation with enhanced validation and analysis"""
    # v2 logic here
    pass

# Include both routers in main app
app.include_router(router_v1)
app.include_router(router_v2)
```

**Client Usage:**

```python
import requests

# Using v1
response = requests.post(
    "http://localhost:8000/api/v1/resumes/upload",
    files={"file": open("resume.pdf", "rb")}
)

# Using v2
response = requests.post(
    "http://localhost:8000/api/v2/resumes/upload",
    files={"file": open("resume.pdf", "rb")}
)
```

#### Header Versioning (Alternative Method)

Header versioning keeps URLs clean while specifying the version via HTTP headers. This approach is useful for clients who prefer consistent URLs.

**Implementation Example:**

```python
from fastapi import Header, HTTPException

async def get_api_version(
    api_version: str = Header(
        None,
        description="API version (e.g., '1.0', '2.0')"
    )
) -> str:
    """
    Extract and validate API version from header.

    Args:
        api_version: Version from X-API-Version header

    Returns:
        Validated version string

    Raises:
        HTTPException: If version is invalid or missing
    """
    if not api_version:
        # Default to latest stable version
        return "1.0"

    valid_versions = ["1.0", "2.0"]
    if api_version not in valid_versions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid API version. Supported: {valid_versions}"
        )

    return api_version

@app.post("/api/resumes/upload")
async def upload_resume(
    file: UploadFile,
    api_version: str = Depends(get_api_version)
):
    """Route handler that delegates to version-specific logic"""
    if api_version == "1.0":
        return await upload_resume_v1_logic(file)
    elif api_version == "2.0":
        return await upload_resume_v2_logic(file)
```

**Client Usage:**

```python
import requests

# Using header versioning
response = requests.post(
    "http://localhost:8000/api/resumes/upload",
    headers={
        "X-API-Version": "2.0",
        "Authorization": "Bearer your-token"
    },
    files={"file": open("resume.pdf", "rb")}
)
```

**Supported Headers:**

- `X-API-Version`: Primary version header (e.g., "1.0", "2.0")
- `Accept`: Can include version in content type (see Content Negotiation below)

#### Content Negotiation Versioning

Content negotiation uses the `Accept` header to specify the desired API version through media types.

**Implementation Example:**

```python
from fastapi import Header, Accept
from typing import Optional

async def parse_version_from_accept(
    accept: Optional[str] = Header(None)
) -> str:
    """
    Parse API version from Accept header.

    Supports formats:
    - application/vnd.agenthr.v1+json
    - application/vnd.agenthr.v2+json

    Args:
        accept: Accept header value

    Returns:
        Parsed version string
    """
    if not accept:
        return "1.0"  # Default version

    # Parse vendor-specific media type
    if "application/vnd.agenthr.v" in accept:
        # Extract version: application/vnd.agenthr.v1+json -> 1.0
        version_part = accept.split("application/vnd.agenthr.v")[1]
        version = version_part.split("+")[0]
        return f"{version}.0"

    # Fallback for standard JSON
    if "application/json" in accept:
        return "1.0"

    return "1.0"

@app.get("/api/resumes/{resume_id}")
async def get_resume(
    resume_id: str,
    accept_version: str = Depends(parse_version_from_accept)
):
    """Return resume data in version-specific format"""
    resume = await get_resume_by_id(resume_id)

    if accept_version == "1.0":
        return format_resume_v1(resume)
    elif accept_version == "2.0":
        return format_resume_v2(resume)
```

**Client Usage:**

```python
import requests

# Using content negotiation
response = requests.get(
    "http://localhost:8000/api/resumes/123",
    headers={
        "Accept": "application/vnd.agenthr.v2+json"
    }
)

# Response format matches v2 schema
data = response.json()
```

**Vendor Media Type Format:**

```
application/vnd.agenthr.v{major_version}+json

Examples:
- application/vnd.agenthr.v1+json
- application/vnd.agenthr.v2+json
- application/vnd.agenthr.v1+xml (future XML support)
```

#### Versioning Approach Comparison

| Approach | Pros | Cons | Use Case |
|----------|------|------|----------|
| **URL Path** | Clear versioning, easy to cache, explicit, browser-friendly | Requires client updates, longer URLs | **Default choice** for public APIs |
| **Header Versioning** | Clean URLs, flexible routing | Harder to cache, less explicit, debugging complexity | Internal APIs, URL-sensitive clients |
| **Content Negotiation** | RESTful, standard HTTP semantics | Complex implementation, limited tooling | Enterprise clients with strict REST requirements |

#### Version Detection Flow

```python
# Pseudo-code showing version detection priority
async def determine_api_version(request: Request) -> str:
    """
    Determine API version using priority order:
    1. URL path (/api/v1/, /api/v2/)
    2. Accept header (content negotiation)
    3. X-API-Version header
    4. Default to latest stable
    """

    # 1. Check URL path
    path = request.url.path
    if "/api/v1/" in path:
        return "1.0"
    elif "/api/v2/" in path:
        return "2.0"

    # 2. Check Accept header
    accept = request.headers.get("Accept", "")
    if "application/vnd.agenthr.v2" in accept:
        return "2.0"
    elif "application/vnd.agenthr.v1" in accept:
        return "1.0"

    # 3. Check X-API-Version header
    header_version = request.headers.get("X-API-Version")
    if header_version:
        return validate_version(header_version)

    # 4. Default to latest stable
    return "1.0"
```

#### Best Practices for Version Identification

1. **Be Explicit:** Always include the version in your API calls
   ```python
   # Good
   url = "http://localhost:8000/api/v1/resumes/"

   # Bad (relies on default)
   url = "http://localhost:8000/api/resumes/"
   ```

2. **Use URL Versioning for Public APIs:** Most intuitive for API consumers
   ```python
   BASE_URL = "https://api.agenthr.com/api/v1"
   ```

3. **Document Version Headers:** Clearly communicate which headers to use
   ```http
   GET /api/v1/resumes/123
   X-API-Version: 1.0
   Accept: application/vnd.agenthr.v1+json
   ```

4. **Return Version in Response:** Help clients identify which version they received
   ```json
   {
     "id": "123",
     "filename": "resume.pdf",
     "_meta": {
       "api_version": "1.0.0",
       "schema_version": "2023-12-01"
     }
   }
   ```

5. **Handle Version Mismatches:** Gracefully handle version-related errors
   ```python
   try:
       response = call_api()
   except InvalidVersionError as e:
       logger.warning(f"Invalid API version: {e.version}")
       # Fall back to default version
       response = call_api(version="1.0")
   ```

### Version Numbering Scheme

We follow **Semantic Versioning (SemVer)** for API versions:

```
MAJOR.MINOR.PATCH

MAJOR: Breaking changes
MINOR: New features, backward compatible
PATCH: Bug fixes, backward compatible
```

**Examples:**
- `1.0.0` → Initial release
- `1.1.0` → New endpoints added
- `1.1.1` → Bug fix
- `2.0.0` → Breaking changes

---

## Versioning Principles

### 1. Backward Compatibility

**Maintain backward compatibility whenever possible:**

✅ **Adding New Fields**
```json
// v1 Response
{
  "id": "123",
  "filename": "resume.pdf"
}

// v1.1 Response (backward compatible)
{
  "id": "123",
  "filename": "resume.pdf",
  "file_size": 2048,  // New field
  "content_type": "application/pdf"  // New field
}
```

❌ **Removing Fields (Breaking Change)**
```json
// v1 Response
{
  "id": "123",
  "filename": "resume.pdf",
  "legacy_field": "old data"
}

// v2 Response (breaking change)
{
  "id": "123",
  "filename": "resume.pdf"
  // legacy_field removed
}
```

### 2. New Endpoints vs. Modifying Existing

**Prefer creating new endpoints over modifying existing ones:**

✅ **Add New Endpoint**
```
POST /api/v1/resumes/upload
POST /api/v1/resumes/upload-with-analysis  # New endpoint
```

❌ **Modify Existing Endpoint**
```
POST /api/v1/resumes/upload  # Original: upload only
POST /api/v1/resumes/upload  # Modified: auto-analyzes (breaking)
```

### 3. Deprecation Warnings

**Include deprecation headers for outdated endpoints:**

```http
HTTP/1.1 200 OK
X-API-Deprecated: true
X-API-Sunset: 2026-12-31
X-API-Recommended-Version: v2
X-API-Recommended-Endpoint: /api/v2/resumes/upload
Link: </api/v2/resumes/upload>; rel="successor-version"
```

---

## Current API Version

### Version 1.0.0 (Current Stable)

**Base URL:** `http://localhost:8000/api/v1/`

**Status:** ✅ Active (Current)

**Release Date:** 2026-01-15

**Key Features:**
- Resume upload and analysis
- Job matching with skill synonyms
- Candidate workflow management
- Advanced search with boolean queries
- Report generation
- ML model versioning

**Documentation:** [API_REFERENCE.md](./API_REFERENCE.md)

### Version 2.0.0 (Beta - Coming Soon)

**Base URL:** `http://localhost:8000/api/v2/`

**Status:** 🚧 In Development

**Planned Features:**
- Enhanced security with OAuth2
- Real-time webhook notifications
- GraphQL support
- Advanced analytics endpoints
- Batch operation optimizations

---

## Migration Path

### From v1 to v2 (Planned)

**Step 1: Review Breaking Changes**

Check the [Breaking Changes](#breaking-changes) section below.

**Step 2: Update Base URL**

```python
# Old (v1)
BASE_URL = "http://localhost:8000/api/v1"

# New (v2)
BASE_URL = "http://localhost:8000/api/v2"
```

**Step 3: Update Authentication**

```python
# Old (v1) - Basic API Key
headers = {
    "X-API-Key": "your-api-key"
}

# New (v2) - OAuth2 Bearer Token
headers = {
    "Authorization": "Bearer your-oauth-token"
}
```

**Step 4: Test in Staging Environment**

```bash
# Test v2 endpoints before production
curl -X GET http://staging.agenthr.com/api/v2/resumes/ \
  -H "Authorization: Bearer test-token"
```

**Step 5: Gradual Rollout**

1. Route 10% of traffic to v2
2. Monitor error rates and performance
3. Incrementally increase to 50%, then 100%
4. Decommission v1 after sunset date

---

## Breaking Changes

### Breaking Change Categories

Breaking changes are modifications to the API that may require updates to client code. Understanding these categories helps you prepare for migrations and assess the impact of version upgrades.

#### Category 1: Endpoint Removal

**Description:** Complete removal of an endpoint from the API.

**Impact:** High - Clients using this endpoint must migrate to alternative endpoints.

**Example:**

**v1:**
```http
POST /api/v1/resumes/quick-upload
```

**v2:** Endpoint removed, clients must use:
```http
POST /api/v2/resumes/upload
```

**Migration:**
```python
# v1 code
def quick_upload(file_path):
    url = "http://localhost:8000/api/v1/resumes/quick-upload"
    # ...

# v2 code - use standard upload endpoint
def upload_resume(file_path):
    url = "http://localhost:8000/api/v2/resumes/upload"
    # ...
```

---

#### Category 2: Schema Changes

**Description:** Changes to the structure or format of request/response bodies.

**Impact:** Medium to High - Clients must update data parsing and serialization logic.

**Subcategories:**

**A. Field Removal**
```json
// v1 Response
{
  "id": "123",
  "filename": "resume.pdf",
  "legacy_field": "old data"
}

// v2 Response (breaking change)
{
  "id": "123",
  "filename": "resume.pdf"
  // legacy_field removed
}
```

**B. Field Renaming**
```json
// v1 Request
{
  "resume_id": "123",
  "vacancy_id": "456"
}

// v2 Request (breaking change)
{
  "resumeId": "123",  // snake_case → camelCase
  "vacancyId": "456"
}
```

**C. Type Changes**
```json
// v1 Response
{
  "match_percentage": "85.5"  // String
}

// v2 Response (breaking change)
{
  "match_percentage": 85.5  // Number
}
```

**D. Nested Structure Changes**
```json
// v1 Response
{
  "error": "Resume not found"
}

// v2 Response (breaking change)
{
  "error": {
    "code": "RESUME_NOT_FOUND",
    "message": "Resume not found",
    "details": {
      "resume_id": "123"
    }
  }
}
```

---

#### Category 3: Parameter Changes

**Description:** Modifications to endpoint parameters, including query parameters, path parameters, or request body fields.

**Impact:** Medium - Clients must update parameter names, values, or structure.

**Subcategories:**

**A. Parameter Removal**
```http
# v1
GET /api/v1/resumes/?include_deleted=true

# v2 - parameter removed
GET /api/v2/resumes/
```

**B. Parameter Renaming**
```http
# v1
GET /api/v1/candidates/?skip=0&limit=50

# v2 - parameters renamed
GET /api/v2/candidates/?offset=0&pageSize=50
```

**C. Parameter Type Changes**
```http
# v1 - limit as integer
GET /api/v1/resumes/?limit=50

# v2 - limit as string (requires validation)
GET /api/v2/resumes/?limit="50"
```

**D. Required vs Optional Changes**
```json
// v1 - optional parameter
{
  "resume_id": "123",
  "vacancy_data": {...}
}

// v2 - vacancy_data now required
{
  "resume_id": "123",
  "vacancy_data": {...}  // Now required, was optional
}
```

**E. Default Value Changes**
```http
# v1 - default limit=100
GET /api/v1/resumes/

# v2 - default limit=50 (breaking change for clients relying on default)
GET /api/v2/resumes/
```

---

#### Category 4: HTTP Method Changes

**Description:** Changing the HTTP method for an endpoint.

**Impact:** High - Clients must update the HTTP verb used.

**Example:**
```http
# v1
POST /api/v1/resumes/analyze

# v2 - changed to GET (breaking change)
GET /api/v2/resumes/analyze?resume_id=123
```

---

#### Category 5: Response Format Changes

**Description:** Changes to how responses are structured, including pagination, error handling, and metadata.

**Impact:** Medium to High - Clients must update response parsing logic.

**Subcategories:**

**A. Pagination Structure**
```json
// v1 Response
{
  "total": 100,
  "resumes": [...],
  "skip": 0,
  "limit": 50
}

// v2 Response (breaking change)
{
  "meta": {
    "total": 100,
    "page": 1,
    "per_page": 50,
    "total_pages": 2
  },
  "data": [...]
}
```

**B. Date Format**
```json
// v1 Response - ISO 8601 with milliseconds
{
  "created_at": "2026-01-15T10:30:00.123Z"
}

// v2 Response - ISO 8601 without milliseconds (breaking change)
{
  "created_at": "2026-01-15T10:30:00Z"
}
```

**C. Error Response Format**
```json
// v1 Error Response
{
  "detail": "Resume not found"
}

// v2 Error Response (breaking change)
{
  "error": {
    "code": "RESUME_NOT_FOUND",
    "message": "Resume not found",
    "details": {
      "resume_id": "123",
      "suggestion": "Check the resume ID and try again"
    }
  }
}
```

---

#### Category 6: Authentication/Authorization Changes

**Description:** Changes to how authentication and authorization are handled.

**Impact:** High - All authenticated requests must be updated.

**Example:**
```http
# v1 - API Key authentication
POST /api/v1/resumes/upload
X-API-Key: your-api-key

# v2 - OAuth2 Bearer token (breaking change)
POST /api/v2/resumes/upload
Authorization: Bearer your-oauth-token
```

**Migration:**
```python
# v1 code
def make_request(url):
    headers = {"X-API-Key": API_KEY}
    return requests.post(url, headers=headers)

# v2 code
def make_request(url):
    token = get_oauth_token()
    headers = {"Authorization": f"Bearer {token}"}
    return requests.post(url, headers=headers)
```

---

#### Category 7: Header Changes

**Description:** Changes to required or optional HTTP headers.

**Impact:** Medium - Clients must update headers sent with requests.

**Examples:**

**A. Required Header Addition**
```http
# v1
GET /api/v1/resumes/
Accept-Language: en

# v2 - new required header (breaking change)
GET /api/v2/resumes/
Accept-Language: en
X-Request-ID: required-uuid  # New required header
```

**B. Header Renaming**
```http
# v1
X-API-Version: 1.0

# v2 - header renamed (breaking change)
X-API-Version-String: 1.0
```

---

#### Category 8: Status Code Changes

**Description:** Changes to HTTP status codes returned for specific scenarios.

**Impact:** Medium - Clients must update error handling logic.

**Example:**
```http
# v1 - Resume not found returns 404
GET /api/v1/resumes/nonexistent-id
Response: 404 Not Found

# v2 - Returns 400 with validation error (breaking change)
GET /api/v2/resumes/nonexistent-id
Response: 400 Bad Request
```

---

### Breaking Change Severity Levels

| Severity | Description | Migration Effort | Example |
|----------|-------------|------------------|---------|
| **Critical** | Fundamental changes requiring complete rewrite of client code | High | Authentication method changes |
| **High** | Major structural changes affecting core functionality | High | Schema changes, endpoint removal |
| **Medium** | Changes requiring updates to request/response handling | Medium | Parameter changes, status codes |
| **Low** | Minor changes with backward-compatible alternatives | Low | Optional field additions (non-breaking) |

---

### Breaking Change Detection Checklist

Use this checklist to identify breaking changes in new API versions:

- [ ] **Endpoints**: Are any endpoints removed or renamed?
- [ ] **Methods**: Have HTTP methods changed for any endpoints?
- [ ] **Parameters**: Are any parameters added (required), removed, or renamed?
- [ ] **Schema**: Have request/response schemas changed?
  - [ ] Fields removed?
  - [ ] Fields renamed?
  - [ ] Field types changed?
  - [ ] Nested structures changed?
- [ ] **Headers**: Are any headers now required or removed?
- [ ] **Authentication**: Has the authentication mechanism changed?
- [ ] **Status Codes**: Have success/error status codes changed?
- [ ] **Response Format**: Has pagination, sorting, or filtering changed?
- [ ] **Data Formats**: Have date formats, encoding, or serialization changed?
- [ ] **Rate Limits**: Have rate limits or throttling policies changed?

---

### Minimizing Breaking Changes

**Our Commitment:**

AgentHR follows these principles to minimize breaking changes:

1. **Additive Changes First**: Prefer adding new endpoints/fields over modifying existing ones
2. **Deprecation Period**: Provide minimum 6 months notice before breaking changes
3. **Version Coexistence**: Support multiple API versions simultaneously
4. **Clear Documentation**: Document all breaking changes with migration guides
5. **Graceful Degradation**: Where possible, support old and new formats during transition

**When Breaking Changes Are Unavoidable:**

- Security vulnerabilities requiring immediate fixes
- Fundamental architectural changes
- Removal of deprecated functionality
- Third-party dependency updates

---

### Anticipated Breaking Changes in v2

The following breaking changes are planned for API v2.0.0:

#### 1. Authentication Method (Critical)

**v1:**
```http
POST /api/v1/resumes/upload
X-API-Key: your-api-key
```

**v2:**
```http
POST /api/v2/resumes/upload
Authorization: Bearer your-oauth-token
```

**Migration:**
```python
# v1 code
def upload_resume(file_path):
    headers = {"X-API-Key": API_KEY}
    # ...

# v2 code
def upload_resume(file_path):
    headers = {"Authorization": f"Bearer {get_oauth_token()}"}
    # ...
```

#### 2. Response Format for Errors

**v1:**
```json
{
  "detail": "Resume not found"
}
```

**v2:**
```json
{
  "error": {
    "code": "RESUME_NOT_FOUND",
    "message": "Resume not found",
    "details": {
      "resume_id": "123",
      "suggestion": "Check the resume ID and try again"
    }
  }
}
```

#### 3. Date Format

**v1:** ISO 8601 with milliseconds
```json
{
  "created_at": "2026-01-15T10:30:00.123Z"
}
```

**v2:** ISO 8601 without milliseconds
```json
{
  "created_at": "2026-01-15T10:30:00Z"
}
```

#### 4. Pagination Structure

**v1:**
```json
{
  "total": 100,
  "resumes": [...],
  "skip": 0,
  "limit": 50
}
```

**v2:**
```json
{
  "meta": {
    "total": 100,
    "page": 1,
    "per_page": 50,
    "total_pages": 2
  },
  "data": [...]
}
```

---

## Deprecation Policy

### Overview

AgentHR follows a **predictable deprecation policy** to ensure API consumers have adequate time to migrate to newer versions. Our policy balances innovation with stability, giving you at least **12 months** of notice before any API version is sunset.

### Deprecation Timeline

```
┌─────────────────────────────────────────────────────────────┐
│  API Lifecycle                                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Release ───► Stable ───► Deprecated ───► Sunset            │
│     ▲            ▲              ▲              ▲            │
│     │            │              │              │            │
│  New features   Fully        Warning      No longer       │
│  added         supported      issued        available      │
│                  (min 6        (6 months)   (12 months    │
│                   months)                    after         │
│                                           deprecation)    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Lifecycle Phases

#### 1. Release Phase (Duration: 0-6 months)

**Characteristics:**
- New API version released
- May have bugs or instability
- Feature additions possible
- Not recommended for production

**Requirements:**
- Clearly marked as "Beta" or "Release Candidate"
- No backward compatibility guarantees
- Frequent updates possible

**Example Headers:**
```http
HTTP/1.1 200 OK
X-API-Version: 2.0.0
X-API-Stability: Beta
```

#### 2. Stable Phase (Duration: Minimum 12 months)

**Characteristics:**
- Fully supported and production-ready
- Backward compatible within major version
- Security patches and bug fixes
- Feature additions (minor versions)

**Requirements:**
- No breaking changes without major version bump
- Comprehensive documentation
- 99.9% uptime SLA

**Example Headers:**
```http
HTTP/1.1 200 OK
X-API-Version: 1.0.0
X-API-Stability: Stable
```

#### 3. Deprecated Phase (Duration: 6-12 months)

**Characteristics:**
- No new features
- Security fixes only
- Clients must migrate to newer version
- Clear sunset date communicated

**Notification Requirements:**
- Deprecation headers on all responses
- Email notifications to registered API users
- Blog post announcement
- In-product notifications for UI clients

**Example Headers:**
```http
HTTP/1.1 200 OK
X-API-Version: 1.0.0
X-API-Stability: Deprecated
X-API-Deprecated: true
X-API-Sunset: 2027-12-31
X-API-Recommended-Version: 2.0.0
X-API-Recommended-Endpoint: /api/v2/resumes/upload
Link: </api/v2/resumes/upload>; rel="successor-version"
```

#### 4. Sunset Phase

**Characteristics:**
- End of life
- No longer available
- Requests return 410 Gone
- Documentation archived

**Example Response:**
```http
HTTP/1.1 410 Gone
Content-Type: application/json

{
  "error": {
    "code": "API_VERSION_SUNSET",
    "message": "API v1.0.0 is no longer available. Please upgrade to v2.0.0.",
    "details": {
      "sunset_date": "2027-12-31",
      "recommended_version": "2.0.0",
      "migration_guide": "https://docs.agenthr.com/api/migration-v1-to-v2"
    }
  }
}
```

### Policy Rules

| Rule | Description | Duration |
|------|-------------|----------|
| **Minimum Support Period** | All API versions supported for at least 12 months after stable release | 12 months minimum |
| **Deprecation Notice Period** | Advance notice before sunset | 6 months minimum |
| **Sunset Timeline** | Time between deprecation and sunset | 6-12 months |
| **Emergency Security Fixes** | Critical security patches for deprecated versions | Until sunset |
| **Feature Freeze** | No new features added to deprecated versions | Immediately on deprecation |
| **Breaking Changes** | Never introduced within a major version | Never |

### Example Timeline

**API v1.0.0:**
- ✅ Released: 2026-01-15
- ✅ Stable: 2026-07-15 (after 6 months beta)
- ⚠️ Deprecated: 2026-12-31 (planned)
- ❌ Sunset: 2027-12-31 (planned)

**Total Support Duration:** 23 months (6 months beta + 12 months stable + 6 months deprecation notice)

### Deprecation Notification Process

#### Notification Timeline

We use a **multi-channel notification strategy** to ensure all API consumers are aware of upcoming deprecations.

**T-Minus 90 Days (Pre-Deprecation):**
- 📧 Email notification to all registered API users
- 📢 Blog post: "Upcoming API v1 Deprecation"
- 📋 Dashboard banner for admin users
- 📱 In-app notification for integrated clients

**T-Minus 60 Days:**
- 📧 Follow-up email reminder
- 🎯 Targeted outreach to high-volume API users
- 📊 Usage analytics shared with affected users

**T-Minus 30 Days:**
- 📧 Final reminder before deprecation
- 📞 Direct outreach to enterprise clients
- 🆘 Migration support office hours

**Deprecation Day (Day 0):**
- 🚨 Deprecation headers activated on all responses
- 📝 Documentation updated with deprecation notice
- 🔄 Auto-redirect to newer version (where applicable)

#### Notification Channels

| Channel | Description | Frequency | Audience |
|---------|-------------|-----------|----------|
| **Email** | Direct email to API registrants | T-90, T-60, T-30 days | All registered users |
| **Blog** | Public announcement posts | T-90, T-30, Day 0 | All users |
| **Dashboard** | In-product banners | Continuous from T-90 | Admin users |
| **Headers** | HTTP response headers | Day 0 to Sunset | API clients |
| **Webhook** | Push notifications (opt-in) | All milestones | Webhook subscribers |
| **Changelog** | API changelog updates | Each milestone | Documentation readers |
| **Slack/Discord** | Community channel posts | T-90, T-30, Day 0 | Community members |

#### HTTP Headers Implementation

**Server-Side Implementation (FastAPI):**

```python
from fastapi import Response
from datetime import datetime

def add_deprecation_headers(
    response: Response,
    api_version: str,
    sunset_date: str,
    recommended_version: str
):
    """
    Add deprecation headers to API responses.

    Args:
        response: FastAPI Response object
        api_version: Current API version (e.g., "1.0.0")
        sunset_date: Sunset date (ISO 8601 format)
        recommended_version: Recommended upgrade version
    """
    # Check if version is deprecated
    is_deprecated = check_if_deprecated(api_version)

    if is_deprecated:
        response.headers["X-API-Deprecated"] = "true"
        response.headers["X-API-Sunset"] = sunset_date
        response.headers["X-API-Recommended-Version"] = recommended_version
        response.headers["X-API-Deprecation-Info"] = (
            f"Version {api_version} will be sunset on {sunset_date}. "
            f"Please migrate to {recommended_version}. "
            f"See: https://docs.agenthr.com/api/migration-{api_version}-to-{recommended_version}"
        )

        # Add Link header for HTTP-based discovery
        response.headers["Link"] = (
            f"</api/v{recommended_version.split('.')[0]}>; "
            f'rel="successor-version", '
            f'<https://docs.agenthr.com/api/migration>; '
            f'rel="deprecation-documentation"'
        )

    return response

# Usage in endpoint
@app.get("/api/v1/resumes/{resume_id}")
async def get_resume(resume_id: str, response: Response):
    resume = await get_resume_by_id(resume_id)

    # Add deprecation headers
    add_deprecation_headers(
        response,
        api_version="1.0.0",
        sunset_date="2027-12-31",
        recommended_version="2.0.0"
    )

    return resume
```

**Client-Side Detection (Python):**

```python
import requests
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

class APIDeprecationWarning(UserWarning):
    """Warning raised when using deprecated API version."""
    pass

def check_deprecation_headers(response: requests.Response) -> Optional[dict]:
    """
    Check response for deprecation headers and parse them.

    Args:
        response: requests Response object

    Returns:
        Dict with deprecation info if deprecated, None otherwise
    """
    deprecated = response.headers.get("X-API-Deprecated", "false").lower()

    if deprecated == "true":
        sunset = response.headers.get("X-API-Sunset")
        recommended = response.headers.get("X-API-Recommended-Version")
        info = response.headers.get("X-API-Deprecation-Info", "")

        # Calculate days until sunset
        if sunset:
            sunset_date = datetime.fromisoformat(sunset)
            days_remaining = (sunset_date - datetime.now()).days
        else:
            days_remaining = None

        return {
            "sunset_date": sunset,
            "recommended_version": recommended,
            "days_remaining": days_remaining,
            "info": info
        }

    return None

def make_api_request(url: str, **kwargs) -> requests.Response:
    """
    Make API request with deprecation checking.

    Args:
        url: API endpoint URL
        **kwargs: Arguments to pass to requests

    Returns:
        Response object

    Raises:
        APIDeprecationWarning: If API version is deprecated
    """
    response = requests.get(url, **kwargs)

    # Check for deprecation
    deprecation_info = check_deprecation_headers(response)

    if deprecation_info:
        warning_msg = (
            f"⚠️  API DEPRECATION WARNING ⚠️\n"
            f"Version will be sunset on: {deprecation_info['sunset_date']}\n"
            f"Days remaining: {deprecation_info['days_remaining']}\n"
            f"Recommended version: {deprecation_info['recommended_version']}\n"
            f"Info: {deprecation_info['info']}"
        )
        logger.warning(warning_msg)
        raise APIDepationWarning(warning_msg)

    return response

# Usage example
try:
    response = make_api_request(
        "http://localhost:8000/api/v1/resumes/123",
        headers={"X-API-Key": "your-key"}
    )
except APIDeprecationWarning as e:
    # Log and handle deprecation
    print(f"Warning: {e}")
    # Automatically retry with recommended version
    # or prompt user to upgrade
```

**Client-Side Detection (JavaScript/TypeScript):**

```typescript
interface DeprecationInfo {
  sunsetDate: string;
  recommendedVersion: string;
  daysRemaining: number;
  info: string;
}

function checkDeprecationHeaders(response: Response): DeprecationInfo | null {
  const deprecated = response.headers.get('X-API-Deprecated');

  if (deprecated === 'true') {
    const sunset = response.headers.get('X-API-Sunset') || '';
    const recommended = response.headers.get('X-API-Recommended-Version') || '';
    const info = response.headers.get('X-API-Deprecation-Info') || '';

    // Calculate days until sunset
    const sunsetDate = new Date(sunset);
    const daysRemaining = Math.ceil(
      (sunsetDate.getTime() - Date.now()) / (1000 * 60 * 60 * 24)
    );

    return {
      sunsetDate: sunset,
      recommendedVersion: recommended,
      daysRemaining,
      info
    };
  }

  return null;
}

// Usage with fetch
async function fetchWithDeprecationCheck(url: string): Promise<any> {
  const response = await fetch(url);

  const deprecationInfo = checkDeprecationHeaders(response);

  if (deprecationInfo) {
    console.warn('⚠️ API DEPRECATION WARNING ⚠️', {
      sunsetDate: deprecationInfo.sunsetDate,
      daysRemaining: deprecationInfo.daysRemaining,
      recommendedVersion: deprecationInfo.recommendedVersion
    });

    // Show in-app notification
    showDeprecationNotification(deprecationInfo);
  }

  return response.json();
}

// In-app notification component
function showDeprecationNotification(info: DeprecationInfo): void {
  const notification = `
    <div class="deprecation-banner">
      <strong>⚠️ API Version Deprecation</strong><br>
      This API version will be sunset on ${info.sunsetDate}<br>
      (${info.daysRemaining} days remaining)<br>
      Please upgrade to version ${info.recommendedVersion}<br>
      <a href="/docs/migration">View Migration Guide</a>
    </div>
  `;

  document.body.insertAdjacentHTML('afterbegin', notification);
}
```

### Monitoring and Compliance

#### Usage Analytics

AgentHR tracks API usage by version to identify laggards and provide targeted support:

```python
# API usage monitoring
from prometheus_client import Counter

api_requests = Counter(
    'api_requests_total',
    'Total API requests',
    ['api_version', 'endpoint', 'status']
)

@app.middleware("http")
async def track_api_usage(request: Request, call_next):
    """Track API usage by version."""
    response = await call_next(request)

    # Extract version from path
    version = extract_version_from_path(request.url.path)

    # Record metrics
    api_requests.labels(
        api_version=version,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()

    return response
```

#### Compliance Dashboard

Monitor migration progress:

```python
# Admin endpoint to check migration compliance
@app.get("/admin/api/migration-status")
async def get_migration_status():
    """
    Get API version usage statistics for compliance monitoring.

    Returns:
        Dict with usage breakdown by version
    """
    return {
        "v1_usage": {
            "percentage": 35,  # 35% still on v1
            "request_count": 3500000,
            "users": [
                {"user_id": "123", "last_seen": "2026-02-01"},
                {"user_id": "456", "last_seen": "2026-02-03"}
            ]
        },
        "v2_usage": {
            "percentage": 65,  # 65% migrated to v2
            "request_count": 6500000
        },
        "sunset_date": "2027-12-31",
        "days_remaining": 700
    }
```

### Migration Support Resources

**Available Resources:**
- 📖 [Migration Guide](#migration-examples) - Step-by-step migration instructions
- 🔧 [API Reference](./API_REFERENCE.md) - Complete API documentation
- 💬 Community Support - Slack channel for migration questions
- 📧 Enterprise Support - Dedicated support for enterprise customers
- 🆘 Migration Office Hours - Weekly Q&A sessions during deprecation period

**Migration Checklist:**
- [ ] Review breaking changes documentation
- [ ] Update API client configuration
- [ ] Test in staging environment
- [ ] Update authentication (if required)
- [ ] Update request/response handling
- [ ] Deploy to production
- [ ] Monitor error rates
- [ ] Remove old API version references

---

## Version Compatibility

### Support Matrix

| API Version | Released | Deprecated | Sunset | Status |
|-------------|----------|------------|--------|--------|
| v1.0.0 | 2026-01-15 | 2026-12-31 | 2027-12-31 | ✅ Stable |
| v2.0.0 | TBD | TBD | TBD | 🚧 In Development |

### Client Compatibility

**Recommended Client Updates:**

| Client Type | Recommended Version | Minimum Compatible |
|-------------|---------------------|-------------------|
| Python SDK | 2.0.0+ | 1.5.0+ |
| JavaScript SDK | 2.0.0+ | 1.5.0+ |
| Mobile App | 3.0.0+ | 2.1.0+ |

---

## Backward Compatibility

### Overview

AgentHR is committed to maintaining **backward compatibility** within major API versions to ensure stability for our API consumers. This section outlines our compatibility guarantees, what changes are considered breaking, and strategies for maintaining compatibility during API evolution.

### Compatibility Guarantees

#### What We Guarantee

Within a **major API version** (e.g., v1.x.x), we guarantee:

| Guarantee Type | Description | Duration |
|----------------|-------------|----------|
| **Endpoint Stability** | Existing endpoints will not be removed without major version bump | Until major version increment |
| **Field Stability** | Required fields in requests/responses will not be removed | Until major version increment |
| **Data Types** | Field data types will not change in breaking ways | Until major version increment |
| **HTTP Methods** | HTTP verbs for endpoints remain consistent | Until major version increment |
| **Authentication** | Authentication mechanisms will not change within major version | Until major version increment |
| **Error Codes** | Error response format remains consistent | Until major version increment |

#### Backward Compatible Changes

The following changes **ARE** considered backward compatible and can be made within a major version:

✅ **Adding New Optional Fields**
```json
// v1.0 Response
{
  "id": "123",
  "filename": "resume.pdf"
}

// v1.1 Response (backward compatible)
{
  "id": "123",
  "filename": "resume.pdf",
  "file_size": 2048,  // New optional field
  "content_type": "application/pdf"  // New optional field
}
```

✅ **Adding New Endpoints**
```http
# Existing endpoints remain functional
GET /api/v1/resumes/

# New endpoints added without affecting existing ones
POST /api/v1/resumes/batch-upload
GET /api/v1/resumes/analytics
```

✅ **Adding New Query Parameters**
```http
# Existing calls work without new parameter
GET /api/v1/resumes/?skip=0&limit=50

# New parameter is optional
GET /api/v1/resumes/?skip=0&limit=50&include_deleted=true
```

✅ **Adding New Values to Enum Fields**
```json
// v1.0: status could be "pending" or "completed"
{"status": "pending"}

// v1.1: adds new status "in_progress" (old clients ignore)
{"status": "in_progress"}
```

✅ **Relaxing Validation Rules**
```python
# v1.0: username must be 3-20 characters
# v1.1: username can be 1-30 characters (relaxed requirement)
```

✅ **Changing Order of Fields**
```json
// Field order change is not breaking for JSON
{"id": "123", "filename": "resume.pdf"}
// vs
{"filename": "resume.pdf", "id": "123"}
```

✅ **Adding New Headers**
```http
# New optional headers don't break existing clients
X-Request-ID: optional-uuid
X-Client-Version: 1.0.0
```

#### Breaking Changes (Require Major Version Bump)

The following changes **ARE NOT** backward compatible and require a major version increment:

❌ **Removing Fields**
```json
// v1 Response
{
  "id": "123",
  "filename": "resume.pdf",
  "legacy_field": "old data"
}

// v2 Response (breaking change)
{
  "id": "123",
  "filename": "resume.pdf"
  // legacy_field removed
}
```

❌ **Renaming Fields**
```json
// v1 Request
{
  "resume_id": "123",
  "vacancy_id": "456"
}

// v2 Request (breaking change)
{
  "resumeId": "123",  // snake_case → camelCase
  "vacancyId": "456"
}
```

❌ **Changing Field Types**
```json
// v1 Response
{
  "match_percentage": "85.5"  // String
}

// v2 Response (breaking change)
{
  "match_percentage": 85.5  // Number
}
```

❌ **Making Optional Fields Required**
```json
// v1: optional parameter
{
  "resume_id": "123",
  "vacancy_data": {...}  // Optional
}

// v2: vacancy_data now required (breaking change)
{
  "resume_id": "123",
  "vacancy_data": {...}  // Required
}
```

❌ **Removing or Renaming Endpoints**
```http
# v1
POST /api/v1/resumes/quick-upload

# v2: endpoint removed (breaking change)
# Clients must use POST /api/v2/resumes/upload instead
```

❌ **Changing HTTP Methods**
```http
# v1
POST /api/v1/resumes/analyze

# v2: changed to GET (breaking change)
GET /api/v2/resumes/analyze?resume_id=123
```

❌ **Changing Response Format Structure**
```json
// v1 Response
{
  "total": 100,
  "resumes": [...],
  "skip": 0,
  "limit": 50
}

// v2 Response (breaking change - new structure)
{
  "meta": {
    "total": 100,
    "page": 1,
    "per_page": 50
  },
  "data": [...]
}
```

### Compatibility Strategies

#### Strategy 1: Version Coexistence

Maintain multiple API versions simultaneously to allow gradual migration:

```python
from fastapi import APIRouter

# Both v1 and v2 routers active in same application
router_v1 = APIRouter(prefix="/api/v1", tags=["v1"])
router_v2 = APIRouter(prefix="/api/v2", tags=["v2"])

# Include both routers
app.include_router(router_v1)
app.include_router(router_v2)

# v1 endpoint continues working
@router_v1.get("/resumes/{resume_id}")
async def get_resume_v1(resume_id: str):
    """Legacy v1 implementation"""
    return await get_resume_legacy_format(resume_id)

# v2 endpoint with new features
@router_v2.get("/resumes/{resume_id}")
async def get_resume_v2(resume_id: str):
    """Enhanced v2 implementation"""
    return await get_resume_enhanced_format(resume_id)
```

#### Strategy 2: Feature Flags

Use feature flags to introduce new behavior gradually:

```python
from typing import Optional
from pydantic import BaseModel

class ResumeUploadRequest(BaseModel):
    file_id: str
    use_new_parser: Optional[bool] = False  # Feature flag

@app.post("/api/v1/resumes/upload")
async def upload_resume(request: ResumeUploadRequest):
    """Upload resume with optional new parser"""

    if request.use_new_parser:
        # Use new improved parser
        result = await parse_resume_v2(request.file_id)
    else:
        # Use legacy parser
        result = await parse_resume_v1(request.file_id)

    return result
```

#### Strategy 3: Content Negotiation

Support multiple response formats based on client preferences:

```python
from fastapi import Header, Accept

@app.get("/api/v1/resumes/{resume_id}")
async def get_resume(
    resume_id: str,
    accept: str = Header(None)
):
    """Return resume in client-preferred format"""

    resume = await get_resume_by_id(resume_id)

    # Check Accept header for format preference
    if "application/vnd.agenthr.v2+json" in accept:
        # Return v2 format
        return format_resume_v2(resume)
    else:
        # Default to v1 format
        return format_resume_v1(resume)
```

#### Strategy 4: Adapter Layer

Implement an adapter layer to maintain backward compatibility:

```python
from typing import Dict, Any

class ResumeAdapter:
    """Adapter to convert between v1 and v2 formats"""

    @staticmethod
    def v1_to_v2(v1_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert v1 format to v2 format"""
        return {
            "meta": {
                "version": "2.0",
                "total": 1
            },
            "data": [{
                "resumeId": v1_data["id"],  # snake_case → camelCase
                "fileName": v1_data["filename"],
                # ... field mappings
            }]
        }

    @staticmethod
    def v2_to_v1(v2_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert v2 format to v1 format"""
        items = v2_data.get("data", [])
        if items:
            item = items[0]
            return {
                "id": item["resumeId"],  # camelCase → snake_case
                "filename": item["fileName"],
                # ... field mappings
            }
        return {}

# Usage in endpoint
@app.get("/api/v1/resumes/{resume_id}")
async def get_resume_v1(resume_id: str):
    """v1 endpoint that uses v2 backend logic"""

    # Get data from v2 service
    v2_data = await resume_service_v2.get_resume(resume_id)

    # Adapt to v1 format for backward compatibility
    return ResumeAdapter.v2_to_v1(v2_data)
```

#### Strategy 5: Deprecation Period

Provide adequate notice before removing deprecated features:

```python
from fastapi import Response
import logging

logger = logging.getLogger(__name__)

@app.get("/api/v1/resumes/legacy-search")
async def legacy_search(query: str, response: Response):
    """Legacy search endpoint (deprecated)"""

    # Add deprecation headers
    response.headers["X-API-Deprecated"] = "true"
    response.headers["X-API-Sunset"] = "2027-12-31"
    response.headers["X-API-Recommended-Endpoint"] = "/api/v2/search/candidates"

    # Log usage for monitoring
    logger.warning(f"Legacy endpoint used: /api/v1/resumes/legacy-search")

    # Execute legacy logic
    results = await legacy_search_service.search(query)

    # Include deprecation notice in response
    results["_deprecation_notice"] = (
        "This endpoint is deprecated and will be removed on 2027-12-31. "
        "Please migrate to /api/v2/search/candidates"
    )

    return results
```

### Compatibility Testing

#### Version Contract Tests

Ensure API contracts remain stable across versions:

```python
import pytest
from typing import Dict, Any

class APIContractTest:
    """Test suite to verify API contract compatibility"""

    def test_v1_response_structure(self):
        """Verify v1 response structure matches contract"""
        response = requests.get("/api/v1/resumes/123")
        data = response.json()

        # Required fields must exist
        assert "id" in data
        assert "filename" in data

        # Data types must match
        assert isinstance(data["id"], str)
        assert isinstance(data["filename"], str)

    def test_v1_backward_compatible_with_v1_0(self):
        """Verify current v1.1 is backward compatible with v1.0"""
        # Test that old client code still works
        old_client_response = get_resume_using_old_client("123")

        # Should still have all expected fields
        assert "id" in old_client_response
        assert "filename" in old_client_response

        # New optional fields shouldn't break old clients
        # (they're simply ignored by old code)

    def test_new_fields_are_optional(self):
        """Verify that new fields added are truly optional"""
        response = requests.post(
            "/api/v1/resumes/upload",
            json={"filename": "test.pdf"}  # Without new optional fields
        )

        # Should succeed without new fields
        assert response.status_code == 200
```

### Migration Support Tools

#### Compatibility Checker

Provide tools to help clients check compatibility:

```python
class APICompatibilityChecker:
    """Check if client code is compatible with API version"""

    @staticmethod
    def check_response_compatibility(
        api_version: str,
        response_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check if response matches expected schema for version.

        Returns:
            Dict with compatibility status and issues
        """
        compatibility = {
            "compatible": True,
            "issues": [],
            "warnings": []
        }

        if api_version == "1.0":
            # Check v1 required fields
            required_fields = ["id", "filename"]
            for field in required_fields:
                if field not in response_data:
                    compatibility["compatible"] = False
                    compatibility["issues"].append(
                        f"Missing required field: {field}"
                    )

            # Check for unexpected fields (warnings)
            expected_fields = ["id", "filename", "created_at"]
            for field in response_data:
                if field not in expected_fields:
                    compatibility["warnings"].append(
                        f"Unexpected field in v1 response: {field}"
                    )

        return compatibility

# Usage
checker = APICompatibilityChecker()
result = checker.check_response_compatibility("1.0", response_data)

if not result["compatible"]:
    print(f"Compatibility issues: {result['issues']}")
```

---

## Testing and Validation

### Overview

Comprehensive testing is critical for ensuring API migrations proceed smoothly and backward compatibility is maintained. This section provides recommendations for testing API changes, version compatibility, and migration validation.

### Testing Strategy

#### Testing Pyramid

```
           ┌─────────────┐
           │  E2E Tests  │  ←少量: 关键用户流程
           ├─────────────┤
           │Integration  │  ←中等: API版本兼容性
           │   Tests     │
           ├─────────────┤
           │  Unit Tests │  ←大量: 单个函数/方法
           └─────────────┘
```

### Unit Testing

#### Test Individual Version Logic

```python
import pytest
from backend.api.v1.resumes import format_resume_v1
from backend.api.v2.resumes import format_resume_v2

class TestResumeFormatting:
    """Test resume formatting for different API versions"""

    def test_v1_formatting(self):
        """Test v1 response format"""
        resume = {
            "id": "123",
            "filename": "resume.pdf",
            "created_at": "2026-01-15T10:30:00.123Z"
        }

        result = format_resume_v1(resume)

        assert result["id"] == "123"
        assert result["filename"] == "resume.pdf"
        assert "created_at" in result
        assert "meta" not in result  # v1 doesn't have meta wrapper

    def test_v2_formatting(self):
        """Test v2 response format"""
        resume = {
            "id": "123",
            "filename": "resume.pdf",
            "created_at": "2026-01-15T10:30:00Z"
        }

        result = format_resume_v2(resume)

        assert "meta" in result
        assert "data" in result
        assert result["data"]["resumeId"] == "123"  # camelCase
        assert result["meta"]["version"] == "2.0"

    def test_v1_to_v2_adapter(self):
        """Test adapter conversion from v1 to v2"""
        v1_data = {
            "id": "123",
            "filename": "resume.pdf",
            "file_size": 2048
        }

        v2_data = ResumeAdapter.v1_to_v2(v1_data)

        assert v2_data["data"][0]["resumeId"] == "123"
        assert v2_data["meta"]["version"] == "2.0"
```

### Integration Testing

#### Test API Version Compatibility

```python
import pytest
import requests
from typing import Dict, Any

class APIVersionIntegrationTest:
    """Integration tests for API version compatibility"""

    @pytest.fixture(scope="module")
    def v1_client(self):
        """V1 API client fixture"""
        return APIClientV1(base_url="http://localhost:8000/api/v1")

    @pytest.fixture(scope="module")
    def v2_client(self):
        """V2 API client fixture"""
        return APIClientV2(base_url="http://localhost:8000/api/v2")

    def test_both_versions_active(self, v1_client, v2_client):
        """Verify both v1 and v2 are accessible"""
        # v1 endpoint
        v1_response = v1_client.get_resume("123")
        assert v1_response.status_code == 200

        # v2 endpoint
        v2_response = v2_client.get_resume("123")
        assert v2_response.status_code == 200

    def test_v1_backward_compatibility(self, v1_client):
        """Verify v1 maintains backward compatibility"""
        response = v1_client.upload_resume("test.pdf")
        data = response.json()

        # Check v1 required fields exist
        assert "id" in data
        assert "filename" in data

        # Verify response structure hasn't changed
        assert "meta" not in data  # v1 doesn't have meta wrapper

    def test_v2_new_features(self, v2_client):
        """Verify v2 includes new features"""
        response = v2_client.get_resume("123")
        data = response.json()

        # Check v2 structure
        assert "meta" in data
        assert "data" in data
        assert data["meta"]["version"] == "2.0"

    def test_cross_version_data_consistency(self, v1_client, v2_client):
        """Verify data consistency across versions"""
        resume_id = "123"

        # Get same resume from both versions
        v1_data = v1_client.get_resume(resume_id).json()
        v2_data = v2_client.get_resume(resume_id).json()

        # Core data should be consistent
        assert v1_data["id"] == v2_data["data"]["resumeId"]
        assert v1_data["filename"] == v2_data["data"]["fileName"]

    def test_pagination_differences(self, v1_client, v2_client):
        """Test pagination parameter differences"""
        # v1 uses skip/limit
        v1_response = v1_client.list_resumes(skip=0, limit=50)
        v1_data = v1_response.json()

        assert "skip" in v1_data
        assert "limit" in v1_data
        assert "resumes" in v1_data

        # v2 uses page/per_page
        v2_response = v2_client.list_resumes(page=1, per_page=50)
        v2_data = v2_response.json()

        assert "meta" in v2_data
        assert "page" in v2_data["meta"]
        assert "per_page" in v2_data["meta"]
        assert "data" in v2_data
```

### Contract Testing

#### Verify API Contracts

```python
import pytest
import jsonschema

class APIContractTest:
    """Test API contracts using JSON Schema validation"""

    # V1 Response Schema
    V1_RESUME_SCHEMA = {
        "type": "object",
        "required": ["id", "filename", "created_at"],
        "properties": {
            "id": {"type": "string"},
            "filename": {"type": "string"},
            "created_at": {"type": "string", "format": "date-time"},
            "file_size": {"type": "integer"}  # Optional
        },
        "additionalProperties": True
    }

    # V2 Response Schema
    V2_RESUME_SCHEMA = {
        "type": "object",
        "required": ["meta", "data"],
        "properties": {
            "meta": {
                "type": "object",
                "required": ["version", "total", "page"],
                "properties": {
                    "version": {"type": "string"},
                    "total": {"type": "integer"},
                    "page": {"type": "integer"},
                    "per_page": {"type": "integer"}
                }
            },
            "data": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["resumeId", "fileName"],
                    "properties": {
                        "resumeId": {"type": "string"},
                        "fileName": {"type": "string"},
                        "fileSize": {"type": "integer"}
                    }
                }
            }
        }
    }

    def test_v1_response_contract(self):
        """Verify v1 responses match contract"""
        response = requests.get("/api/v1/resumes/123")
        data = response.json()

        # Validate against schema
        jsonschema.validate(instance=data, schema=self.V1_RESUME_SCHEMA)

    def test_v2_response_contract(self):
        """Verify v2 responses match contract"""
        response = requests.get("/api/v2/resumes/123")
        data = response.json()

        # Validate against schema
        jsonschema.validate(instance=data, schema=self.V2_RESUME_SCHEMA)

    def test_contract_backward_compatibility(self):
        """Ensure contract changes don't break existing clients"""
        # Load previous version's contract
        old_contract = load_contract_from_file("v1.0-contract.json")
        new_contract = load_contract_from_file("v1.1-contract.json")

        # Verify no required fields were removed
        for field in old_contract["required"]:
            assert field in new_contract["required"], (
                f"Required field '{field}' was removed in new version"
            )

        # Verify field types haven't changed
        for field, field_type in old_contract["properties"].items():
            new_field_type = new_contract["properties"][field]
            assert new_field_type["type"] == field_type["type"], (
                f"Field '{field}' type changed from {field_type['type']} "
                f"to {new_field_type['type']}"
            )
```

### Migration Testing

#### Test Migration Paths

```python
import pytest

class MigrationTest:
    """Test API migration scenarios"""

    def test_v1_to_v2_authentication_migration(self):
        """Test authentication migration from v1 to v2"""
        # v1 authentication
        v1_client = AgentHRClientV1(api_key="test-key")
        v1_result = v1_client.upload_resume("test.pdf")
        assert v1_result["filename"] == "test.pdf"

        # v2 authentication
        v2_client = AgentHRClientV2(
            client_id="test-client",
            client_secret="test-secret"
        )
        v2_result = v2_client.upload_resume("test.pdf")
        assert v2_result["fileName"] == "test.pdf"

    def test_pagination_parameter_migration(self):
        """Test pagination parameter migration"""
        # Convert v1 params to v2
        skip, limit = 0, 50
        page, per_page = migrate_pagination_params(skip, limit)

        assert page == 1  # (0 // 50) + 1
        assert per_page == 50

        # Verify results match
        v1_results = list_resumes_v1(skip=skip, limit=limit)
        v2_results = list_resumes_v2(page=page, per_page=per_page)

        assert v1_results["total"] == v2_results["total"]

    def test_error_handling_migration(self):
        """Test error format migration"""
        # v1 error format
        with pytest.raises(APIErrorV1) as v1_error:
            make_request_v1("/api/v1/resumes/nonexistent")

        assert "detail" in str(v1_error.value)

        # v2 error format
        with pytest.raises(APIErrorV2) as v2_error:
            make_request_v2("/api/v2/resumes/nonexistent")

        assert v2_error.value.code == "RESUME_NOT_FOUND"
        assert v2_error.value.message is not None
        assert v2_error.value.status_code == 404

    def test_end_to_end_migration(self):
        """Test complete migration workflow"""
        # Old v1 workflow
        v1_client = AgentHRClientV1(api_key="test-key")
        resume = v1_client.upload_resume("test.pdf")
        resume_id = resume["id"]

        # Migrate to v2
        v2_client = AgentHRClientV2(
            client_id="test-client",
            client_secret="test-secret"
        )

        # Same resume accessible in v2
        v2_resume = v2_client.get_resume(resume_id)
        assert v2_resume["resumeId"] == resume_id

        # New v2 features available
        analytics = v2_client.get_resume_analytics(resume_id)
        assert "score" in analytics
```

### Performance Testing

#### Load Test API Versions

```python
import pytest
import locust
from locust import HttpUser, task, between

class APIV1User(HttpUser):
    """Simulate v1 API users"""
    wait_time = between(1, 3)
    host = "http://localhost:8000"

    @task
    def get_resume(self):
        """Test v1 resume retrieval"""
        self.client.get("/api/v1/resumes/123")

    @task(3)
    def list_resumes(self):
        """Test v1 resume listing (higher weight)"""
        self.client.get("/api/v1/resumes/?skip=0&limit=50")

class APIV2User(HttpUser):
    """Simulate v2 API users"""
    wait_time = between(1, 3)
    host = "http://localhost:8000"

    @task
    def get_resume(self):
        """Test v2 resume retrieval"""
        self.client.get("/api/v2/resumes/123")

    @task(3)
    def list_resumes(self):
        """Test v2 resume listing (higher weight)"""
        self.client.get("/api/v2/resumes/?page=1&per_page=50")

# Performance assertions
class PerformanceAssertionTest:
    """Assert performance characteristics"""

    def test_v1_response_time_under_200ms(self):
        """Verify v1 response time is acceptable"""
        import time

        start = time.time()
        response = requests.get("/api/v1/resumes/123")
        duration = (time.time() - start) * 1000  # Convert to ms

        assert response.status_code == 200
        assert duration < 200, f"Response time {duration}ms exceeds 200ms threshold"

    def test_v2_not_slower_than_v1(self):
        """Ensure v2 performance is comparable to v1"""
        import time

        # Measure v1
        start = time.time()
        requests.get("/api/v1/resumes/123")
        v1_duration = (time.time() - start) * 1000

        # Measure v2
        start = time.time()
        requests.get("/api/v2/resumes/123")
        v2_duration = (time.time() - start) * 1000

        # v2 should not be more than 20% slower
        assert v2_duration < v1_duration * 1.2, (
            f"v2 ({v2_duration}ms) is significantly slower than v1 ({v1_duration}ms)"
        )
```

### Regression Testing

#### Prevent Breaking Changes

```python
import pytest

class RegressionTestSuite:
    """Ensure no regressions in API behavior"""

    def test_v1_still_works_after_v2_release(self):
        """Verify v1 continues working after v2 deployment"""
        # This test catches accidental v1 breakage
        response = requests.get(
            "/api/v1/resumes/",
            headers={"X-API-Key": "test-key"}
        )

        assert response.status_code == 200
        data = response.json()

        # Ensure v1 response structure hasn't changed
        assert "resumes" in data
        assert "total" in data

    def test_no_undocumented_breaking_changes(self):
        """Catch breaking changes not documented in migration guide"""
        # Load expected v1 schema
        expected_schema = load_v1_schema()

        # Test actual v1 response
        actual_response = requests.get("/api/v1/resumes/123")
        actual_data = actual_response.json()

        # Compare
        for field in expected_schema["required"]:
            assert field in actual_data, (
                f"Breaking change: required field '{field}' missing from v1 response"
            )

    def test_authentication_not_broken_within_major_version(self):
        """Ensure authentication mechanism stable within v1.x"""
        # Test v1.0 authentication
        v1_0_response = requests.get(
            "/api/v1/resumes/123",
            headers={"X-API-Key": "test-key"}
        )
        assert v1_0_response.status_code == 200

        # Test v1.1 authentication (should still work)
        v1_1_response = requests.get(
            "/api/v1.1/resumes/123",
            headers={"X-API-Key": "test-key"}
        )
        assert v1_1_response.status_code == 200
```

### Test Automation

#### CI/CD Integration

```yaml
# .github/workflows/api-compatibility-test.yml
name: API Compatibility Tests

on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [main, develop]

jobs:
  test-api-compatibility:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt

      - name: Run v1 API tests
        run: |
          pytest tests/api/v1/ -v --tb=short

      - name: Run v2 API tests
        run: |
          pytest tests/api/v2/ -v --tb=short

      - name: Run compatibility tests
        run: |
          pytest tests/api/compatibility/ -v --tb=short

      - name: Run contract tests
        run: |
          pytest tests/api/contracts/ -v --tb=short

      - name: Generate compatibility report
        if: always()
        run: |
          python scripts/generate_compatibility_report.py > compatibility-report.txt

      - name: Upload compatibility report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: compatibility-report
          path: compatibility-report.txt
```

### Pre-Migration Checklist

Use this checklist before deploying API changes:

- [ ] **Unit Tests Pass**: All version-specific unit tests passing
- [ ] **Integration Tests Pass**: Cross-version integration tests passing
- [ ] **Contract Tests Pass**: API contract validation passing
- [ ] **Performance Tests Pass**: Response times within acceptable thresholds
- [ ] **Regression Tests Pass**: No regressions in existing functionality
- [ ] **Documentation Updated**: Migration guide updated with breaking changes
- [ ] **Deprecation Headers Added**: Deprecated endpoints include warning headers
- [ ] **Backward Compatibility Verified**: Old clients still work with new version
- [ ] **Staging Environment Validated**: Changes tested in staging environment
- [ ] **Rollback Plan Prepared**: Plan to revert changes if issues arise
- [ ] **Monitoring Configured**: Alerts set up for error rates and latency
- [ ] **Communication Ready**: Users notified of upcoming changes

### Testing Best Practices

#### 1. Test Real-World Scenarios

```python
def test_real_world_migration_workflow():
    """Test actual user migration scenario"""
    # Setup: User has existing v1 integration
    v1_client = AgentHRClientV1(api_key=production_api_key)

    # User uploads resume in v1
    resume = v1_client.upload_resume("candidate_resume.pdf")
    resume_id = resume["id"]

    # Migration: User updates to v2 client
    v2_client = AgentHRClientV2(
        client_id=production_client_id,
        client_secret=production_client_secret
    )

    # Verify: Same data accessible in v2
    v2_resume = v2_client.get_resume(resume_id)
    assert v2_resume["resumeId"] == resume_id

    # Verify: New v2 features work
    match = v2_client.match_to_vacancy(resume_id, vacancy_id="456")
    assert "score" in match
```

#### 2. Test Edge Cases

```python
def test_edge_cases():
    """Test edge cases and boundary conditions"""

    # Empty responses
    response = requests.get("/api/v1/resumes/?skip=999999&limit=1")
    assert response.json()["resumes"] == []

    # Large data sets
    response = requests.get("/api/v1/resumes/?limit=1000")
    assert len(response.json()["resumes"]) <= 1000

    # Special characters in IDs
    response = requests.get("/api/v1/resumes/test-id-with-special-chars_123")
    # Should handle gracefully

    # Invalid date formats
    response = requests.post(
        "/api/v1/resumes/search",
        json={"date_from": "invalid-date"}
    )
    assert response.status_code == 422  # Validation error
```

#### 3. Test Error Scenarios

```python
def test_error_handling():
    """Test error responses are consistent"""

    # Not found error
    response = requests.get("/api/v1/resumes/nonexistent-id")
    assert response.status_code == 404

    # Authentication error
    response = requests.get(
        "/api/v1/resumes/123",
        headers={"X-API-Key": "invalid-key"}
    )
    assert response.status_code == 401

    # Validation error
    response = requests.post(
        "/api/v1/resumes/upload",
        json={}  # Missing required fields
    )
    assert response.status_code == 422
```

---

## Migration Examples

### Overview of Changes: v1 → v2

| Area | v1 Approach | v2 Approach | Migration Effort |
|------|-------------|-------------|------------------|
| **Authentication** | API Key (X-API-Key header) | OAuth2 Bearer Token | High - All requests need update |
| **Error Format** | Simple string with "detail" key | Structured error object with code, message, details | Medium - Error parsing needs update |
| **Pagination** | skip/limit parameters with inline pagination | page/per_page with meta wrapper | Medium - Request and response handling changes |
| **Date Format** | ISO 8601 with milliseconds | ISO 8601 without milliseconds | Low - Date parsing adjustments |
| **Response Structure** | Flat structure with direct data access | Nested structure with meta/data wrapper | Medium - Response parsing changes |

### Migration Templates

#### Template 1: Authentication Migration

**Use Case:** Migrating from API Key authentication to OAuth2 Bearer tokens.

**v1 Code (Before Migration):**
```python
import requests
from typing import Dict, Any

class AgentHRClientV1:
    """AgentHR API v1 client using API Key authentication."""

    def __init__(self, api_key: str, base_url: str = "http://localhost:8000"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()

    def _get_headers(self) -> Dict[str, str]:
        """Prepare headers with API key."""
        return {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "Accept-Language": "en"
        }

    def upload_resume(self, file_path: str) -> Dict[str, Any]:
        """Upload a resume file."""
        url = f"{self.base_url}/api/v1/resumes/upload"
        headers = self._get_headers()

        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = self.session.post(url, headers=headers, files=files)

        response.raise_for_status()
        return response.json()

    def get_resume(self, resume_id: str) -> Dict[str, Any]:
        """Get resume by ID."""
        url = f"{self.base_url}/api/v1/resumes/{resume_id}"
        headers = self._get_headers()

        response = self.session.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

# Usage
client = AgentHRClientV1(api_key="your-api-key")
result = client.upload_resume("resume.pdf")
```

**v2 Code (After Migration):**
```python
import requests
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

class AgentHRClientV2:
    """AgentHR API v2 client using OAuth2 Bearer token authentication."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        base_url: str = "http://localhost:8000"
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url
        self.session = requests.Session()
        self._access_token: Optional[str] = None
        self._token_expires: Optional[datetime] = None

    def _get_access_token(self) -> str:
        """Get OAuth2 access token, refreshing if necessary."""
        # Check if token is still valid
        if self._access_token and self._token_expires:
            if datetime.now() < self._token_expires:
                return self._access_token

        # Obtain new token
        url = f"{self.base_url}/oauth2/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }

        response = self.session.post(url, data=data)
        response.raise_for_status()
        token_data = response.json()

        # Store token and expiration
        self._access_token = token_data["access_token"]
        expires_in = token_data.get("expires_in", 3600)
        self._token_expires = datetime.now() + timedelta(seconds=expires_in - 60)

        return self._access_token

    def _get_headers(self) -> Dict[str, str]:
        """Prepare headers with OAuth2 Bearer token."""
        return {
            "Authorization": f"Bearer {self._get_access_token()}",
            "Content-Type": "application/json",
            "Accept-Language": "en"
        }

    def upload_resume(self, file_path: str) -> Dict[str, Any]:
        """Upload a resume file."""
        url = f"{self.base_url}/api/v2/resumes/upload"
        headers = self._get_headers()

        with open(file_path, 'rb') as f:
            files = {'file': f}
            # Remove Content-Type for file uploads
            headers.pop("Content-Type", None)
            response = self.session.post(url, headers=headers, files=files)

        # Handle v2 error format
        if response.status_code >= 400:
            error = response.json()["error"]
            raise Exception(f"{error['code']}: {error['message']}")

        return response.json()

    def get_resume(self, resume_id: str) -> Dict[str, Any]:
        """Get resume by ID."""
        url = f"{self.base_url}/api/v2/resumes/{resume_id}"
        headers = self._get_headers()

        response = self.session.get(url, headers=headers)

        # Handle v2 error format
        if response.status_code >= 400:
            error = response.json()["error"]
            raise Exception(f"{error['code']}: {error['message']}")

        return response.json()

# Usage
client = AgentHRClientV2(
    client_id="your-client-id",
    client_secret="your-client-secret"
)
result = client.upload_resume("resume.pdf")
```

**Migration Steps:**
1. Update client initialization to use OAuth2 credentials
2. Implement token management logic (storage, refresh)
3. Replace `X-API-Key` header with `Authorization: Bearer {token}`
4. Update error handling to parse new error format
5. Test authentication flow thoroughly

---

#### Template 2: Pagination Migration

**Use Case:** Migrating from skip/limit pagination to page/per_page with meta wrapper.

**v1 Code (Before Migration):**
```python
def list_resumes_v1(skip: int = 0, limit: int = 50) -> Dict[str, Any]:
    """List resumes with v1 pagination."""
    url = "http://localhost:8000/api/v1/resumes/"
    headers = {"X-API-Key": "your-api-key"}

    params = {
        "skip": skip,
        "limit": limit
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    data = response.json()

    return {
        "total": data["total"],
        "resumes": data["resumes"],
        "skip": data["skip"],
        "limit": data["limit"]
    }

# Usage with pagination
def get_all_resumes_v1():
    """Fetch all resumes using v1 pagination."""
    all_resumes = []
    skip = 0
    limit = 50

    while True:
        result = list_resumes_v1(skip=skip, limit=limit)
        all_resumes.extend(result["resumes"])

        # Check if we've fetched all resumes
        if len(all_resumes) >= result["total"]:
            break

        skip += limit

    return all_resumes
```

**v2 Code (After Migration):**
```python
from typing import List, Dict, Any

def list_resumes_v2(page: int = 1, per_page: int = 50) -> Dict[str, Any]:
    """List resumes with v2 pagination."""
    url = "http://localhost:8000/api/v2/resumes/"
    headers = {"Authorization": f"Bearer {get_oauth_token()}"}

    params = {
        "page": page,
        "per_page": per_page
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    data = response.json()

    return {
        "total": data["meta"]["total"],
        "page": data["meta"]["page"],
        "per_page": data["meta"]["per_page"],
        "total_pages": data["meta"]["total_pages"],
        "resumes": data["data"]
    }

# Usage with pagination
def get_all_resumes_v2():
    """Fetch all resumes using v2 pagination."""
    all_resumes: List[Dict[str, Any]] = []
    page = 1
    per_page = 50

    while True:
        result = list_resumes_v2(page=page, per_page=per_page)
        all_resumes.extend(result["resumes"])

        # Check if we've fetched all pages
        if page >= result["total_pages"]:
            break

        page += 1

    return all_resumes

# Additional utility: Convert v1 params to v2 params
def migrate_pagination_params(skip: int, limit: int) -> tuple:
    """
    Convert v1 pagination parameters to v2 format.

    Args:
        skip: Number of items to skip (v1)
        limit: Number of items per page (v1)

    Returns:
        Tuple of (page, per_page) for v2
    """
    page = (skip // limit) + 1
    per_page = limit
    return page, per_page
```

**Migration Steps:**
1. Replace `skip` parameter with `page` (calculated as `skip / limit + 1`)
2. Replace `limit` parameter with `per_page`
3. Update response parsing to use `meta` wrapper
4. Extract data from `data` array instead of direct field access
5. Update pagination loops to use `total_pages` instead of comparing count to total

---

#### Template 3: Error Handling Migration

**Use Case:** Migrating from simple error format to structured error objects.

**v1 Code (Before Migration):**
```python
import requests
from typing import Optional

class APIErrorV1(Exception):
    """API v1 error with simple message."""
    pass

def make_request_v1(url: str, **kwargs) -> dict:
    """Make API request with v1 error handling."""
    response = requests.get(url, **kwargs)

    if response.status_code >= 400:
        error_detail = response.json().get("detail", "Unknown error")
        raise APIErrorV1(f"API Error ({response.status_code}): {error_detail}")

    return response.json()

# Usage
try:
    result = make_request_v1(
        "http://localhost:8000/api/v1/resumes/123",
        headers={"X-API-Key": "your-api-key"}
    )
except APIErrorV1 as e:
    print(f"Error occurred: {e}")
    # Log and handle error
```

**v2 Code (After Migration):**
```python
import requests
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class APIErrorV2(Exception):
    """API v2 error with structured information."""
    code: str
    message: str
    status_code: int
    details: Optional[Dict[str, Any]] = None
    suggestion: Optional[str] = None

    def __str__(self):
        msg = f"API Error ({self.status_code}): [{self.code}] {self.message}"
        if self.suggestion:
            msg += f"\nSuggestion: {self.suggestion}"
        return msg

def make_request_v2(url: str, **kwargs) -> dict:
    """Make API request with v2 error handling."""
    response = requests.get(url, **kwargs)

    if response.status_code >= 400:
        error_data = response.json()["error"]

        # Extract suggestion from details if available
        suggestion = None
        if error_data.get("details") and "suggestion" in error_data["details"]:
            suggestion = error_data["details"]["suggestion"]

        raise APIErrorV2(
            code=error_data["code"],
            message=error_data["message"],
            status_code=response.status_code,
            details=error_data.get("details"),
            suggestion=suggestion
        )

    return response.json()

# Usage
try:
    result = make_request_v2(
        "http://localhost:8000/api/v2/resumes/123",
        headers={"Authorization": f"Bearer {get_oauth_token()}"}
    )
except APIErrorV2 as e:
    print(f"Error occurred: {e}")
    print(f"Error code: {e.code}")

    # Handle specific error codes
    if e.code == "RESUME_NOT_FOUND":
        print(f"Suggested action: {e.suggestion}")
        # Resume not found - handle gracefully
    elif e.code == "AUTHENTICATION_FAILED":
        # Re-authenticate
        refresh_token()
    else:
        # Generic error handling
        log_error(e)
```

**Common v2 Error Codes:**

| Error Code | Description | Suggested Action |
|------------|-------------|------------------|
| `RESUME_NOT_FOUND` | Resume ID doesn't exist | Verify ID or list available resumes |
| `AUTHENTICATION_FAILED` | Invalid or expired token | Refresh OAuth2 token |
| `INVALID_FILE_FORMAT` | Uploaded file not supported | Use PDF or DOCX format |
| `FILE_TOO_LARGE` | File exceeds size limit | Compress file or split into smaller files |
| `RATE_LIMIT_EXCEEDED` | Too many requests | Implement backoff/retry logic |
| `VALIDATION_ERROR` | Request validation failed | Check request payload format |

---

#### Template 4: Complete API Client Migration

**Use Case:** Migrating a complete API client class from v1 to v2.

**v1 Client (Before Migration):**
```python
import requests
from typing import Dict, Any, List, Optional

class AgentHRClient:
    """AgentHR API v1 client."""

    def __init__(self, api_key: str, base_url: str = "http://localhost:8000"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make API request."""
        url = f"{self.base_url}/api/v1{endpoint}"
        headers = kwargs.pop("headers", {})
        headers["X-API-Key"] = self.api_key

        response = self.session.request(method, url, headers=headers, **kwargs)

        if response.status_code >= 400:
            error_detail = response.json().get("detail", "Unknown error")
            raise Exception(f"API Error: {error_detail}")

        return response.json()

    def upload_resume(self, file_path: str) -> Dict[str, Any]:
        """Upload resume."""
        url = "/resumes/upload"
        with open(file_path, 'rb') as f:
            files = {'file': f}
            return self._request("POST", url, files=files)

    def list_resumes(self, skip: int = 0, limit: int = 50) -> Dict[str, Any]:
        """List all resumes."""
        return self._request("GET", "/resumes/", params={"skip": skip, "limit": limit})

    def get_resume(self, resume_id: str) -> Dict[str, Any]:
        """Get resume by ID."""
        return self._request("GET", f"/resumes/{resume_id}")

    def search_candidates(
        self,
        query: str,
        filters: Optional[Dict] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Search candidates."""
        payload = {
            "query": query,
            "filters": filters or {},
            "skip": skip,
            "limit": limit
        }
        return self._request("POST", "/search/candidates", json=payload)

    def match_resume_to_vacancy(
        self,
        resume_id: str,
        vacancy_id: str
    ) -> Dict[str, Any]:
        """Match resume to vacancy."""
        payload = {
            "resume_id": resume_id,
            "vacancy_id": vacancy_id
        }
        return self._request("POST", "/matching/compare", json=payload)
```

**v2 Client (After Migration):**
```python
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

@dataclass
class APIError(Exception):
    """Structured API error."""
    code: str
    message: str
    status_code: int
    details: Optional[Dict[str, Any]] = None
    suggestion: Optional[str] = None

    def __str__(self):
        msg = f"[{self.code}] {self.message}"
        if self.suggestion:
            msg += f"\n💡 Suggestion: {self.suggestion}"
        return msg

class AgentHRClientV2:
    """AgentHR API v2 client with OAuth2 and enhanced features."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        base_url: str = "http://localhost:8000",
        auto_refresh_token: bool = True
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url
        self.auto_refresh_token = auto_refresh_token
        self.session = requests.Session()
        self._access_token: Optional[str] = None
        self._token_expires: Optional[datetime] = None

    def _get_token(self) -> str:
        """Get OAuth2 access token with auto-refresh."""
        if self._access_token and self._token_expires:
            if datetime.now() < self._token_expires:
                return self._access_token

        # Obtain new token
        url = f"{self.base_url}/oauth2/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }

        response = self.session.post(url, data=data)
        if response.status_code >= 400:
            raise APIError(
                code="AUTH_FAILED",
                message="Failed to obtain OAuth2 token",
                status_code=response.status_code
            )

        token_data = response.json()
        self._access_token = token_data["access_token"]
        expires_in = token_data.get("expires_in", 3600)
        self._token_expires = datetime.now() + timedelta(seconds=expires_in - 60)

        return self._access_token

    def _request(
        self,
        method: str,
        endpoint: str,
        handle_errors: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """Make API request with v2 error handling."""
        url = f"{self.base_url}/api/v2{endpoint}"
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self._get_token()}"

        response = self.session.request(method, url, headers=headers, **kwargs)

        if handle_errors and response.status_code >= 400:
            error_data = response.json().get("error", {})
            suggestion = None
            if error_data.get("details") and "suggestion" in error_data["details"]:
                suggestion = error_data["details"]["suggestion"]

            raise APIError(
                code=error_data.get("code", "UNKNOWN_ERROR"),
                message=error_data.get("message", "Unknown error"),
                status_code=response.status_code,
                details=error_data.get("details"),
                suggestion=suggestion
            )

        return response.json()

    def upload_resume(self, file_path: str) -> Dict[str, Any]:
        """Upload resume with enhanced validation."""
        with open(file_path, 'rb') as f:
            files = {'file': f}
            return self._request("POST", "/resumes/upload", files=files)

    def list_resumes(
        self,
        page: int = 1,
        per_page: int = 50
    ) -> Dict[str, Any]:
        """List resumes with v2 pagination."""
        return self._request(
            "GET",
            "/resumes/",
            params={"page": page, "per_page": per_page}
        )

    def get_all_resumes(self) -> List[Dict[str, Any]]:
        """Fetch all resumes with automatic pagination."""
        all_resumes = []
        page = 1

        while True:
            result = self.list_resumes(page=page, per_page=50)
            all_resumes.extend(result["data"])

            if page >= result["meta"]["total_pages"]:
                break

            page += 1

        return all_resumes

    def get_resume(self, resume_id: str) -> Dict[str, Any]:
        """Get resume by ID with metadata."""
        return self._request("GET", f"/resumes/{resume_id}")

    def search_candidates(
        self,
        query: str,
        filters: Optional[Dict] = None,
        page: int = 1,
        per_page: int = 50
    ) -> Dict[str, Any]:
        """Search candidates with v2 parameters."""
        payload = {
            "query": query,
            "filters": filters or {},
            "page": page,
            "per_page": per_page
        }
        return self._request("POST", "/search/candidates", json=payload)

    def match_resume_to_vacancy(
        self,
        resume_id: str,
        vacancy_id: str
    ) -> Dict[str, Any]:
        """Match resume to vacancy with enhanced scoring."""
        payload = {
            "resumeId": resume_id,  # Note: camelCase in v2
            "vacancyId": vacancy_id
        }
        return self._request("POST", "/matching/compare", json=payload)

    # Helper method for migration
    @classmethod
    def from_v1_credentials(cls, api_key: str) -> "AgentHRClientV2":
        """
        Create v2 client from v1 credentials (temporary migration helper).

        Note: This is a bridge method. Migrate to OAuth2 credentials ASAP.
        """
        # In production, exchange API key for OAuth2 credentials
        # This is a simplified example
        return cls(
            client_id="migrated_from_api_key",
            client_secret=api_key  # Temporary: use API exchange endpoint
        )
```

**Migration Checklist:**
- [ ] Update client initialization with OAuth2 credentials
- [ ] Implement token management and auto-refresh
- [ ] Replace `X-API-Key` with `Authorization: Bearer` header
- [ ] Update pagination parameters (skip/limit → page/per_page)
- [ ] Update response parsing (meta/data wrapper)
- [ ] Implement structured error handling
- [ ] Update field names (snake_case → camelCase if applicable)
- [ ] Test all endpoints in staging environment
- [ ] Update unit tests and integration tests
- [ ] Monitor error rates post-migration

---

### Quick Reference: v1 → v2 Changes

**Authentication:**
```python
# v1
"X-API-Key": "your-api-key"

# v2
"Authorization": f"Bearer {access_token}"
```

**Pagination:**
```python
# v1
params = {"skip": 0, "limit": 50}
response = {"total": 100, "resumes": [...], "skip": 0, "limit": 50}

# v2
params = {"page": 1, "per_page": 50}
response = {"meta": {"total": 100, "page": 1, ...}, "data": [...]}
```

**Error Format:**
```python
# v1
{"detail": "Resume not found"}

# v2
{
  "error": {
    "code": "RESUME_NOT_FOUND",
    "message": "Resume not found",
    "details": {"resume_id": "123", "suggestion": "Check the ID"}
  }
}
```

**Date Format:**
```python
# v1
"created_at": "2026-01-15T10:30:00.123Z"  # With milliseconds

# v2
"created_at": "2026-01-15T10:30:00Z"  # Without milliseconds
```

---

## Best Practices

### 1. Always Specify API Version

**❌ Bad:**
```python
# Relies on default version (risky)
url = "http://localhost:8000/api/resumes/"
```

**✅ Good:**
```python
# Explicit version
url = "http://localhost:8000/api/v1/resumes/"
```

### 2. Handle Version-Specific Responses

```python
def get_resume(resume_id, api_version="v1"):
    url = f"http://localhost:8000/api/{api_version}/resumes/{resume_id}"
    response = requests.get(url)

    data = response.json()

    # Handle version-specific response format
    if api_version == "v1":
        return process_v1_response(data)
    elif api_version == "v2":
        return process_v2_response(data)
```

### 3. Monitor Deprecation Headers

```python
def check_deprecation(response):
    deprecated = response.headers.get("X-API-Deprecated", "false").lower()
    if deprecated == "true":
        sunset = response.headers.get("X-API-Sunset")
        recommended = response.headers.get("X-API-Recommended-Version")
        logger.warning(
            f"API version deprecated! Sunset: {sunset}, "
            f"Upgrade to: {recommended}"
        )
```

### 4. Graceful Degradation

```python
def upload_resume_with_fallback(file_path):
    try:
        # Try v2 first
        return upload_resume_v2(file_path)
    except AuthenticationError:
        # Fall back to v1 if v2 auth fails
        logger.warning("v2 authentication failed, trying v1")
        return upload_resume_v1(file_path)
```

### 5. Version-Specific Tests

```python
# tests/test_api_v1.py
def test_v1_resume_upload():
    response = upload_resume_v1("test.pdf")
    assert response["filename"] == "test.pdf"

# tests/test_api_v2.py
def test_v2_resume_upload():
    response = upload_resume_v2("test.pdf")
    assert response["filename"] == "test.pdf"
    assert response["meta"]["version"] == "2.0"
```

---

## Checking Your Current Version

### Method 1: Check Response Headers

```bash
curl -I http://localhost:8000/api/v1/resumes/

# Response includes:
X-API-Version: 1.0.0
```

### Method 2: Version Endpoint

```bash
curl http://localhost:8000/api/v1/version

# Response:
{
  "version": "1.0.0",
  "status": "stable",
  "release_date": "2026-01-15",
  "documentation": "/docs/api/v1"
}
```

### Method 3: OpenAPI Documentation

```bash
curl http://localhost:8000/openapi.json | jq '.info.version'
```

---

## Quick Reference

### Common Migration Tasks

| Task | Command/Action | Documentation |
|------|----------------|---------------|
| **Check current API version** | `curl http://localhost:8000/api/v1/version` | [Version Check](#checking-your-current-version) |
| **Upload resume (v1)** | `POST /api/v1/resumes/upload` | [API Reference](./API_REFERENCE.md#resumes) |
| **Upload resume (v2)** | `POST /api/v2/resumes/upload` | [API Reference](./API_REFERENCE.md#resumes) |
| **Analyze resume** | `POST /api/v1/resumes/analyze` | [API Reference](./API_REFERENCE.md#resume-analysis) |
| **Match candidate** | `POST /api/v1/matching/compare` | [API Reference](./API_REFERENCE.md#job-matching) |
| **Search candidates** | `POST /api/v1/search/candidates` | [API Reference](./API_REFERENCE.md#search) |

### Versioning Methods

| Method | Example | Status |
|--------|---------|--------|
| **URL Path** | `/api/v1/resumes/` | ✅ Primary (Recommended) |
| **Header** | `X-API-Version: 1.0` | ✅ Supported |
| **Content Negotiation** | `Accept: application/vnd.agenthr.v1+json` | ✅ Supported |

### Quick Links to Documentation

- **[API Reference](./API_REFERENCE.md)** - Complete API endpoint documentation
- **[Changelog](#changelog)** - Version history and changes
- **[OpenAPI/Swagger](http://localhost:8000/docs)** - Interactive API documentation
- **[Breaking Changes](#breaking-changes)** - List of breaking changes by version
- **[Migration Path](#migration-path)** - Step-by-step migration guide
- **[Best Practices](#best-practices)** - Recommended development patterns

### Version Status

| Version | Status | Release Date | Deprecated | Sunset Date |
|---------|--------|--------------|------------|-------------|
| **1.0.0** | ✅ Stable | 2026-01-15 | - | - |
| **1.1.0** | 🚧 Planned | Q2 2026 | - | - |
| **2.0.0** | 🚧 In Development | Q4 2026 | - | - |

### Migration Checklist

When migrating between API versions:

- [ ] Review [Breaking Changes](#breaking-changes)
- [ ] Update API base URL to new version
- [ ] Update request/response handlers for changed fields
- [ ] Test with [version-specific tests](#testing-and-validation)
- [ ] Update authentication headers if required
- [ ] Verify webhook compatibility
- [ ] Monitor [deprecation timeline](#deprecation-policy)

### Client Library Support

| Language/Library | v1.0 Support | v2.0 Support | Documentation |
|------------------|--------------|--------------|---------------|
| Python (requests) | ✅ | 🚧 Planned | [Migration Examples](#migration-examples) |
| JavaScript (axios) | ✅ | 🚧 Planned | [Migration Examples](#migration-examples) |
| cURL | ✅ | ✅ | [Migration Examples](#migration-examples) |

### Support Resources

| Resource Type | Link | Description |
|---------------|------|-------------|
| **Interactive Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) | Swagger UI with live testing |
| **ReDoc** | [http://localhost:8000/redoc](http://localhost:8000/redoc) | Alternative documentation view |
| **OpenAPI Spec** | [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json) | Machine-readable API spec |
| **Email Support** | [support@agenthr.com](mailto:support@agenthr.com) | Direct email support |
| **Issue Tracker** | Project Repository | Bug reports and feature requests |

### Common Error Codes

| HTTP Code | Error | Description | Action |
|-----------|-------|-------------|--------|
| **400** | Bad Request | Invalid version specified | Check API version header/URL |
| **404** | Not Found | Endpoint not available in version | Verify endpoint exists in version |
| **410** | Gone | API version deprecated | Migrate to newer version |
| **422** | Validation Error | Schema changed in new version | Update request body format |

---

## Getting Help

### Resources

- **API Reference:** [API_REFERENCE.md](./API_REFERENCE.md)
- **Interactive Docs:** `http://localhost:8000/docs`
- **OpenAPI Spec:** `http://localhost:8000/openapi.json`
- **Migration Support:** support@agenthr.com

### Support Channels

- **Documentation:** See [API_REFERENCE.md](./API_REFERENCE.md)
- **Email:** support@agenthr.com
- **Issues:** Create issue in project repository
- **Community:** Join our Slack channel

---

## Changelog

### v1.0.0 (2026-01-15)
- ✅ Initial stable release
- ✅ Resume upload and analysis endpoints
- ✅ Job matching with skill synonyms
- ✅ Candidate workflow management
- ✅ Advanced search with boolean queries
- ✅ Report generation
- ✅ ML model versioning

### v1.1.0 (Planned - Q2 2026)
- 🚧 Webhook notifications
- 🚧 Enhanced filtering options
- 🚧 Performance optimizations

### v2.0.0 (Planned - Q4 2026)
- 🚧 OAuth2 authentication
- 🚧 GraphQL support
- 🚧 Breaking changes (see [Breaking Changes](#breaking-changes))

---

**Document Version:** 1.0.0
**Last Updated:** 2026-02-04
**Current API Version:** 1.0.0
**Next API Version:** 2.0.0 (In Development)
