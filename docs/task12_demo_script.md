# Inventory Agent — Final Demo Script

## 1. Project Introduction

The Inventory Agent is an AI-assisted inventory operations system.

It combines:

- Inventory management
- Reorder calculations
- Supplier information
- Procurement workflows
- Purchase request approvals
- Stock movements
- Alerts
- Human handoffs
- Audit logs
- AI conversational access
- RAG-based policy retrieval

The AI is not the source of truth.

Operational quantities and business decisions are controlled by the database,
Python business rules and FastAPI services.

---

## 2. Architecture

User
↓
Streamlit Dashboard
↓
FastAPI Backend
↓
Business Services / AI Agent
↓
Approved Tools
↓
SQLAlchemy
↓
Inventory Database

Document-based questions use:

AI Agent
↓
RAG / File Search
↓
Approved business documents

---

## 3. Inventory Demonstration

Open the Inventory tab.

Explain:

The inventory database stores:

- Product
- Location
- Quantity on hand
- Reserved quantity

Available inventory is calculated as:

Available = Quantity On Hand - Reserved Quantity

The UI does not directly modify stock.

All stock changes must go through a stock movement transaction.

---

## 4. Reorder Demonstration

Open the Reorder tab.

Explain:

A product becomes low stock when:

Available Quantity <= Reorder Point

Recommended replenishment is:

Target Stock - Available Quantity

These calculations are performed by deterministic Python rules,
not by the LLM.

---

## 5. AI Assistant Demonstration

Ask:

"How many Wireless Mouse units are available in Main Warehouse?"

Explain:

The AI understands the request but does not invent the quantity.

It calls approved inventory tools that retrieve the verified result
from the operational system.

Ask:

"What is our damaged goods procedure?"

Explain:

This is a policy question, so the agent uses RAG/file search instead
of the inventory database.

---

## 6. Human Handoff Demonstration

Ask the agent for an unsupported inventory operation and request escalation.

Explain:

Instead of guessing or performing an unsupported action,
the AI creates a human handoff.

The handoff creates an alert for management review.

---

## 7. Procurement Demonstration

When an item is low stock:

1. Procurement reviews the calculated reorder quantity.
2. Supplier options are retrieved.
3. A purchase request is prepared.
4. Status starts as DRAFT.
5. Procurement submits it.
6. Status becomes PENDING_APPROVAL.
7. A manager approves or rejects it.

The requester cannot approve their own purchase request.

---

## 8. Stock Receipt Demonstration

Once an approved purchase is physically delivered:

Warehouse staff record:

Movement Type: RECEIPT

The backend validates:

- User role
- Product
- Location
- Quantity
- Transaction rules

The system then:

- Updates inventory
- Creates stock movement history
- Creates an audit record

Approval of a purchase request does not automatically increase inventory.

Inventory changes only when goods are physically received.

---

## 9. Alert Demonstration

When inventory becomes low, the system can create a LOW_STOCK alert.

When stock is replenished, the reorder engine recalculates the state.

Low-stock alerts can then be synchronized and resolved.

Resolved alerts remain available historically rather than being deleted.

---

## 10. Audit Demonstration

Open the Activity Log.

Explain:

Every important business action can be traced.

The system records:

- Who performed the action
- What action occurred
- Which entity was affected
- Previous state
- New state
- When it occurred
- Relevant transaction details

Examples:

- Purchase Request Draft Created
- Purchase Request Submitted
- Purchase Request Approved
- Purchase Request Rejected
- Stock Movement Recorded
- Human Handoff Created
- Human Handoff Resolved

---

## 11. Key Design Principle

The system is not simply an AI chatbot.

It is a controlled operational system with an AI interface.

The LLM is responsible for:

- Understanding user requests
- Selecting approved tools
- Explaining verified results

The LLM is not responsible for:

- Inventing stock quantities
- Directly changing inventory
- Approving purchases
- Bypassing permissions
- Writing arbitrary SQL

---

## 12. Real-World Application

In a production company, the same architecture could sit on top of:

- ERP systems
- Warehouse management systems
- Procurement databases
- Existing inventory databases
- SAP
- Microsoft Dynamics
- Oracle
- Custom systems

Instead of SQLite, a production implementation could use PostgreSQL
or integrate directly with the company's existing operational system.

The AI layer would provide conversational access while existing business
rules and systems remain authoritative.