# Production Readiness Checklist

**Document Created:** 2026-01-17
**Application:** ACES - Acquisition Contracting Enterprise System
**Status:** Development/Pilot Phase

---

## Executive Summary

This document outlines the requirements for moving the ACES application from development to production. The app has solid security foundations (password validation, account lockout, audit logging, rate limiting). For a **pilot/internal deployment**, expect 1-2 weeks of hardening. For **FedRAMP/ATO production**, expect 3-6 months of compliance work plus infrastructure buildout.

---

## 1. Critical Security Issues (Must Fix Before Production)

| Issue | Current State | Production Requirement | Priority |
|-------|---------------|------------------------|----------|
| **Secrets in .env.example** | Contains real API keys & Supabase JWT | Use placeholders only (`your-key-here`) | P0 |
| **SECRET_KEY** | Default fallback value in code | Generate 256-bit random key, store in vault | P0 |
| **CORS Origins** | `localhost` only | Configure production domain(s) | P0 |
| **HTTPS/TLS** | Not configured | Required - use reverse proxy (nginx/caddy) | P0 |
| **JWT Algorithm** | HS256 | Consider RS256 for distributed systems | P1 |

### Action Items

1. **Clean .env.example immediately:**
   ```bash
   # Replace real keys with placeholders
   ANTHROPIC_API_KEY=your-anthropic-api-key-here
   SECRET_KEY=generate-a-secure-random-key-here
   DATABASE_URL=postgresql://user:password@localhost:5432/aces
   ```

2. **Generate production SECRET_KEY:**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(64))"
   ```

3. **Configure CORS for production:**
   ```python
   CORS_ORIGINS=https://aces.yourdomain.mil,https://aces-staging.yourdomain.mil
   ```

---

## 2. Infrastructure Requirements

### Current vs Production

| Component | Current | Production Requirement |
|-----------|---------|------------------------|
| **Database** | SQLite/Supabase dev | PostgreSQL with replication, automated backups, encryption at rest |
| **File Storage** | Local `./uploads` directory | S3/Azure Blob with encryption at rest, versioning enabled |
| **Redis** | Optional (not configured) | Required for rate limiting, session management, WebSocket pub/sub |
| **Containerization** | None | Dockerfile, docker-compose.prod.yml, Kubernetes manifests |
| **Reverse Proxy** | None | nginx/Traefik with TLS termination, rate limiting |
| **Load Balancer** | None | Application Load Balancer with health checks |
| **CDN** | None | CloudFront/Azure CDN for static assets |

### Recommended Architecture

```
                                    ┌─────────────────┐
                                    │   CloudFront    │
                                    │   (Static CDN)  │
                                    └────────┬────────┘
                                             │
┌─────────────┐     ┌─────────────┐    ┌─────┴─────┐
│   Users     │────▶│    ALB      │───▶│  nginx    │
│             │     │ (HTTPS/TLS) │    │  (proxy)  │
└─────────────┘     └─────────────┘    └─────┬─────┘
                                             │
                    ┌────────────────────────┼────────────────────────┐
                    │                        │                        │
              ┌─────┴─────┐           ┌──────┴──────┐          ┌──────┴──────┐
              │  FastAPI  │           │   FastAPI   │          │   FastAPI   │
              │  Pod 1    │           │   Pod 2     │          │   Pod 3     │
              └─────┬─────┘           └──────┬──────┘          └──────┬──────┘
                    │                        │                        │
                    └────────────────────────┼────────────────────────┘
                                             │
              ┌──────────────────────────────┼──────────────────────────────┐
              │                              │                              │
        ┌─────┴─────┐                 ┌──────┴──────┐               ┌───────┴───────┐
        │ PostgreSQL│                 │    Redis    │               │      S3       │
        │ (Primary) │                 │   Cluster   │               │  (Documents)  │
        └─────┬─────┘                 └─────────────┘               └───────────────┘
              │
        ┌─────┴─────┐
        │ PostgreSQL│
        │ (Replica) │
        └───────────┘
```

### Files to Create

```
├── Dockerfile
├── docker-compose.prod.yml
├── k8s/
│   ├── namespace.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── configmap.yaml
│   ├── secrets.yaml (template only)
│   └── hpa.yaml (horizontal pod autoscaler)
├── nginx/
│   └── nginx.conf
├── .env.production.template  # No secrets - placeholders only
└── scripts/
    ├── health-check.sh
    ├── backup-db.sh
    └── rotate-secrets.sh
