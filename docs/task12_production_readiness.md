# Inventory Agent — Production Readiness Notes

## Current Prototype Strengths

- Structured inventory database
- Controlled stock transactions
- Role-based workflow checks
- Reorder calculations
- Procurement workflow
- Purchase request approval lifecycle
- Supplier records
- Operational alerts
- Human escalation
- Audit trail
- AI tool calling
- RAG-based policy retrieval
- Streamlit operational dashboard
- Automated test suite

---

## Current Prototype Limitations

### Authentication

Current user IDs are supplied by the demo application.

Production should use authenticated identity such as:

- JWT
- OAuth
- SSO
- Enterprise identity provider

The backend should derive user identity from the authenticated session.

---

### Database

SQLite is suitable for development and demonstration.

Production should use a transactional database such as PostgreSQL.

---

### Concurrency

Production inventory operations should use appropriate locking or
transaction isolation to prevent simultaneous updates from creating
incorrect stock balances.

---

### Reorder Logic

Current reorder calculation is intentionally simple.

Production calculations may include:

- Open purchase orders
- In-transit stock
- Demand history
- Forecast demand
- Supplier lead time
- Safety stock
- Seasonality
- Location-specific thresholds

---

### Duplicate Procurement

The dashboard currently detects an existing open purchase request.

Production duplicate prevention must also be enforced by the backend.

---

### Alert Synchronization

Low-stock alert synchronization is currently manually triggered.

Production should automatically reevaluate alerts after relevant stock
transactions or through an event/background-job mechanism.

---

### RAG Governance

Production document retrieval should include:

- Document ownership
- Version control
- Permission filtering
- Effective dates
- Archiving of outdated policies
- Source traceability

---

### Monitoring

Production should include:

- Centralized logs
- Error monitoring
- API monitoring
- AI usage monitoring
- Cost monitoring
- Security alerts

---

### Rate Limiting

Production APIs and AI endpoints should use rate limiting and abuse controls.

---

### Secrets

Production secrets should not be stored directly in local environment files.

Use a managed secret store.

---

## Production Architecture Direction

User
↓
Authenticated Web Application
↓
FastAPI
↓
Business Services
↓
AI Orchestrator / Approved Tools
↓
PostgreSQL / ERP / WMS
↓
Audit + Monitoring

Document Knowledge
↓
Controlled Retrieval System
↓
AI Agent

---

## Final Principle

AI should assist business operations without becoming the uncontrolled
source of operational truth.

Data integrity, authorization, transaction processing and approvals remain
under deterministic backend control.