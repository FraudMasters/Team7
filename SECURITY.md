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

**Last Updated**: 2026-02-04
**Version**: 1.0.0
**Maintainer**: Security Team