```

---

## 3. DoD/Government Compliance Requirements

### Compliance Frameworks

| Requirement | Current Status | Notes | Effort |
|-------------|----------------|-------|--------|
| **FedRAMP** | Not certified | Required for federal cloud deployment | 3-6 months |
| **NIST 800-53** | Partial | Audit logging exists, need full control mapping | 2-3 months |
| **FIPS 140-2** | Not verified | Cryptography modules need certification | 1-2 months |
| **IL4/IL5** | Not assessed | Impact level classification needed | 1 month |
| **STIGs** | Not applied | Security Technical Implementation Guides | 1-2 months |
| **ATO** | None | Authority to Operate process required | 3-6 months |
| **Section 508** | Not assessed | Accessibility compliance for federal apps | 1-2 months |

### Key NIST 800-53 Controls to Address

| Control Family | Status | Gap |
|----------------|--------|-----|
| AC (Access Control) | Partial | Need MFA, session timeout |
| AU (Audit) | Implemented | Need log retention policy, SIEM integration |
| IA (Identification & Auth) | Partial | Need CAC/PIV support |
| SC (System & Comms Protection) | Partial | Need HTTPS, encryption at rest |
| SI (System & Info Integrity) | Partial | Need vulnerability scanning |

### CAC/PIV Integration

For DoD production, Common Access Card (CAC) authentication is typically required:

```python
# Future implementation needed
# Options:
# 1. mod_ssl with client certificate verification
# 2. SAML integration with DoD Identity Provider
# 3. OAuth2/OIDC with DoD-approved IdP
```

---

## 4. Authentication & Authorization Enhancements

### Current State (Implemented)

| Feature | Status | Location |
|---------|--------|----------|
| Password validation (12+ chars, complexity) | ✅ Implemented | `main.py` |
| Account lockout (5 attempts, 15 min) | ✅ Implemented | `main.py` |
| Rate limiting (login, register) | ✅ Implemented | `main.py` |
| Role-based access control | ✅ Implemented | `middleware/auth.py` |
| Audit logging | ✅ Implemented | `models/audit.py` |
| Path traversal protection | ✅ Implemented | `services/rag_service.py` |

### Missing for Production

| Feature | Priority | Effort | Notes |
|---------|----------|--------|-------|
| Multi-factor auth (MFA) | P1 | 1-2 weeks | TOTP or hardware keys |
| CAC/PIV integration | P1 (DoD) | 2-4 weeks | Required for DoD |
| SSO/SAML integration | P1 | 1-2 weeks | Enterprise identity |
| OAuth2/OIDC | P2 | 1 week | Modern auth standard |
| Session management | P1 | 3-5 days | Redis-backed sessions |
| API key rotation | P2 | 2-3 days | Scheduled rotation |
| Password expiration | P2 | 1-2 days | 90-day policy |
| Login notifications | P3 | 1-2 days | Email on new device |

---

## 5. Operational Requirements

### Logging

| Aspect | Current | Production |
|--------|---------|------------|
| Format | Text files | Structured JSON |
| Storage | Local `./logs/` | Centralized (ELK/Splunk/CloudWatch) |
| Retention | None defined | 1 year minimum (compliance) |
| Search | Manual | Full-text search, dashboards |
| Alerts | None | Real-time security alerts |

### Recommended Log Structure

```json
{
  "timestamp": "2026-01-17T14:30:00Z",
  "level": "INFO",
  "service": "aces-api",
  "trace_id": "abc123",
  "user_id": "user-uuid",
  "action": "document_generated",
  "entity_type": "document",
  "entity_id": "doc-uuid",
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "duration_ms": 1234,
  "status": "success"
}
```

### Monitoring & Alerting

| Component | Tool Options | Metrics |
|-----------|--------------|---------|
| APM | Datadog, New Relic, Jaeger | Request latency, error rates |
| Infrastructure | Prometheus + Grafana | CPU, memory, disk, network |
| Logs | ELK Stack, Splunk, CloudWatch | Error patterns, security events |
| Uptime | Pingdom, UptimeRobot | Availability SLA |
| Alerting | PagerDuty, OpsGenie | On-call rotation |

### Critical Alerts to Configure

| Event | Threshold | Severity |
|-------|-----------|----------|
| Account lockouts | > 10/hour | High |
| Failed logins | > 50/hour | Medium |
| API errors (5xx) | > 1% of requests | High |
| Response time | p99 > 5 seconds | Medium |
| Disk usage | > 80% | High |
| Certificate expiry | < 30 days | Medium |

### Backup & Disaster Recovery

| Aspect | Requirement |
|--------|-------------|
| Database backups | Daily full, hourly incremental |
| Backup retention | 30 days minimum |
| Point-in-time recovery | Required |
| Backup testing | Monthly restore tests |
| RTO (Recovery Time) | Define based on business needs (e.g., 4 hours) |
| RPO (Recovery Point) | Define based on business needs (e.g., 1 hour) |
| DR site | Separate availability zone/region |

---

## 6. Environment Configuration

### Production Environment Variables

```bash
# Database (use secrets manager, not .env file)
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@prod-db.internal:5432/aces?sslmode=require
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=false
CORS_ORIGINS=https://aces.yourdomain.mil

