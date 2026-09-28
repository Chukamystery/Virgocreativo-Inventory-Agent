# Task 11 — Testing, Security, Failure Handling, Logging and Guardrails

## Status

Completed.

Final automated regression result:

- 52 tests passed
- 14 warnings
- Execution time: 33.77 seconds

The warnings do not currently cause test failures. Dependency warnings should still be reviewed during future package upgrades.

---

# 1. Test Environment Isolation

Automated tests use a temporary SQLite database.

The development database:

`data/inventory_agent.db`

is not used for destructive automated tests.

This prevents test movements, purchase requests, approvals, alerts and handoffs from changing development data.

---

# 2. Inventory Integrity Controls

Verified by automated tests:

- Negative on-hand inventory is rejected.
- Reserved quantity cannot exceed on-hand quantity.
- Available quantity is calculated as:

  `quantity_on_hand - reserved_quantity`

- Failed stock operations do not leave partial inventory changes.
- Inventory quantities are not directly writable through the LLM.

---

# 3. Reorder Controls

Verified business rule:

`available = quantity_on_hand - reserved_quantity`

An item is considered low stock when:

`available <= reorder_point`

Recommended reorder quantity:

`target_stock - available`

when the item is low stock.

Automated tests cover:

- stock above reorder point
- stock exactly equal to reorder point
- stock below reorder point
- zero available stock
- database-backed reorder recommendations

---

# 4. Stock Movement Security

Only these roles can execute stock movements:

- INVENTORY_MANAGER
- ADMIN

Verified controls:

- INVENTORY_STAFF cannot execute stock movements.
- Stock cannot be issued beyond available quantity.
- Valid stock movements update inventory correctly.
- Successful movements create StockMovement history.
- Successful movements create AuditLog history.
- Failed movements do not create movement history.

---

# 5. Procurement Approval Controls

Purchase request workflow:

DRAFT
→ PENDING_APPROVAL
→ APPROVED or REJECTED

Verified controls:

- Authorized users can submit DRAFT requests.
- INVENTORY_STAFF cannot approve requests.
- Purchase request creator cannot approve their own request.
- Purchase request creator cannot reject their own request.
- Only PENDING_APPROVAL requests can be approved or rejected.
- Approved requests cannot be approved again.
- Rejections require a comment.
- Approval history is persisted.
- Approval actions create audit records.
- Approval/rejection resolves the related pending-approval alert.

---

# 6. Alert Controls

Verified controls:

- Low-stock alerts can be persisted.
- Duplicate OPEN alerts are prevented.
- Purchase-request submission creates a PENDING_APPROVAL alert.
- Approval/rejection resolves that alert.
- Human handoffs create HUMAN_HANDOFF alerts.
- Resolving a handoff resolves its alert.

---

# 7. Human Handoff Controls

Supported escalation reasons include:

- AUTHORIZATION_FAILURE
- CONFLICTING_DATA
- SUPPLIER_SELECTION
- UNSUPPORTED_ACTION
- TOOL_FAILURE
- HIGH_RISK_EXCEPTION

Verified controls:

- Human handoffs are persisted.
- Duplicate OPEN handoffs are prevented.
- INVENTORY_STAFF cannot resolve handoffs.
- INVENTORY_MANAGER and ADMIN can resolve handoffs.
- Creation and resolution are audited.
- AI-created handoffs retain the acting user ID.
- Related alerts are created and resolved with the handoff lifecycle.

---

# 8. LLM Tool Guardrails

The LLM currently has approved tools for:

- product lookup
- location lookup
- inventory balance lookup
- reorder recommendations
- low-stock listing
- supplier-option lookup
- human handoff creation

The LLM does NOT have direct tools for:

- arbitrary inventory overwrite
- purchase-request approval
- purchase-request rejection
- arbitrary SQL execution
- audit-log modification
- unrestricted Python execution

Unknown tool names are blocked by the backend dispatcher.

Human escalation is permitted because it creates a review request rather than performing a high-risk business action.

---

# 9. RAG / Operational Data Boundary

Structured operational facts must come from the database and validated backend services.

Examples:

- inventory quantity
- reserved quantity
- reorder recommendation
- supplier records
- purchase-request state
- approval state

RAG/file search is used for unstructured knowledge such as:

- SOPs
- policies
- procedures
- receiving guidance
- procurement guidance

Policy documents must not be treated as the source of truth for live inventory quantities.

---

# 10. Agent Identity Controls

The agent requires a valid active user before processing chat.

Verified controls:

