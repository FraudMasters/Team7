# Security Best Practices & Hardening Guide

## Project: AgentHR Resume Analysis System

## Table of Contents

1. [Security Overview](#security-overview)
2. [Threat Model](#threat-model)
3. [Secure Configuration](#secure-configuration)
4. [Authentication & Authorization](#authentication--authorization)
5. [API Security](#api-security)
6. [Data Security & Encryption](#data-security--encryption)
7. [File Upload Security](#file-upload-security)
8. [Dependency Management](#dependency-management)
9. [Logging & Monitoring Security](#logging--monitoring-security)
10. [Compliance & Data Privacy](#compliance--data-privacy)
11. [Incident Response](#incident-response)
12. [Security Testing](#security-testing)
13. [Vulnerability Disclosure](#vulnerability-disclosure)
14. [Security Checklist](#security-checklist)

---

## Security Overview

The AgentHR Resume Analysis System handles **sensitive personal information (PII)** including candidate names, contact details, work history, educational background, and complete resumes. This makes security a **critical priority** for all deployments.

### Why Security Matters

**Data Sensitivity**: The system processes and stores:
- **Personally Identifiable Information (PII)**: Full names, email addresses, phone numbers, physical addresses
- **Professional Data**: Complete work history, salary information, educational records
- **Documents**: Resume files (PDF, DOCX) containing extensive personal and professional details
- **Hiring Decisions**: Candidate rankings, assessment results, feedback data

**Legal & Compliance Requirements**:
- **GDPR** (EU General Data Protection Regulation) - For EU residents' data
- **CCPA** (California Consumer Privacy Act) - For California residents
- **Data Protection Laws** - Various jurisdictions have specific requirements
- **Industry Standards** - SOC 2, ISO 27001 compliance may be required

**Business Impact**:
- **Reputation Damage**: Data breaches can destroy trust with candidates and clients
- **Legal Liability**: Fines and penalties for non-compliance with data protection laws
- **Financial Loss**: Costs of breach response, notification, and potential lawsuits
- **Competitive Disadvantage**: Loss of proprietary ranking algorithms and data

### Security Architecture Principles

The system follows **defense-in-depth** principles:

1. **Least Privilege**: Services and users have minimum required access
2. **Secure by Default**: Security settings enabled, not opt-in
3. **Fail Securely**: Errors don't compromise security
4. **Defense in Depth**: Multiple security layers (no single point of failure)
5. **Zero Trust**: Verify explicitly, use least privilege access, assume breach

### Current Security Posture

**Implemented**:
- ✅ Docker network isolation
- ✅ Environment variable configuration
- ✅ Structured logging (Loki)
- ✅ Health check endpoints
- ✅ Database connection pooling
- ✅ CORS middleware (configurable)

**Not Yet Implemented** (requires development):
- ⚠️ Authentication/authorization system
- ⚠️ Rate limiting on API endpoints
- ⚠   Input validation on all endpoints
- ⚠   File upload malware scanning
- ⚠   Encryption at rest for uploaded files
- ⚠   API key management for external services

**This Guide** provides both:
- **Immediate actions** for securing current deployments
- **Implementation guidance** for future security features

---

## Threat Model

### System Assets

#### High-Value Assets

| Asset | Sensitivity | Impact if Compromised |
|-------|-------------|----------------------|
| **Candidate PII Database** | Critical | Legal penalties, identity theft risk, reputation damage |
| **Resume Files Storage** | Critical | Exposure of complete personal and professional histories |
| **Ranking Algorithm/Models** | High | Competitive disadvantage, gaming of hiring system |
| **Hiring Decisions Data** | High | Discrimination claims, bias exposure, legal liability |
| **API Credentials** (LLM providers) | Medium | Financial loss from unauthorized API usage |
| **Admin Access** | Critical | Full system compromise, data destruction, ransomware |

#### Attack Surface

**External Interfaces**:
- Backend API (port 8000) - FastAPI REST endpoints
- Frontend (port 3000) - React application
- Grafana Dashboard (port 3001) - Monitoring interface
- Prometheus (port 9090) - Metrics endpoint

**Data Flows**:
```
┌──────────────┐      ┌──────────────┐      ┌─────────────┐
│   Frontend   │─────▶│   Backend    │─────▶│  PostgreSQL │
│   (React)    │      │   (FastAPI)  │      │  Database   │
└──────────────┘      └──────────────┘      └─────────────┘
                            │
                    ┌───────┴──────────────────┐
                    ▼                          ▼
              ┌─────────┐              ┌─────────────┐
              │  Redis  │              │ File Storage│
              │  Cache  │              │ (Resumes)   │
              └─────────┘              └─────────────┘
```

**Third-Party Dependencies**:
- LLM Providers (ZAI, OpenAI, Anthropic, Google)
- Hugging Face Models (ML model downloads)
- LanguageTool API (grammar checking)
- S3 Storage (optional, for backups)

### Threat Actors

#### 1. External Attackers

**Motivation**: Financial gain, data theft, disruption

**Capabilities**:
- Network scanning and vulnerability exploitation
- SQL injection, XSS, CSRF attacks
- Brute force authentication attacks
- Malware upload via file uploads

**Attack Vectors**:
- Exploiting unpatched vulnerabilities in dependencies
- Intercepting unencrypted network traffic
- Brute forcing weak authentication (once implemented)
- Uploading malicious files (malware, ransomware)
- API abuse (endpoint exhaustion, data harvesting)

**Mitigation**:
- Regular dependency updates and vulnerability scanning
- TLS/HTTPS for all network traffic
- Strong password policies and rate limiting
- File upload validation and malware scanning
- API rate limiting and monitoring

#### 2. Insiders (Malicious or Compromised)

**Motivation**: Revenge, financial gain, coercion

**Capabilities**:
- Legitimate access to systems and data
- Knowledge of internal architecture and security controls
- Ability to exfiltrate data using legitimate channels

**Attack Vectors**:
- Unauthorized export of candidate data
- Manipulation of ranking algorithms
- Sabotage of backups or monitoring systems
- Theft of API keys and credentials

**Mitigation**:
- Principle of least privilege access
- Audit logging of all data access
- Separation of duties (no single admin has all access)
- Regular access reviews and revocation
- Monitoring for anomalous data access patterns

#### 3. Automated Threats (Bots & Scripts)

**Motivation**: Automated exploitation, data harvesting

**Capabilities**:
- High-speed automated attacks
- Distributed attack sources (botnets)
- Continuous probing for vulnerabilities

**Attack Vectors**:
- Credential stuffing attacks
- API endpoint scraping
- Brute force on authentication endpoints
- DDoS attacks on public endpoints

**Mitigation**:
- Rate limiting and request throttling
- CAPTCHA for suspicious activity
- IP-based blocking after repeated failures
- Web Application Firewall (WAF)
- API authentication and quota management

#### 4. Third-Party Compromise

**Motivation**: Supply chain attacks

**Capabilities**:
- Compromise of upstream dependencies
- Malicious code in library updates
- Data breach at API providers

**Attack Vectors**:
- Malicious package in dependency chain
- Compromised LLM provider API keys
- Data breach at S3 storage provider
- Malicious ML model from Hugging Face

**Mitigation**:
- Dependency pinning and vulnerability scanning
- Regular security audits of third-party services
- API key rotation and usage monitoring
- ML model verification before deployment
- Private PyPI mirrors for critical dependencies

### Specific Threat Scenarios

#### Scenario 1: Resume Database Breach

**Attack**: SQL injection on `/api/resumes/` endpoint

**Impact**:
- Exposure of all candidate PII
- Legal liability under GDPR/CCPA
- Reputational damage and loss of clients

**Likelihood**: Medium (parameterized queries prevent SQLi, but other injection risks exist)

**Mitigation**:
- ✅ SQLAlchemy ORM with parameterized queries (implemented)
- ⚠️ Input validation on all API endpoints (needs implementation)
- ⚠️ Web Application Firewall (recommended for production)
- ✅ Database user with least privileges (configured in Docker)

#### Scenario 2: Malware Upload via Resume

**Attack**: Attacher uploads malicious PDF/DOCX with embedded malware

**Impact**:
- Malware execution on backend server when processing files
- Server compromise and data exfiltration
- Ransomware deployment

**Likelihood**: High (file upload currently has minimal validation)

**Mitigation**:
- ⚠️ File type validation (magic numbers, not just extension)
- ⚠   Malware scanning (ClamAV or similar)
- ⚠   Sandboxed file processing environment
- ⚠   Size limits and format restrictions
- ✅ Docker container isolation (partial mitigation)

#### Scenario 3: API Credential Theft

**Attack**: Extraction of LLM provider API keys from environment variables

**Impact**:
- Unauthorized usage of paid API services
- Financial loss from excessive API calls
- Data exfiltration through LLM prompts

**Likelihood**: Medium (if server is compromised)

**Mitigation**:
- ⚠   Secrets management system (HashiCorp Vault, AWS Secrets Manager)
- ⚠   API key rotation policies
- ⚠   Usage monitoring and quota alerts
- ⚠   Separate API keys for dev/staging/production
- ✅ Environment variables not committed to git (implemented)

#### Scenario 4: Ranking Algorithm Manipulation

**Attack**: Attacker manipulates training data or feedback to bias rankings

**Impact**:
- Degraded ranking quality
- Gaming of hiring system
- Discrimination claims if bias introduced

**Likelihood**: Low (requires authenticated access and ML knowledge)

**Mitigation**:
- ⚠   Authentication and authorization for feedback submission
- ⚠   Rate limiting on feedback endpoints
- ⚠   Anomaly detection for unusual feedback patterns
- ⚠   Regular model performance monitoring
- ✅ A/B testing framework for model comparison (implemented)

#### Scenario 5: Data Harvesting via Public API

**Attack**: Automated scraping of all resume and vacancy data

**Impact**:
- Complete database exfiltration
- Sensitive PII exposure
- Competitive intelligence loss

**Likelihood**: High (no authentication currently implemented)

**Mitigation**:
- ⚠   API authentication (required for all endpoints)
- ⚠   Rate limiting per API key/user
- ⚠   IP-based blocking for abusive patterns
- ⚠   Data access logging and monitoring
- ⚠   Web Application Firewall (WAF)

### Risk Assessment Matrix

| Threat | Likelihood | Impact | Risk Level | Priority |
|--------|-----------|---------|------------|----------|
| **SQL Injection** | Low | Critical | **High** | P1 |
| **Malware Upload** | High | Critical | **Critical** | P0 |
| **PII Data Breach** | Medium | Critical | **High** | P1 |
| **API Key Theft** | Medium | High | **Medium** | P2 |
| **DDoS Attack** | High | Medium | **Medium** | P2 |
| **Ranking Manipulation** | Low | High | **Medium** | P2 |
| **Data Harvesting** | High | Critical | **Critical** | P0 |
| **Insider Threat** | Low | Critical | **Medium** | P2 |
| **Third-Party Compromise** | Low | High | **Medium** | P2 |

**Priority Definitions**:
- **P0 (Critical)**: Immediate action required before production deployment
- **P1 (High)**: Must be addressed within first sprint
- **P2 (Medium)**: Should be addressed in subsequent sprints

### Compliance & Legal Considerations

**GDPR Requirements**:
- Data minimization (collect only necessary PII)
- Right to erasure (delete candidate data on request)
- Data portability (export data on request)
- Breach notification (within 72 hours)
- Privacy by design and by default

**Implementation Status**:
- ⚠️ Data deletion endpoints (not implemented)
- ⚠️ Data export functionality (not implemented)
- ✅ Audit logging (Loki aggregation implemented)
- ⚠️ Breach detection and response procedures (needs documentation)

**CCPA Requirements**:
- "Do not sell my personal information" opt-out
- Access to specific pieces of personal information
- Deletion of personal information
- Opt-in for sale of minors' data

**Implementation Status**:
- ⚠️ CCPA compliance not yet addressed

---

## Secure Configuration

Proper configuration is the foundation of system security. This section provides detailed guidance for securing AgentHR deployments.

### Environment Variable Security

Environment variables are the primary method for configuring the system. Protect them carefully.

#### Generation of Secure Values

```bash
# Generate strong SECRET_KEY (64 character hexadecimal)
openssl rand -hex 32

# Generate strong database password (32 character base64)
openssl rand -base64 32

# Generate API keys
openssl rand -hex 24

# Generate JWT secrets
openssl rand -base64 48
```

#### Critical Security Variables

| Variable | Purpose | Security Requirements |
|----------|---------|----------------------|
| `SECRET_KEY` | Cryptographic signing | Must be cryptographically random, 64+ characters, never shared |
| `DATABASE_URL` | Database connection | Use strong password, SSL required in production |
| `POSTGRES_PASSWORD` | PostgreSQL admin | Separate from app DB user, 32+ characters, rotated quarterly |
| `REDIS_URL` | Redis connection | Use Redis AUTH in production, separate password |
| `ZAI_API_KEY` | LLM provider API | Treat as secret, monitor usage, separate keys per environment |
| `JWT_SECRET` | Token signing | Separate from SECRET_KEY, 48+ characters |
| `BACKUP_S3_SECRET_KEY` | S3 backup storage | Use IAM roles instead when possible, rotate quarterly |

#### Environment Variable Protection

**Never Commit Secrets**:

```bash
# .gitignore
.env
.env.local
.env.*.local
*.key
*.pem
secrets/
```

**File Permissions**:

```bash
# Restrict .env file to owner only
chmod 600 .env

# Verify permissions
ls -la .env
# Should show: -rw------- (600)
```

**Separate Environments**:

```bash
# Use different environment files
.env.development    # Local development
.env.staging        # Staging environment
.env.production     # Production environment (never commit)

# Load environment-specific file
export $(cat .env.production | xargs)
```

**Docker Secrets (Recommended for Production)**:

```yaml
# docker-compose.yml
services:
  backend:
    secrets:
      - db_password
      - secret_key
      - api_key
    environment:
      DATABASE_URL: postgresql://user:${db_password}@db:5432/resume_analysis
      SECRET_KEY: ${secret_key}
      ZAI_API_KEY: ${api_key}

secrets:
  db_password:
    file: ./secrets/db_password.txt
  secret_key:
    file: ./secrets/secret_key.txt
  api_key:
    file: ./secrets/api_key.txt
```

**Kubernetes Secrets**:

```yaml
# kubernetes-secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: backend-secrets
type: Opaque
stringData:
  SECRET_KEY: "your-secret-key-here"
  DATABASE_URL: "postgresql://user:pass@host:5432/db"
  ZAI_API_KEY: "your-api-key"
```

### Secrets Management Recommendations

For production deployments, use a dedicated secrets management system.

#### HashiCorp Vault

**Why**: Industry-standard secret management with audit logging, automatic rotation, and dynamic credentials.

**Implementation**:

```bash
# Install Vault
docker run -d --name vault \
  -p 8200:8200 \
  -e 'VAULT_DEV_ROOT_TOKEN_ID=myroot' \
  hashicorp/vault

# Configure backend to use Vault
# Install dependencies
pip install hvac

# Configure in backend/config.py
import hvac
vault_client = hvac.Client(url='http://vault:8200')

def get_secret(path, key):
    vault_client.auth.approle.login(role_id='...', secret_id='...')
    return vault_client.secrets.kv.v2.read_secret_version(path=path)['data']['data'][key]

SECRET_KEY = get_secret('secret/agenthr', 'secret_key')
```

**Best Practices**:
- Enable audit logging
- Use AppRole authentication for services
- Implement automatic secret rotation
- Set TTL on dynamic credentials
- Use transit backend for encryption

#### AWS Secrets Manager

**Why**: Managed service with automatic rotation, fine-grained access control, and CloudTrail integration.

**Implementation**:

```bash
# Store secret
aws secretsmanager create-secret \
  --name agenthr/prod/database \
  --secret-string '{"username":"appuser","password":"***"}'

# Configure automatic rotation (30 days)
aws secretsmanager rotate-secret \
  --secret-id agenthr/prod/database \
  --rotation-lambda-arn arn:aws:lambda:region:account:function:RotateSecret

# Access in backend
import boto3
client = boto3.client('secretsmanager')
secret = client.get_secret_value(SecretId='agenthr/prod/database')
db_config = json.loads(secret['SecretString'])
DATABASE_URL = f"postgresql://{db_config['username']}:{db_config['password']}@..."
```

**Cost Note**: AWS Secrets Manager charges $0.40 per secret per month.

#### Docker Swarm Secrets

**Why**: Built-in Docker secret management without external dependencies.

**Implementation**:

```bash
# Create secret
echo "my-secret-key" | docker secret create agenthr_secret_key -

# Use in stack deploy
docker stack deploy -c docker-compose.yml agenthr

# Access in container (mounted at /run/secrets/)
with open('/run/secrets/agenthr_secret_key', 'r') as f:
    SECRET_KEY = f.read().strip()
```

#### Environment-Based Selection

| Deployment | Recommended Solution |
|------------|---------------------|
| Local Development | `.env` file (gitignored) |
| Small Production | Docker Secrets / Swarm Secrets |
| Medium Production | AWS Secrets Manager / Azure Key Vault |
| Large/Enterprise | HashiCorp Vault + IAM integration |

### Database Hardening

Secure the PostgreSQL database to protect candidate PII and system data.

#### Connection Security

**Require SSL**:

```bash
# DATABASE_URL format
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require

# In postgresql.conf
ssl = on
ssl_cert_file = '/var/lib/postgresql/server.crt'
ssl_key_file = '/var/lib/postgresql/server.key'
```

**Connection Restrictions** (`pg_hba.conf`):

```bash
# TYPE  DATABASE        USER            ADDRESS                 METHOD

# Local connections
local   all             postgres                                peer

# Require SSL for remote connections
host    resume_analysis app_user        10.0.0.0/8            scram-sha-256
host    resume_analysis app_user        172.16.0.0/12         scram-sha-256

# Reject non-SSL connections
hostnossl all          all             0.0.0.0/0              reject

# Admin access from specific IPs only
host    all            postgres        192.168.1.0/24        scram-sha-256
```

#### User Privilege Management

**Principle of Least Privilege**:

```sql
-- Application user (no superuser, no createdb)
CREATE USER app_user WITH LOGIN PASSWORD 'strong-password' NOCREATEDB NOCREATEROLE NOSUPERUSER;

-- Grant only necessary permissions
GRANT CONNECT ON DATABASE resume_analysis TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;

-- Backup user (read-only access)
CREATE USER backup_user WITH LOGIN PASSWORD 'different-password' NOCREATEDB NOCREATEROLE NOSUPERUSER;
GRANT CONNECT ON DATABASE resume_analysis TO backup_user;
GRANT USAGE ON SCHEMA public TO backup_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO backup_user;

-- Monitoring user (read-only, can connect)
CREATE USER monitoring_user WITH LOGIN PASSWORD 'monitoring-password' NOCREATEDB NOCREATEROLE NOSUPERUSER;
GRANT pg_monitor TO monitoring_user;
```

**Default Accounts**:

```bash
# Change postgres superuser password
docker-compose exec postgres psql -U postgres -c "ALTER USER postgres PASSWORD 'new-strong-password';"

# Or set in docker-compose.yml
environment:
  POSTGRES_PASSWORD: $(openssl rand -base64 32)
```

#### Data Encryption

**Transparent Data Encryption (TDE)**:

PostgreSQL doesn't have built-in TDE. Use filesystem encryption:

```bash
# LUKS encryption on Linux
cryptsetup -y -v luksFormat /dev/sdb1
cryptsetup luksOpen /dev/sdb1 encrypted_postgres
mkfs.ext4 /dev/mapper/encrypted_postgres
mount /dev/mapper/encrypted_postgres /var/lib/postgresql

# Add to crypttab for auto-mount on boot
echo "encrypted_postgres /dev/sdb1 none luks" >> /etc/crypttab
```

**Column-Level Encryption** (for sensitive PII):

```sql
-- Install pgcrypto extension
CREATE EXTENSION pgcrypto;

-- Encrypt sensitive columns
CREATE TABLE candidates (
    id SERIAL PRIMARY KEY,
    name_encrypted BYTEA,
    email_encrypted BYTEA,
    -- Other non-sensitive fields
);

-- Encrypt data on insert
INSERT INTO candidates (name_encrypted, email_encrypted)
VALUES (
    pgp_sym_encrypt('John Doe', 'encryption-key'),
    pgp_sym_encrypt('john@example.com', 'encryption-key')
);

-- Decrypt on read
SELECT pgp_sym_decrypt(name_encrypted, 'encryption-key') AS name
FROM candidates;
```

#### Database Hardening Checklist

- [ ] Change default postgres password
- [ ] Create separate application user with limited privileges
- [ ] Enable SSL/TLS for all connections
- [ ] Configure `pg_hba.conf` to restrict access by IP
- [ ] Disable superuser access for application user
- [ ] Enable connection logging
- [ ] Set up database-level audit logging
- [ ] Implement regular backups with encryption
- [ ] Use prepared statements (SQLAlchemy ORM provides this)
- [ ] Install security updates regularly
- [ ] Monitor for suspicious queries (connection spikes, full table scans)
- [ ] Restrict access to pg_stat_activity for monitoring
- [ ] Implement row-level security for multi-tenant scenarios
- [ ] Use disk encryption for data directory

#### Backup Security

```bash
# Encrypt backups
BACKUP_ENCRYPTION_KEY=$(openssl rand -base64 32)

# GPG encryption for backup files
pg_dump resume_analysis | gpg --cipher-algo AES256 --compress-algo 1 --symmetric --output backup.sql.gpg

# Store encryption key separately (not with backup)
echo $BACKUP_ENCRYPTION_KEY | vault kv put secret/agenthr/backup key=-
```

### Redis Hardening

Secure the Redis cache to prevent unauthorized access.

**Enable Authentication**:

```bash
# Generate strong password
REDIS_PASSWORD=$(openssl rand -base64 32)

# Configure in redis.conf
requirepass your-redis-password-here

# Or use Docker environment
REDIS_URL=redis://:your-password@localhost:6379/0
```

**Disable Dangerous Commands**:

```bash
# In redis.conf or Docker command
redis-server --rename-command FLUSHDB ""
redis-server --rename-command FLUSHALL ""
redis-server --rename-command CONFIG "CONFIG_c8f2e4c1"
```

**Bind to Localhost Only**:

```bash
# In redis.conf
bind 127.0.0.1 ::1

# Or use Docker networks (no external binding)
```

### Production Hardening Checklist

Complete this checklist before deploying to production.

#### Network Security

- [ ] Firewall configured (ufw/iptables)
- [ ] Only required ports open (80, 443, maybe 22)
- [ ] Database not accessible from internet
- [ ] Redis not accessible from internet
- [ ] Docker network isolation enabled
- [ ] Intrusion detection/prevention system (IDS/IPS) configured
- [ ] DDoS protection enabled (Cloudflare, AWS Shield)
- [ ] VPN or bastion host for admin access

#### TLS/HTTPS Configuration

- [ ] Valid SSL/TLS certificate installed (Let's Encrypt or commercial)
- [ ] HTTP redirected to HTTPS
- [ ] Strong cipher suites only (TLS 1.2+)
- [ ] HSTS header enabled
- [ ] Security headers configured
- [ ] Certificate auto-renewal configured

#### Application Security

- [ ] `DEBUG=false` in production
- [ ] Strong `SECRET_KEY` set (64+ characters)
- [ ] CORS configured for specific origins only
- [ ] Rate limiting enabled
- [ ] Input validation on all endpoints
- [ ] File upload restrictions in place
- [ ] Error messages don't leak sensitive information
- [ ] API documentation restricted or authenticated
- [ ] Health check endpoint doesn't expose sensitive info

#### Infrastructure Security

- [ ] Operating system patches applied
- [ ] Docker base images updated
- [ ] Python dependencies updated and scanned
- [ ] Container vulnerability scanning enabled
- [ ] Security logging and monitoring configured
- [ ] Automated backup system enabled
- [ ] Backup restoration tested
- [ ] Disaster recovery plan documented
- [ ] Incident response procedures defined

#### Access Control

- [ ] Strong password policy enforced
- [ ] Multi-factor authentication (MFA) enabled for admin access
- [ ] SSH key-based authentication only (no passwords)
- [ ] Root login disabled via SSH
- [ ] Separate admin accounts (no shared credentials)
- [ ] Access review process in place
- [ ] Offboarding procedure for revoked access

#### Monitoring & Alerting

- [ ] Grafana dashboards configured
- [ ] Prometheus metrics enabled
- [ ] Log aggregation (Loki) configured
- [ ] Security event logging enabled
- [ ] Alert notifications configured
- [ ] Regular security audit scheduled
- [ ] Failed login monitoring
- [ ] Anomaly detection configured
- [ ] Performance baseline established

#### Compliance & Privacy

- [ ] GDPR compliance measures implemented
- [ ] Data retention policy configured
- [ ] Right to erasure endpoints available
- [ ] Data export functionality available
- [ ] Privacy policy published
- [ ] Cookie consent implemented (if applicable)
- [ ] Data processing agreement with vendors
- [ ] Breach notification procedures defined

#### Secrets & Credentials

- [ ] No credentials in code or version control
- [ ] Secrets management system configured
- [ ] API keys rotated quarterly
- [ ] Database passwords rotated quarterly
- [ ] Certificate expiration monitored
- [ ] Secrets audit trail enabled
- [ ] Emergency access procedure documented

#### Testing & Validation

- [ ] Security testing completed
- [ ] Penetration testing performed
- [ ] Dependency vulnerability scan clean
- [ ] OWASP Top 10 mitigations verified
- [ ] Load testing completed
- [ ] Failover testing completed
- [ ] Backup restoration tested
- [ ] Security review signed off

---

## Authentication & Authorization

> **Status**: ⚠️ **NOT YET IMPLEMENTED** - This section provides implementation guidance for the future authentication system.

The AgentHR system currently lacks authentication and authorization. Implementing robust identity and access management is **critical** before production deployment.

### Authentication Architecture

#### Recommended Approach: JWT-Based Authentication

**Why JSON Web Tokens (JWT)**:
- Stateless authentication (suitable for containerized deployments)
- Built-in expiration and refresh mechanisms
- Industry standard with extensive library support
- Works well with FastAPI's `security` module

**Architecture Overview**:

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   Frontend   │────────▶│   Backend    │────────▶│   Database   │
│   (React)    │  Token  │   (FastAPI)  │  Query  │  PostgreSQL  │
└──────────────┘         └──────────────┘         └──────────────┘
                                  │
                                  ▼
                           ┌──────────────┐
                           │    Redis     │
                           │ Token Blacklist│
                           └──────────────┘
```

#### Implementation Guide

##### Step 1: Add Authentication Dependencies

```bash
# backend/requirements.txt
fastapi[all]==0.104.1
python-jose[cryptography]==3.3.0  # JWT token creation/validation
passlib[bcrypt]==1.7.4            # Password hashing
python-multipart==0.0.6           # Form data parsing
pydantic[email]==2.5.0            # Email validation
```

##### Step 2: Extend Configuration

Add authentication settings to `backend/config.py`:

```python
# Authentication Configuration
secret_key: str = Field(
    default="change-this-in-production-use-openssl-rand-hex-32",
    description="Secret key for JWT token signing",
)

jwt_algorithm: str = Field(
    default="HS256",
    description="JWT signing algorithm",
)

access_token_expire_minutes: int = Field(
    default=30,
    ge=5,
    le=1440,
    description="Access token expiration time in minutes",
)

refresh_token_expire_days: int = Field(
    default=7,
    ge=1,
    le=30,
    description="Refresh token expiration time in days",
)

password_min_length: int = Field(
    default=12,
    ge=8,
    le=128,
    description="Minimum password length",
)

password_require_uppercase: bool = Field(
    default=True,
    description="Require uppercase letters in passwords",
)

password_require_lowercase: bool = Field(
    default=True,
    description="Require lowercase letters in passwords",
)

password_require_numbers: bool = Field(
    default=True,
    description="Require numbers in passwords",
)

password_require_special: bool = Field(
    default=True,
    description="Require special characters in passwords",
)

# API Key Configuration
api_key_enabled: bool = Field(
    default=True,
    description="Enable API key authentication",
)

api_key_header: str = Field(
    default="X-API-Key",
    description="Header name for API key authentication",
)
```

##### Step 3: Create Authentication Models

`backend/models/auth.py`:

```python
"""
Authentication models for user management and JWT tokens.
"""
from datetime import datetime, timedelta
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator
import re


class UserBase(BaseModel):
    """Base user model with common fields."""

    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    is_active: bool = True


class UserCreate(UserBase):
    """User creation model with password."""

    password: str = Field(..., min_length=12, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets security requirements."""
        settings = get_settings()

        if len(v) < settings.password_min_length:
            raise ValueError(
                f"Password must be at least {settings.password_min_length} characters"
            )

        if settings.password_require_uppercase and not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")

        if settings.password_require_lowercase and not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")

        if settings.password_require_numbers and not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")

        if settings.password_require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError("Password must contain at least one special character")

        # Check for common passwords
        common_passwords = [
            "password", "password123", "admin", "welcome",
            "qwerty", "letmein", "monkey", "123456"
        ]
        if v.lower() in common_passwords:
            raise ValueError("Password is too common")

        return v


class UserUpdate(BaseModel):
    """User update model (all fields optional)."""

    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=12, max_length=128)


class UserInDB(UserBase):
    """User model as stored in database."""

    id: int
    hashed_password: str
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class User(UserBase):
    """User model returned to clients (password excluded)."""

    id: int
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    """JWT token response model."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenPayload(BaseModel):
    """JWT token payload model."""

    sub: int  # user_id
    exp: datetime
    iat: datetime
    type: str  # "access" or "refresh"
    email: str


class TokenRefresh(BaseModel):
    """Token refresh request model."""

    refresh_token: str


class LoginRequest(BaseModel):
    """User login request model."""

    email: EmailStr
    password: str


class APIKey(BaseModel):
    """API key model."""

    id: int
    name: str
    key_prefix: str  # First 8 characters for identification
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    is_active: bool


class APIKeyCreate(BaseModel):
    """API key creation model."""

    name: str = Field(..., min_length=1, max_length=100)
    expires_days: Optional[int] = Field(None, ge=1, le=365)
```

##### Step 4: Implement Authentication Utilities

`backend/core/security.py`:

```python
"""
Authentication and security utilities for JWT tokens and password hashing.
"""
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from config import get_settings

settings = get_settings()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database

    Returns:
        True if password matches hash, False otherwise

    Example:
        >>> verify_password("user123", "$2b$12$...")
        True
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password

    Example:
        >>> hash = get_password_hash("securepassword")
        >>> len(hash)
        60
    """
    return pwd_context.hash(password)


def create_access_token(user_id: int, email: str) -> tuple[str, datetime]:
    """
    Create a JWT access token.

    Args:
        user_id: User's database ID
        email: User's email address

    Returns:
        Tuple of (token_string, expiration_datetime)

    Example:
        >>> token, expires = create_access_token(1, "user@example.com")
        >>> len(token.split("."))  # JWT has 3 parts
        3
    """
    expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    expire = datetime.utcnow() + expires_delta

    to_encode = {
        "sub": user_id,
        "email": email,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.jwt_algorithm
    )

    return encoded_jwt, expire


def create_refresh_token(user_id: int, email: str) -> str:
    """
    Create a JWT refresh token.

    Args:
        user_id: User's database ID
        email: User's email address

    Returns:
        Refresh token string

    Example:
        >>> token = create_refresh_token(1, "user@example.com")
        >>> len(token) > 0
        True
    """
    expires_delta = timedelta(days=settings.refresh_token_expire_days)
    expire = datetime.utcnow() + expires_delta

    to_encode = {
        "sub": user_id,
        "email": email,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.jwt_algorithm
    )

    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token string

    Returns:
        Token payload if valid, None if invalid

    Example:
        >>> payload = decode_token(valid_token)
        >>> payload["type"]
        'access'
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        return None


def generate_api_key() -> str:
    """
    Generate a secure API key.

    Returns:
        64-character hexadecimal API key

    Example:
        >>> key = generate_api_key()
        >>> len(key)
        64
    """
    import secrets
    return secrets.token_hex(32)
```

##### Step 5: Implement Authentication Dependencies

`backend/api/deps.py`:

```python
"""
Authentication dependencies for FastAPI routes.
"""
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import decode_token
from database import get_db
from models.auth import User, TokenPayload

# OAuth2 scheme for token-based authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# HTTP Bearer scheme for API key authentication
bearer_scheme = HTTPBearer()


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from JWT token.

    Args:
        token: JWT access token
        db: Database session

    Returns:
        Current user object

    Raises:
        HTTPException: If token is invalid or user not found

    Example:
        >>> @app.get("/api/profile")
        >>> async def profile(user: User = Depends(get_current_user)):
        ...     return user
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Decode token
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    # Validate token type
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    # Get user ID from token
    user_id: int = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    # Query user from database
    from sqlalchemy import select
    from models.auth import UserInDB

    result = await db.execute(select(UserInDB).where(UserInDB.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    return User(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login=user.last_login,
    )


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get the current active user.

    Args:
        current_user: Current user from token

    Returns:
        Current user if active

    Raises:
        HTTPException: If user is inactive

    Example:
        >>> @app.get("/api/protected")
        >>> async def protected(user: User = Depends(get_current_active_user)):
        ...     return user
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    return current_user


async def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Verify API key and return associated user.

    Args:
        credentials: HTTP Bearer credentials
        db: Database session

    Returns:
        User associated with API key

    Raises:
        HTTPException: If API key is invalid

    Example:
        >>> @app.get("/api/v1/data")
        >>> async def data(user: User = Depends(verify_api_key)):
        ...     return user
    """
    from config import get_settings
    from sqlalchemy import select
    from models.auth import APIKey

    settings = get_settings()
    api_key = credentials.credentials

    # Query API key from database
    result = await db.execute(
        select(APIKey).where(APIKey.key == api_key)
    )
    key_record = result.scalar_one_or_none()

    if key_record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    if not key_record.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is disabled",
        )

    if key_record.expires_at and key_record.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has expired",
        )

    # Update last used timestamp
    key_record.last_used = datetime.utcnow()
    await db.commit()

    # Get associated user
    user_result = await db.execute(
        select(UserInDB).where(UserInDB.id == key_record.user_id)
    )
    user = user_result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled",
        )

    return User(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login=user.last_login,
    )
```

### Authorization & Role-Based Access Control (RBAC)

Implement role-based permissions for different user types.

#### Role Design

**Recommended Roles**:

| Role | Permissions | Use Case |
|------|-------------|----------|
| `admin` | Full system access, user management, configuration | System administrators |
| `recruiter` | Create vacancies, view candidates, manage rankings | HR professionals |
| `hiring_manager` | View candidates for their vacancies, provide feedback | Hiring managers |
| `viewer` | Read-only access to reports and analytics | Executives, stakeholders |
| `api` | API-only access, specific quotas | Third-party integrations |

#### Implementation

`backend/models/auth.py` (add to existing):

```python
class Role(BaseModel):
    """User role model."""

    id: int
    name: str
    description: Optional[str] = None
    permissions: list[str] = []


class UserRole(BaseModel):
    """User role assignment."""

    user_id: int
    role_id: int
    assigned_at: datetime
    assigned_by: int  # user_id of admin who assigned


class Permission(str, enum.Enum):
    """System permissions."""

    # Resume management
    RESUME_CREATE = "resume:create"
    RESUME_READ = "resume:read"
    RESUME_UPDATE = "resume:update"
    RESUME_DELETE = "resume:delete"

    # Vacancy management
    VACANCY_CREATE = "vacancy:create"
    VACANCY_READ = "vacancy:read"
    VACANCY_UPDATE = "vacancy:update"
    VACANCY_DELETE = "vacancy:delete"

    # Candidate management
    CANDIDATE_READ = "candidate:read"
    CANDIDATE_UPDATE = "candidate:update"

    # Analytics
    ANALYTICS_VIEW = "analytics:view"
    REPORTS_GENERATE = "reports:generate"

    # User management
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"

    # System administration
    SYSTEM_CONFIG = "system:config"
    SYSTEM_BACKUP = "system:backup"
    SYSTEM_LOGS = "system:logs"
```

#### Permission Checker Dependency

`backend/api/deps.py` (add to existing):

```python
async def require_permission(permission: Permission):
    """
    Dependency that requires specific permission.

    Args:
        permission: Required permission

    Returns:
        Dependency function

    Example:
        >>> @app.post("/api/vacancies")
        >>> async def create_vacancy(
        ...     vacancy: VacancyCreate,
        ...     _: None = Depends(require_permission(Permission.VACANCY_CREATE))
        ... ):
        ...     return vacancy
    """
    async def check_permission(
        current_user: User = Depends(get_current_user)
    ) -> User:
        # Get user permissions from database
        # (Implementation depends on your RBAC table structure)

        # For now, check if user is admin (has all permissions)
        if current_user.email.endswith("@admin.local"):
            return current_user

        # Check specific permission
        # TODO: Implement proper permission lookup
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission '{permission.value}' required",
        )

    return check_permission
```

### Session Management

#### Token Storage (Frontend)

```typescript
// Frontend: store tokens securely

// ✅ GOOD: Use httpOnly cookies (set by backend)
// Backend sets: Set-Cookie: access_token=<token>; HttpOnly; Secure; SameSite=Strict

// ✅ ACCEPTABLE: Memory (not persisted across refreshes)
let accessToken: string | null = null;

// ❌ BAD: localStorage (accessible to XSS)
localStorage.setItem('token', accessToken);

// ❌ BAD: sessionStorage (accessible to XSS)
sessionStorage.setItem('token', accessToken);
```

#### Token Refresh Flow

```python
@router.post("/refresh")
async def refresh_token(
    refresh_request: TokenRefresh,
    db: AsyncSession = Depends(get_db)
) -> Token:
    """
    Refresh access token using refresh token.

    Args:
        refresh_request: Refresh token request
        db: Database session

    Returns:
        New access and refresh tokens

    Raises:
        HTTPException: If refresh token is invalid
    """
    # Decode refresh token
    payload = decode_token(refresh_request.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Get user
    user_id = payload.get("sub")
    user = await get_user_by_id(db, user_id)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Generate new tokens
    access_token, expires = create_access_token(user.id, user.email)
    new_refresh_token = create_refresh_token(user.id, user.email)

    # Invalidate old refresh token (if using token blacklist)
    # await blacklist_token(refresh_request.refresh_token)

    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=int(settings.access_token_expire_minutes * 60)
    )
```

### Multi-Factor Authentication (MFA)

#### Implementation Recommendations

**Time-Based One-Time Password (TOTP)**:
- Use `pyotp` library for TOTP generation/validation
- Store TOTP secrets encrypted in database
- Require MFA for admin accounts
- Allow backup codes for account recovery

```python
# backend/core/mfa.py
import pyotp
import qrcode
from io import BytesIO
import base64

def generate_totp_secret() -> str:
    """Generate a new TOTP secret."""
    return pyotp.random_base32()

def generate_totp_qr_code(user_email: str, secret: str) -> str:
    """Generate QR code for TOTP setup."""
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=user_email,
        issuer_name="AgentHR"
    )

    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_uri)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')

    return base64.b64encode(buffer.getvalue()).decode()

def verify_totp(secret: str, token: str) -> bool:
    """Verify TOTP token."""
    totp = pyotp.TOTP(secret)
    return totp.verify(token, valid_window=1)
```

### Authentication Security Checklist

#### Password Security

- [ ] Minimum 12 character password length
- [ ] Require uppercase, lowercase, numbers, special characters
- [ ] Check against common password lists
- [ ] Use bcrypt (cost factor 12+) for password hashing
- [ ] Never store plain text passwords
- [ ] Implement password strength meter on frontend
- [ ] Provide clear password requirements to users

#### Token Security

- [ ] Use strong random secret key (64+ characters)
- [ ] Set appropriate token expiration (30 minutes access, 7 days refresh)
- [ ] Implement token blacklist for logout
- [ ] Use HTTPS for all token transmission
- [ ] Validate token signature on every request
- [ ] Include token type in payload
- [ ] Implement token refresh mechanism

#### Session Security

- [ ] Use httpOnly, Secure, SameSite cookies for tokens
- [ ] Implement session timeout
- [ ] Provide secure logout functionality
- [ ] Detect and prevent session hijacking
- [ ] Implement concurrent session limits
- [ ] Log all authentication events
- [ ] Detect and prevent brute force attacks

#### Account Security

- [ ] Implement account lockout after failed attempts (5 attempts)
- [ ] Require email verification for new accounts
- [ ] Implement secure password reset flow (time-limited tokens)
- [ ] Require MFA for admin accounts
- [ ] Provide audit log of user actions
- [ ] Implement "last login" tracking
- [ ] Allow users to view active sessions
- [ ] Provide "logout all sessions" functionality

#### API Key Security

- [ ] Generate cryptographically random API keys (64+ characters)
- [ ] Store only hashed keys in database
- [ ] Implement API key expiration
- [ ] Allow API key revocation
- [ ] Log all API key usage
- [ ] Implement rate limiting per API key
- [ ] Provide key rotation mechanism
- [ ] Show only key prefix to users

#### Authorization Security

- [ ] Implement role-based access control (RBAC)
- [ ] Default deny policy (deny unless explicitly allowed)
- [ ] Implement least privilege principle
- [ ] Validate permissions on every request
- [ ] Log all authorization failures
- [ ] Implement resource-level permissions where needed
- [ ] Regular permission audits

---

## API Security

Secure the backend API against common attacks and implement defense-in-depth measures.

### Rate Limiting

Rate limiting prevents API abuse, brute force attacks, and resource exhaustion.

#### Implementation: SlowAPI

```bash
# Add to backend/requirements.txt
slowapi==0.1.9
```

#### Configuration

`backend/main.py`:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/hour", "50/minute"],
    storage_uri="redis://localhost:6379/1",  # Use Redis for distributed limiting
    headers_enabled=True,  # Add rate limit headers to responses
)

# Add rate limit error handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

#### Endpoint-Specific Limits

```python
from fastapi import Depends
from slowapi import Limiter

# Apply default limits to all endpoints
@app.get("/api/resumes")
@limiter.limit("100/minute")
async def list_resumes(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """List resumes with rate limit."""
    pass

# Stricter limits for expensive operations
@app.post("/api/resumes/analyze")
@limiter.limit("10/minute")
async def analyze_resume(
    request: Request,
    resume_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Analyze resume with stricter rate limit."""
    pass

# Public endpoints (authentication)
@app.post("/api/auth/login")
@limiter.limit("5/minute")
async def login(
    request: Request,
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Login with very strict rate limit to prevent brute force."""
    pass

# File upload limits
@app.post("/api/resumes/upload")
@limiter.limit("20/hour")
async def upload_resume(
    request: Request,
    file: UploadFile,
    db: AsyncSession = Depends(get_db)
):
    """Upload resume with hourly limit."""
    pass
```

#### Rate Limit Strategies

| Endpoint Type | Rate Limit | Rationale |
|---------------|------------|-----------|
| **Authentication** | 5/minute | Prevent brute force attacks |
| **File Upload** | 20/hour | Prevent storage exhaustion |
| **Analysis** | 10/minute | Prevent CPU/LLM abuse |
| **Read Operations** | 100/minute | Allow normal usage |
| **Write Operations** | 50/minute | Prevent data flood |
| **Admin Operations** | 20/minute | Additional protection for sensitive actions |

#### Advanced Rate Limiting

**Per-User Rate Limiting**:

```python
def get_user_id(request: Request) -> str:
    """Get user ID for rate limiting (prefers user ID over IP)."""
    # Try to get user from token
    auth_header = request.headers.get("Authorization")
    if auth_header:
        try:
            token = auth_header.split(" ")[1]
            payload = decode_token(token)
            if payload:
                return f"user:{payload['sub']}"
        except:
            pass

    # Fall back to IP address
    return f"ip:{get_remote_address(request)}"


limiter = Limiter(
    key_func=get_user_id,  # Use user ID instead of IP
    default_limits=["1000/hour"],  # Higher limit for authenticated users
)

# Higher limits for authenticated users
@app.get("/api/resumes")
@limiter.limit("200/minute", key_func=get_user_id)
async def list_resumes(request: Request):
    """Higher rate limit for authenticated users."""
    pass
```

**Redis-Based Distributed Rate Limiting**:

```python
import redis
from fastapi import Request

redis_client = redis.from_url("redis://localhost:6379/1")

async def check_rate_limit(
    user_id: str,
    endpoint: str,
    limit: int,
    window: int  # seconds
) -> bool:
    """
    Check rate limit using Redis sliding window.

    Args:
        user_id: User identifier
        endpoint: Endpoint path
        limit: Max requests allowed
        window: Time window in seconds

    Returns:
        True if request allowed, False otherwise
    """
    key = f"ratelimit:{user_id}:{endpoint}"
    current = redis_client.incr(key)

    if current == 1:
        redis_client.expire(key, window)

    return current <= limit
```

### CORS Configuration

Cross-Origin Resource Sharing (CORS) controls which domains can access your API.

#### Current Configuration

The system currently uses a permissive CORS configuration (`backend/config.py`):

```python
@property
def cors_origins(self) -> List[str]:
    """Get list of allowed CORS origins."""
    return [
        self.frontend_url,
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
```

#### Production CORS Configuration

**Update `backend/config.py`**:

```python
# CORS Configuration
cors_origins: str = Field(
    default="http://localhost:3000,http://localhost:5173",
    description="Comma-separated list of allowed CORS origins",
)

cors_allow_credentials: bool = Field(
    default=True,
    description="Allow credentials in CORS requests",
)

cors_allow_methods: List[str] = Field(
    default=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    description="Allowed HTTP methods for CORS",
)

cors_allow_headers: List[str] = Field(
    default=[
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Accept",
        "Origin",
    ],
    description="Allowed headers for CORS",
)

cors_max_age: int = Field(
    default=600,
    ge=0,
    le=86400,
    description="CORS preflight cache duration in seconds",
)

@property
def cors_origins_list(self) -> List[str]:
    """Parse CORS origins from comma-separated string."""
    origins = [origin.strip() for origin in self.cors_origins.split(",")]

    # Validate origins
    for origin in origins:
        if origin != "*" and not origin.startswith(("http://", "https://")):
            logger.warning(f"Invalid CORS origin: {origin}")

    return origins
```

**Update `backend/main.py`**:

```python
from config import get_settings

settings = get_settings()

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
    max_age=settings.cors_max_age,  # Cache preflight for 10 minutes
)
```

#### Production Recommendations

**Restrictive CORS**:

```bash
# .env.production
CORS_ORIGINS=https://app.agenthr.com,https://www.agenthr.com
```

**Development CORS**:

```bash
# .env.development
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

**Never Use Wildcard in Production**:

```python
# ❌ BAD - Allows any origin
allow_origins=["*"]

# ✅ GOOD - Specific origins only
allow_origins=["https://app.agenthr.com"]
```

### Input Validation

Validate all user input to prevent injection attacks and data corruption.

#### Pydantic Validation

FastAPI uses Pydantic for automatic request validation. Ensure all endpoints use type hints and validation.

**Example: Resume Upload Validation**:

```python
from pydantic import BaseModel, Field, field_validator, HttpUrl
from typing import Optional, List
import re

class ResumeCreate(BaseModel):
    """Resume creation model with validation."""

    candidate_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Candidate full name"
    )

    candidate_email: EmailStr = Field(
        ...,
        description="Candidate email address"
    )

    candidate_phone: Optional[str] = Field(
        None,
        max_length=50,
        description="Candidate phone number"
    )

    experience_years: int = Field(
        ...,
        ge=0,
        le=50,
        description="Years of experience"
    )

    expected_salary: Optional[int] = Field(
        None,
        ge=0,
        le=10000000,
        description="Expected annual salary"
    )

    skills: List[str] = Field(
        default_factory=list,
        min_length=0,
        max_length=100,
        description="List of candidate skills"
    )

    @field_validator("candidate_phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format."""
        if v is None:
            return v

        # Remove common formatting
        cleaned = re.sub(r"[^\d+]", "", v)

        # Basic validation: 10-15 digits
        if not re.match(r"^\+?\d{10,15}$", cleaned):
            raise ValueError("Invalid phone number format")

        return cleaned

    @field_validator("skills")
    @classmethod
    def validate_skills(cls, v: List[str]) -> List[str]:
        """Validate and normalize skills."""
        # Remove duplicates
        unique_skills = list(set(v))

        # Normalize (trim, title case)
        normalized = [skill.strip().title() for skill in unique_skills]

        # Filter empty strings
        return [skill for skill in normalized if skill]


class VacancyCreate(BaseModel):
    """Vacancy creation model with validation."""

    title: str = Field(
        ...,
        min_length=5,
        max_length=255,
        description="Job title"
    )

    description: str = Field(
        ...,
        min_length=50,
        max_length=10000,
        description="Job description"
    )

    requirements: List[str] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Required skills/qualifications"
    )

    min_salary: Optional[int] = Field(
        None,
        ge=0,
        description="Minimum salary offer"
    )

    max_salary: Optional[int] = Field(
        None,
        ge=0,
        description="Maximum salary offer"
    )

    @field_validator("max_salary")
    @classmethod
    def validate_salary_range(cls, v: Optional[int], info) -> Optional[int]:
        """Validate salary range is logical."""
        if v is not None and info.data.get("min_salary") is not None:
            if v < info.data["min_salary"]:
                raise ValueError("max_salary must be >= min_salary")
        return v

    @field_validator("description")
    @classmethod
    def sanitize_description(cls, v: str) -> str:
        """Sanitize job description to prevent XSS."""
        # Strip HTML tags
        import html
        cleaned = html.escape(v)

        # Remove excessive whitespace
        cleaned = " ".join(cleaned.split())

        return cleaned
```

#### SQL Injection Prevention

The system uses SQLAlchemy ORM which provides protection against SQL injection through parameterized queries.

**✅ SAFE: Using ORM**:

```python
# Safe - SQLAlchemy ORM with parameterized queries
query = select(Resume).where(Resume.candidate_email == email)
result = await db.execute(query)
```

**❌ UNSAFE: Raw SQL with user input**:

```python
# NEVER DO THIS - SQL injection vulnerability
query = f"SELECT * FROM resumes WHERE email = '{user_input}'"
result = await db.execute(text(query))
```

**✅ SAFE: Raw SQL with parameters**:

```python
# Safe - Parameterized query
from sqlalchemy import text

query = text("SELECT * FROM resumes WHERE email = :email")
result = await db.execute(query, {"email": user_input})
```

#### XSS Prevention

Prevent Cross-Site Scripting by sanitizing user input and escaping output.

**Input Sanitization**:

```python
import html
import bleach

def sanitize_html(content: str, allow_tags: List[str] = None) -> str:
    """
    Sanitize HTML content to prevent XSS.

    Args:
        content: User-provided HTML content
        allow_tags: List of allowed HTML tags (default: none)

    Returns:
        Sanitized string
    """
    if allow_tags is None:
        # No HTML allowed - escape everything
        return html.escape(content)

    # Some HTML allowed - use bleach for sanitization
    return bleach.clean(
        content,
        tags=allow_tags,
        attributes={},
        strip=True
    )


# Usage
class FeedbackCreate(BaseModel):
    """Feedback creation with XSS prevention."""

    comments: str = Field(..., max_length=5000)

    @field_validator("comments")
    @classmethod
    def sanitize_comments(cls, v: str) -> str:
        """Sanitize user comments."""
        # Allow basic formatting but strip scripts/events
        return sanitize_html(v, allow_tags=["p", "br", "strong", "em"])
```

**Output Escaping**:

```python
# FastAPI's JSONResponse automatically escapes data
# But be careful with HTML responses

from fastapi.responses import HTMLResponse

@app.get("/api/resumes/{resume_id}", response_class=HTMLResponse)
async def resume_html(resume_id: int):
    """❌ UNSAFE: Direct HTML output without escaping."""
    resume = await get_resume(resume_id)
    return f"""
    <h1>{resume.candidate_name}</h1>
    <p>{resume.description}</p>
    """

# ✅ SAFE: Use template engine with auto-escaping
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

@app.get("/api/resumes/{resume_id}", response_class=HTMLResponse)
async def resume_html(request: Request, resume_id: int):
    """✅ SAFE: Template engine auto-escapes variables."""
    resume = await get_resume(resume_id)
    return templates.TemplateResponse(
        "resume.html",
        {"request": request, "resume": resume}
    )
```

### OWASP Top 10 Mitigations

Implement protections against the OWASP Top 10 web application security risks.

#### A01:2021 – Broken Access Control

**Risk**: Users can access or modify resources they shouldn't have access to.

**Mitigation**:

```python
# ✅ GOOD: Check ownership on every operation
@router.delete("/api/resumes/{resume_id}")
async def delete_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete resume - only by owner or admin."""
    resume = await get_resume(db, resume_id)

    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found")

    # Check ownership
    if resume.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to delete this resume"
        )

    await delete_resume(db, resume_id)
    return {"message": "Resume deleted"}


# ❌ BAD: No ownership check
@router.delete("/api/resumes/{resume_id}")
async def delete_resume(resume_id: int, db: AsyncSession = Depends(get_db)):
    """❌ BAD: Anyone can delete any resume!"""
    await delete_resume(db, resume_id)
    return {"message": "Resume deleted"}
```

#### A02:2021 – Cryptographic Failures

**Risk**: Sensitive data not encrypted or uses weak encryption.

**Mitigation**:

```python
# ✅ GOOD: Strong password hashing
from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Cost factor (higher = more secure but slower)
)

hashed_password = pwd_context.hash(user_password)


# ✅ GOOD: Encrypt data at rest
from cryptography.fernet import Fernet

# Generate and store key securely
key = Fernet.generate_key()
cipher = Fernet(key)

# Encrypt sensitive data
encrypted_data = cipher.encrypt(sensitive_info.encode())


# ✅ GOOD: Use TLS for data in transit
# Ensure DATABASE_URL uses sslmode=require
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require


# ❌ BAD: Weak encryption
# MD5, SHA1, DES are broken - never use them!
import hashlib
hashed = hashlib.md5(password.encode()).hexdigest()  # ❌ BROKEN
```

#### A03:2021 – Injection

**Risk**: Attacker can inject malicious code through user input.

**Mitigation** (see [Input Validation](#input-validation) section above).

#### A04:2021 – Insecure Design

**Risk**: Flaws in system architecture and design.

**Mitigation**:

```python
# ✅ GOOD: Implement rate limiting
@router.post("/api/auth/login")
@limiter.limit("5/minute")
async def login(credentials: LoginRequest):
    """Prevent brute force with rate limiting."""
    pass


# ✅ GOOD: Validate business logic
@router.post("/api/vacancies/{vacancy_id}/rank")
async def rank_candidate(
    vacancy_id: int,
    candidate_id: int,
    current_user: User = Depends(get_current_user)
):
    """Ensure user can rank for this vacancy."""
    # Check vacancy exists and is active
    vacancy = await get_vacancy(vacancy_id)
    if not vacancy or not vacancy.is_active:
        raise HTTPException(400, "Invalid vacancy")

    # Check candidate exists
    candidate = await get_candidate(candidate_id)
    if not candidate:
        raise HTTPException(404, "Candidate not found")

    # Check user has permission
    if not user_can_rank_for_vacancy(current_user, vacancy):
        raise HTTPException(403, "No permission")

    # Check for duplicate ranking
    existing = await get_existing_ranking(vacancy_id, candidate_id)
    if existing:
        raise HTTPException(400, "Already ranked")

    # Proceed with ranking
    return await create_ranking(vacancy_id, candidate_id)
```

#### A05:2021 – Security Misconfiguration

**Risk**: Default configurations, unpatched systems, verbose error messages.

**Mitigation**:

```python
# ✅ GOOD: Secure error messages
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Log detailed error, return generic message to user."""
    logger.error(f"Error: {exc}", exc_info=True)

    # ✅ GOOD: Generic message to user
    return JSONResponse(
        status_code=500,
        content={"error": "An error occurred. Please try again later."}
    )

# ❌ BAD: Expose internal details
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # ❌ BAD: Exposes stack trace to users!
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "traceback": traceback.format_exc()}
    )


# ✅ GOOD: Disable debug in production
DEBUG = False  # Set via environment variable

# ✅ GOOD: Secure defaults
class Settings(BaseSettings):
    # Use secure defaults
    cors_origins: str = Field(default="")  # Empty = no CORS by default
    allow_registration: bool = Field(default=False)  # Require explicit enable
    max_upload_size_mb: int = Field(default=10, ge=1, le=100)  # Reasonable limit
```

#### A06:2021 – Vulnerable and Outdated Components

**Risk**: Using libraries with known vulnerabilities.

**Mitigation**:

```bash
# Regular dependency updates
pip list --outdated

# Security scanning
pip-audit
safety check

# Automated scanning in CI/CD
- name: Run security scan
  run: |
    pip-audit
    safety check --continue-on-error
```

See [Dependency Management](#dependency-management) section for detailed guidance.

#### A07:2021 – Identification and Authentication Failures

**Risk**: Weak authentication, session management, password policies.

**Mitigation**: See [Authentication & Authorization](#authentication--authorization) section above.

#### A08:2021 – Software and Data Integrity Failures

**Risk**: Using untrusted sources, integrity verification missing.

**Mitigation**:

```bash
# ✅ GOOD: Verify package signatures
pip install --require-hashes -r requirements.txt

# ✅ GOOD: Pin dependency versions
# requirements.txt with exact versions
fastapi==0.104.1
uvicorn[standard]==0.24.0

# ✅ GOOD: Use package hashes
# requirements.txt
fastapi==0.104.1 \
    --hash=sha256:abc123...
uvicorn[standard]==0.24.0 \
    --hash=sha256:def456...


# ✅ GOOD: Subresource Integrity (SRI) for frontend
# <script src="https://cdn.example.com/library.js"
#   integrity="sha384-abc123def456..."
#   crossorigin="anonymous"></script>
```

#### A09:2021 – Security Logging and Monitoring Failures

**Risk**: Insufficient logging, missing monitoring, no incident response.

**Mitigation**:

```python
# ✅ GOOD: Comprehensive security logging
import logging

logger = logging.getLogger(__name__)

@router.post("/api/auth/login")
async def login(credentials: LoginRequest, request: Request):
    """Log login attempts for security monitoring."""

    # Log successful login
    logger.info(
        "login_success",
        extra={
            "user": credentials.email,
            "ip": request.client.host,
            "user_agent": request.headers.get("user-agent"),
            "timestamp": datetime.utcnow().isoformat()
        }
    )

    # Return token
    return {"token": "..."}


@router.post("/api/auth/login")
async def login(credentials: LoginRequest, request: Request):
    """Log failed login attempts."""

    # Log failed login
    logger.warning(
        "login_failed",
        extra={
            "email": credentials.email,
            "ip": request.client.host,
            "reason": "Invalid credentials",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

    raise HTTPException(401, "Invalid credentials")


# ✅ GOOD: Alert on suspicious activity
async def check_suspicious_activity(email: str, ip: str):
    """Check for suspicious login patterns."""
    recent_failures = await get_recent_login_failures(email, ip, minutes=5)

    if recent_failures >= 5:
        logger.critical(
            "brute_force_detected",
            extra={"email": email, "ip": ip, "failures": recent_failures}
        )

        # Send alert to security team
        await send_security_alert(
            f"Brute force attack detected from {ip} on {email}"
        )

        # Block IP
        await block_ip(ip, duration=timedelta(hours=1))
```

See [Logging & Monitoring Security](#logging--monitoring-security) section for detailed guidance.

#### A10:2021 – Server-Side Request Forgery (SSRF)

**Risk**: Application fetches remote resources without validation.

**Mitigation**:

```python
from urllib.parse import urlparse
import ipaddress

# ✅ GOOD: Validate and sanitize URLs
def is_safe_url(url: str) -> bool:
    """
    Check if URL is safe to fetch (prevent SSRF).

    Args:
        url: URL to validate

    Returns:
        True if URL is safe, False otherwise
    """
    try:
        parsed = urlparse(url)

        # Only allow HTTP/HTTPS
        if parsed.scheme not in ("http", "https"):
            return False

        # Resolve hostname to IP
        hostname = parsed.hostname
        if not hostname:
            return False

        # Block private/internal IPs
        import socket
        ips = socket.getaddrinfo(hostname, None)

        for ip in ips:
            addr = ipaddress.ip_address(ip[4][0])

            # Block private IPs
            if addr.is_private or addr.is_loopback or addr.is_link_local:
                return False

        # Block localhost
        if hostname in ("localhost", "127.0.0.1"):
            return False

        return True

    except:
        return False


# ✅ GOOD: Validate before fetching
@router.post("/api/fetch-url")
async def fetch_url(url: str):
    """Fetch URL with SSRF protection."""

    if not is_safe_url(url):
        logger.warning(f"ssrf_attempt_blocked", extra={"url": url})
        raise HTTPException(400, "Invalid URL")

    # Safe to fetch
    response = await httpx.AsyncClient().get(url)
    return response.json()


# ❌ BAD: No validation
@router.post("/api/fetch-url")
async def fetch_url(url: str):
    """❌ BAD: Allows SSRF attacks!"""
    response = await httpx.AsyncClient().get(url)  # What if url = "http://localhost:6379/"?
    return response.json()
```

### API Security Checklist

#### Rate Limiting

- [ ] Rate limiting enabled on all endpoints
- [ ] Stricter limits for expensive operations (analysis, file upload)
- [ ] Rate limits use Redis for distributed systems
- [ ] Rate limit headers included in responses
- [ ] Per-user rate limiting implemented
- [ ] API key rate limiting configured
- [ ] Rate limit alerts configured

#### CORS Configuration

- [ ] CORS origins restricted to specific domains
- [ ] Wildcard (*) not used in production
- [ ] Credentials handled securely
- [ ] Preflight cache configured appropriately
- [ ] CORS headers minimized
- [ ] OPTIONS requests handled correctly

#### Input Validation

- [ ] All endpoints use Pydantic models
- [ ] String length limits enforced
- [ ] Numeric range validation implemented
- [ ] Email validation using EmailStr
- [ ] Custom validators for business logic
- [ ] File type validation (magic numbers)
- [ ] XSS prevention (HTML sanitization)
- [ ] SQL injection prevention (parameterized queries)
- [ ] Command injection prevention
- [ ] Path traversal prevention

#### Output Security

- [ ] Error messages don't leak sensitive information
- [ ] Stack traces not exposed to users
- [ ] HTML output escaped (templates)
- [ ] JSON responses don't include internal fields
- [ ] Pagination prevents large responses
- [ ] Sensitive data filtered from logs

#### OWASP Top 10

- [ ] A01: Access control implemented
- [ ] A02: Strong encryption used
- [ ] A03: Injection prevented
- [ ] A04: Secure design patterns
- [ ] A05: Secure configuration
- [ ] A06: Dependencies updated
- [ ] A07: Strong authentication
- [ ] A08: Code integrity verified
- [ ] A09: Security logging enabled
- [ ] A10: SSRF protection implemented

#### Additional Security Measures

- [ ] API versioning implemented
- [ ] Deprecation policy documented
- [ ] Webhook signature verification
- [ ] Request ID tracking for debugging
- [ ] Security headers configured
- [ ] API documentation (secured/authenticated)
- [ ] Penetration testing completed

---

## Data Security & Encryption

Protecting sensitive candidate and hiring data through encryption and secure data handling practices is critical for compliance and trust.

### Data Classification

Classify data based on sensitivity to apply appropriate security controls.

| Classification | Data Types | Storage Requirements | Transmission Requirements |
|----------------|------------|---------------------|---------------------------|
| **Critical** | SSN, passport numbers, financial data | Encryption at rest required, strict access control | TLS 1.3, end-to-end encryption |
| **Sensitive** | PII (names, emails, phones), resumes | Encryption at rest recommended | TLS 1.2+, secure protocols |
| **Internal** | Ranking algorithms, business logic | Access controlled | TLS recommended |
| **Public** | Marketing content, public job postings | Standard security | HTTPS required |

### Encryption at Rest

Protect data stored in databases, file systems, and backups.

#### Database Encryption

**PostgreSQL SSL/TLS**:

```bash
# DATABASE_URL with SSL requirement
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require

# Or verify certificate
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=verify-full&sslrootcert=/path/to/ca.crt
```

**Application-Level Encryption** (for highly sensitive fields):

```python
from cryptography.fernet import Fernet
import base64
import os
from typing import Any

class FieldEncryption:
    """
    Encrypt/decrypt sensitive fields at application level.

    Use for: SSN, financial data, sensitive PII that needs extra protection.
    """

    def __init__(self, key: str = None):
        """
        Initialize encryption with key.

        Args:
            key: 32-byte URL-safe base64-encoded key.
                 If None, reads from FIELD_ENCRYPTION_KEY env variable.
        """
        if key is None:
            key = os.getenv("FIELD_ENCRYPTION_KEY")
            if not key:
                raise ValueError("FIELD_ENCRYPTION_KEY environment variable not set")

        # Ensure key is properly formatted
        if len(key) != 44:  # Fernet keys are 44 chars (base64 of 32 bytes)
            raise ValueError("Invalid encryption key length")

        self.cipher = Fernet(key.encode())

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext string.

        Args:
            plaintext: String to encrypt

        Returns:
            Base64-encoded encrypted string
        """
        if plaintext is None:
            return None

        encrypted = self.cipher.encrypt(plaintext.encode())
        return base64.urlsafe_b64encode(encrypted).decode()

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt ciphertext string.

        Args:
            ciphertext: Base64-encoded encrypted string

        Returns:
            Decrypted plaintext string
        """
        if ciphertext is None:
            return None

        encrypted = base64.urlsafe_b64decode(ciphertext.encode())
        decrypted = self.cipher.decrypt(encrypted)
        return decrypted.decode()


# Usage in models
field_encryptor = FieldEncryption()

# Encrypting before storage
candidate.ssn_encrypted = field_encryptor.encrypt(candidate_ssn)

# Decrypting after retrieval
candidate_ssn = field_encryptor.decrypt(candidate.ssn_encrypted)
```

**Generate Encryption Key**:

```bash
# Generate Fernet-compatible key (44 characters)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Set as environment variable
export FIELD_ENCRYPTION_KEY="<generated-key>"

# Add to .env.production
echo "FIELD_ENCRYPTION_KEY=<generated-key>" >> .env.production
```

**Column-Level Encryption with pgcrypto**:

```sql
-- Install extension
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Encrypt sensitive data
INSERT INTO candidates (name, ssn_encrypted)
VALUES (
    'John Doe',
    pgp_sym_encrypt('123-45-6789', 'encryption-key')
);

-- Decrypt when needed
SELECT
    name,
    pgp_sym_decrypt(ssn_encrypted::bytea, 'encryption-key') AS ssn
FROM candidates;
```

#### File Storage Encryption

**Resume File Encryption**:

```python
import os
from pathlib import Path
from cryptography.fernet import Fernet

class EncryptedFileStorage:
    """
    Handle encrypted storage of uploaded resumes.

    Files are encrypted before storage and decrypted on retrieval.
    """

    def __init__(self, storage_path: str, encryption_key: str):
        """
        Initialize encrypted file storage.

        Args:
            storage_path: Base path for encrypted file storage
            encryption_key: Fernet encryption key
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.cipher = Fernet(encryption_key)

    def save_encrypted(self, file_content: bytes, filename: str) -> str:
        """
        Encrypt and save file.

        Args:
            file_content: Raw file content
            filename: Original filename

        Returns:
            Path to encrypted file
        """
        # Encrypt content
        encrypted_content = self.cipher.encrypt(file_content)

        # Generate unique filename
        import secrets
        unique_name = f"{secrets.token_hex(16)}_{filename}"
        file_path = self.storage_path / unique_name

        # Save encrypted content
        with open(file_path, 'wb') as f:
            f.write(encrypted_content)

        return str(file_path)

    def read_encrypted(self, file_path: str) -> bytes:
        """
        Read and decrypt file.

        Args:
            file_path: Path to encrypted file

        Returns:
            Decrypted file content
        """
        with open(file_path, 'rb') as f:
            encrypted_content = f.read()

        return self.cipher.decrypt(encrypted_content)
```

#### Backup Encryption

**Automated Encrypted Backups**:

```bash
#!/bin/bash
# backup_database.sh - Encrypted database backup script

# Configuration
BACKUP_DIR="/backups/postgres"
ENCRYPTION_KEY_FILE="/secure/backup_key.txt"
RETENTION_DAYS=30

# Generate backup filename with timestamp
BACKUP_FILE="$BACKUP_DIR/db_backup_$(date +%Y%m%d_%H%M%S).sql.gz.gpg"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Dump, compress, and encrypt database
pg_dump "$DATABASE_URL" | \
    gzip | \
    gpg --cipher-algo AES256 --compress-algo 1 --symmetric \
        --batch --passphrase-file "$ENCRYPTION_KEY_FILE" \
        --output "$BACKUP_FILE"

# Set file permissions
chmod 600 "$BACKUP_FILE"

# Delete old backups
find "$BACKUP_DIR" -name "db_backup_*.sql.gz.gpg" -mtime +$RETENTION_DAYS -delete

echo "Backup completed: $BACKUP_FILE"
```

**Restore from Encrypted Backup**:

```bash
# Decrypt and restore
gpg --decrypt --batch --passphrase-file /secure/backup_key.txt \
    /backups/postgres/db_backup_20260204_120000.sql.gz.gpg | \
    gunzip | \
    psql "$DATABASE_URL"
```

### Encryption in Transit

Protect data as it travels between services and clients.

#### TLS/SSL Configuration

**Backend API (FastAPI/Uvicorn)**:

```bash
# Generate self-signed certificate for development
openssl req -x509 -newkey rsa:4096 -nodes \
    -keyout key.pem -out cert.pem -days 365 \
    -subj "/CN=localhost"

# Run with TLS
uvicorn main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --ssl-keyfile key.pem \
    --ssl-certfile cert.pem
```

**Production Certificate (Let's Encrypt)**:

```bash
# Install certbot
apt-get install certbot

# Generate certificate
certbot certonly --standalone -d api.agenthr.com

# Paths to certificates
cert.pem = /etc/letsencrypt/live/api.agenthr.com/fullchain.pem
key.pem = /etc/letsencrypt/live/api.agenthr.com/privkey.pem
```

**Docker Compose with TLS**:

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    image: agenthr-backend:latest
    ports:
      - "443:8000"
    volumes:
      - ./certs:/certs:ro
    command: >
      uvicorn main:app
      --host 0.0.0.0
      --port 8000
      --ssl-keyfile /certs/key.pem
      --ssl-certfile /certs/cert.pem
```

#### Database Connection Security

**Require SSL for PostgreSQL**:

```python
# config.py
DATABASE_URL: str = Field(
    default="postgresql://user:pass@localhost:5432/db",
    description="PostgreSQL connection URL"
)

@field_validator("DATABASE_URL")
@classmethod
def require_ssl_in_production(cls, v: str, info) -> str:
    """Ensure SSL is enabled in production."""
    settings = info.data
    if settings.environment == "production" and "sslmode" not in v:
        logger.warning("SSL not enabled for DATABASE_URL in production")
        # Force SSL mode
        if "?" in v:
            v += "&sslmode=require"
        else:
            v += "?sslmode=require"
    return v
```

**Verify SSL Certificates**:

```bash
# In production, verify certificates
DATABASE_URL="postgresql://user:pass@host:5432/db?sslmode=verify-full&sslrootcert=/path/to/ca.crt"
```

#### Redis TLS

**Enable Redis TLS**:

```python
# config.py
REDIS_URL: str = Field(
    default="redis://localhost:6379/0",
    description="Redis connection URL"
)

# For production with TLS
# redis_url: str = "rediss://localhost:6379/0?ssl_cert_reqs=required"
```

**Redis TLS Configuration**:

```yaml
# docker-compose.yml
services:
  redis:
    image: redis:7-alpine
    command: >
      redis-server
      --tls-port 6379
      --port 0
      --tls-cert-file /etc/redis/tls/redis.crt
      --tls-key-file /etc/redis/tls/redis.key
      --tls-ca-cert-file /etc/redis/tls/ca.crt
      --tls-auth-clients no
    volumes:
      - ./redis-tls:/etc/redis/tls:ro
```

### PII Data Handling

Special handling for Personally Identifiable Information (PII).

#### PII Detection

```python
import re
from typing import List, Dict

class PIIDetector:
    """
    Detect PII in text data for proper handling.
    """

    # PII patterns
    PATTERNS = {
        "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "phone": r'\b\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
        "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
        "credit_card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
        "ip_address": r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
        "passport": r'\b[A-Z]{1,2}\d{6,9}\b',
    }

    @classmethod
    def detect_pii(cls, text: str) -> Dict[str, List[str]]:
        """
        Detect PII in text.

        Args:
            text: Text to scan for PII

        Returns:
            Dictionary of PII type to list of matches
        """
        findings = {}

        for pii_type, pattern in cls.PATTERNS.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                findings[pii_type] = matches

        return findings

    @classmethod
    def contains_pii(cls, text: str) -> bool:
        """
        Check if text contains any PII.

        Args:
            text: Text to check

        Returns:
            True if PII detected, False otherwise
        """
        findings = cls.detect_pii(text)
        return len(findings) > 0

    @classmethod
    def redact_pii(cls, text: str, replacement: str = "[REDACTED]") -> str:
        """
        Redact PII from text.

        Args:
            text: Text to redact
            replacement: Replacement string

        Returns:
            Text with PII redacted
        """
        for pattern in cls.PATTERNS.values():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        return text
```

#### PII Data Minimization

```python
from pydantic import BaseModel, Field
from typing import Optional

class CandidatePII(BaseModel):
    """
    Candidate PII model with data minimization.
    Only collect and store necessary PII.
    """

    # Required PII
    full_name: str = Field(..., max_length=255)
    email: str = Field(..., max_length=255)

    # Optional PII - only collect if needed
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)

    # Avoid collecting SSN unless absolutely necessary
    ssn: Optional[str] = Field(None, max_length=11)  # Encrypted if collected

    # Consider using tokenized IDs instead of PII
    candidate_token: str = Field(..., description="Unique token for anonymous identification")


class PublicCandidateView(BaseModel):
    """
    Public view with minimal PII exposure.
    Used for APIs that don't need full PII.
    """

    id: int
    initials: str  # Only initials, not full name
    candidate_token: str  # Anonymous token
    skills_summary: list[str]
    experience_years: int
    # No email, phone, or other identifying information
```

#### Data Retention Policy

```python
from datetime import datetime, timedelta
from sqlalchemy import delete

class DataRetentionPolicy:
    """
    Implement data retention policies for compliance.
    """

    # Retention periods
    RESUME_RETENTION_YEARS = 7
    APPLICATION_RETENTION_YEARS = 3
    LOG_RETENTION_DAYS = 90

    @staticmethod
    async def delete_old_resumes(db: AsyncSession):
        """
        Delete resumes older than retention period.

        Args:
            db: Database session
        """
        cutoff_date = datetime.utcnow() - timedelta(
            years=DataRetentionPolicy.RESUME_RETENTION_YEARS
        )

        # Soft delete (mark as deleted)
        await db.execute(
            update(Resume)
            .where(Resume.created_at < cutoff_date)
            .values(deleted_at=datetime.utcnow(), is_deleted=True)
        )
        await db.commit()

    @staticmethod
    async def purge_soft_deleted(db: AsyncSession):
        """
        Permanently delete soft-deleted records older than grace period.

        Args:
            db: Database session
        """
        grace_period = datetime.utcnow() - timedelta(days=30)

        # Hard delete soft-deleted records
        await db.execute(
            delete(Resume)
            .where(Resume.deleted_at < grace_period)
        )
        await db.commit()

    @staticmethod
    async def anonymize_old_applications(db: AsyncSession):
        """
        Anonymize old application data (keep analytics, remove PII).

        Args:
            db: Database session
        """
        cutoff_date = datetime.utcnow() - timedelta(
            years=DataRetentionPolicy.APPLICATION_RETENTION_YEARS
        )

        # Replace PII with anonymized data
        await db.execute(
            update(Application)
            .where(Application.created_at < cutoff_date)
            .values(
                candidate_name="[ANONYMIZED]",
                candidate_email=f"anon-{Application.id}@anonymous.local",
                candidate_phone=None
            )
        )
        await db.commit()
```

### Data Masking for Development

Never use real PII in development environments.

```python
from faker import Faker
import random

class DataMasker:
    """
    Mask/anonymize PII for development environments.
    """

    fake = Faker()

    @classmethod
    def mask_email(cls, email: str) -> str:
        """Mask email address."""
        username, domain = email.split("@")
        return f"{username[:3]}***@{domain}"

    @classmethod
    def mask_phone(cls, phone: str) -> str:
        """Mask phone number."""
        return f"***-***-{phone[-4:]}"

    @classmethod
    def mask_name(cls, name: str) -> str:
        """Mask person's name."""
        parts = name.split()
        if len(parts) == 2:
            return f"{parts[0][0]}. {parts[1]}"
        return "***"

    @classmethod
    def anonymize_database_dump(cls, input_file: str, output_file: str):
        """
        Anonymize a database dump for development use.

        Args:
            input_file: Path to SQL dump file
            output_file: Path to anonymized dump file
        """
        with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
            for line in infile:
                # Replace emails
                line = re.sub(
                    r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}',
                    lambda m: cls.fake.email(),
                    line
                )

                # Replace names
                line = re.sub(
                    r"'([A-Z][a-z]+ [A-Z][a-z]+)'",
                    lambda m: f"'{cls.fake.name()}'",
                    line
                )

                # Replace phone numbers
                line = re.sub(
                    r'\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
                    lambda m: cls.fake.phone_number(),
                    line
                )

                outfile.write(line)
```

### Secure Data Destruction

Permanently delete sensitive data when no longer needed.

```python
import os
import random

class SecureDataDestructor:
    """
    Securely delete sensitive data from disk and database.
    """

    @staticmethod
    def secure_file_delete(file_path: str, passes: int = 3):
        """
        Securely delete file by overwriting multiple times.

        Args:
            file_path: Path to file to delete
            passes: Number of overwrite passes
        """
        file_size = os.path.getsize(file_path)

        with open(file_path, 'r+b') as f:
            for pass_num in range(passes):
                # Overwrite with random data
                f.seek(0)
                f.write(os.urandom(file_size))
                f.flush()
                os.fsync(f.fileno())

                # Overwrite with zeros
                f.seek(0)
                f.write(b'\x00' * file_size)
                f.flush()
                os.fsync(f.fileno())

        # Finally remove the file
        os.remove(file_path)

    @staticmethod
    async def secure_pii_deletion(record_id: int, db: AsyncSession):
        """
        Securely delete PII record and associated files.

        Args:
            record_id: ID of record to delete
            db: Database session
        """
        # Get record
        resume = await db.get(Resume, record_id)
        if not resume:
            return

        # Delete associated files securely
        if resume.file_path:
            SecureDataDestructor.secure_file_delete(resume.file_path)

        # Overwrite sensitive fields in database before deletion
        resume.candidate_name = "DELETED"
        resume.candidate_email = f"deleted-{resume.id}@deleted.local"
        resume.candidate_phone = None
        await db.commit()

        # Finally delete record
        await db.delete(resume)
        await db.commit()

        # Log the deletion
        logger.info(f"Securely deleted resume {record_id}")
```

### Data Security Checklist

#### Encryption at Rest

- [ ] Database uses SSL/TLS for connections
- [ ] Sensitive PII fields encrypted at application level
- [ ] File storage encrypted (or filesystem encryption enabled)
- [ ] Backups encrypted before storage
- [ ] Encryption keys stored securely (not in code)
- [ ] Key rotation policy implemented
- [ ] Multiple encryption keys for different data types

#### Encryption in Transit

- [ ] TLS 1.2+ enforced for all services
- [ ] HTTP redirected to HTTPS
- [ ] Certificate expiration monitored
- [ ] Certificate auto-renewal configured
- [ ] HSTS header enabled
- [ ] Strong cipher suites only
- [ ] Certificate pinning for mobile apps (if applicable)

#### PII Handling

- [ ] PII inventory maintained
- [ ] PII detection implemented
- [ ] Data minimization practiced (collect only necessary data)
- [ ] Data classification implemented
- [ ] PII access logged and audited
- [ ] Right to erasure implemented (GDPR)
- [ ] Data portability implemented (GDPR)
- [ ] Consent management implemented
- [ ] PII masked in development environment

#### Data Retention

- [ ] Retention policy documented
- [ ] Auto-deletion of expired data implemented
- [ ] Soft delete before hard delete
- [ ] Backup retention policy defined
- [ ] Log retention policy defined (90 days recommended)
- [ ] Legal holds process defined

#### Data Destruction

- [ ] Secure file deletion implemented
- [ ] Database records anonymized before deletion
- [ ] Certificate/key revocation process
- [ ] Backup destruction process
- [ ] Destruction audit trail

---

## File Upload Security

File uploads are a critical attack vector. The security scan identified several areas requiring attention.

### Current Security Posture

**✅ Implemented**:
- File type validation by extension
- MIME type validation
- File size limits enforced (10MB default)
- Unique filename generation with random bytes
- Files stored outside web root
- Path traversal prevention (using `Path(file.filename).name`)

**⚠️ Needs Implementation**:
- Magic number validation (file header checking)
- Malware/virus scanning
- Rate limiting on upload endpoint
- File content sanitization (for PDF/DOCX)
- Upload quota per user
- Encryption of uploaded files at rest

### Threat Model

#### File Upload Attack Vectors

| Attack Type | Description | Impact | Mitigation |
|-------------|-------------|--------|------------|
| **Malware Upload** | Upload executable malware or infected documents | Server compromise, data breach, ransomware | Magic number validation, malware scanning, sandboxed processing |
| **Path Traversal** | Upload files to arbitrary directories | Server configuration overwrite, system compromise | Strip directory paths, validate filenames |
| **DoS via Upload** | Upload massive files or file bomb | Storage exhaustion, service disruption | File size limits, per-user quotas, rate limiting |
| **File Type Spoofing** | Rename malicious file as valid type | Bypass file type checks | Magic number validation, MIME verification |
| **XSS via File Content** | Upload HTML/JS files with malicious scripts | Execute malicious code in victim's browser | Content-Type validation, Content-Disposition headers |
| **XXE via XML Upload** | Upload XML with external entity references | Server-side request forgery, data exfiltration | Disable XML external entities, validate XML |

### Comprehensive File Upload Security

#### Implementation: Secure File Upload Handler

`backend/api/upload.py`:

```python
import os
import magic
import hashlib
from pathlib import Path
from typing import Optional
from fastapi import UploadFile, HTTPException, status
import aiofiles
import clamav
import logging

logger = logging.getLogger(__name__)

# Allowed file types and their magic numbers
ALLOWED_FILE_TYPES = {
    "application/pdf": {
        "extensions": [".pdf"],
        "magic_numbers": [b"%PDF-"],
        "max_size_mb": 10
    },
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": {
        "extensions": [".docx"],
        "magic_numbers": [b"PK\x03\x04"],  # DOCX is a ZIP file
        "max_size_mb": 10
    },
    "application/msword": {
        "extensions": [".doc"],
        "magic_numbers": [b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"],  # OLE2 format
        "max_size_mb": 10
    },
    "text/plain": {
        "extensions": [".txt"],
        "magic_numbers": None,  # No specific magic number for text
        "max_size_mb": 1
    },
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {
        "extensions": [".xlsx"],
        "magic_numbers": [b"PK\x03\x04"],
        "max_size_mb": 5
    }
}

# Dangerous file extensions to always block
BLOCKED_EXTENSIONS = {
    ".exe", ".bat", ".cmd", ".com", ".scr", ".pif", ".msi", ".dll",
    ".vbs", ".vbe", ".js", ".jse", ".ws", ".wsf", ".wsc", ".wsh",
    ".ps1", ".ps1xml", ".ps2", ".ps2xml", ".psc1", ".psc2",
    ".msh", ".msh1", ".msh2", ".mshxml", ".msh1xml", ".msh2xml",
    ".scf", ".lnk", ".inf", ".reg", ".docm", ".dotm", ".xlsm",
    ".xltm", ".xlam", ".pptm", ".potm", ".ppam", ".ppsm", ".sldm"
}


class SecureFileUploader:
    """
    Secure file upload handler with comprehensive validation.
    """

    def __init__(
        self,
        upload_dir: str,
        max_file_size_mb: int = 10,
        enable_malware_scan: bool = True,
        clamav_host: str = "localhost:3310"
    ):
        """
        Initialize secure file uploader.

        Args:
            upload_dir: Directory for uploaded files (outside web root)
            max_file_size_mb: Maximum file size in MB
            enable_malware_scan: Enable ClamAV malware scanning
            clamav_host: ClamAV scanner host:port
        """
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.max_file_size = max_file_size_mb * 1024 * 1024
        self.enable_malware_scan = enable_malware_scan
        self.clamav_host = clamav_host

    async def validate_and_upload(
        self,
        file: UploadFile,
        user_id: int
    ) -> dict:
        """
        Validate and securely upload a file.

        Args:
            file: FastAPI UploadFile object
            user_id: ID of user uploading the file

        Returns:
            Dictionary with file metadata

        Raises:
            HTTPException: If validation fails
        """
        # 1. Check file size
        await self._validate_file_size(file)

        # 2. Validate filename
        self._validate_filename(file.filename)

        # 3. Read file content
        file_content = await file.read()

        # 4. Validate magic numbers
        declared_mime_type = file.content_type or "application/octet-stream"
        await self._validate_magic_numbers(file_content, declared_mime_type)

        # 5. Scan for malware
        if self.enable_malware_scan:
            await self._scan_for_malware(file_content)

        # 6. Generate secure filename
        secure_filename = self._generate_secure_filename(file.filename, user_id)

        # 7. Save file
        file_path = self.upload_dir / secure_filename
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_content)

        # 8. Set secure permissions
        os.chmod(file_path, 0o644)

        # 9. Calculate file hash for integrity checking
        file_hash = hashlib.sha256(file_content).hexdigest()

        logger.info(
            f"File uploaded successfully",
            extra={
                "user_id": user_id,
                "filename": secure_filename,
                "original_filename": file.filename,
                "size": len(file_content),
                "hash": file_hash
            }
        )

        return {
            "filename": secure_filename,
            "original_filename": file.filename,
            "file_path": str(file_path),
            "file_size": len(file_content),
            "content_type": declared_mime_type,
            "file_hash": file_hash
        }

    async def _validate_file_size(self, file: UploadFile):
        """
        Validate file size is within limits.

        Args:
            file: UploadFile to validate

        Raises:
            HTTPException: If file too large
        """
        # Get file size
        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)  # Reset pointer

        if file_size > self.max_file_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size {file_size} bytes exceeds maximum {self.max_file_size} bytes"
            )

        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty"
            )

    def _validate_filename(self, filename: str):
        """
        Validate filename is safe.

        Args:
            filename: Original filename

        Raises:
            HTTPException: If filename is suspicious
        """
        if not filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required"
            )

        # Check for path traversal
        if ".." in filename or "/" in filename or "\\" in filename:
            logger.warning(f"Path traversal attempt blocked: {filename}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename"
            )

        # Check for blocked extensions
        file_ext = Path(filename).suffix.lower()
        if file_ext in BLOCKED_EXTENSIONS:
            logger.warning(f"Blocked file extension: {file_ext}")
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"File type {file_ext} is not allowed"
            )

        # Check for suspicious characters
        if any(char in filename for char in ['\x00', '\n', '\r']):
            logger.warning(f"Suspicious characters in filename: {filename}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename"
            )

    async def _validate_magic_numbers(
        self,
        file_content: bytes,
        declared_mime_type: str
    ):
        """
        Validate file content using magic numbers.

        Args:
            file_content: File content as bytes
            declared_mime_type: MIME type declared by client

        Raises:
            HTTPException: If magic numbers don't match declared type
        """
        # Get declared file type config
        file_config = ALLOWED_FILE_TYPES.get(declared_mime_type)
        if not file_config:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"File type {declared_mime_type} is not allowed"
            )

        # Check magic numbers if defined for this type
        if file_config["magic_numbers"]:
            header = file_content[:8]  # Read first 8 bytes

            magic_match = any(
                header.startswith(magic)
                for magic in file_config["magic_numbers"]
            )

            if not magic_match:
                logger.warning(
                    f"Magic number mismatch for {declared_mime_type}",
                    extra={"header": header.hex()}
                )
                raise HTTPException(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    detail=f"File content does not match declared type {declared_mime_type}"
                )

    async def _scan_for_malware(self, file_content: bytes):
        """
        Scan file content for malware using ClamAV.

        Args:
            file_content: File content as bytes

        Raises:
            HTTPException: If malware detected
        """
        try:
            # Import clamd module
            import pyclamd

            # Initialize ClamAV scanner
            cd = pyclamd.ClamdUnixSocket()
            if not cd.ping():
                # Try TCP socket
                cd = pyclamd.ClamdNetworkSocket(self.clamav_host.split(":")[0],
                                                 int(self.clamav_host.split(":")[1]))
                if not cd.ping():
                    logger.error("ClamAV scanner not accessible")
                    if self.enable_malware_scan:
                        raise HTTPException(
                            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="Malware scanner unavailable"
                        )
                    return

            # Scan file
            result = cd.scan_stream(file_content)

            if result and 'FOUND' in str(result):
                logger.critical(
                    f"Malware detected in upload",
                    extra={"scan_result": result}
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Malware detected in uploaded file"
                )

            logger.info(f"Malware scan passed")

        except ImportError:
            logger.warning("pyclamd not installed - skipping malware scan")
        except Exception as e:
            logger.error(f"Malware scan error: {e}")
            if self.enable_malware_scan:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Malware scanner error"
                )

    def _generate_secure_filename(self, original_filename: str, user_id: int) -> str:
        """
        Generate a secure, unique filename.

        Args:
            original_filename: Original filename
            user_id: ID of user uploading

        Returns:
            Secure filename
        """
        # Get file extension
        file_ext = Path(original_filename).suffix.lower()

        # Generate unique components
        import secrets
        import time

        timestamp = int(time.time())
        random_bytes = secrets.token_hex(8)

        # Construct secure filename
        # Format: user_id-timestamp-random.extension
        secure_filename = f"{user_id}-{timestamp}-{random_bytes}{file_ext}"

        return secure_filename


# Initialize uploader instance
file_uploader = SecureFileUploader(
    upload_dir="/var/uploads/resumes",
    max_file_size_mb=10,
    enable_malware_scan=True  # Disable in development
)
```

#### Usage in FastAPI Endpoint

`backend/api/routes/resumes.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from api.upload import SecureFileUploader, file_uploader
from database import get_db

router = APIRouter(prefix="/api/resumes", tags=["resumes"])


@router.post("/upload")
async def upload_resume(
    file: UploadFile,
    user_id: int,  # From authentication when implemented
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a resume file with comprehensive security validation.

    Security checks:
    - File size validation
    - Filename validation (path traversal prevention)
    - Magic number validation
    - Malware scanning
    - Secure filename generation
    """
    try:
        # Upload file with all security checks
        file_metadata = await file_uploader.validate_and_upload(file, user_id)

        # Create database record
        resume = Resume(
            candidate_name="",  # Extract from file content
            file_path=file_metadata["file_path"],
            file_hash=file_metadata["file_hash"],
            uploaded_by=user_id
        )
        db.add(resume)
        await db.commit()
        await db.refresh(resume)

        return {
            "id": resume.id,
            "filename": file_metadata["filename"],
            "size": file_metadata["file_size"],
            "status": "uploaded"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File upload failed"
        )
```

### Malware Scanning Implementation

#### ClamAV Setup

**Docker Compose with ClamAV**:

```yaml
# docker-compose.yml
version: '3.8'

services:
  clamav:
    image: clamav/clamav:latest
    ports:
      - "3310:3310"
    volumes:
      - clamav_db:/var/lib/clamav
    environment:
      - CLAMAV_NO_MILTERD=true

  backend:
    image: agenthr-backend:latest
    depends_on:
      - clamav
    environment:
      - CLAMAV_HOST=clamav:3310
      - ENABLE_MALWARE_SCAN=true

volumes:
  clamav_db:
```

**Update ClamAV Signatures**:

```bash
# In clamav container
docker-compose exec clamav freshclam

# Or run periodically via cron
echo "0 */6 * * * docker-compose exec -T clamav freshclam" | crontab -
```

**Python ClamAV Client**:

```python
# backend/requirements.txt
pyclamd==0.1.5  # ClamAV Python client
```

#### Alternative: Cloud-Based Malware Scanning

**AWS Lambda + Amazon GuardDuty**:

```python
import boto3

class AWSSecurityScanner:
    """Use AWS services for malware scanning."""

    def __init__(self):
        self.lambda_client = boto3.client('lambda')

    async def scan_file(self, file_content: bytes, filename: str) -> dict:
        """
        Scan file using AWS Lambda with GuardDuty integration.

        Args:
            file_content: File content
            filename: Filename

        Returns:
            Scan results
        """
        # Invoke Lambda function for scanning
        response = self.lambda_client.invoke(
            FunctionName='malware-scanner',
            Payload=json.dumps({
                'file_content': base64.b64encode(file_content).decode(),
                'filename': filename
            })
        )

        result = json.loads(response['Payload'].read())

        if result.get('threat_found'):
            raise HTTPException(400, "Malware detected")

        return result
```

### File Content Sanitization

Sanitize document content to remove embedded threats.

#### PDF Sanitization

```python
import PyPDF2
from io import BytesIO

class PDFSanitizer:
    """Sanitize PDF files to remove embedded threats."""

    @staticmethod
    async def sanitize_pdf(pdf_content: bytes) -> bytes:
        """
        Sanitize PDF by removing JavaScript and embedded files.

        Args:
            pdf_content: Raw PDF content

        Returns:
            Sanitized PDF content
        """
        try:
            pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_content))
            pdf_writer = PyPDF2.PdfWriter()

            # Copy pages without embedded files or JavaScript
            for page in pdf_reader.pages:
                pdf_writer.add_page(page)

            # Remove metadata
            pdf_writer.add_metadata({})

            # Remove embedded files (if any)
            if hasattr(pdf_reader, '/EmbeddedFiles'):
                del pdf_writer._root_object['/EmbeddedFiles']

            # Write sanitized PDF
            output = BytesIO()
            pdf_writer.write(output)
            return output.getvalue()

        except Exception as e:
            logger.error(f"PDF sanitization error: {e}")
            # If sanitization fails, reject file
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not sanitize PDF file"
            )
```

#### DOCX Sanitization

```python
from docx import Document
import zipfile

class DOCXSanitizer:
    """Sanitize DOCX files to remove macros and embedded threats."""

    @staticmethod
    async def sanitize_docx(docx_content: bytes) -> bytes:
        """
        Sanitize DOCX by removing macros and embedded objects.

        Args:
            docx_content: Raw DOCX content

        Returns:
            Sanitized DOCX content
        """
        try:
            # DOCX is a ZIP file
            with zipfile.ZipFile(BytesIO(docx_content), 'r') as zip_ref:
                # Check for macros (vbaProject.bin)
                if 'word/vbaProject.bin' in zip_ref.namelist():
                    logger.warning("Macro detected in DOCX file")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Macros are not allowed in uploaded documents"
                    )

                # Check for embedded objects
                embedded = [f for f in zip_ref.namelist() if 'oleObject' in f.lower()]
                if embedded:
                    logger.warning(f"Embedded objects found: {embedded}")
                    # Option: Remove or reject
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Embedded objects are not allowed"
                    )

            # If safe, use python-docx to further sanitize
            doc = Document(BytesIO(docx_content))

            # Remove any existing macros
            if doc.core_properties and hasattr(doc.core_properties, 'digital_signature'):
                doc.core_properties.digital_signature = None

            # Save sanitized document
            output = BytesIO()
            doc.save(output)
            return output.getvalue()

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"DOCX sanitization error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not sanitize DOCX file"
            )
```

### Rate Limiting for Uploads

Prevent abuse through rate-limited file uploads.

```python
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request

limiter = Limiter(key_func=get_remote_address)


@router.post("/upload")
@limiter.limit("10/hour")  # 10 uploads per hour per IP
async def upload_resume(
    request: Request,
    file: UploadFile,
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Upload endpoint with rate limiting."""
    # ... upload logic ...


# Stricter limit for unauthenticated users (when auth is implemented)
@router.post("/upload/public")
@limiter.limit("3/hour")  # Only 3 uploads per hour for anonymous
async def public_upload(
    request: Request,
    file: UploadFile,
    db: AsyncSession = Depends(get_db)
):
    """Public upload with stricter rate limit."""
    # ... upload logic ...
```

### User Upload Quotas

Implement per-user upload quotas to prevent storage exhaustion.

```python
from datetime import datetime, timedelta

class UploadQuotaManager:
    """Manage user upload quotas."""

    def __init__(self, daily_limit_mb: int = 100, monthly_limit_mb: int = 1000):
        self.daily_limit = daily_limit_mb * 1024 * 1024
        self.monthly_limit = monthly_limit_mb * 1024 * 1024

    async def check_user_quota(self, user_id: int, db: AsyncSession) -> dict:
        """
        Check user's upload quota usage.

        Args:
            user_id: User ID
            db: Database session

        Returns:
            Dictionary with quota usage

        Raises:
            HTTPException: If quota exceeded
        """
        # Get today's uploads
        today = datetime.utcnow().date()
        daily_uploads = await db.execute(
            select(func.sum(Resume.file_size))
            .where(Resume.uploaded_by == user_id)
            .where(func.date(Resume.created_at) == today)
        )
        daily_total = daily_uploads.scalar() or 0

        # Get this month's uploads
        month_start = today.replace(day=1)
        monthly_uploads = await db.execute(
            select(func.sum(Resume.file_size))
            .where(Resume.uploaded_by == user_id)
            .where(Resume.created_at >= month_start)
        )
        monthly_total = monthly_uploads.scalar() or 0

        return {
            "daily_used": daily_total,
            "daily_limit": self.daily_limit,
            "daily_remaining": self.daily_limit - daily_total,
            "monthly_used": monthly_total,
            "monthly_limit": self.monthly_limit,
            "monthly_remaining": self.monthly_limit - monthly_total
        }

    async def enforce_quota(self, user_id: int, file_size: int, db: AsyncSession):
        """
        Enforce quota limits before upload.

        Args:
            user_id: User ID
            file_size: Size of file to upload
            db: Database session

        Raises:
            HTTPException: If quota exceeded
        """
        quota = await self.check_user_quota(user_id, db)

        if quota["daily_remaining"] < file_size:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Daily upload quota exceeded. {quota['daily_used'] / 1024 / 1024:.1f}MB used"
            )

        if quota["monthly_remaining"] < file_size:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Monthly upload quota exceeded. {quota['monthly_used'] / 1024 / 1024:.1f}MB used"
            )


# Initialize quota manager
quota_manager = UploadQuotaManager(daily_limit_mb=100, monthly_limit_mb=1000)


# Usage in upload endpoint
@router.post("/upload")
async def upload_resume(
    file: UploadFile,
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Upload with quota enforcement."""
    # Check quota
    await quota_manager.enforce_quota(user_id, file.size, db)

    # Proceed with upload
    # ...
```

### Secure File Storage

#### Directory Structure

```bash
/var/uploads/
├── resumes/           # Resume files
│   └── incoming/      # New uploads (quarantine)
├── avatar/           # User avatars
├── backups/          # Backup files
└── temp/             # Temporary processing files
```

**Permissions**:

```bash
# Create upload directories
sudo mkdir -p /var/uploads/resumes/incoming
sudo mkdir -p /var/uploads/avatar
sudo mkdir -p /var/uploads/backups
sudo mkdir -p /var/uploads/temp

# Set ownership (application user)
sudo chown -R appuser:appgroup /var/uploads

# Set permissions
sudo chmod 755 /var/uploads
sudo chmod 750 /var/uploads/resumes
sudo chmod 750 /var/uploads/resumes/incoming

# Ensure files are not executable
find /var/uploads -type f -exec chmod 644 {} \;
```

#### Docker Volume Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    image: agenthr-backend:latest
    volumes:
      - upload_data:/uploads:rw
    environment:
      - UPLOAD_DIR=/uploads/resumes
      - MAX_UPLOAD_SIZE_MB=10

volumes:
  upload_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /var/uploads
```

### File Upload Security Checklist

#### Validation

- [ ] File size limits enforced
- [ ] File extension whitelist implemented
- [ ] Magic number validation (file header checking)
- [ ] MIME type validation
- [ ] Filename sanitization (path traversal prevention)
- [ ] Character encoding validation
- [ ] Blocked dangerous extensions

#### Malware Protection

- [ ] ClamAV or similar malware scanner configured
- [ ] Scanner signatures updated regularly
- [ ] Scanning before file acceptance
- [ ] Quarantine for suspicious files
- [ ] Content sanitization for PDF/DOCX
- [ ] Macro/embedded object detection

#### Storage Security

- [ ] Files stored outside web root
- [ ] Unique filename generation
- [ ] File permissions set correctly (644)
- [ ] Directory permissions set correctly (755/750)
- [ ] Encryption at rest for sensitive files
- [ ] Regular cleanup of temp files
- [ ] File integrity verification (hashing)

#### Access Control

- [ ] Upload endpoint requires authentication
- [ ] Rate limiting per user/IP
- [ ] Per-user upload quotas
- [ ] Upload logging and monitoring
- [ ] Failed upload attempt monitoring

#### Processing Security

- [ ] Sandboxed file processing environment
- [ ] Resource limits for file processing
- [ ] Timeout for file operations
- [ ] Secure file deletion
- [ ] No shell execution on uploaded files

#### Monitoring & Alerting

- [ ] Upload volume monitoring
- [ ] Malware detection alerts
- [ ] Quota exceeded alerts
- [ ] Suspicious pattern detection
- [ ] Regular security audit of uploaded files

---

## Dependency Management

Dependencies represent a significant attack vector. A compromised dependency can lead to supply chain attacks, data breaches, and complete system compromise. This section covers dependency management, vulnerability scanning, and update procedures.

### Current Security Posture

**✅ Implemented**:
- `requirements.txt` for Python dependency tracking
- `safety` scanning integrated in security scan results
- Pinned dependency versions in requirements.txt

**⚠️ Needs Implementation**:
- Automated vulnerability scanning in CI/CD pipeline
- Dependency lock file (requirements.lock or Poetry.lock)
- Software Bill of Materials (SBOM) generation
- Automated dependency update bot (Dependabot, Renovate)
- Pre-commit hooks for vulnerability scanning

### Dependency Security Threats

#### Supply Chain Attack Vectors

| Attack Type | Description | Impact | Mitigation |
|-------------|-------------|--------|------------|
| **Malicious Dependency** | Attacker publishes malicious package to public repository | Code execution, data theft, backdoor | Verify package source, check maintainer identity |
| **Dependency Confusion** | Attacker publishes package with same name to public registry | System installs malicious internal package | Use private registry with proper namespacing |
| **Typosquatting** | Attacker publishes package with similar name to popular package | Developer accidentally installs malicious package | Use lock files, verify package names |
| **Transitive Vulnerability** | Vulnerability in dependency's dependency | Indirect compromise via trusted package | Scan full dependency tree |
| **Abandoned Package** | Maintainer stops updating, vulnerabilities unpatched | Known vulnerabilities remain exploitable | Monitor package health, have migration plan |
| **Compromised Maintainer** | Attacker gains access to maintainer account | Malicious code pushed to trusted package | Enable 2FA, require code review for updates |

### Vulnerability Scanning Tools

#### 1. pip-audit

**pip-audit** audits Python dependencies for known vulnerabilities.

**Installation**:
```bash
pip install pip-audit
```

**Usage**:
```bash
# Audit requirements.txt
pip-audit --requirement requirements.txt

# Audit installed packages
pip-audit

# Generate SARIF output for CI/CD
pip-audit --format json --output audit-report.json

# Exclude specific vulnerabilities (use sparingly)
pip-audit --exclude-vuln <CVE-ID>
```

**CI/CD Integration**:
```yaml
# .github/workflows/security-scan.yml
name: Security Scan

on:
  push:
    branches: [main, develop]
  pull_request:
  schedule:
    - cron: '0 0 * * 0'  # Weekly

jobs:
  pip-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install pip-audit
        run: pip install pip-audit
      - name: Run vulnerability scan
        run: pip-audit --requirement backend/requirements.txt --format json --output audit-report.json
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: pip-audit-report
          path: audit-report.json
```

#### 2. Safety

**safety** checks installed dependencies against security vulnerabilities database.

**Installation**:
```bash
pip install safety
```

**Usage**:
```bash
# Scan requirements.txt
safety check --file requirements.txt

# Scan with JSON output
safety check --file requirements.txt --json --output safety-report.json

# Ignore specific vulnerabilities (document reason)
safety check --file requirements.txt --ignore 51457

# Continuous monitoring API
safety check --api-key <KEY> --continue-on-error
```

**Current Integration**:
```json
// From backend/security_scan_results.json
{
  "safety_dependency_scan": {
    "scan_date": "2026-01-24",
    "python_version": "3.9+",
    "dependencies_scanned": 35,
    "vulnerabilities_found": 0,
    "results": []
  }
}
```

#### 3. Snyk

**Snyk** provides comprehensive dependency scanning with remediation advice.

**Installation**:
```bash
npm install -g snyk
# or
pip install snyk
```

**Usage**:
```bash
# Authenticate
snyk auth <API-KEY>

# Test for vulnerabilities
snyk test --file=requirements.txt

# Monitor for new vulnerabilities
snyk monitor --file=requirements.txt

# Generate SBOM
snyk sbom --file=requirements.txt --format=spdx-json > sbom.json
```

#### 4. Trivy

**Trivy** is a comprehensive security scanner that supports multiple languages.

**Installation**:
```bash
# macOS
brew install trivy

# Linux
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
```

**Usage**:
```bash
# Scan filesystem
trivy fs --security-checks vuln .

# Scan Docker image
trivy image agenthr-backend:latest

# Scan with severity filter
trivy fs --severity HIGH,CRITICAL .

# Generate SARIF report
trivy fs --format sarif --output trivy-report.json .
```

#### 5. OWASP Dependency-Check

**Dependency-Check** identifies project dependencies and checks for vulnerabilities.

**Installation**:
```bash
# Docker (recommended)
docker pull owasp/dependency-check
```

**Usage**:
```bash
# Scan Python dependencies
docker run --rm \
  -v /path/to/project:/scan \
  owasp/dependency-check \
  --scan /scan \
  --format JSON \
  --out /scan/reports

# View results
cat reports/dependency-check-report.json
```

### Dependency Management Best Practices

#### 1. Use Dependency Lock Files

**Poetry** (recommended for Python):
```bash
# Install Poetry
pip install poetry

# Initialize project
poetry init

# Install dependencies
poetry add fastapi uvicorn sqlalchemy

# Generate poetry.lock (commit this file)
poetry lock

# Install exact versions from lock file
poetry install
```

**pip-tools** (alternative):
```bash
# Install pip-tools
pip install pip-tools

# Create requirements.in (specify dependencies)
cat > requirements.in << EOF
fastapi>=0.100.0,<0.101.0
uvicorn[standard]>=0.23.0,<0.24.0
sqlalchemy>=2.0.0,<2.1.0
EOF

# Compile pinned requirements
pip-compile requirements.in --output-file requirements.txt

# Upgrade dependencies
pip-compile --upgrade requirements.in
```

#### 2. Pin Dependency Versions

**Bad** (unpinned):
```txt
fastapi
uvicorn
sqlalchemy
```

**Good** (pinned):
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
```

**Better** (version ranges):
```txt
fastapi>=0.104.0,<0.105.0
uvicorn[standard]>=0.24.0,<0.25.0
sqlalchemy>=2.0.23,<2.1.0
```

#### 3. Separate Development Dependencies

**requirements.txt** (production):
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
pydantic-settings==2.1.0
```

**requirements-dev.txt** (development):
```txt
-r requirements.txt
pytest==7.4.3
pytest-cov==4.1.0
black==23.12.0
flake8==6.1.0
mypy==1.7.1
safety==2.3.5
bandit==1.7.5
```

#### 4. Vendor Critical Dependencies

For security-critical code, consider vendoring dependencies:

```bash
# Copy dependency into project
pip install -t vendor/ package-name

# Use vendored dependency
import sys
sys.path.insert(0, 'vendor')
import package_name
```

#### 5. Regular Dependency Updates

**Weekly Review Process**:
1. Run `pip-audit` and `safety check`
2. Review flagged vulnerabilities
3. Check if update is compatible
4. Test in staging environment
5. Deploy to production

**Automated Updates** (GitHub Dependabot):
```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/backend"
    schedule:
      interval: "weekly"
      day: "monday"
    open-pull-requests-limit: 10
    reviewers:
      - "security-team"
    labels:
      - "dependencies"
      - "security"
    ignore:
      # Ignore major version updates for stability
      - dependency-name: "fastapi"
        update-types: ["version-update:semver-major"]
```

### Software Bill of Materials (SBOM)

An SBOM provides a complete inventory of all software components.

#### Generate SBOM with Syft

```bash
# Install Syft
brew install syft  # macOS
# or
curl -ssL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin

# Generate SBOM
syft backend -o spdx-json > sbom.json

# Generate in multiple formats
syft backend -o cyclonedx-json > sbom-cyclonedx.json
syft backend -o spdx-json > sbom-spdx.json
syft backend -o table > sbom.txt
```

#### SBOM Format (SPDX JSON)

```json
{
  "spdxVersion": "SPDX-2.3",
  "dataLicense": "CC0-1.0",
  "SPDXID": "SPDXRef-DOCUMENT",
  "name": "agenthr-backend",
  "documentNamespace": "https://agenthr.com/sbom/backend-1.0.0",
  "creationInfo": {
    "created": "2026-02-04T12:00:00Z",
    "creators": ["Tool: syft-0.85.0"]
  },
  "packages": [
    {
      "SPDXID": "SPDXRef-Package-fastapi",
      "name": "fastapi",
      "versionInfo": "0.104.1",
      "downloadLocation": "https://pypi.org/pypi/fastapi/0.104.1",
      "filesAnalyzed": false,
      "licenseConcluded": "NOASSERTION",
      "externalRefs": [
        {
          "referenceCategory": "PACKAGE-MANAGER",
          "referenceType": "purl",
          "referenceLocator": "pkg:pypi/fastapi@0.104.1"
        }
      ]
    }
  ]
}
```

### Dependency Security Checklist

#### Initial Setup

- [ ] Pin all dependency versions in requirements.txt
- [ ] Use Poetry or pip-tools for dependency resolution
- [ ] Separate production and development dependencies
- [ ] Add requirements.txt to version control
- [ ] Add poetry.lock or requirements.lock to version control

#### Vulnerability Scanning

- [ ] Integrate pip-audit in CI/CD pipeline
- [ ] Integrate safety check in CI/CD pipeline
- [ ] Configure automated scanning (weekly minimum)
- [ ] Set up vulnerability alerts (email, Slack)
- [ ] Fail builds on HIGH/CRITICAL vulnerabilities
- [ ] Document vulnerability exceptions with justification

#### Dependency Updates

- [ ] Enable Dependabot or Renovate for automated updates
- [ ] Establish dependency update review process
- [ ] Test updates in staging before production
- [ ] Monitor security advisories for dependencies
- [ ] Maintain list of approved dependency versions

#### Supply Chain Security

- [ ] Verify package maintainer identity
- [ ] Check package download counts and activity
- [ ] Review package source code for critical dependencies
- [ ] Use private registry for internal packages
- [ ] Enable 2FA for package maintainer accounts
- [ ] Generate and maintain SBOM

#### Documentation

- [ ] Document all third-party dependencies
- [ ] Maintain dependency inventory with versions
- [ ] Document licensing information
- [ ] Track security policy URLs for dependencies
- [ ] Update architecture diagrams with dependencies

#### Monitoring

- [ ] Monitor dependency security advisories
- [ ] Subscribe to Python Security Announcements
- [ ] Set up Google Alerts for dependency names
- [ ] Review dependency changelogs regularly
- [ ] Track dependency deprecation notices

---

## Logging & Monitoring Security

Security monitoring and logging are critical for detecting, investigating, and responding to security incidents. Proper logging practices must balance security visibility with privacy protection.

### Current Security Posture

**✅ Implemented**:
- Structured JSON logging (Loki integration)
- Log aggregation via Loki
- Metrics collection via Prometheus
- Grafana dashboards for monitoring
- Celery task logging

**⚠️ Needs Implementation**:
- Security event classification and tagging
- PII redaction in logs
- Centralized security alerting
- Log tamper detection
- Audit log retention policy
- Log forwarding to SIEM (Security Information and Event Management)
- Real-time threat detection rules

### Security Event Logging

#### Security Event Categories

**Critical Security Events** (immediate alerting):
- Authentication failures (5+ in 5 minutes)
- Authorization failures (access denied to protected resources)
- SQL injection attempts
- XSS attempt signatures
- Path traversal attempts
- Command injection attempts
- File upload malware detection
- Rate limit exceeded
- Admin access granted
- Database connection failures
- System configuration changes

**Warning Security Events** (hourly digest):
- Unusual API request patterns
- Large file uploads (>8MB)
- Multiple failed file uploads
- Unknown user agents
- Requests from unusual geolocations
- Spike in error rates
- Slow API responses (>5s)

**Informational Security Events** (daily summary):
- Successful logins
- New user registrations
- File uploads processed
- API rate limit usage
- System health checks
- Scheduled task completion

#### Security Logging Implementation

**backend/core/security_logging.py**:

```python
import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional
from fastapi import Request
from user_agents import parse as parse_user_agent

logger = logging.getLogger(__name__)


class SecurityEventLogger:
    """
    Centralized security event logging with PII redaction.
    """

    # Fields to redact from logs
    PII_FIELDS = {
        'password', 'secret', 'token', 'api_key', 'apikey',
        'private_key', 'authorization', 'cookie', 'session',
        'ssn', 'social_security', 'credit_card', 'email',
        'phone', 'address', 'full_name', 'real_name'
    }

    # Patterns to redact (regex)
    SENSITIVE_PATTERNS = [
        r'Bearer\s+[A-Za-z0-9\-._~+/]+=*',  # Bearer tokens
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Emails
        r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
        r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # Credit card
    ]

    @classmethod
    def redact_pii(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively redact PII from log data.
        """
        if isinstance(data, dict):
            return {
                key: cls.redact_pii(value)
                if key.lower() not in cls.PII_FIELDS
                else "***REDACTED***"
                for key, value in data.items()
            }
        elif isinstance(data, list):
            return [cls.redact_pii(item) for item in data]
        else:
            return data

    @classmethod
    def log_security_event(
        cls,
        event_type: str,
        severity: str,  # critical, warning, info
        request: Optional[Request] = None,
        details: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None
    ) -> None:
        """
        Log a security event with full context.
        """
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'severity': severity,
            'category': 'security',
        }

        # Add request context
        if request:
            user_agent = request.headers.get('user-agent', 'unknown')
            ua_parsed = parse_user_agent(user_agent)

            event['request'] = {
                'method': request.method,
                'path': request.url.path,
                'query_params': dict(request.query_params),
                'client_host': request.client.host if request.client else None,
                'user_agent': {
                    'browser': ua_parsed.browser.family,
                    'os': ua_parsed.os.family,
                    'device': ua_parsed.device.family,
                    'is_bot': ua_parsed.is_bot,
                    'is_mobile': ua_parsed.is_mobile
                }
            }

        # Add user context (without PII)
        if user_id:
            event['user'] = {
                'user_id': user_id,
                # Never log user PII (email, name, etc.)
            }

        # Add event details (with PII redaction)
        if details:
            event['details'] = cls.redact_pii(details)

        # Log to structured logger
        log_method = {
            'critical': logger.critical,
            'warning': logger.warning,
            'info': logger.info
        }.get(severity, logger.info)

        log_method('security_event', extra={'event': event})


# Usage examples
security_logger = SecurityEventLogger()


def log_failed_login(request: Request, username: str, reason: str):
    """Log failed login attempt."""
    security_logger.log_security_event(
        event_type='auth_failure',
        severity='warning',
        request=request,
        details={
            'username': username,  # Will be redacted
            'reason': reason,
            'login_method': 'password'
        }
    )


def log_sql_injection_attempt(request: Request, payload: str):
    """Log SQL injection attempt."""
    security_logger.log_security_event(
        event_type='sql_injection_attempt',
        severity='critical',
        request=request,
        details={
            'payload': payload[:100],  # Truncate for safety
            'pattern_detected': 'sql_injection_signature'
        }
    )


def log_file_upload_malware_detected(request: Request, filename: str, threat_name: str):
    """Log malware detection."""
    security_logger.log_security_event(
        event_type='malware_detected',
        severity='critical',
        request=request,
        details={
            'filename': filename,
            'threat_name': threat_name,
            'action': 'quarantined'
        }
    )


def log_rate_limit_exceeded(request: Request, limit: int, window: int):
    """Log rate limit exceeded."""
    security_logger.log_security_event(
        event_type='rate_limit_exceeded',
        severity='warning',
        request=request,
        details={
            'limit': limit,
            'window_seconds': window,
            'action': 'request_blocked'
        }
    )
```

### Avoiding PII in Logs

#### PII Redaction Patterns

**Email Addresses**:
```python
import re

def redact_email(text: str) -> str:
    """Redact email addresses."""
    return re.sub(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        '***@***.***',
        text
    )
```

**Phone Numbers**:
```python
def redact_phone(text: str) -> str:
    """Redact phone numbers."""
    return re.sub(
        r'\b\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
        '***-***-****',
        text
    )
```

**Names** (context-specific):
```python
# Instead of logging:
logger.info(f"User {user.full_name} uploaded resume")

# Log user ID only:
logger.info(f"User {user.id} uploaded resume")

# Or use anonymized identifier:
logger.info(f"User {hash_email(user.email)} uploaded resume")
```

**Request Body Sanitization**:
```python
def sanitize_request_body(body: dict) -> dict:
    """Remove sensitive fields from request body."""
    sensitive_fields = {'password', 'token', 'secret', 'api_key'}

    return {
        k: '***REDACTED***' if k.lower() in sensitive_fields else v
        for k, v in body.items()
    }
```

### Security Monitoring & Alerting

#### Prometheus Security Metrics

**backend/core/security_metrics.py**:

```python
from prometheus_client import Counter, Histogram, Gauge

# Security event counters
auth_failures_total = Counter(
    'security_auth_failures_total',
    'Total authentication failures',
    ['method', 'reason']
)

sql_injection_attempts_total = Counter(
    'security_sql_injection_attempts_total',
    'Total SQL injection attempts detected'
)

path_traversal_attempts_total = Counter(
    'security_path_traversal_attempts_total',
    'Total path traversal attempts detected'
)

malware_detected_total = Counter(
    'security_malware_detected_total',
    'Total malware detections',
    ['threat_name']
)

rate_limit_exceeded_total = Counter(
    'security_rate_limit_exceeded_total',
    'Total rate limit violations',
    ['endpoint']
)

# Security metrics gauge
active_sessions = Gauge(
    'security_active_sessions',
    'Currently active user sessions'
)

failed_requests_by_ip = Gauge(
    'security_failed_requests_by_ip',
    'Failed requests by IP address (last 5 minutes)',
    ['ip_address']
)
```

#### Grafana Alert Rules

**Grafana Alert Configuration**:

```yaml
# grafana/alerts/security_alerts.yml
groups:
  - name: security_alerts
    interval: 30s
    rules:
      - alert: HighAuthenticationFailureRate
        expr: rate(security_auth_failures_total[5m]) > 10
        for: 5m
        labels:
          severity: warning
          category: security
        annotations:
          summary: "High rate of authentication failures"
          description: "{{ $value }} auth failures per second"

      - alert: SQLInjectionAttemptsDetected
        expr: increase(security_sql_injection_attempts_total[5m]) > 0
        for: 0s
        labels:
          severity: critical
          category: security
        annotations:
          summary: "SQL injection attempt detected"
          description: "SQL injection attempt detected from IP: {{ $labels.ip_address }}"

      - alert: MalwareDetected
        expr: increase(security_malware_detected_total[1m]) > 0
        for: 0s
        labels:
          severity: critical
          category: security
        annotations:
          summary: "Malware detected in file upload"
          description: "Threat: {{ $labels.threat_name }}"

      - alert: RateLimitExceeded
        expr: rate(security_rate_limit_exceeded_total[5m]) > 100
        for: 5m
        labels:
          severity: warning
          category: security
        annotations:
          summary: "High rate of rate limit violations"
          description: "{{ $value }} violations per second"
```

#### Loki Security Queries

**Query Examples for Grafana/Loki**:

```logql
# Authentication failures (last hour)
{job="backend"} | logfmt | event_type="auth_failure" | line_format "{{.timestamp}} - {{.request.client_host}} - {{.details.reason}}"

# SQL injection attempts (all time)
{job="backend"} | logfmt | event_type="sql_injection_attempt"

# Failed authorizations by IP (last 24 hours)
{job="backend"} | logfmt | event_type="authz_failure" | line_format "{{.request.client_host}}" | count by (request.client_host)

# Malware detections by threat type
{job="backend"} | logfmt | event_type="malware_detected" | count by (details.threat_name)

# Rate limit violations by endpoint
{job="backend"} | logfmt | event_type="rate_limit_exceeded" | count by (request.path)

# All critical security events (last hour)
{job="backend"} | logfmt | severity="critical"

# Unusual user agents (bots)
{job="backend"} | logfmt | request.user_agent.is_bot="true"

# Requests from unexpected countries
{job="backend"} | logfmt | request.country!~"US|CA|GB|DE"
```

### Log Retention & Archival

#### Retention Policy

**Hot Storage** (immediate access):
- **Duration**: 30 days
- **Storage**: Loki
- **Access**: Grafana dashboards
- **Purpose**: Operational monitoring, incident investigation

**Warm Storage** (scheduled access):
- **Duration**: 1 year
- **Storage**: S3/Glacier with periodic retrieval
- **Purpose**: Compliance, trend analysis, security investigations

**Cold Storage** (archival):
- **Duration**: 7 years (for GDPR/CCPA compliance)
- **Storage**: S3 Glacier Deep Archive
- **Purpose**: Legal hold, regulatory compliance

#### Log Rotation

**Loki Configuration**:

```yaml
# loki-config.yml
schema_config:
  configs:
    - from: 2024-01-01
      store: boltdb-shipper
      object_store: s3
      schema: v11
      index:
        prefix: index_
        period: 24h

limits_config:
  # Retention policy
  retention_period: 720h  # 30 days

  # Per-stream retention
  retention_stream:
    - selector: '{severity="critical"}'
      priority: 1
      period: 2160h  # 90 days for critical logs

    - selector: '{category="security"}'
      priority: 2
      period: 1440h  # 60 days for security logs

chunk_store_config:
  max_look_back_period: 720h
```

### SIEM Integration

#### Send Logs to Splunk

```python
import requests
import json

class SplunkSender:
    """Send security events to Splunk SIEM."""

    def __init__(self, hec_url: str, hec_token: str):
        self.hec_url = hec_url
        self.hec_token = hec_token

    def send_event(self, event: dict):
        """Send event to Splunk HTTP Event Collector."""
        headers = {
            'Authorization': f'Splunk {self.hec_token}',
            'Content-Type': 'application/json'
        }

        data = {
            'event': event,
            'sourcetype': '_json',
            'index': 'security',
            'source': 'agenthr-backend'
        }

        response = requests.post(
            self.hec_url,
            headers=headers,
            data=json.dumps(data),
            timeout=5
        )

        response.raise_for_status()
```

#### Send Logs to Elasticsearch

```python
from elasticsearch import Elasticsearch

class ElasticsearchSender:
    """Send security events to Elasticsearch/ELK stack."""

    def __init__(self, hosts: list, index_prefix: str = 'security-events'):
        self.es = Elasticsearch(hosts)
        self.index_prefix = index_prefix

    def send_event(self, event: dict):
        """Send event to Elasticsearch."""
        # Create daily index
        index = f"{self.index_prefix}-{datetime.now().strftime('%Y.%m.%d')}"

        self.es.index(
            index=index,
            document=event,
            refresh=False
        )
```

### Real-Time Threat Detection

#### Anomaly Detection Rules

**Backend FastAPI Middleware**:

```python
from fastapi import Request, HTTPException, status
from collections import defaultdict
import time
from datetime import datetime, timedelta

class SecurityMonitor:
    """
    Real-time security monitoring with anomaly detection.
    """

    def __init__(self):
        # Track failed requests by IP
        self.failed_requests = defaultdict(list)

        # Track request rates by IP
        self.request_timestamps = defaultdict(list)

        # Track SQL injection signatures
        self.sql_signatures = [
            r"(\%27)|(\')|(\-\-)|(\%23)|(#)",
            r"(\bor\b|\band\b).*?=",
            r"exec(\s|\+)+(s|x)p\w+",
            r"union.*?select",
            r"select.*?from",
            r"drop\s+table",
            r"insert\s+into",
            r"update.*?set"
        ]

        # Track path traversal signatures
        self.path_traversal_signatures = [
            r"\.\./",
            r"\.\./",
            r"%2e%2e%2f",
            r"..%5c",
            r"%2e%2e%5c"
        ]

    async def check_request_security(self, request: Request) -> None:
        """
        Check incoming request for security threats.
        """
        client_ip = request.client.host if request.client else "unknown"

        # Check for SQL injection
        for param in request.query_params:
            if self._detect_sql_injection(request.query_params[param]):
                await self._handle_security_threat(
                    request,
                    threat_type="sql_injection",
                    details={"param": param}
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid request parameter"
                )

        # Check for path traversal
        path = request.url.path
        if self._detect_path_traversal(path):
            await self._handle_security_threat(
                request,
                threat_type="path_traversal",
                details={"path": path}
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid request path"
            )

        # Check request rate
        await self._check_request_rate(request, client_ip)

    def _detect_sql_injection(self, value: str) -> bool:
        """Detect SQL injection patterns."""
        import re
        for signature in self.sql_signatures:
            if re.search(signature, value, re.IGNORECASE):
                return True
        return False

    def _detect_path_traversal(self, path: str) -> bool:
        """Detect path traversal patterns."""
        import re
        for signature in self.path_traversal_signatures:
            if re.search(signature, path, re.IGNORECASE):
                return True
        return False

    async def _check_request_rate(self, request: Request, client_ip: str) -> None:
        """Check if client is exceeding rate limits."""
        now = time.time()

        # Clean old timestamps (older than 1 minute)
        self.request_timestamps[client_ip] = [
            ts for ts in self.request_timestamps[client_ip]
            if now - ts < 60
        ]

        # Add current timestamp
        self.request_timestamps[client_ip].append(now)

        # Check rate limit (100 requests per minute)
        if len(self.request_timestamps[client_ip]) > 100:
            await self._handle_security_threat(
                request,
                threat_type="rate_limit",
                details={
                    "client_ip": client_ip,
                    "request_count": len(self.request_timestamps[client_ip])
                }
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )

    async def _handle_security_threat(
        self,
        request: Request,
        threat_type: str,
        details: dict
    ) -> None:
        """Handle detected security threat."""
        security_logger.log_security_event(
            event_type=f'{threat_type}_attempt',
            severity='critical',
            request=request,
            details=details
        )


# Initialize security monitor
security_monitor = SecurityMonitor()


# FastAPI middleware
@app.middleware("http")
async def security_middleware(request: Request, call_next):
    """Security monitoring middleware."""
    # Skip security checks for health endpoint
    if request.url.path == "/health":
        return await call_next(request)

    # Check request security
    await security_monitor.check_request_security(request)

    # Process request
    response = await call_next(request)

    return response
```

### Logging Security Checklist

#### Log Content

- [ ] No passwords or secrets in logs
- [ ] No API keys or tokens in logs
- [ ] No credit card numbers in logs
- [ ] No SSN or personal IDs in logs
- [ ] Email addresses redacted
- [ ] Phone numbers redacted
- [ ] User IDs instead of names
- [ ] Request bodies sanitized
- [ ] Cookie values redacted

#### Security Events

- [ ] Authentication failures logged
- [ ] Authorization failures logged
- [ ] SQL injection attempts logged
- [ ] XSS attempts logged
- [ ] Path traversal attempts logged
- [ ] File upload malware detection logged
- [ ] Rate limit violations logged
- [ ] Configuration changes logged
- [ ] Admin access logged

#### Alerting

- [ ] Critical security events trigger immediate alerts
- [ ] Warning events trigger hourly/daily digests
- [ ] Alert recipients configured (email, Slack, PagerDuty)
- [ ] Alert escalation rules configured
- [ ] False positive tracking in place
- [ ] Alert response procedures documented

#### Monitoring

- [ ] Grafana dashboards for security metrics
- [ ] Prometheus counters for security events
- [ ] Loki queries for security log search
- [ ] Real-time threat detection rules
- [ ] Anomaly detection configured
- [ ] Baseline of normal behavior

#### Retention & Archival

- [ ] Hot storage retention configured (30 days)
- [ ] Warm storage retention configured (1 year)
- [ ] Cold storage retention configured (7 years)
- [ ] Log rotation configured
- [ ] Log archival process automated
- [ ] Restore process tested

#### SIEM Integration

- [ ] SIEM integration configured (Splunk/ELK)
- [ ] Security logs forwarded to SIEM
- [ ] SIEM alerts configured
- [ ] SIEM dashboards created
- [ ] SIEM user access controlled
- [ ] SIEM retention policy configured

#### Compliance

- [ ] Audit log trail maintained
- [ ] Log tamper detection enabled
- [ ] Log access controlled and audited
- [ ] Data retention policy documented
- [ ] GDPR right to deletion supported
- [ ] CCPA compliance verified

---

## Compliance & Data Privacy

### Overview

The AgentHR Resume Analysis System processes **personally identifiable information (PII)** and must comply with various data protection regulations depending on the jurisdictions where candidates and organizations operate. Non-compliance can result in significant fines, legal liability, and reputational damage.

### Applicable Regulations

#### GDPR (General Data Protection Regulation) - EU/UK

**Scope**: Applies to processing of personal data of EU/UK residents, regardless of where the processing occurs.

**Key Requirements**:

| Requirement | Description | Implementation |
|-------------|-------------|----------------|
| **Lawful Basis** | Must have a legal basis for processing (e.g., consent, contract) | Processing based on recruitment contract with candidates |
| **Data Minimization** | Collect only data necessary for stated purpose | Only collect resume data relevant to hiring decisions |
| **Purpose Limitation** | Use data only for stated, explicit purposes | Resume data used solely for recruitment assessment |
| **Transparency** | Inform individuals what data is collected and how it's used | Privacy policy with clear data usage description |
| **Data Subject Rights** | Grant specific rights to individuals | Implemented data access, correction, deletion endpoints |
| **Data Portability** | Provide data in machine-readable format | Export candidate data in JSON/CSV format |
| **Right to Erasure** | Delete data on request ("right to be forgotten") | Implemented candidate data deletion functionality |
| **Data Breach Notification** | Notify authorities within 72 hours | Incident response plan with breach notification procedures |
| **Data Protection by Design** | Build privacy into system architecture | Privacy impact assessments conducted |
| **DPIA (Data Protection Impact Assessment)** | Required for high-risk processing | DPIA completed for resume analysis and ranking |

**Potential Fines**:
- **Standard violations**: Up to €10 million or 2% of global revenue (whichever is higher)
- **Serious violations**: Up to €20 million or 4% of global revenue (whichever is higher)

#### CCPA (California Consumer Privacy Act) - California, USA

**Scope**: Applies to processing of personal data of California residents.

**Key Requirements**:

| Requirement | Description | Implementation |
|-------------|-------------|----------------|
| **Right to Know** | Inform consumers what data is collected | Privacy policy details data collection practices |
| **Right to Delete** | Delete personal data on request | Implemented deletion endpoint for California residents |
| **Right to Opt-Out** | Opt-out of data sale (if applicable) | System does not sell personal data |
| **Right to Non-Discrimination** | Not discriminate for exercising rights | No penalty for accessing/deleting data |
| **Data Access** | Provide specific categories of data collected | Data access request endpoint implemented |

**Potential Fines**: Up to $7,500 per intentional violation.

#### Other Jurisdictions

| Regulation | Jurisdiction | Key Requirements |
|------------|--------------|------------------|
| **PIPEDA** | Canada | Consent, purpose limitation, access rights, breach notification |
| **LGPD** | Brazil | Similar to GDPR - legal basis, data subject rights, DPIA |
| **PDPA** | Singapore | Consent, access, correction, protection obligations |
| **POPIA** | South Africa | Conditions for lawful processing, data subject rights |

### Data Retention Policies

The system implements **configurable data retention** through environment variables to comply with data minimization principles.

#### Configuration Settings

```python
# From backend/config.py
backup_retention_days = 30          # Backup retention (default: 30 days)
audit_log_retention_days = 90       # Audit log retention (default: 90 days)
```

#### Retention Schedule

| Data Type | Retention Period | Legal Basis | Deletion Method |
|-----------|------------------|-------------|-----------------|
| **Candidate Resumes** | 2 years after hiring decision | Contractual necessity | Automated soft-delete + hard purge |
| **Candidate PII** | 2 years after last activity | Legal compliance requirement | Soft-delete (marked as deleted) |
| **Audit Logs** | 90 days (configurable) | Legal compliance requirement | Automated log rotation + purge |
| **Database Backups** | 30 days (configurable) | Recovery & compliance | Automated backup rotation |
| **Application Logs** | 30 days | Operational need | Automated log rotation |
| **Session Data** | 24 hours | Operational necessity | Automatic session expiration |
| **Cache Data** | 7 days | Performance optimization | Automatic cache eviction |

#### Data Deletion Process

**Soft Delete** (Immediate):
- Mark records as deleted in database
- Remove from search results and API responses
- Retain in database for backup/audit purposes

**Hard Delete** (After Retention Period):
```python
# Automated deletion process (runs weekly)
def cleanup_expired_data():
    """
    Delete expired data based on retention policies.
    """
    # 1. Delete candidates older than retention period
    delete_candidates_older_than(days=730)  # 2 years

    # 2. Delete audit logs older than retention period
    delete_audit_logs_older_than(days=settings.audit_log_retention_days)

    # 3. Delete old backups
    delete_backups_older_than(days=settings.backup_retention_days)

    # 4. Log deletion actions
    log_data_deletion(action="cleanup", timestamp=now())
```

#### Data Subject Rights Implementation

**Right to Access (DSAR)**:
```bash
# API Endpoint
GET /api/candidates/{id}/data-export

# Response: JSON with all personal data
{
  "candidate_id": "uuid",
  "personal_info": { ... },
  "resume_data": { ... },
  "assessment_results": [ ... ],
  "audit_log": [ ... ]
}
```

**Right to Erasure**:
```bash
# API Endpoint
DELETE /api/candidates/{id}

# Action:
# 1. Soft-delete immediately (data inaccessible)
# 2. Schedule hard-delete after compliance period (if required)
# 3. Log deletion action in audit trail
# 4. Confirm deletion to data subject
```

**Right to Rectification**:
```bash
# API Endpoint
PUT /api/candidates/{id}

# Allows candidates to update their personal information
```

**Right to Portability**:
```bash
# API Endpoint
GET /api/candidates/{id}/export

# Provides data in machine-readable format (JSON, CSV, XML)
```

### Privacy by Design & Default

#### Architecture Principles

1. **Data Minimization**: Collect only data required for hiring assessment
2. **Purpose Limitation**: Use data only for recruitment purposes
3. **Storage Limitation**: Retain data only as long as necessary
4. **Security by Default**: Enable all security features automatically
5. **Transparency**: Clear privacy notices and consent mechanisms

#### Privacy Impact Assessment (PIA)

**PIA Checklist**:
- [ ] Data flows documented
- [ ] Data subjects identified (candidates, recruiters)
- [ ] Processing purposes documented
- [ ] Legal basis identified (contract, consent, legal obligation)
- [ ] Privacy risks assessed (unauthorized access, data breach)
- [ ] Mitigation measures implemented (encryption, access control)
- [ ] Data subject rights supported (access, deletion, portability)
- [ ] Third-party processor risks assessed (LLM providers, cloud services)
- [ ] International data transfer risks addressed (EU-US data transfers)
- [ ] DPIA completed for high-risk processing (AI-based ranking)

#### Third-Party Data Processors

**LLM Providers** (OpenAI, Anthropic, Google, Z.ai):
- **Data Usage**: Resume text sent for ATS scoring and analysis
- **Data Retention**: Verify provider's data retention policy
- **Data Processing Agreement (DPA)**: Execute DPA with each provider
- **Data Location**: Ensure EU data remains in EU (if required)
- **Data Deletion**: Request deletion of data from provider systems

**S3 Backup Storage** (if enabled):
- **Data Encryption**: Server-side encryption enabled
- **Access Control**: Bucket access restricted to specific IAM roles
- **Data Location**: Choose appropriate AWS region for compliance
- **Data Deletion**: Implement versioning with lifecycle policies

### Privacy Policy Requirements

The privacy policy must include:

**Required Disclosures**:
1. **Data Controller Identity**: Organization responsible for data processing
2. **Data Collected**: Types of personal data collected (name, email, resume)
3. **Processing Purposes**: Why data is collected (recruitment, assessment)
4. **Legal Basis**: Legal basis for processing (contract, consent)
5. **Data Recipients**: Who has access to data (recruiters, LLM providers)
6. **Data Transfers**: International data transfers (if applicable)
7. **Data Retention**: How long data is retained (2 years for resumes)
8. **Data Subject Rights**: Rights of individuals (access, deletion, portability)
9. **Contact Information**: How to contact data protection officer
10. **Complaint Rights**: Right to lodge complaint with supervisory authority

**Sample Privacy Notice**:
```markdown
## Privacy Policy for AgentHR Resume Analysis

### What Data We Collect
We collect personal information you provide when submitting your resume,
including:
- Contact information (name, email, phone)
- Professional information (work history, education)
- Resume documents (PDF, DOCX)

### How We Use Your Data
Your data is used solely for recruitment purposes:
- Assessing your qualifications for open positions
- Ranking your resume against job requirements
- Communicating with you about the hiring process

### Legal Basis
We process your data based on:
- **Contract**: Pre-contractual steps for potential employment
- **Legitimate Interest**: Assessing your suitability for the role

### Data Retention
Your data is retained for **2 years** after the hiring decision,
then automatically deleted.

### Your Rights
You have the right to:
- **Access**: Request a copy of your data
- **Rectify**: Update incorrect information
- **Erase**: Request deletion of your data
- **Portability**: Receive your data in a structured format
- **Object**: Object to processing based on legitimate interest

### Contact
For privacy inquiries, contact: privacy@company.com
For complaints, contact your local data protection authority.
```

### Compliance Checklist

#### GDPR Compliance

- [ ] **Legal Basis Identified**: Documented legal basis for all processing (contract, consent, legitimate interest)
- [ ] **Records of Processing Activities (ROPA)**: Maintained and up-to-date
- [ ] **Data Protection Impact Assessment (DPIA)**: Completed for AI-based ranking
- [ ] **Data Subject Rights Implemented**:
  - [ ] Right to access (DSAR endpoint)
  - [ ] Right to erasure (deletion endpoint)
  - [ ] Right to rectification (update endpoint)
  - [ ] Right to portability (export endpoint)
  - [ ] Right to object (objection tracking)
  - [ ] Right to restrict processing (data marking)
- [ ] **Privacy Policy Published**: Includes all required disclosures
- [ ] **Cookie Consent**: Cookie banner implemented (if tracking candidates)
- [ ] **Breach Notification**: 72-hour notification process documented
- [ ] **Data Protection Officer (DPO)**: Appointed (if required by scale)
- [ ] **Data Processing Agreements (DPA)**: Signed with all third-party processors
- [ ] **Data Encryption**: At-rest and in-transit encryption implemented
- [ ] **Access Control**: Role-based access control (RBAC) implemented
- [ ] **Audit Logging**: All data access logged
- [ ] **Data Retention**: Configurable retention policies implemented
- [ ] **Data Deletion**: Automated deletion process configured
- [ ] **International Data Transfers**: Adequacy decisions or SCCs in place
- [ ] **Privacy by Design**: PIA conducted for all features
- [ ] **Staff Training**: Data protection training completed for all staff

#### CCPA Compliance

- [ ] **Privacy Policy Updated**: Includes CCPA-specific disclosures
- [ ] **Data Collection Notice**: "Do Not Sell My Info" link (if applicable)
- [ ] **Right to Know**: Data access request endpoint available
- [ ] **Right to Delete**: Deletion request endpoint available
- [ ] **Right to Opt-Out**: Opt-out mechanism (if selling data)
- [ ] **Non-Discrimination**: No penalties for exercising rights
- [ ] **Request Verification**: Identity verification process for requests
- [ ] **Response Timeframes**: Respond within 45 days
- [ ] **Data Categories**: List categories of data collected
- [ ] **Third-Party Disclosure**: Disclose data sharing with third parties

#### Data Security Standards

- [ ] **ISO 27001**: Information security management system (if required)
- [ ] **SOC 2**: Service organization controls (if required)
- [ ] **NIST Framework**: Cybersecurity framework alignment
- [ ] **Penetration Testing**: Annual security assessment
- [ ] **Vulnerability Scanning**: Quarterly vulnerability scans
- [ ] **Security Awareness Training**: Annual training for all staff

---

## Incident Response

### Overview

A well-defined **incident response plan** is critical for minimizing the impact of security breaches, data leaks, and other security incidents. This section outlines the procedures, roles, and communication channels for effective incident response.

### Incident Response Team

#### Roles & Responsibilities

| Role | Responsibilities | Contact (Example) |
|------|------------------|-------------------|
| **Incident Response Lead** | Overall coordination, decision-making, escalation | security-lead@company.com |
| **Security Analyst** | Technical investigation, containment, forensics | security@company.com |
| **Legal Counsel** | Legal advice, regulatory notification, liability | legal@company.com |
| **Communications Lead** | External communication, PR, stakeholder management | pr@company.com |
| **Data Protection Officer (DPO)** | GDPR/CCPA compliance, data subject notifications | dpo@company.com |
| **DevOps Engineer** | System recovery, patches, configuration changes | devops@company.com |
| **Executive Sponsor** | Business impact assessment, high-level decisions | cto@company.com |

#### Escalation Matrix

**Severity 1 - Critical** (Escalate Immediately):
- Confirmed data breach involving PII
- Ransomware or active system compromise
- Complete service unavailability (>1 hour)

**Severity 2 - High** (Escalate within 1 hour):
- Suspected unauthorized access to candidate data
- Malware detected in production systems
- Partial service unavailability

**Severity 3 - Medium** (Escalate within 4 hours):
- Failed login attempts spike
- Potential vulnerability exploitation
- Minor data exposure (non-sensitive)

**Severity 4 - Low** (Escalate within 24 hours):
- Policy violations
- Minor security misconfigurations
- Failed compliance audit items

### Incident Classification

#### Incident Types

| Category | Examples | Severity |
|----------|----------|----------|
| **Data Breach** | Unauthorized access to candidate PII, database exfiltration | Critical |
| **Malware/Ransomware** | Malicious software detected, files encrypted | Critical |
| **DDoS Attack** | Denial of service, service unavailable | High |
| **Unauthorized Access** | Invalid login attempts, credential stuffing | High |
| **Insider Threat** | Data exfiltration by employee, privilege abuse | High |
| **Vulnerability Exploit** | Known CVE exploited in production | High |
| **Misconfiguration** | S3 bucket public, debug logging enabled | Medium |
| **Compliance Violation** | GDPR/CCPA non-compliance finding | Medium |
| **Social Engineering** | Phishing attack on staff | Medium |

#### Severity Levels

**Critical (Severity 1)**:
- Immediate business impact
- Data breach affecting >100 records
- Regulatory reporting required
- Service unavailable >1 hour

**High (Severity 2)**:
- Significant business impact
- Potential data breach
- Security control bypassed
- Service degradation

**Medium (Severity 3)**:
- Limited business impact
- Security policy violation
- No confirmed data exposure
- Service remains available

**Low (Severity 4)**:
- Minimal business impact
- Process improvement needed
- No immediate threat
- Document and monitor

### Incident Response Process

Follow the **NIST Incident Response Lifecycle**: Preparation → Detection → Containment → Eradication → Recovery → Lessons Learned

#### Phase 1: Preparation

**Objective**: Be prepared before an incident occurs.

**Preparation Checklist**:
- [ ] Incident response plan documented and distributed
- [ ] Incident response team (IRT) trained and contact list available
- [ ] Communication channels established (Slack, email, phone)
- [ ] Incident response tools deployed and tested:
  - [ ] SIEM for log analysis
  - [ ] EDR for endpoint detection
  - [ ] Network monitoring tools
  - [ ] Forensic imaging tools
  - [ ] Secure communication channels (Signal, Wickr)
- [ ] Backup and recovery procedures tested
- [ ] Escalation procedures documented
- [ ] Legal notification templates prepared
- [ ] Regulatory reporting requirements documented (GDPR 72h, CCPA 30 days)
- [ ] PR and customer communication templates ready

**Pre-Configured Alert Rules**:
```yaml
# Example Prometheus/Loki alert rules
alerts:
  - name: BruteForceAttack
    condition: rate(failed_logins[5m]) > 10
    severity: high
    action: "Block IP, notify IRT"

  - name: DatabaseAnomaly
    condition: rate(db_queries[1h]) > 10000
    severity: critical
    action: "Investigate potential data exfiltration"

  - name: MalwareDetected
    condition: count(malware_scan_result="positive") > 0
    severity: critical
    action: "Isolate system, notify IRT"

  - name: UnauthorizedAccess
    condition: auth_failures_by_user > 50
    severity: high
    action: "Lock account, notify user"
```

#### Phase 2: Detection & Analysis

**Objective**: Detect incidents and determine scope/impact.

**Detection Sources**:
- **Automated Alerts**: SIEM, EDR, intrusion detection systems
- **User Reports**: Phishing reports, suspicious activity
- **Monitoring**: Grafana dashboards, log analysis
- **Threat Intelligence**: CVE feeds, security advisories

**Analysis Steps**:

1. **Verify the Incident**:
   ```bash
   # Is this a real security incident?
   - Review alert details
   - Correlate with other alerts
   - Check for false positives
   - Confirm anomaly
   ```

2. **Determine Scope**:
   ```bash
   # What systems/data are affected?
   - Check database access logs
   - Review authentication logs
   - Scan for malware on endpoints
   - Analyze network traffic
   - Identify affected accounts
   ```

3. **Assess Impact**:
   ```bash
   # What is the business impact?
   - Number of records exposed
   - Sensitivity of data (PII, financial)
   - Regulatory reporting requirements
   - Customer/stakeholder impact
   - Service availability impact
   ```

4. **Classify Severity**:
   ```bash
   # Based on impact and scope
   - Critical: Data breach, service down
   - High: Potential breach, service degraded
   - Medium: Policy violation, limited impact
   - Low: Process improvement, minimal impact
   ```

**Investigation Commands** (Examples):
```bash
# Check for suspicious login attempts
grep "Failed password" /var/log/auth.log | tail -100

# Check database access logs
grep "SELECT.*candidates" /var/log/postgresql/postgresql.log | tail -100

# Check for malware scan results
cat /var/log/clamav/clamd.log | grep "FOUND"

# Check network connections
netstat -tulpn | grep ESTABLISHED

# Check for recently modified files
find /var/www -mtime -1 -ls

# Check systemd service status
systemctl status backend-api
systemctl status postgresql
```

#### Phase 3: Containment

**Objective**: Stop the incident from spreading and minimize damage.

**Containment Strategies**:

**Immediate Actions** (All Severities):
```bash
# 1. Preserve evidence (before any changes)
mkdir -p /tmp/incident-$(date +%Y%m%d)
cp /var/log/auth.log /tmp/incident-$(date +%Y%m%d)/
cp /var/log/postgresql/*.log /tmp/incident-$(date +%Y%m%d)/
iptables -L -n > /tmp/incident-$(date +%Y%m%d)/iptables.txt

# 2. Document current state
ps aux > /tmp/incident-$(date +%Y%m%d)/ps.txt
netstat -tulpn > /tmp/incident-$(date +%Y%m%d)/netstat.txt
```

**Short-Term Containment** (Stop the bleeding):
```bash
# For DDoS attacks:
# Enable rate limiting
iptables -A INPUT -p tcp --dport 8000 -m limit --limit 10/second -j ACCEPT

# For brute force attacks:
# Block suspicious IPs
iptables -A INPUT -s 192.0.2.0/24 -j DROP

# For unauthorized access:
# Disable compromised accounts
UPDATE users SET active=false WHERE id='compromised-user-id';

# For malware:
# Isolate affected system
iptables -A OUTPUT -p tcp --dport 80,443 -j DROP  # Block outbound

# For database breach:
# Enable read-only mode
ALTER DATABASE resume_analysis SET default_transaction_read_only = on;
```

**Long-Term Containment** (Prevent recurrence):
- Reset all passwords for affected systems
- Revoke and reissue API keys
- Patch exploited vulnerabilities
- Implement additional security controls
- Route traffic through WAF/DDoS protection

#### Phase 4: Eradication

**Objective**: Remove the root cause of the incident.

**Eradication Steps**:

1. **Identify Root Cause**:
   - Vulnerability that was exploited
   - Malware that was executed
   - Misconfiguration that allowed access
   - Phishing email that was clicked

2. **Remove Threat**:
   ```bash
   # Delete malware files
   rm -f /tmp/malicious-file.exe

   # Remove malicious accounts
   DELETE FROM users WHERE email='attacker@evil.com';

   # Patch vulnerability
   apt-get update && apt-get upgrade -y

   # Fix misconfiguration
   # Edit config files to secure settings
   ```

3. **Verify Removal**:
   - Re-scan for malware
   - Verify vulnerability patched
   - Confirm no backdoors installed
   - Check for persistence mechanisms (cron jobs, systemd services)

4. **Document Findings**:
   - Root cause analysis report
   - Timeline of events
   - Attack reconstruction
   - Lessons learned

#### Phase 5: Recovery

**Objective**: Restore normal operations and verify security.

**Recovery Steps**:

1. **Restore from Backup** (if needed):
   ```bash
   # Verify backup integrity before restore
   sha256sum backup.sql.gz

   # Restore database
   gunzip -c backup.sql.gz | psql resume_analysis

   # Restore application files
   rsync -av /backup/app/ /var/www/html/
   ```

2. **Change Credentials**:
   ```bash
   # Reset all admin passwords
   # Reissue API keys
   # Rotate database passwords
   # Update service account credentials
   ```

3. **Patch & Harden**:
   ```bash
   # Apply security updates
   apt-get update && apt-get upgrade -y

   # Implement additional security controls
   # (e.g., 2FA, IP whitelisting, enhanced monitoring)
   ```

4. **Monitor for Recurrence**:
   - Increase logging verbosity
   - Set up additional alerts
   - Monitor for suspicious activity
   - Conduct post-incident review

5. **Gradual Restoration**:
   - Bring systems online one at a time
   - Monitor each system before proceeding
   - Verify data integrity
   - Test functionality

#### Phase 6: Lessons Learned (Post-Incident Activity)

**Objective**: Improve security posture and prevent recurrence.

**Post-Incident Timeline**:
- **Day 1-2**: Root cause analysis draft
- **Day 3-7**: Complete incident report
- **Day 7-14**: Implement corrective actions
- **Day 30**: Review effectiveness of changes

**Incident Report Template**:
```markdown
# Security Incident Report

## Executive Summary
- Incident date/time:
- Incident type:
- Severity level:
- Business impact:
- Status:

## Incident Timeline
| Time | Event | Action Taken |
|------|-------|--------------|
| 2024-02-01 14:30 | Alert triggered | Investigated by Security Analyst |
| 2024-02-01 14:45 | Incident confirmed | IRT activated |
| 2024-02-01 15:00 | Containment started | Blocked malicious IPs |
| 2024-02-01 16:00 | Eradication completed | Removed malware |
| 2024-02-01 18:00 | Recovery completed | Systems restored |

## Root Cause Analysis
- Initial vector: [Phishing email / Vulnerability exploit / Misconfiguration]
- Vulnerability: [CVE-XXXX-XXXX or description]
- Exploited by: [Attacker TTPs]
- Why it wasn't detected earlier: [Gap in monitoring]

## Impact Assessment
- Data affected: [Number of records, data types]
- Systems affected: [List of systems]
- Users affected: [Number of users]
- Regulatory impact: [GDPR notification required, etc.]
- Financial impact: [Estimated costs]

## Corrective Actions Taken
- Immediate: [Actions during incident]
- Short-term: [Actions within 1 week]
- Long-term: [Actions within 1 month]

## Lessons Learned
- What worked well: [Successful aspects of response]
- What didn't work: [Challenges faced]
- Recommendations: [Process improvements]

## Action Items
- [ ] Update incident response plan (add new scenario)
- [ ] Implement additional monitoring for [specific threat]
- [ ] Conduct security training on [topic]
- [ ] Patch [vulnerability] across all systems
```

### Communication Procedures

#### Internal Communication

**Notification Channels**:
- **Urgent**: Phone call, SMS, Slack #incidents channel
- **High**: Email + Slack #incidents
- **Medium/Low**: Email + ticketing system

**Stakeholder Communication**:

| Stakeholder | When to Notify | Who Notifies | What to Include |
|-------------|----------------|--------------|-----------------|
| **IRT Members** | Immediately (Severity 1-2) | Automated Alert | Incident type, severity, initial details |
| **Executive Team** | Within 1 hour (Severity 1-2) | Incident Lead | Business impact, escalation status, ETA |
| **Legal Counsel** | Immediately (data breach) | Incident Lead | Legal exposure, regulatory requirements |
| **IT Operations** | Within 1 hour | Incident Lead | Systems affected, containment actions |
| **HR** | If insider threat | Incident Lead | Employee involved, investigation status |

#### External Communication

**Regulatory Notification**:

| Regulation | Timeframe | Authority | Contact |
|------------|-----------|-----------|---------|
| **GDPR** | 72 hours | Supervisory Authority | Your local DPA |
| **CCPA** | No requirement, but recommended | California Attorney General | N/A |
| **UK GDPR** | 72 hours | ICO | icocasework@ico.org.uk |

**Data Subject Notification**:

**When Required** (GDPR):
- Data breach likely to result in risk to rights/freedoms
- Must notify "without undue delay" (typically within 72 hours)

**Notification Template**:
```markdown
Subject: Important Notice About Your Personal Data

Dear [Candidate Name],

We are writing to inform you about a security incident that may have involved your personal information.

What Happened:
On [date], we discovered [describe incident].

What Information Was Affected:
[List types of data: name, email, resume, etc.]

What We Are Doing:
We have [containment actions]. We are working with [law enforcement/regulators].

What You Can Do:
[Recommend steps: monitor accounts, change passwords, etc.]

Who to Contact:
If you have questions, contact: [contact details]

We sincerely apologize for any inconvenience or concern this may cause.

[Company Name]
```

**Customer/Client Communication**:
- **Severity 1-2**: Notify within 24 hours
- **Severity 3-4**: Notify within 1 week (if any impact)

### Legal & Regulatory Requirements

#### GDPR Breach Notification

**72-Hour Notification** (to Supervisory Authority):
1. **Nature of Breach**: Categories and approximate number of data subjects concerned
2. **Contact Details**: DPO contact information
3. **Consequences**: Likely consequences of the breach
4. **Measures Taken**: Measures taken to address breach and mitigate adverse effects

**Documentation Required** (even if not notified):
- Facts relating to the breach
- Effects of the breach
- Remedial action taken

#### CCPA Breach Notification

**30-Day Notification** (if required):
- No specific breach notification requirement in CCPA
- Follow California Civil Code 1798.82
- Notify if encrypted data is accessed/lost

#### Documentation & Evidence

**Evidence to Preserve**:
- System logs (auth, access, error logs)
- Network traffic captures
- Database query logs
- Audit logs
- Incident response timeline
- Communication logs
- Root cause analysis report
- Remediation actions taken

**Evidence Chain of Custody**:
```bash
# Create forensic image
dd if=/dev/sdb of=/tmp/evidence.img bs=4k conv=noerror,sync

# Calculate checksums
sha256sum /tmp/evidence.img > /tmp/evidence.img.sha256

# Document evidence collection
echo "$(date): Collected evidence image from /dev/sdb" >> /tmp/evidence-chain.txt
```

### Incident Response Drills

**Tabletop Exercises** (Quarterly):
- Simulate data breach scenario
- Walk through incident response steps
- Identify gaps in procedures
- Practice communication procedures

**Red Team Exercises** (Annually):
- Simulated attack by security team
- Test detection and response capabilities
- Identify security gaps
- Validate incident response procedures

**Fire Drills** (Semi-Annually):
- Unannounced incident simulation
- Test response time and procedures
- Evaluate team readiness

### Incident Response Checklist

#### Preparation Checklist
- [ ] Incident response plan documented and approved
- [ ] IRT contact list up-to-date
- [ ] Communication channels established
- [ ] Monitoring and alerting configured
- [ ] Backup and recovery tested
- [ ] Legal notification templates prepared
- [ ] PR communication templates ready
- [ ] Forensic tools available
- [ ] Incident response training completed
- [ ] Tabletop exercise conducted (within last 6 months)

#### Response Checklist (During Incident)
- [ ] Incident detected and verified
- [ ] Severity assessed
- [ ] IRT notified
- [ ] Scope determined (systems, data, users affected)
- [ ] Containment initiated
- [ ] Evidence preserved
- [ ] Root cause identified
- [ ] Eradication completed
- [ ] Recovery initiated
- [ ] Systems restored and verified
- [ ] Monitoring enhanced post-incident

#### Post-Incident Checklist
- [ ] Root cause analysis completed
- [ ] Incident report written and distributed
- [ ] Regulatory notifications sent (if required)
- [ ] Data subject notifications sent (if required)
- [ ] Executive briefing delivered
- [ ] Lessons learned documented
- [ ] Corrective actions implemented
- [ ] Security controls updated
- [ ] Policies updated
- [ ] Training updated (if needed)
- [ ] Incident response plan updated
- [ ] Follow-up review scheduled (30 days)

---

## Security Testing

### Overview

**Security testing** is essential for identifying vulnerabilities before attackers can exploit them. This section provides a comprehensive security testing checklist covering automated scans, manual testing, penetration testing, and continuous security validation.

### Testing Strategy

The system follows a **defense-in-depth testing approach**:

| Testing Type | Frequency | Scope | Automation |
|--------------|-----------|-------|------------|
| **SAST** | Every commit | Source code | Automated (CI/CD) |
| **SCA** | Daily | Dependencies | Automated |
| **DAST** | Weekly | Running application | Automated |
| **Container Scanning** | Every build | Docker images | Automated |
| **Infrastructure Scanning** | Daily | Cloud/Server config | Automated |
| **Penetration Testing** | Annually | Full system | Manual |
| **Red Team Exercises** | Annually | Full system (attacks) | Manual |

### 1. Static Application Security Testing (SAST)

**Objective**: Find security vulnerabilities in source code before deployment.

#### Automated SAST Tools

**Bandit** (Python):
```bash
# Run in CI/CD pipeline
bandit -r backend/ -f json -o bandit-report.json

# Exit on high-severity findings
bandit -r backend/ -lll
```

**Semgrep** (Multi-language):
```bash
# Custom security rules
semgrep --config=security-tests/semgrep-rules/ backend/

# Check for common vulnerabilities
semgrep --config=auto backend/
```

**PyLint with Security Checks**:
```bash
pylint --enable=W0102,W0611,W0702,E1120 backend/
```

#### Security Checks to Implement

**SQL Injection Prevention**:
```python
# ❌ BAD - String concatenation
query = f"SELECT * FROM candidates WHERE id = {user_id}"

# ✅ GOOD - Parameterized query
query = "SELECT * FROM candidates WHERE id = %s"
cursor.execute(query, (user_id,))
```

**XSS Prevention**:
```python
# ❌ BAD - Unsanitized output
return HttpResponse(f"<div>{user_input}</div>")

# ✅ GOOD - Escaped output
from html import escape
return HttpResponse(f"<div>{escape(user_input)}</div>")
```

**Path Traversal Prevention**:
```python
# ❌ BAD - Unvalidated path
file_path = f"/uploads/{filename}"

# ✅ GOOD - Validated path
from pathlib import Path
upload_dir = Path("/uploads")
file_path = (upload_dir / filename).resolve()
if not file_path.is_relative_to(upload_dir):
    raise ValueError("Invalid filename")
```

**Hardcoded Secrets Detection**:
```bash
# Use gitleaks to detect secrets in code
gitleaks detect --source . --report-format json --report-path gitleaks-report.json
```

#### SAST Checklist

- [ ] **SQL Injection**: All database queries use parameterized queries or ORM
- [ ] **XSS**: All user output is HTML-escaped
- [ ] **CSRF**: All state-changing operations have CSRF tokens
- [ ] **Authentication**: Password hashing (bcrypt/argon2), never store plaintext
- [ ] **Authorization**: Every endpoint checks user permissions
- [ ] **Path Traversal**: File paths are validated and sanitized
- [ ] **Command Injection**: No shell commands with user input
- [ ] **Insecure Deserialization**: Validate serialized data
- [ ] **Hardcoded Secrets**: No API keys, passwords, tokens in code
- [ ] **Error Messages**: No sensitive data in error messages
- [ ] **Logging**: No sensitive data (passwords, tokens) in logs
- [ ] **Cryptographic Issues**: Use up-to-date algorithms (AES-256, SHA-256)

---

### 2. Software Composition Analysis (SCA)

**Objective**: Identify vulnerabilities in dependencies and third-party libraries.

#### Automated Dependency Scanning

**Safety** (Python dependencies):
```bash
# Check for vulnerable dependencies
safety check --json > safety-report.json

# Scan requirements files
safety check -r requirements.txt
```

**Pip Audit** (Python):
```bash
# Audit installed packages
pip-audit --format json --output pip-audit-report.json

# Audit requirements files
pip-audit --requirement requirements.txt
```

**Dependabot** (GitHub):
```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/backend"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
```

**Trivy** (Multi-language):
```bash
# Scan Python dependencies
trivy fs --format json --output trivy-deps.json --security-checks vuln,license backend/

# Scan for vulnerabilities and license issues
trivy config . --security-checks vuln,config,license
```

#### SCA Best Practices

1. **Automated Scanning**:
   - Run in CI/CD pipeline on every commit
   - Fail build for high/critical vulnerabilities
   - Generate SBOM (Software Bill of Materials)

2. **Dependency Updates**:
   - Subscribe to security advisories
   - Update dependencies regularly (monthly)
   - Use Dependabot/Renovate for automated PRs

3. **Vulnerability Triageage**:
   - Prioritize based on CVSS score and exploitability
   - Check if vulnerable code is actually used
   - Assess impact on application functionality

4. **License Compliance**:
   - Scan for problematic licenses (GPL, AGPL)
   - Maintain license inventory
   - Ensure compliance with open-source licenses

#### SCA Checklist

- [ ] **Automated Scanning**: SCA integrated into CI/CD pipeline
- [ ] **Vulnerability Alerts**: Configured for all dependencies
- [ ] **CVSS Scoring**: Vulnerabilities assessed by severity
- [ ] **Remediation Timeline**:
  - [ ] Critical (9.0-10.0): Patch within 48 hours
  - [ ] High (7.0-8.9): Patch within 1 week
  - [ ] Medium (4.0-6.9): Patch within 1 month
  - [ ] Low (0.1-3.9): Patch in next release cycle
- [ ] **Dependency Inventory**: List of all dependencies and versions
- [ ] **License Inventory**: All licenses documented and compliant
- [ ] **SBOM**: Software Bill of Materials generated
- [ ] **Vulnerable Code Usage**: Verify vulnerable functions are not called
- [ ] **Update Policy**: Regular dependency updates scheduled
- [ ] **Transitive Dependencies**: All indirect dependencies scanned

---

### 3. Dynamic Application Security Testing (DAST)

**Objective**: Find vulnerabilities in running applications.

#### Automated DAST Tools

**OWASP ZAP** (Zed Attack Proxy):
```bash
# Automated scan in CI/CD
zap-baseline.py -t http://localhost:8000 -r zap-report.html

# API scan
zap-api-scan.py -t http://localhost:8000/openapi.json -f openapi -r zap-api-report.html
```

**Nuclei** (Vulnerability scanner):
```bash
# Scan running application
nuclei -u http://localhost:8000 -t /path/to/nuclei-templates/ -severity critical,high,medium -o nuclei-report.txt

# Scan with specific templates
nuclei -u http://localhost:8000 -t cves/ -o nuclei-cves.txt
```

**SQLMap** (SQL injection testing):
```bash
# Test for SQL injection (authorize with your own testing environment only!)
sqlmap -u "http://localhost:8000/api/candidates?id=1" --batch --dbms=postgresql --level=1 --risk=1
```

#### Manual DAST Testing

**Authentication & Authorization Testing**:
```bash
# Test for broken authentication
# 1. Try accessing protected endpoints without authentication
curl http://localhost:8000/api/candidates -H "Authorization:"

# 2. Try accessing other users' data
curl http://localhost:8000/api/candidates/USER_ID_2 -H "Authorization: Bearer USER_1_TOKEN"

# 3. Test privilege escalation
# (Admin user accessing recruiter-only endpoints, etc.)
```

**Input Validation Testing**:
```bash
# Test for SQL injection
curl -X POST http://localhost:8000/api/candidates/search \
  -H "Content-Type: application/json" \
  -d '{"vacancy_id": "1 OR 1=1--"}'

# Test for XSS
curl -X POST http://localhost:8000/api/candidates \
  -H "Content-Type: application/json" \
  -d '{"name": "<script>alert(\"XSS\")</script>"}'

# Test for command injection
curl -X POST http://localhost:8000/api/upload \
  -F "file=@test.pdf; filename=$(whoami)"
```

**API Security Testing**:
```bash
# Test for rate limiting
for i in {1..1000}; do curl http://localhost:8000/api/candidates; done

# Test for mass assignment
curl -X PUT http://localhost:8000/api/users/1 \
  -H "Content-Type: application/json" \
  -d '{"is_admin": true}'

# Test for IDOR (Insecure Direct Object Reference)
curl http://localhost:8000/api/candidates/OTHER_USER_ID
```

#### DAST Checklist

- [ ] **Authentication Tested**:
  - [ ] Weak passwords allowed
  - [ ] Session fixation
  - [ ] Logout functionality
  - [ ] Session timeout
- [ ] **Authorization Tested**:
  - [ ] Horizontal privilege escalation (access other users' data)
  - [ ] Vertical privilege escalation (regular user → admin)
  - [ ] Missing authorization on API endpoints
  - [ ] Bypassing authorization checks
- [ ] **Input Validation Tested**:
  - [ ] SQL injection on all input fields
  - [ ] XSS on all input/output fields
  - [ ] Command injection
  - [ ] Path traversal
  - [ ] LDAP injection
  - [ ] XXE (XML External Entity)
- [ ] **API Security Tested**:
  - [ ] Rate limiting enforced
  - [ ] Mass assignment prevented
  - [ ] IDOR vulnerabilities
  - [ ] Excessive data exposure
  - [ ] Improper asset management
- [ ] **Session Management Tested**:
  - [ ] Session timeout configured
  - [ ] Secure cookies (HttpOnly, Secure, SameSite)
  - [ ] Session fixation prevented
  - [ ] Logout invalidates session
- [ ] **Error Handling Tested**:
  - [ ] Stack traces not exposed
  - [ ] Sensitive data not in error messages
  - [ ] Custom error pages

---

### 4. Container Security Testing

**Objective**: Ensure Docker images and containers are secure.

#### Container Image Scanning

**Trivy**:
```bash
# Scan Docker image for vulnerabilities
trivy image agenthr-backend:latest --format json --output trivy-image.json

# Scan with severity filtering
trivy image agenthr-backend:latest --severity HIGH,CRITICAL

# Scan for vulnerabilities and misconfigurations
trivy image agenthr-backend:latest --security-checks vuln,config,secret
```

**Grype** (Anchore):
```bash
# Scan Docker image
grype agenthr-backend:latest -o json -f grype-report.json

# Scan by severity
grype agenthr-backend:latest --fail-on high
```

#### Dockerfile Security Best Practices

```dockerfile
# ✅ GOOD - Secure Dockerfile
FROM python:3.11-slim

# Use non-root user
RUN adduser --disabled-password --gecos '' appuser

# Install security updates
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=appuser:appuser . /app
WORKDIR /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Minimal attack surface
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Container Security Checklist

- [ ] **Base Image**: Use minimal, official images (alpine, slim)
- [ ] **Non-Root User**: Container runs as non-privileged user
- [ ] **Image Scanning**: All images scanned for vulnerabilities
- [ ] **No Secrets**: No secrets in Dockerfile or image layers
- [ ] **Minimal Packages**: Only necessary packages installed
- [ ] **Security Updates**: Base images updated regularly
- [ ] **File Permissions**: Sensitive files have restricted permissions
- [ ] **Network**: Containers isolated, minimal exposed ports
- [ ] **Resource Limits**: CPU/memory limits configured
- [ ] **Read-Only**: Container filesystem read-only where possible
- [ ] **Health Checks**: Health check endpoints configured
- [ ] **Signatures**: Images signed (Docker Content Trust)

---

### 5. Infrastructure Security Testing

**Objective**: Validate cloud and server configurations.

#### Infrastructure as Code (IaC) Scanning

**Terraform Security Scanning**:
```bash
# Scan Terraform files
tfsec . --format json --output tfsec-report.json

# Check for misconfigurations
checkov -d . -o json > checkov-report.json
```

**Kubernetes Configuration Scanning**:
```bash
# Scan Kubernetes manifests
kube-score score k8s/*.yaml --output-format cm-aware

# Check for security issues
kubesec scan k8s/deployment.yaml
```

#### Cloud Security Scanning

**AWS Security Hub** (if using AWS):
```bash
# Run security checks
aws securityhub get-findings --severity_normalized HIGH

# Enable CIS benchmarks
aws securityhub enable-security-hub --enable-standards \
  arn:aws:securityhub:::standards/aws-foundational-security-best-practices/v/1.0.0
```

#### Infrastructure Security Checklist

- [ ] **S3 Buckets**: No public access, encryption enabled
- [ ] **Databases**: No public access, encryption at rest/transit
- [ ] **IAM Roles**: Least privilege, no hardcoded credentials
- [ ] **Security Groups**: Minimal ports, IP whitelisting
- [ ] **TLS**: All communications encrypted (HTTPS, WSS)
- [ ] **Secrets Management**: Secrets stored in vault (not env vars)
- [ ] **Monitoring**: CloudWatch, logs, metrics configured
- [ ] **Backup**: Automated backups, recovery tested
- [ ] **CIS Benchmarks**: Aligned with CIS hardening guides

---

### 6. Penetration Testing

**Objective**: Manual, comprehensive security assessment by security professionals.

#### Penetration Testing Scope

**In-Scope**:
- Backend API (`*.api.example.com`)
- Frontend application (`app.example.com`)
- Admin panel (`admin.example.com`)
- Authentication mechanisms
- File upload functionality
- Database security
- API endpoints

**Out-of-Scope** (typically):
- Third-party services (LLM providers, S3 storage)
- Physical security
- Social engineering
- Denial of service attacks

#### Penetration Testing Methodology

1. **Reconnaissance**:
   - Information gathering
   - DNS enumeration
   - Technology stack identification

2. **Scanning**:
   - Vulnerability scanning
   - Port scanning
   - Service enumeration

3. **Exploitation**:
   - Attempt to exploit vulnerabilities
   - Test authentication bypass
   - Test authorization bypass

4. **Post-Exploitation**:
   - Determine impact
   - Lateral movement
   - Data exfiltration

5. **Reporting**:
   - Document findings
   - Prioritize by risk
   - Provide remediation guidance

#### Penetration Testing Checklist

- [ ] **Planning**: Scope, rules of engagement, timelines defined
- [ ] **Vendor Selection**: Reputable, certified penetration testing firm
- [ ] **Testing Schedule**: Annual or after major changes
- [ ] **Authorization**: Written authorization for testing
- [ ] **Communication**: Point of contact established
- [ ] **Testing Types**:
  - [ ] Black box (no prior knowledge)
  - [ ] Gray box (some knowledge, like user credentials)
  - [ ] White box (full knowledge, including source code)
- [ ] **Findings Report**: Detailed vulnerabilities with CVSS scores
- [ ] **Remediation**: Fix all high/critical findings
- [ ] **Re-testing**: Verify fixes within 30 days
- [ ] **Executive Summary**: High-level overview for management

---

### 7. Continuous Security Monitoring

**Objective**: Ongoing security validation and threat detection.

#### Security Monitoring Stack

**Prometheus + Grafana** (Metrics):
```yaml
# Security-related metrics
- Failed authentication attempts
- Rate of API requests per user
- Database query volume
- File upload count and size
- System resource usage
```

**Loki** (Log Aggregation):
```yaml
# Security logs to monitor
- Authentication logs
- Authorization failures
- Database access logs
- API error logs
- System logs
```

**AlertManager** (Alerting):
```yaml
# Security alerts
groups:
  - name: security
    rules:
      - alert: BruteForceAttack
        expr: rate(failed_logins[5m]) > 10
        annotations:
          summary: "Brute force attack detected"
          description: "{{ $value }} failed logins per second"

      - alert: DatabaseAnomaly
        expr: rate(db_queries[1h]) > 10000
        annotations:
          summary: "Unusual database activity"
```

#### Continuous Monitoring Checklist

- [ ] **Metrics**: Security metrics collected and visualized
- [ ] **Alerts**: Configured for suspicious activity
- [ ] **Logs**: All security-relevant logs centralized
- [ ] **Dashboards**: Grafana dashboards for security monitoring
- [ ] **Threat Intelligence**: CVE feeds integrated
- [ ] **Baseline**: Normal behavior baseline established
- [ ] **Anomaly Detection**: Automated detection of anomalies
- [ ] **Response**: Incident response team notified of alerts

---

### 8. Security Testing Checklist (Summary)

#### Automated Testing (CI/CD)
- [ ] **SAST**: Runs on every commit (Bandit, Semgrep)
- [ ] **SCA**: Runs daily (Safety, Pip-Audit)
- [ ] **Secret Scanning**: Runs on every commit (Gitleaks)
- [ ] **Container Scanning**: Runs on every build (Trivy)
- [ ] **IaC Scanning**: Runs on infrastructure changes (tfsec, checkov)

#### Manual Testing (Periodic)
- [ ] **Penetration Testing**: Annual (external vendor)
- [ ] **Red Team Exercise**: Annual (internal team)
- [ ] **Security Review**: Before major releases
- [ ] **Architecture Review**: Quarterly
- [ ] **Code Review**: Security-focused peer review

#### Documentation
- [ ] **Testing Plan**: Documented testing schedule
- [ ] **Test Results**: All test results archived
- [ ] **Remediation Tracker**: Vulnerability tracking and remediation
- [ ] **Security Reports**: Quarterly security assessment reports

---

## Vulnerability Disclosure

### Overview

A **vulnerability disclosure policy** (VDP) provides clear guidelines for security researchers to report security vulnerabilities responsibly. This encourages the security community to help improve the system's security while protecting both researchers and the organization.

### Disclosure Policy

#### Reporting Security Vulnerabilities

**We Welcome Responsible Disclosure**:

If you discover a security vulnerability in the AgentHR Resume Analysis System, we encourage you to report it to us responsibly. We appreciate your help in keeping our users and their data safe.

#### How to Report

**Reporting Channels**:

| Method | Contact | Response Time | Use For |
|--------|---------|---------------|---------|
| **Email** | security@company.com | 24 hours | All vulnerability reports |
| **PGP Key** | Available at: https://company.com/pgp-key.txt | 24 hours | Encrypted reports |
| **HackerOne** | https://hackerone.com/company | 48 hours | Coordinated disclosure |
| **Bug Bounty** | https://company.com/bug-bounty | 48 hours | Paid bug bounty program |

**Report Format**:

Please include the following information in your report:

```markdown
Subject: Security Vulnerability Report - [Vulnerability Name]

## Vulnerability Summary
- Vulnerability Type: [SQL Injection / XSS / etc.]
- Severity: [Critical / High / Medium / Low]
- Affected Components: [API endpoint, URL, module]

## Vulnerability Description
[Describe the vulnerability in detail]

## Steps to Reproduce
1. [Step 1]
2. [Step 2]
3. [Step 3]
[Include proof of concept: code snippets, screenshots, videos]

## Impact
[Describe the impact: data exposure, privilege escalation, etc.]

## Suggested Fix (Optional)
[If you have a suggestion for how to fix it]

## Additional Information
- Your name/handle: [Optional - for credit]
- Your preferred contact method: [Email, Twitter, etc.]
```

#### What to Expect

**Our Commitment**:

- **Response Time**: We will acknowledge your report within 24-48 hours
- **Updates**: We will provide regular updates on remediation progress
- **Timeline**: We aim to fix critical vulnerabilities within 7 days, high within 14 days
- **Credit**: We will credit you in our security advisories (if you wish)
- **Safe Harbor**: We will not pursue legal action if you follow this policy

**Remediation Timeline**:

| Severity | Initial Response | Fix Timeline | Public Disclosure |
|----------|------------------|--------------|-------------------|
| **Critical** | 24 hours | 7 days | After fix deployed |
| **High** | 48 hours | 14 days | After fix deployed |
| **Medium** | 3 days | 30 days | After fix deployed |
| **Low** | 7 days | 90 days | Next release |

### Safe Harbor

**What We Ask**:

To qualify for safe harbor under this policy, please:

1. **Don't Break the System**:
   - [ ] Do not access, modify, or delete data that is not yours
   - [ ] Do not use automated tools at high rates (causing DoS)
   - [ ] Do not disrupt service for other users
   - [ ] Do not test on users' data without consent

2. **Respect Privacy**:
   - [ ] Only access data you have created for testing
   - [ ] Do not exfiltrate PII or confidential data
   - [ ] Do not share data with third parties
   - [ ] Delete test data after reporting

3. **Responsible Disclosure**:
   - [ ] Report vulnerabilities through official channels
   - [ ] Provide reasonable time for remediation before public disclosure
   - [ ] Do not exploit the vulnerability for any malicious purpose
   - [ ] Do not sell or trade vulnerability information

**What We Promise**:

- **No Legal Action**: We will not pursue legal action if you follow this policy
- **Credit**: We will acknowledge your contribution (with your permission)
- **Bug Bounty**: We may offer monetary rewards for qualifying vulnerabilities (see below)
- **Swag**: We may send company swag as a thank you

### Out of Scope (Not Eligible)

The following are **out of scope** and do not qualify for safe harbor or bug bounty:

- **Third-Party Vulnerabilities**: Issues in LLM providers, cloud services, libraries
- **Social Engineering**: Phishing, impersonation, social manipulation
- **Physical Security**: Physical access to offices, servers, devices
- **Denial of Service**: DoS/DDoS attacks that disrupt service
- **Spam**: Sending unsolicited emails to users
- **UI/UX Bugs**: Visual issues, typos, usability problems
- **Known Issues**: Vulnerabilities already publicly disclosed
- **Missing Best Practices**: Missing security headers, lack of hardening (informational only)

### Bug Bounty Program

**Rewards** (if applicable):

| Severity | Reward Range | Example Vulnerabilities |
|----------|--------------|--------------------------|
| **Critical** | $1,000 - $5,000 | SQL injection, authentication bypass, data breach |
| **High** | $500 - $1,000 | XSS, CSRF, privilege escalation |
| **Medium** | $100 - $500 | Information disclosure, security misconfiguration |
| **Low** | $50 - $100 | Missing headers, minor info disclosure |

**Bounty Qualification Criteria**:

- [ ] **First to Report**: Only the first reporter receives bounty
- [ ] **Technical Detail**: Provide clear reproduction steps and impact
- [ ] **Original Research**: Not previously reported or known
- [ ] **In Scope**: Vulnerability is within scope (see above)
- [ ] **Responsible**: Followed safe harbor guidelines
- [ ] **No Exploitation**: No data accessed, modified, or exfiltrated
- [ ] **Remediation Confirmed**: Vendor confirmed and reproduced the vulnerability

**Reward Disbursement**:

- **Method**: PayPal, wire transfer, or donation to charity
- **Timeline**: Within 30 days of vulnerability fix
- **Tax**: Recipient responsible for any applicable taxes
- **Credit**: Name/handle credited in security advisory (optional)

### Coordinated Vulnerability Disclosure (CVD)

**Disclosure Process**:

1. **Report Received**: Vulnerability reported by researcher
2. **Triage & Validation**: Security team validates vulnerability (24-48 hours)
3. **Remediation**: Development team fixes vulnerability (7-90 days, depending on severity)
4. **Testing**: Internal testing and verification of fix
5. **Deployment**: Fix deployed to production
6. **Disclosure**: Public security advisory published

**Security Advisory Template**:

```markdown
# Security Advisory: [Vulnerability Title]

## Summary
[Brief description of the vulnerability]

## Affected Versions
- [All versions before X.Y.Z]
- [Versions A.B.C through D.E.F]

## Patched Versions
- [Version X.Y.Z or later]

## Vulnerability Details
- **CVE ID**: [CVE-YYYY-NNNN] (if assigned)
- **CWE ID**: [CWE-NNN] (Common Weakness Enumeration)
- **Severity**: [CVSS 3.1 Score / Severity Level]
- **Impact**: [Description of impact]
- **Attack Vector**: [Description of how to exploit]

## Proof of Concept
[Description of how to reproduce (sanitized)]

## Credits
Discovered by: [Researcher name/handle]
Reported on: [Date]

## Recommendations
[Upgrade to patched version or apply workaround]

## References
- [Commit/PR with fix]
- [Related documentation]
- [Other resources]

## Timeline
- [Date] - Vulnerability reported
- [Date] - Vulnerability confirmed
- [Date] - Patch released
- [Date] - Advisory published
```

**Disclosure Timing**:

- **Critical**: Publish advisory 7 days after fix (or after exploit appears in the wild)
- **High**: Publish advisory 14 days after fix
- **Medium**: Publish advisory 30 days after fix
- **Low**: Publish advisory with next release notes

### Security Acknowledgments

**Hall of Fame** (optional):

We recognize the contributions of security researchers who have helped make our system more secure:

| Researcher | Vulnerabilities | Date |
|------------|-----------------|------|
| @researcher1 | SQL Injection in search API | 2024-01-15 |
| @securitypro | XSS in candidate profile | 2024-02-20 |
| @hacker123 | CSRF in vacancy creation | 2024-03-10 |

### Contact Information

**Security Team**:
- **Email**: security@company.com
- **PGP Key**: https://company.com/pgp-key.txt
- **Key Fingerprint**: `XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX`

**General Inquiries**:
- **Email**: info@company.com
- **Website**: https://company.com
- **Twitter**: @company

### Vulnerability Disclosure Checklist

- [ ] **Policy Published**: Vulnerability disclosure policy published on website
- [ ] **Reporting Email**: security@ email address configured and monitored
- [ ] **PGP Key**: Public PGP key available for encrypted reports
- [ ] **Response SLA**: 24-48 hour initial response time commitment
- [ ] **Safe Harbor**: Legal safe harbor for responsible disclosure documented
- [ ] **Remediation Timeline**: Defined fix timelines by severity
- [ ] **Bug Bounty**: Bug bounty program rules and rewards (if applicable)
- [ ] **HackerOne Program**: HackerOne or similar platform setup (if applicable)
- [ ] **Security Advisories**: Template for security advisories prepared
- [ ] **Credit Policy**: Researcher credit and acknowledgment policy
- [ ] **Scope Documentation**: Clear in-scope and out-of-scope documentation
- [ ] **Response Team**: Security team designated and trained
- [ ] **Escalation**: Escalation process for critical vulnerabilities
- [ ] **Legal Review**: Policy reviewed by legal counsel
- [ ] **Regular Updates**: Policy reviewed and updated annually

---

## Security Checklist

### Overview

This comprehensive **security checklist** consolidates all security requirements and best practices into a single, actionable checklist. Use this to verify security posture before production deployments, after major changes, or for periodic security assessments.

### Quick Reference Checklist

#### Critical Security Controls (Must Have)

- [ ] **Authentication**: Multi-factor authentication (MFA) for admin access
- [ ] **Password Policy**: Strong password requirements (12+ chars, complexity)
- [ ] **Password Hashing**: bcrypt/argon2 with minimum 12 rounds
- [ ] **TLS/HTTPS**: All communications encrypted (TLS 1.3)
- [ ] **Database Encryption**: Encryption at rest for sensitive data
- [ ] **Input Validation**: All user input validated and sanitized
- [ ] **SQL Injection**: Parameterized queries or ORM only
- [ ] **XSS Prevention**: HTML encoding for all user output
- [ ] **CSRF Protection**: CSRF tokens on all state-changing operations
- [ ] **Access Control**: Role-based access control (RBAC) implemented
- [ ] **Audit Logging**: All security-relevant events logged
- [ ] **Error Handling**: No sensitive data in error messages
- [ ] **Dependencies**: All dependencies scanned for vulnerabilities
- [ ] **Secrets Management**: No hardcoded secrets, use vault
- [ ] **Backup**: Automated backups with restoration tested
- [ ] **Monitoring**: Security metrics and alerting configured

### Comprehensive Security Checklist

#### 1. Authentication & Authorization

**Password Policy**:
- [ ] Minimum 12 characters
- [ ] Require uppercase, lowercase, numbers, special characters
- [ ] Password history (prevent reuse of last 5 passwords)
- [ ] Account lockout after 5 failed attempts (15-minute lockout)
- [ ] Password expiration (90 days) - *Note: NIST now recommends no expiration unless compromised*
- [ ] Password strength meter on user-facing forms

**Password Storage**:
- [ ] Passwords hashed using bcrypt or argon2
- [ ] Minimum work factor 12 for bcrypt
- [ ] Unique salt per password (automatic with bcrypt/argon2)
- [ ] No password encryption (hashing only)
- [ ] No password hashing with MD5, SHA1, SHA256 (use bcrypt/argon2)

**Multi-Factor Authentication (MFA)**:
- [ ] MFA required for admin accounts
- [ ] MFA optional for regular users (recommended)
- [ ] TOTP-based (Google Authenticator, Authy) supported
- [ ] Backup codes provided
- [ ] MFA bypass recovery process documented

**Session Management**:
- [ ] Session timeout after 30 minutes of inactivity
- [ ] Secure cookie flags: HttpOnly, Secure, SameSite=Strict
- [ ] Session ID regeneration after login
- [ ] Logout functionality invalidates session
- [ ] No session fixation vulnerabilities

**Authorization**:
- [ ] Role-based access control (RBAC) implemented
- [ ] Principle of least privilege enforced
- [ ] Authorization checks on every API endpoint
- [ ] No privilege escalation vulnerabilities
- [ ] No direct object reference (IDOR) vulnerabilities
- [ ] Admin-only endpoints properly protected

#### 2. Data Security

**Encryption at Rest**:
- [ ] Database encryption enabled (PostgreSQL: pgcrypto)
- [ ] File storage encrypted (LUKS, EBS encryption)
- [ ] Backup files encrypted
- [ ] Encryption key management system (AWS KMS, HashiCorp Vault)
- [ ] AES-256 encryption algorithm used

**Encryption in Transit**:
- [ ] TLS 1.3 enforced (minimum TLS 1.2)
- [ ] HTTPS for all web traffic
- [ ] Database connections encrypted (PostgreSQL SSL)
- [ ] API calls encrypted (HTTPS, not HTTP)
- [ ] Certificate management and renewal automated
- [ ] HSTS header enabled

**PII Data Protection**:
- [ ] Data minimization (only collect necessary data)
- [ ] Data retention policy implemented (2 years for resumes)
- [ ] Automated deletion after retention period
- [ ] Right to erasure implemented (GDPR)
- [ ] Right to access implemented (DSAR endpoint)
- [ ] Data masking in logs (no passwords, tokens in logs)

**Data Backup**:
- [ ] Automated daily backups
- [ ] Backup retention: 30 days (configurable)
- [ ] Backup encryption enabled
- [ ] Backup off-site storage (S3, remote server)
- [ ] Backup restoration tested quarterly
- [ ] Backup integrity verification (checksums)

#### 3. Application Security

**Input Validation**:
- [ ] All user input validated on server-side
- [ ] Allow-list approach (not block-list)
- [ ] Length limits enforced on all inputs
- [ ] Type validation (integer, string, email, etc.)
- [ ] File upload validation (type, size, content)
- [ ] Path traversal prevention

**Output Encoding**:
- [ ] HTML encoding for all user output in web pages
- [ ] JavaScript encoding for data in scripts
- [ ] URL encoding for data in URLs
- [ ] JSON encoding for API responses
- [ ] No unescaped user input in responses

**SQL Injection Prevention**:
- [ ] Parameterized queries only (no string concatenation)
- [ ] ORM used (SQLAlchemy) with safe query methods
- [ ] No dynamic SQL with user input
- [ ] Database principle of least privilege (no dba user for app)
- [ ] SQL injection tested in penetration test

**XSS Prevention**:
- [ ] Content Security Policy (CSP) header enabled
- [ ] X-XSS-Protection header enabled
- [ ] HTML escaping for all user output
- [ ] No `innerHTML` with user input
- [ ] DOM-based XSS tested
- [ ] XSS tested in penetration test

**CSRF Prevention**:
- [ ] CSRF tokens on all state-changing operations
- [ ] Token validated on server-side
- [ ] SameSite cookie attribute set
- [ ] CSRF token refreshed on login
- [ ] CSRF tested in penetration test

**File Upload Security**:
- [ ] File type validation (by content, not extension)
- [ ] File size limit enforced (max 10MB)
- [ ] Virus/malware scanning implemented
- [ ] Uploaded files stored outside webroot
- [ ] Random filename generated on upload
- [ ] File execution prevented (no execute permission)

#### 4. API Security

**Authentication**:
- [ ] API key or token-based authentication
- [ ] JWT tokens signed and verified
- [ ] Token expiration enforced (short-lived tokens)
- [ ] Token refresh mechanism implemented
- [ ] Invalid tokens revoked

**Rate Limiting**:
- [ ] Rate limiting on all public endpoints
- [ ] Rate limiting on authentication endpoints
- [ ] Different limits per user role
- [ ] Rate limit exceeded returns 429 status
- [ ] Distributed rate limiting (Redis-based)

**API Versioning**:
- [ ] API versioning strategy (/api/v1/, /api/v2/)
- [ ] Deprecation policy for old versions
- [ ] Breaking changes documented in changelog

**API Security Headers**:
- [ ] `X-Content-Type-Options: nosniff`
- [ ] `X-Frame-Options: DENY`
- [ ] `X-XSS-Protection: 1; mode=block`
- [ ] `Strict-Transport-Security: max-age=31536000`
- [ ] `Content-Security-Policy` configured
- [ ] `Referrer-Policy: strict-origin-when-cross-origin`

**Input Validation (API)**:
- [ ] Request schema validation (Pydantic)
- [ ] JSON validation
- [ ] Type validation
- [ ] SQL injection tested
- [ ] Mass assignment prevented

#### 5. Network Security

**Firewall Configuration**:
- [ ] Only necessary ports open (80, 443, 22 for SSH)
- [ ] SSH restricted to specific IPs (firewall rule)
- [ ] Database not accessible from internet
- [ ] Intrusion detection/prevention system (IDS/IPS)
- [ ] DDoS protection enabled (Cloudflare, AWS Shield)

**TLS Configuration**:
- [ ] TLS 1.3 preferred, TLS 1.2 minimum
- [ ] Strong cipher suites only
- [ ] Certificate signed by trusted CA
- [ ] Certificate expiration monitored
- [ ] Certificate renewal automated (Let's Encrypt)

**Network Segmentation**:
- [ ] Docker network isolation
- [ ] Database on private network
- [ ] Redis on private network
- [ ] No inter-container communication unless required

#### 6. Logging & Monitoring

**Audit Logging**:
- [ ] All authentication attempts logged
- [ ] All authorization failures logged
- [ ] All data access logged
- [ ] All configuration changes logged
- [ ] Audit log retention: 90 days (configurable)
- [ ] Audit logs tamper-evident (append-only, signed)

**Security Monitoring**:
- [ ] Failed login attempts monitored and alerted
- [ ] Brute force attack detection (>10 failures in 5 minutes)
- [ ] Anomaly detection (unusual API usage, data access)
- [ ] Security metrics dashboard (Grafana)
- [ ] Real-time alerting (Prometheus AlertManager)

**Log Security**:
- [ ] No sensitive data in logs (passwords, tokens, PII)
- [ ] Log access controlled
- [ ] Log aggregation (Loki, ELK)
- [ ] Log retention configured (30 days for app logs)
- [ ] Log rotation configured

#### 7. Dependency Management

**Vulnerability Scanning**:
- [ ] Automated SAST in CI/CD (Bandit, Semgrep)
- [ ] Automated SCA in CI/CD (Safety, pip-audit)
- [ ] Dependency scanning daily
- [ ] Zero-day vulnerability monitoring
- [ ] CVSS scores for vulnerabilities

**Dependency Updates**:
- [ ] Regular dependency updates (monthly)
- [ ] Dependabot or Renovate configured
- [ ] Security patches applied within SLA:
  - [ ] Critical: 48 hours
  - [ ] High: 1 week
  - [ ] Medium: 1 month
- [ ] Outdated dependencies monitored

**Third-Party Risk Assessment**:
- [ ] Security assessment for all third-party services
- [ ] Data Processing Agreements (DPA) signed
- [ ] GDPR compliance verified for EU data processors
- [ ] Service level agreements (SLA) reviewed

#### 8. Infrastructure Security

**Container Security**:
- [ ] Docker images scanned (Trivy)
- [ ] Minimal base images used (alpine, slim)
- [ ] Containers run as non-root user
- [ ] No secrets in Dockerfiles or images
- [ ] Container resource limits configured

**Cloud Security** (if applicable):
- [ ] S3 buckets not publicly accessible
- [ ] IAM roles follow least privilege
- [ ] Security groups minimal access
- [ ] CloudTrail enabled (AWS)
- [ ] CIS benchmarks compliance

**Server Hardening**:
- [ ] SSH key-based authentication only (no passwords)
- [ ] SSH root login disabled
- [ ] Unnecessary services disabled
- [ ] System updates applied regularly
- [ ] CIS hardening guidelines followed

#### 9. Compliance

**GDPR Compliance**:
- [ ] Legal basis for processing documented
- [ ] Records of Processing Activities (ROPA) maintained
- [ ] Data Protection Impact Assessment (DPIA) completed
- [ ] Data subject rights implemented:
  - [ ] Right to access (DSAR endpoint)
  - [ ] Right to erasure (deletion endpoint)
  - [ ] Right to rectification (update endpoint)
  - [ ] Right to portability (export endpoint)
  - [ ] Right to object (objection tracking)
- [ ] Privacy policy published
- [ ] Cookie consent implemented (if applicable)
- [ ] Data breach notification process (72 hours)
- [ ] Data Protection Officer (DPO) appointed (if required)

**CCPA Compliance**:
- [ ] Privacy policy includes CCPA disclosures
- [ ] Right to know implemented (data access)
- [ ] Right to delete implemented
- [ ] Right to opt-out implemented (if selling data)
- [ ] Do Not Sell My Info link (if applicable)
- [ ] Non-discrimination policy documented

**Data Retention**:
- [ ] Data retention policy documented
- [ ] Retention periods configured:
  - [ ] Candidate resumes: 2 years
  - [ ] Audit logs: 90 days
  - [ ] Backups: 30 days
  - [ ] Application logs: 30 days
- [ ] Automated deletion process
- [ ] Deletion logging

#### 10. Incident Response

**Incident Response Plan**:
- [ ] Incident response plan documented
- [ ] Incident response team (IRT) established
- [ ] Roles and responsibilities defined
- [ ] Escalation procedures documented
- [ ] Communication channels established
- [ ] Incident classification severity levels defined

**Incident Response Tools**:
- [ ] SIEM integration (Splunk, ELK)
- [ ] EDR (Endpoint Detection and Response)
- [ ] Forensic imaging tools
- [ ] Secure communication channels (Signal)
- [ ] Incident tracking system (Jira, tickets)

**Incident Response Testing**:
- [ ] Tabletop exercises conducted (quarterly)
- [ ] Penetration testing conducted (annually)
- [ ] Red team exercises conducted (annually)
- [ ] Incident response drills (semi-annually)

#### 11. Vulnerability Management

**Vulnerability Disclosure**:
- [ ] Vulnerability disclosure policy published
- [ ] Security email address (security@) configured
- [ ] PGP key available for encrypted reports
- [ ] Bug bounty program (optional)
- [ ] Safe harbor policy documented
- [ ] Security advisories template prepared

**Penetration Testing**:
- [ ] Annual penetration testing scheduled
- [ ] External penetration testing firm selected
- [ ] Scope defined (in-scope and out-of-scope)
- [ ] Rules of engagement documented
- [ ] Findings remediated within SLA
- [ ] Re-testing to verify fixes

**Vulnerability Remediation**:
- [ ] Vulnerability tracking system
- [ ] Remediation SLA defined by severity
- [ ] Patch management process
- [ ] Emergency patching procedure for critical CVEs
- [ ] Vulnerability disclosure process for fixed issues

#### 12. Security Training & Awareness

**Staff Training**:
- [ ] Security awareness training for all staff (annual)
- [ ] Phishing simulations conducted (quarterly)
- [ ] Secure coding training for developers
- [ ] GDPR/CCPA training for relevant staff
- [ ] Incident response training for IRT

**Documentation**:
- [ ] Security policies documented and distributed
- [ ] Security procedures documented
- [ ] Playbooks for common incidents
- [ ] Architecture decision records (ADRs)
- [ ] Runbooks for operational tasks

#### 13. DevSecOps & CI/CD Security

**Pipeline Security**:
- [ ] SAST integrated into CI/CD (every commit)
- [ ] SCA integrated into CI/CD (daily)
- [ ] Secret scanning in CI/CD (every commit)
- [ ] Container image scanning in CI/CD (every build)
- [ ] Infrastructure-as-code scanning (every deploy)

**Deployment Security**:
- [ ] Immutable infrastructure
- [ ] Blue-green deployments
- [ ] Automated rollback capability
- [ ] Pre-production security testing
- [ ] Production access restricted (no direct deployment)

**Change Management**:
- [ ] Change approval process
- [ ] Change risk assessment
- [ ] Change documentation
- [ ] Rollback plans for all changes

#### 14. Physical Security (if on-premise)

**Data Center Security**:
- [ ] Physical access controls (badges, biometrics)
- [ ] Visitor logs and escorts required
- [ ] Video surveillance
- [ ] Environmental controls (fire suppression, temperature)
- [ ] Backup power (UPS, generator)

**Device Security**:
- [ ] Workstations encrypted (BitLocker, FileVault)
- [ ] Lost device remote wipe capability
- [ ] USB port blocked or controlled
- [ ] Screen lock required after 5 minutes
- [ ] Secure disposal of old equipment

### Pre-Production Deployment Checklist

Use this checklist **before deploying to production**:

**Critical Items** (Must Pass):
- [ ] All high and critical vulnerabilities fixed
- [ ] Penetration testing completed and findings addressed
- [ ] Security review approved
- [ ] Audit logging enabled and tested
- [ ] TLS/HTTPS configured and verified
- [ ] Database encryption enabled
- [ ] Backup and restore tested
- [ ] Monitoring and alerting configured
- [ ] Incident response team notified
- [ ] Legal and compliance review completed

**Important Items** (Should Pass):
- [ ] SAST and SCA scans passing
- [ ] Security headers configured
- [ ] Rate limiting configured
- [ ] Input validation tested
- [ ] Error handling tested
- [ ] Authentication and authorization tested
- [ ] API security tested
- [ ] Dependencies up-to-date
- [ ] Docker images scanned
- [ ] Infrastructure security verified

**Nice to Have**:
- [ ] Bug bounty program launched
- [ ] Security training completed for new features
- [ ] Documentation updated
- [ ] Security advisory prepared for new features
- [ ] Threat model updated

### Periodic Security Review Checklist

Use this checklist **periodically** (quarterly or semi-annually):

- [ ] Security posture review
- [ ] Vulnerability assessment completed
- [ ] Penetration testing scheduled or completed
- [ ] Compliance audit (GDPR, CCPA)
- [ ] Access review (revoke unnecessary access)
- [ ] Dependency audit (update or remove unused dependencies)
- [ ] Security policy review and update
- [ ] Incident response plan review and update
- [ ] Security training refresher
- [ ] Threat model update for new features

---

## Appendix

### Useful Security Resources

**Standards & Frameworks**:
- **OWASP Top 10**: https://owasp.org/www-project-top-ten/
- **CIS Benchmarks**: https://www.cisecurity.org/cis-benchmarks/
- **NIST Cybersecurity Framework**: https://www.nist.gov/cyberframework
- **ISO 27001**: Information security management standard
- **SOC 2**: Service organization controls
- **PCI DSS**: Payment card industry security standards

**Vulnerability Databases**:
- **CVE**: https://cve.mitre.org/
- **NVD**: https://nvd.nist.gov/
- **CWE**: https://cwe.mitre.org/
- **Exploit-DB**: https://www.exploit-db.com/

**Security Tools**:
- **OWASP ZAP**: https://www.zaproxy.org/
- **Burp Suite**: https://portswigger.net/burp
- **Metasploit**: https://www.metasploit.com/
- **Nmap**: https://nmap.org/
- **Wireshark**: https://www.wireshark.org/

**Learning Resources**:
- **OWASP Cheat Sheets**: https://cheatsheetseries.owasp.org/
- **Web Security Academy**: https://portswigger.net/web-security
- **SANS Security Resources**: https://www.sans.org/
- **Coursera Cybersecurity**: https://www.coursera.org/browse/cybersecurity

### Security Metrics to Track

**Vulnerability Management**:
- Mean time to detect (MTTD) vulnerabilities
- Mean time to remediate (MTTR) vulnerabilities
- Vulnerability backlog count by severity
- Percentage of dependencies up-to-date

**Incident Response**:
- Mean time to detect (MTTD) incidents
- Mean time to respond (MTTR) incidents
- Number of incidents per month
- Time to restore service

**Security Posture**:
- Percentage of systems with security agents installed
- Number of failed login attempts per week
- Number of security exceptions granted
- Security training completion rate

**Compliance**:
- GDPR/CCPA policy compliance percentage
- Data subject request response time
- Data breach notification timeliness
- Audit findings remediation rate

---

**Last Updated**: 2026-02-04
**Version**: 1.0.0
**Maintainer**: Security Team
