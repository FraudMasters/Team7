# GDPR Data Mapping and PII Inventory

**Version:** 1.0
**Last Updated:** 2026-02-03
**Purpose:** Complete inventory of personal data processing, data flow, and PII storage locations

---

## Table of Contents

1. [Data Flow Overview](#data-flow-overview)
2. [PII Data Inventory](#pii-data-inventory)
3. [Database Schema and PII Storage](#database-schema-and-pii-storage)
4. [Data Lifecycle](#data-lifecycle)
5. [Data Processing Purposes](#data-processing-purposes)
6. [Data Sharing and Transfers](#data-sharing-and-transfers)
7. [Retention and Deletion](#retention-and-deletion)
8. [Third-Party Data Processors](#third-party-data-processors)

---

## Data Flow Overview

### Candidate Data Entry Flow

```
┌─────────────────┐
│ Resume Upload   │
│ (PDF/DOCX)      │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ File Storage (Encrypted at Rest)        │
│ - Original resume file                  │
│ - AES-256 encryption                    │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ NLP/ML Processing                       │
│ - Text extraction                       │
│ - PII identification                    │
│ - Entity recognition (NER)              │
│ - Skill extraction                      │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ Database Storage (PostgreSQL)           │
│ - Resumes table (metadata)              │
│ - ParsedResume (structured data)        │
│ - HiringStage (pipeline history)        │
│ - ConsentRecord (GDPR compliance)       │
└─────────────────────────────────────────┘
```

### Data Access Flow

```
┌─────────────────┐    ┌─────────────────┐
│ Recruiters      │    │  Candidates     │
│ (Org Members)   │    │  (Data Owners)  │
└────────┬────────┘    └────────┬────────┘
         │                      │
         │ Auth & AuthZ         │ Auth & AuthZ
         ▼                      ▼
┌─────────────────────────────────────────┐
│ API Gateway (JWT Authentication)        │
│ - TLS 1.2+ encryption in transit        │
│ - Role-based access control (RBAC)      │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ Business Logic Layer                    │
│ - Consent validation                    │
│ - Data filtering (org-scoped)           │
│ - Purpose checking                      │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ Data Access Layer                       │
│ - SQLAlchemy ORM                        │
│ - Query filtering                       │
│ - Audit logging                         │
└─────────────────────────────────────────┘
```

---

## PII Data Inventory

### Personal Data Categories

#### 1. Contact Information ✅

| Data Field | Source | Storage Location | Retention | Legal Basis |
|------------|--------|------------------|-----------|-------------|
| Email Address | Resume extraction | `ParsedResume.email` | 2 years | Consent (data_processing) |
| Phone Number | Resume extraction | `ParsedResume.phone` | 2 years | Consent (data_processing) |
| Physical Address | Resume extraction | `ParsedResume.location` | 2 years | Consent (data_processing) |
| Links/URLs | Resume extraction | `ParsedResume.links` | 2 years | Consent (data_processing) |

**Table:** `parsed_resumes` (JSON column)
**Access:** Recruiter access within organization
**Encryption:** Encrypted at rest (AES-256), in transit (TLS 1.2+)

---

#### 2. Professional Information ✅

| Data Field | Source | Storage Location | Retention | Legal Basis |
|------------|--------|------------------|-----------|-------------|
| Current Position | Resume extraction | `ParsedResume.position` | 2 years | Consent (data_processing) |
| Work History | Resume extraction | `ParsedResume.work_experience` | 2 years | Consent (data_processing) |
| Education History | Resume extraction | `ParsedResume.education` | 2 years | Consent (data_processing) |
| Skills | Resume extraction + AI analysis | `ParsedResume.skills` | 2 years | Consent (ai_analysis) |
| Languages | Resume extraction | `ParsedResume.languages` | 2 years | Consent (data_processing) |
| Experience Summary | Calculated | `ParsedResume.experience_summary` | 2 years | Consent (data_processing) |

**Table:** `parsed_resumes` (JSON column)
**Processing:** AI-powered skill extraction and matching
**Purpose:** Recruitment and talent acquisition

---

#### 3. Identification Information ✅

| Data Field | Source | Storage Location | Retention | Legal Basis |
|------------|--------|------------------|-----------|-------------|
| Full Name | Resume extraction | `ParsedResume.name` | 2 years | Consent (data_processing) |
| Age | Resume extraction (if provided) | `ParsedResume.age` | 2 years | Consent (data_processing) |
| Resume Filename | User upload | `Resume.filename` | 1 year | Consent (data_storage) |

**Note:** Age is only stored if explicitly mentioned in resume. Not actively collected.

---

#### 4. Recruitment Pipeline Data ✅

| Data Field | Source | Storage Location | Retention | Legal Basis |
|------------|--------|------------------|-----------|-------------|
| Hiring Stage | Recruiter action | `HiringStage.stage_name` | 2 years | Consent (profile_creation) |
| Stage Notes | Recruiter input | `CandidateNote.content` | 2 years | Consent (profile_creation) |
| Tags | Recruiter assigned | `CandidateTag.tag_name` | 2 years | Consent (profile_creation) |
| Activities | System actions | `CandidateActivity.activity_type` | 3 months | Consent (analytics) |
| Feedback | Recruiter input | `CandidateFeedback.content` | 2 years | Consent (profile_creation) |

**Tables:** `hiring_stages`, `candidate_notes`, `candidate_tags`, `candidate_activities`, `candidate_feedback`

---

#### 5. Consent Records ✅

| Data Field | Source | Storage Location | Retention | Legal Basis |
|------------|--------|------------------|-----------|-------------|
| Consent Type | User action | `ConsentRecord.consent_type` | 7 years | Legal requirement |
| Granted/Withdrawn | User action | `ConsentRecord.granted` | 7 years | Legal requirement |
| Consent Text | System | `ConsentRecord.consent_text` | 7 years | Legal requirement |
| Consent Version | System | `ConsentRecord.consent_version` | 7 years | Legal requirement |
| IP Address | System capture | `ConsentRecord.ip_address` | 7 years | Legal requirement |
| User Agent | System capture | `ConsentRecord.user_agent` | 7 years | Legal requirement |
| Withdrawal Timestamp | User action | `ConsentRecord.withdrawn_at` | 7 years | Legal requirement |

**Table:** `consent_records`
**Retention:** 7 years (legal requirement for audit trail)

---

#### 6. Cookie Consent Data ✅

| Data Field | Source | Storage Location | Retention | Legal Basis |
|------------|--------|------------------|-----------|-------------|
| Essential Cookies | System default | `CookieConsent.essential` | Session | Legal necessity |
| Functional Cookies | User choice | `CookieConsent.functional` | 1 year | Consent |
| Analytics Cookies | User choice | `CookieConsent.analytics` | 1 year | Consent |
| Marketing Cookies | User choice | `CookieConsent.marketing` | 1 year | Consent |

**Table:** `cookie_consent`
**Storage:** Browser localStorage + backend database

---

#### 7. Metadata and Technical Data ✅

| Data Field | Source | Storage Location | Retention | Legal Basis |
|------------|--------|------------------|-----------|-------------|
| Upload Timestamp | System | `Resume.created_at` | 1 year | Consent (data_storage) |
| Processing Status | System | `Resume.status` | 1 year | Consent (data_storage) |
| Language Detection | System | `Resume.language` | 1 year | Consent (data_storage) |
| User ID | System | `Resume.user_id` | 1 year | Legal necessity |
| Organization ID | System | `Resume.organization_id` | 1 year | Legal necessity |

---

## Database Schema and PII Storage

### Primary PII Tables

#### 1. resumes

**Purpose:** Store resume file metadata
**PII Fields:** None directly (filename only)
**Relationships:** One-to-many with parsed_resumes, hiring_stages

```sql
CREATE TABLE resumes (
    id UUID PRIMARY KEY,
    filename VARCHAR(255),              -- Original filename (no PII)
    file_path VARCHAR(512),             -- Encrypted file storage path
    content_type VARCHAR(100),          -- MIME type
    status VARCHAR(50),                 -- Processing status
    raw_text TEXT,                      -- Extracted text (may contain PII)
    language VARCHAR(10),               -- Detected language
    error_message TEXT,                 -- Processing errors
    user_id UUID REFERENCES users(id),  -- Owner
    organization_id UUID,               -- Organization scope
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**Indexes:**
- `user_id` - Fast user data lookup
- `organization_id` - Organization data filtering
- `status` - Processing pipeline queries
- `created_at` - Retention policy queries

---

#### 2. parsed_resumes

**Purpose:** Structured data extracted from resumes
**PII Fields:** **ALL FIELDS ARE PII**
**Storage:** JSON column containing structured personal data

```sql
CREATE TABLE parsed_resumes (
    id UUID PRIMARY KEY,
    resume_id UUID REFERENCES resumes(id) ON DELETE CASCADE,
    parsed_data JSONB NOT NULL,         -- Complete PII structure
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**JSON Structure (parsed_data field):**
```json
{
  "raw_text": "...",                    // May contain PII
  "language": "en",
  "position": "Senior Developer",
  "age": 35,                            // If provided
  "name": "John Smith",                 // PII
  "email": "john@example.com",          // PII
  "phone": "+1-234-567-8900",           // PII
  "location": "San Francisco, CA",      // PII
  "links": ["linkedin.com/in/john"],    // PII
  "skills": [...],                      // Professional data
  "education": [...],                   // Professional data
  "work_experience": [...],             // Professional data
  "languages": [...],                   // Professional data
  "experience_summary": {...}
}
```

**Privacy Note:** This is the primary PII storage table. All data deletion requests must cascade to this table.

---

#### 3. hiring_stages

**Purpose:** Track candidate progress through recruitment pipeline
**PII Fields:** Indirect (via resume_id foreign key)

```sql
CREATE TABLE hiring_stages (
    id UUID PRIMARY KEY,
    resume_id UUID REFERENCES resumes(id) ON DELETE CASCADE,
    vacancy_id UUID REFERENCES job_vacancies(id),
    stage_name VARCHAR(100),            // Pipeline stage
    notes TEXT,                         // Recruiter notes (may contain PII)
    user_id UUID REFERENCES users(id),  // Recruiter who created
    organization_id UUID,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**Cascade Deletion:** When resume is deleted, all hiring stages are deleted.

---

#### 4. candidate_notes

**Purpose:** Recruiter notes about candidates
**PII Fields:** `content` (may contain PII about candidate)

```sql
CREATE TABLE candidate_notes (
    id UUID PRIMARY KEY,
    resume_id UUID REFERENCES resumes(id) ON DELETE CASCADE,
    content TEXT,                       // Recruiter notes (may contain PII)
    note_type VARCHAR(50),
    user_id UUID REFERENCES users(id),  // Note creator
    organization_id UUID,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**Privacy Note:** Notes are manually created by recruiters and may contain subjective assessments.

---

#### 5. candidate_tags

**Purpose:** Organizational labels for candidates
**PII Fields:** None directly (tags are organizational metadata)

```sql
CREATE TABLE candidate_tags (
    id UUID PRIMARY KEY,
    tag_id UUID REFERENCES tags(id) ON DELETE CASCADE,
    resume_id UUID REFERENCES resumes(id) ON DELETE CASCADE,
    organization_id UUID,
    created_at TIMESTAMP
);
```

**Cascade Deletion:** Tags removed when resume is deleted.

---

#### 6. consent_records

**Purpose:** GDPR compliance - consent tracking
**PII Fields:** `ip_address`, `user_agent` (technical identifiers)

```sql
CREATE TABLE consent_records (
    id UUID PRIMARY KEY,
    consent_type VARCHAR(50) NOT NULL,  // Type of consent
    granted BOOLEAN NOT NULL,           // True = consented
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID,
    consent_text TEXT,                  // Legal text shown
    consent_version VARCHAR(20),        // Policy version
    ip_address VARCHAR(45),             // Technical identifier
    user_agent TEXT,                    // Technical identifier
    withdrawn_at TIMESTAMP,             // When consent withdrawn
    withdrawal_reason TEXT,             // Optional reason
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**Retention:** 7 years (legal requirement)
**Purpose:** Audit trail for consent compliance

---

#### 7. data_deletion_requests

**Purpose:** GDPR Article 17 - Right to Erasure requests
**PII Fields:** `requester_email`

```sql
CREATE TABLE data_deletion_requests (
    id UUID PRIMARY KEY,
    requester_email VARCHAR(255) NOT NULL,  // PII
    requester_type VARCHAR(50),             // candidate/recruiter
    status VARCHAR(50) NOT NULL,            // pending/verified/processing/completed
    verification_token VARCHAR(255) UNIQUE, // Email verification
    verified_at TIMESTAMP,
    processed_at TIMESTAMP,
    rejection_reason TEXT,
    notes TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**Privacy Note:** Email used only for verification, deleted after request completion.

---

#### 8. data_retention_policies

**Purpose:** Automated data cleanup policies
**PII Fields:** None (organizational configuration)

```sql
CREATE TABLE data_retention_policies (
    id UUID PRIMARY KEY,
    organization_id UUID,               // NULL = global policy
    entity_type VARCHAR(50) NOT NULL,   // resume, candidate_data, etc.
    retention_days INTEGER NOT NULL,    // Days to retain
    action_type VARCHAR(50) NOT NULL,   // delete, anonymize, archive
    policy_name VARCHAR(255),
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

---

#### 9. cookie_consent

**Purpose:** Cookie consent tracking
**PII Fields:** None (browser-stored preferences)

```sql
CREATE TABLE cookie_consent (
    id UUID PRIMARY KEY,
    consent_key VARCHAR(100) UNIQUE,    // Browser fingerprint
    essential BOOLEAN DEFAULT TRUE,     // Required
    functional BOOLEAN,                 // User choice
    analytics BOOLEAN,                  // User choice
    marketing BOOLEAN,                  // User choice
    user_id UUID REFERENCES users(id),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

---

### Data Relationships and Cascade Rules

```
resumes (1) ──┬──> (N) parsed_resumes [CASCADE DELETE]
              │
              ├──> (N) hiring_stages [CASCADE DELETE]
              │
              ├──> (N) candidate_notes [CASCADE DELETE]
              │
              ├──> (N) candidate_activities [CASCADE DELETE]
              │
              └──> (N) data_deletion_requests [SET NULL]

users (1) ────┬──> (N) resumes [CASCADE DELETE]
              │
              ├──> (N) consent_records [CASCADE DELETE]
              │
              └──> (N) candidate_notes [CASCADE DELETE]

organizations (1) ──> (N) resumes [CASCADE DELETE]
```

**Important:** When a resume is deleted (right to erasure), all related data is automatically cascade deleted.

---

## Data Lifecycle

### 1. Data Collection Phase

**Trigger:** User uploads resume via frontend

**Process:**
1. Frontend validates file type (PDF/DOCX, max 10MB)
2. File uploaded to backend via POST /api/resumes/upload
3. Consent banner displayed (first-time visitors)
4. User grants consents (13 consent types available)
5. Consent records created in `consent_records` table
6. File stored in encrypted storage (AES-256)
7. Resume metadata stored in `resumes` table

**PII Collected:**
- Filename (no PII)
- File content (contains PII)
- IP address (technical identifier)
- User agent (technical identifier)
- Consent timestamps

**Legal Basis:** Explicit consent (data_processing, data_storage)

---

### 2. Data Processing Phase

**Trigger:** Resume file uploaded

**Process:**
1. Celery task triggered for async processing
2. PDF/DOCX text extraction
3. NLP/ML analysis:
   - Named Entity Recognition (NER) for PII extraction
   - Skill extraction and classification
   - Experience calculation
   - Education parsing
   - Language detection
4. Structured data stored in `parsed_resumes` table (JSON)
5. Initial hiring stage created: `NEW`

**PII Processed:**
- Email, phone, address (contact info)
- Name, age (identification)
- Work history, education (professional)
- Skills, languages (professional)

**Legal Basis:** Consent (ai_analysis, data_processing)

---

### 3. Data Storage Phase

**Trigger:** Processing completed

**Storage Locations:**
1. **File Storage:** Original resume file (encrypted at rest)
2. **Database:** `resumes` table (metadata)
3. **Database:** `parsed_resumes` table (structured PII)
4. **Database:** `consent_records` table (consent audit trail)

**Access Controls:**
- Recruiters can only access candidates in their organization
- Candidates can only access their own data
- Admins have organization-wide access
- All access logged to `audit_logs` table

**Retention Timer Starts:** `created_at` timestamp

---

### 4. Data Usage Phase

**Valid Use Cases:**

1. **Resume Matching:** Compare candidate to job vacancies
   - Consent required: `AUTOMATED_PROCESSING`
   - API: POST /api/matching/compare

2. **Candidate Search:** Find candidates matching criteria
   - Consent required: `DATA_PROCESSING`
   - API: POST /api/search/candidates

3. **Pipeline Management:** Move candidates through hiring stages
   - Consent required: `PROFILE_CREATION`
   - API: POST /api/candidates/{id}/move

4. **Notes and Tags:** Add recruiter annotations
   - Consent required: `PROFILE_CREATION`
   - API: POST /api/notes/

5. **Analytics:** Aggregate reporting
   - Consent required: `ANALYTICS`
   - API: GET /api/reports/

**Invalid Use Cases (blocked):**
- Marketing without `MARKETING_EMAILS` consent
- AI analysis without `AI_ANALYSIS` consent
- Data sharing without `DATA_SHARING_THIRD_PARTY` consent

---

### 5. Data Export Phase

**Trigger:** Candidate requests data export (right to portability)

**Process:**
1. User initiates export via frontend (DataExportDialog)
2. API call: GET /api/data-export/resume/{id}?format=json
3. Export service gathers all related data:
   - Resume metadata
   - Parsed resume (all PII fields)
   - Hiring stages
   - Activities and notes
   - Tags and feedback
   - Consent records
4. Format as JSON or CSV
5. File download triggered in browser
6. Audit log entry created: `data_exported`

**PII Exported:** All personal data stored in system
**Format:** Machine-readable (JSON/CSV)
**Legal Basis:** GDPR Article 20 - Right to Data Portability

---

### 6. Data Deletion Phase

**Trigger:** Data deletion request (right to erasure) OR retention policy expiry

**Manual Deletion (Right to Erasure):**
1. User submits deletion request via frontend
2. API call: POST /api/data-deletion/request
3. Email verification required
4. Once verified, status changes to `VERIFIED`
5. Admin processes request
6. **Cascade deletion triggered:**
   - Delete from `resumes` table
   - Delete from `parsed_resumes` (CASCADE)
   - Delete from `hiring_stages` (CASCADE)
   - Delete from `candidate_notes` (CASCADE)
   - Delete from `candidate_activities` (CASCADE)
   - Delete from `candidate_tags` (CASCADE)
   - Delete original file from storage
7. Audit log entry created: `deletion_request_processed`
8. Deletion request marked `COMPLETED`

**Automated Deletion (Retention Policy):**
1. Celery task runs daily at 00:00 UTC
2. Finds entities exceeding retention period
3. Applies configured action:
   - `DELETE` - Permanent removal
   - `ANONYMIZE` - Remove PII, keep aggregates
   - `ARCHIVE` - Move to cold storage
   - `FLAG_REVIEW` - Manual review required
4. Audit log entry created: `retention_cleanup`
5. Cleanup statistics logged

**Legal Basis:**
- Manual: GDPR Article 17 - Right to Erasure
- Automated: GDPR Article 5(1)(e) - Storage Limitation

---

## Data Processing Purposes

### Purpose 1: Resume Analysis

**Description:** Extract structured data from resume documents

**Legal Basis:** Consent (`AI_ANALYSIS`)

**Data Processed:**
- Raw text extraction
- PII identification (email, phone, name)
- Skill extraction
- Experience calculation
- Education parsing

**Processing Activities:**
- NLP/ML model inference
- Named Entity Recognition (NER)
- Skill classification
- Text parsing

**Data Storage:** `parsed_resumes` table

---

### Purpose 2: Job Matching

**Description:** Compare candidates to job vacancies

**Legal Basis:** Consent (`AUTOMATED_PROCESSING`)

**Data Processed:**
- Skills matching
- Experience verification
- Education requirements
- Location preferences

**Processing Activities:**
- Skill synonym matching
- Score calculation
- Ranking algorithms

**Data Storage:** `match_results` table

---

### Purpose 3: Pipeline Management

**Description:** Track candidates through hiring stages

**Legal Basis:** Consent (`PROFILE_CREATION`)

**Data Processed:**
- Stage transitions
- Notes and feedback
- Tag assignments
- Activity tracking

**Processing Activities:**
- State machine transitions
- Notification triggers
- Reporting aggregation

**Data Storage:** `hiring_stages`, `candidate_notes`, `candidate_activities`

---

### Purpose 4: Analytics and Reporting

**Description:** Generate insights from recruitment data

**Legal Basis:** Consent (`ANALYTICS`)

**Data Processed:**
- Aggregate statistics
- Conversion rates
- Time-to-hire metrics
- Source attribution

**Processing Activities:**
- Data aggregation
- Metric calculation
- Trend analysis
- Visualization generation

**Data Storage:** `reports`, `analytics_events` tables

---

### Purpose 5: Communication

**Description:** Send job-related communications to candidates

**Legal Basis:** Consent (`MARKETING_EMAILS` or `JOB_ALERTS`)

**Data Processed:**
- Email address (for sending)
- Communication preferences
- Engagement tracking

**Processing Activities:**
- Email dispatch
- Open/click tracking
- Unsubscribe processing

**Data Storage:** `communications` table (if implemented)

---

## Data Sharing and Transfers

### Internal Data Sharing

**Organization Scoping:**
- Recruiters can only access candidates in their organization
- Data isolation enforced at database query level
- No cross-organization data visibility

**User Roles:**
- **Candidate:** Access own data only
- **Recruiter:** Access organization's candidates
- **Admin:** Organization-wide access + configuration
- **Super Admin:** Cross-organization access (rare)

**Data Sharing Controls:**
- `DATA_SHARING_RECRUITERS` consent required for internal sharing
- `DATA_SHARING_THIRD_PARTY` consent required for external sharing

---

### External Data Transfers

**Current Policy:** No external data transfers

**Third-Party Processors:**
- Cloud hosting provider (data storage)
- Email service provider (notifications)
- Analytics provider (if `ANALYTICS` consent granted)

**GDPR Cross-Border Transfers:**
- All data stored in EU region
- No transfers to non-EU countries without adequate safeguards
- Standard Contractual Clauses (SCCs) available if needed
- Data location tracked in `processing_agreements` table

**Data Categories Not Shared:**
- Never sold to third parties
- Never used for unrelated marketing
- Never shared without explicit consent

---

## Retention and Deletion

### Default Retention Periods

| Entity Type | Retention Period | Legal Basis | Action |
|-------------|------------------|-------------|--------|
| Resumes | 1 year (365 days) | Purpose limitation | DELETE |
| Candidate Data | 2 years (730 days) | Business requirement | DELETE |
| Parsed Resumes | 2 years (730 days) | Purpose limitation | DELETE |
| Hiring Stages | 2 years (730 days) | Business requirement | DELETE |
| Analytics Events | 3 months (90 days) | Data minimization | DELETE |
| Match Results | 6 months (180 days) | Relevance decay | DELETE |
| Analysis Results | 1 year (365 days) | ML performance tracking | DELETE |
| Audit Logs | 7 years (2555 days) | Legal requirement | ARCHIVE |
| Search History | 3 months (90 days) | Privacy optimization | DELETE |
| Reports | 1 year (365 days) | Business reporting | ARCHIVE |
| Backups | 3 months (90 days) | Disaster recovery | DELETE |

**Note:** Hired candidate data is preserved indefinitely (legal requirement).

---

### Deletion Methods

#### 1. Cascade Deletion

**Trigger:** Right to erasure request

**Process:**
```sql
BEGIN TRANSACTION;

-- Delete from child tables (cascade)
DELETE FROM candidate_notes WHERE resume_id = ?;
DELETE FROM hiring_stages WHERE resume_id = ?;
DELETE FROM candidate_activities WHERE resume_id = ?;
DELETE FROM parsed_resumes WHERE resume_id = ?;

-- Delete from parent table
DELETE FROM resumes WHERE id = ?;

-- Delete file from storage
DELETE FROM file_storage WHERE path = ?;

COMMIT;
```

**Result:** Complete data removal

---

#### 2. Anonymization

**Trigger:** Retention policy with `ANONYMIZE` action

**Process:**
```sql
UPDATE parsed_resumes
SET parsed_data = jsonb_set(
    parsed_data,
    '{name}',
    '"[REDACTED]"'
)
WHERE resume_id = ?;

-- Redact PII fields
-- Keep aggregate data for analytics
```

**Result:** PII removed, aggregate data preserved

---

#### 3. Archival

**Trigger:** Long-term retention requirement

**Process:**
- Data compressed and moved to cold storage
- Limited access (DPO only)
- Encrypted storage
- Scheduled review

**Result:** Data preserved but inaccessible for normal operations

---

## Third-Party Data Processors

### Current Processors

1. **Cloud Infrastructure Provider**
   - **Services:** Database hosting, file storage
   - **Data Categories:** All personal data
   - **Location:** EU region
   - **Security Measures:** ISO 27001, SOC 2 Type II
   - **DPA Required:** Yes (Article 28 GDPR)

2. **Email Service Provider**
   - **Services:** Transactional emails, notifications
   - **Data Categories:** Email addresses only
   - **Location:** EU region
   - **Security Measures:** TLS encryption, SPF/DKIM
   - **DPA Required:** Yes (Article 28 GDPR)

3. **Analytics Provider** (if consent granted)
   - **Services:** Usage analytics, error tracking
   - **Data Categories:** Aggregate statistics (no PII)
   - **Location:** EU region
   - **Security Measures:** Data anonymization
   - **DPA Required:** Yes (Article 28 GDPR)

---

### Processing Agreement Tracking

**Table:** `processing_agreements`

**Fields Tracked:**
- Vendor name and contact
- Data categories processed
- Processing activities
- Security measures
- Data location
- Subprocessor consent
- Retention period
- Review date

**Compliance:**
- All processors have signed DPA
- Regular reviews scheduled
- Subprocessor changes tracked
- Data location verified

---

## Data Mapping Summary

### Total PII Fields

| Category | Count | Storage Location |
|----------|-------|------------------|
| Contact Info | 4 | `parsed_resumes` (JSON) |
| Professional Info | 7 | `parsed_resumes` (JSON) |
| Identification | 3 | `parsed_resumes` (JSON) + `resumes` |
| Pipeline Data | 5 | `hiring_stages`, `candidate_notes`, etc. |
| Consent Data | 7 | `consent_records` |
| Technical Data | 2 | `consent_records` (IP, user agent) |

**Total:** 28 PII fields across 8 database tables

---

### Data Flow Summary

1. **Entry:** Resume upload → Consent granted → File stored
2. **Processing:** NLP extraction → Structured data → PII identification
3. **Storage:** Database tables (encrypted) + File storage (encrypted)
4. **Usage:** Matching → Searching → Pipeline management → Analytics
5. **Export:** JSON/CSV generation → File download (right to portability)
6. **Deletion:** Manual request or automated retention → Cascade deletion

---

### Compliance Summary

| GDPR Principle | Implementation |
|----------------|----------------|
| Lawfulness, fairness, transparency | ✅ Explicit consent tracking |
| Purpose limitation | ✅ 13 granular consent types |
| Data minimization | ✅ Only necessary PII collected |
| Accuracy | ✅ Profile editing allowed |
| Storage limitation | ✅ Automated cleanup policies |
| Integrity and confidentiality | ✅ Encryption + access control |
| Accountability | ✅ Complete audit trail (7 years) |

---

**Document Owner:** Data Protection Officer (DPO)
**Review Frequency:** Annual
**Last Updated:** 2026-02-03
**Next Review:** 2027-02-03

For questions about data mapping, contact: dpo@agenthr.com