- unknown user is blocked
- inactive user is blocked
- AI-created handoff requires an acting user
- handoff audit uses the same acting user

Current implementation uses a user ID supplied in the request body.

This is suitable only for the project/demo environment.

It is NOT production authentication.

---

# 11. API Error Handling

Verified API behavior:

- unknown/inactive user → HTTP 403
- malformed request → HTTP 422
- invalid request values → HTTP 422
- expected validation errors → controlled API response
- unexpected internal errors → generic HTTP 500 response

Internal exception details are not returned to the API caller.

---

# 12. Logging

Unexpected Inventory Agent failures are logged for developers.

The API user receives a generic safe error message.

This allows:

- developer troubleshooting
- safer API responses
- separation between internal diagnostics and user-facing errors

Current logging is local/application logging.

Production systems should use centralized monitoring.

---

# 13. Automated Test Result

Final regression command:

`python -m pytest tests -q`

Result:

`52 passed, 14 warnings in 33.77s`

This confirms that the tested components continue to work together after the Task 11 security and guardrail changes.

---

# 14. Known Gaps Before Production

## Authentication

Current requests accept `user_id` from the request body.

A caller could potentially claim another user's ID.

Production must derive identity from authentication such as:

- secure login session
- JWT/access token
- enterprise identity provider
- OAuth/OIDC

Authorization must use the authenticated identity rather than trusting a submitted user ID.

## Database

Current project uses SQLite.

SQLite is suitable for learning and demonstration but not the final concurrent production architecture.

Recommended production migration:

PostgreSQL.

## Concurrency

The current learning implementation does not yet include production-grade row locking for simultaneous approvals or stock transactions.

PostgreSQL transaction/locking controls should be added before production use.

## Replenishment Logic

Current reorder calculation is intentionally simplified.

It does not yet account for:

- open purchase requests
- open purchase orders
- goods already in transit
- demand history
- safety stock
- supplier lead-time demand
- seasonality

Without these controls, repeated replenishment requests could cause over-ordering.

## Duplicate Procurement

The system can currently create additional purchase-request drafts for the same product/location even when another procurement process may already exist.

A production version should check existing:

- DRAFT requests
- PENDING_APPROVAL requests
- APPROVED requests awaiting ordering
- open purchase orders
- incoming goods

before recommending or creating another request.

## Reorder Threshold Scope

Reorder point and target stock are currently stored at product level.

A production implementation may need product-location-specific thresholds.

For example:

Main Warehouse may require a reorder point of 50,
while a smaller retail location may require only 10.

## Policy Router

The current policy/SOP router uses keyword detection.

This is suitable for the learning version but can miss unusual phrasing.

Future versions can use a stronger intent-classification mechanism with deterministic safety fallbacks.

## RAG Governance

Production should control:

- who can upload knowledge documents
- document versioning
- effective dates
- expired policies
- approval status
- source ownership

The agent should not retrieve outdated or unapproved operating procedures.

## LLM Testing

Most automated security tests deliberately avoid live OpenAI calls.

This keeps tests deterministic and avoids unnecessary API cost.

A separate controlled integration-test suite should periodically test:

- real model tool selection
- escalation behavior
- hallucination resistance
- prompt injection attempts
- RAG grounding
- ambiguous requests
- tool failures

## Rate Limiting

API rate limiting has not yet been implemented.

Production should protect public or external-facing endpoints from abuse and excessive model/API usage.

## Secret Management

Environment variables are used for development.

Production should use an appropriate secrets-management solution rather than storing credentials in source code or committed configuration.

## Monitoring

Current logs are local.

Production should add centralized monitoring, alerting and trace correlation.

---

# 15. Task 11 Conclusion

The Inventory Agent now has automated evidence for:

- data integrity
- deterministic inventory calculations
- stock transaction controls
- role-based authorization
- purchase-request state controls
- four-eyes approval separation
- auditability
- alerts
- human escalation
- LLM tool restrictions
- actor validation
- safe API error handling
- application failure logging

The system is now sufficiently tested for the project/demo stage.

Production hardening remains a separate deployment concern and is documented above.

## Final Regression — Task 12

Final regression test completed after dashboard integration
and end-to-end workflow testing.

Result:

- 52 tests collected
- 52 tests passed
- 0 tests failed
- 14 deprecation warnings
- Execution time: 43.24 seconds

The final local prototype successfully completed an end-to-end
inventory replenishment workflow from low-stock detection through
procurement, approval, goods receipt, alert resolution and audit
verification.