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

## Next Sections

The following sections will provide detailed guidance on:
- [Secure Configuration](#secure-configuration) - Environment setup, secrets management, production hardening
- [Authentication & Authorization](#authentication--authorization) - Implementation guidance for future auth system
- [API Security](#api-security) - Rate limiting, CORS, input validation, OWASP Top 10
- [Data Security & Encryption](#data-security--encryption) - Encryption at rest/in transit, PII handling
- [File Upload Security](#file-upload-security) - Validation, malware scanning, secure storage
- [Dependency Management](#dependency-management) - Vulnerability scanning, update procedures
- [Logging & Monitoring Security](#logging--monitoring-security) - Security events, avoiding PII in logs
- [Compliance & Data Privacy](#compliance--data-privacy) - GDPR, data retention, audit requirements
- [Incident Response](#incident-response) - Procedures for security incidents
- [Security Testing](#security-testing) - Checklist for verifying security measures
- [Vulnerability Disclosure](#vulnerability-disclosure) - Reporting security issues
- [Security Checklist](#security-checklist) - Pre-deployment verification

---

**Last Updated**: 2026-02-04
**Version**: 1.0.0
**Maintainer**: Security Team