# Security (retrieve from secrets manager)
SECRET_KEY=${JWT_SECRET_FROM_VAULT}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# AI Services (retrieve from secrets manager)
ANTHROPIC_API_KEY=${ANTHROPIC_KEY_FROM_VAULT}
TAVILY_API_KEY=${TAVILY_KEY_FROM_VAULT}

# Redis
REDIS_URL=redis://redis.internal:6379/0

# File Storage
UPLOAD_DIR=s3://aces-uploads-prod/
GENERATED_DOCS_DIR=s3://aces-generated-prod/
MAX_UPLOAD_SIZE=52428800

# Logging
LOG_LEVEL=WARNING
LOG_FORMAT=json

# Feature Flags
ENABLE_DEBUG_ENDPOINTS=false
ENABLE_SWAGGER_UI=false  # Disable in production
```

### Secrets Management Options

| Option | Pros | Cons |
|--------|------|------|
| AWS Secrets Manager | Native AWS, rotation | AWS-only |
| HashiCorp Vault | Multi-cloud, powerful | Complex setup |
| Azure Key Vault | Native Azure | Azure-only |
| Kubernetes Secrets | Native K8s | Less secure by default |
| SOPS | GitOps friendly | Manual rotation |

---

## 7. Estimated Effort by Priority

### P0 - Must Have (Week 1-2)

| Task | Effort | Owner |
|------|--------|-------|
| Remove secrets from .env.example | 1 hour | DevOps |
| Generate production SECRET_KEY | 1 hour | DevOps |
| HTTPS/TLS setup with nginx | 1-2 days | DevOps |
| Production PostgreSQL setup | 1-2 days | DevOps |
| Environment variable externalization | 1 day | Backend |

### P1 - Should Have (Week 3-4)

| Task | Effort | Owner |
|------|--------|-------|
| Dockerfile & container build | 2-3 days | DevOps |
| Kubernetes deployment manifests | 2-3 days | DevOps |
| Centralized logging (ELK/CloudWatch) | 2-3 days | DevOps |
| Monitoring with Prometheus/Grafana | 3-5 days | DevOps |
| Alerting setup | 1-2 days | DevOps |
| S3 file storage migration | 2-3 days | Backend |

### P2 - Nice to Have (Month 2)

| Task | Effort | Owner |
|------|--------|-------|
| MFA implementation | 1-2 weeks | Backend |
| SSO/SAML integration | 1-2 weeks | Backend |
| Redis session management | 3-5 days | Backend |
| Automated backup testing | 2-3 days | DevOps |
| Load testing | 3-5 days | QA |

### P3 - Future / Compliance (Month 3+)

| Task | Effort | Owner |
|------|--------|-------|
| FedRAMP documentation | 3-6 months | Compliance |
| NIST 800-53 control mapping | 2-3 months | Compliance |
| CAC/PIV integration | 2-4 weeks | Backend |
| Penetration testing | 1-2 weeks | Security |
| ATO package preparation | 2-3 months | Compliance |

---

## 8. Pre-Production Checklist

### Security

- [ ] All secrets removed from code and .env.example
- [ ] SECRET_KEY generated and stored in secrets manager
- [ ] HTTPS/TLS configured with valid certificate
- [ ] CORS configured for production domains only
- [ ] Rate limiting verified and tuned
- [ ] All debug endpoints disabled
- [ ] Swagger UI disabled or protected
- [ ] Security headers configured (CSP, HSTS, X-Frame-Options)
- [ ] Dependency vulnerability scan completed
- [ ] Penetration test completed (if required)

### Infrastructure

- [ ] Production database provisioned and configured
- [ ] Database backups automated and tested
- [ ] Redis cluster deployed
- [ ] S3 buckets created with proper permissions
- [ ] Container images built and tested
- [ ] Kubernetes manifests validated
- [ ] Load balancer configured with health checks
- [ ] CDN configured for static assets
- [ ] DNS configured

### Operations

- [ ] Centralized logging configured
- [ ] Monitoring dashboards created
- [ ] Alerting rules configured
- [ ] On-call rotation established
- [ ] Runbooks documented
- [ ] Incident response plan documented
- [ ] Disaster recovery plan tested

### Compliance (DoD)

- [ ] Impact level determined (IL4/IL5)
- [ ] STIG compliance verified
- [ ] NIST 800-53 controls mapped
- [ ] FedRAMP package prepared (if applicable)
- [ ] ATO documentation complete
- [ ] Security assessment completed

---

## 9. References

- [NIST 800-53 Security Controls](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final)
- [FedRAMP Authorization](https://www.fedramp.gov/)
- [DoD Cloud Computing SRG](https://public.cyber.mil/dccs/)
- [DISA STIGs](https://public.cyber.mil/stigs/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CIS Benchmarks](https://www.cisecurity.org/cis-benchmarks/)

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-17 | Claude Code | Initial document |

---

*This document should be reviewed and updated quarterly or when significant changes are made to the application architecture.*
