# Virgocreativo Inventory Agent

An AI-assisted inventory operations system built to demonstrate how artificial intelligence can interact safely with structured business operations.

The system combines inventory management, procurement workflows, reorder rules, approvals, alerts, audit logging, human escalation, RAG-based knowledge retrieval and an AI conversational interface.

---

## Project Objective

The goal of this project is to build an Inventory Agent that allows users to interact with inventory operations through both a dashboard and natural-language AI assistant.

The AI is not the source of truth.

Operational data and business transactions are controlled by:

- FastAPI
- Python business rules
- SQLAlchemy
- Database records
- Role-based permissions
- Validated tools

The LLM is primarily responsible for understanding requests, selecting approved tools and explaining verified results.

---

## Architecture

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

For document and policy questions:

AI Agent

↓

RAG / File Search

↓

Approved Business Documents

---

## Technology Stack

### Backend

- Python
- FastAPI
- SQLAlchemy
- Pydantic
- SQLite

### AI

- OpenAI LLM
- Function / Tool Calling
- RAG / File Search

### Frontend

- Streamlit

### Testing

- Pytest
- FastAPI TestClient

### Development

- Visual Studio Code
- Git
- GitHub
- Python virtual environment
- Environment variables

---

## Core Features

The Inventory Agent currently supports:

- Product management
- Inventory balances
- Multiple inventory locations
- Stock receipts
- Stock issues
- Inventory adjustments
- Stock movement history
- Low-stock detection
- Reorder recommendations
- Supplier information
- Purchase request preparation
- Purchase request submission
- Manager approval and rejection
- Operational alerts
- Human handoffs
- Audit logging
- AI inventory questions
- AI reorder questions
- RAG-based policy questions
- Tool transparency
- Streamlit operations dashboard

---

## Inventory Rules

Available inventory is calculated as:

Available Quantity = Quantity On Hand - Reserved Quantity

An inventory item is considered low stock when:

Available Quantity <= Reorder Point

The current simplified reorder calculation is:

Recommended Reorder Quantity = Target Stock - Available Quantity

These calculations are performed by deterministic Python services rather than by the LLM.

---

## Controlled Stock Movements

Inventory quantities cannot be directly overwritten from the dashboard or by the AI.

Stock changes must be recorded as approved business transactions:

- RECEIPT
- ISSUE
- ADJUSTMENT_IN
- ADJUSTMENT_OUT

Each successful movement creates:

- An inventory update
- A stock movement record
- An audit record

---

## Procurement Workflow

The current procurement lifecycle is:

Low Stock

↓

Reorder Recommendation

↓

Purchase Request DRAFT

↓

PENDING_APPROVAL

↓

APPROVED or REJECTED

The requester and approver are treated as separate business actors.

---

## AI Agent

The AI assistant can use approved tools such as:

- Product search
- Location search
- Inventory balance lookup
- Reorder recommendation
- Low-stock lookup
- Supplier lookup
- Human handoff creation

The AI cannot directly:

- Invent inventory quantities
- Approve purchase requests
- Overwrite stock quantities
- Execute arbitrary SQL
- Bypass user permissions

---

## RAG

RAG is used for unstructured business knowledge such as:

- Procurement policies
- Warehouse procedures
- Receiving procedures
- Product notes
- Supplier policies

Structured operational information remains in the database.

---

## Human-in-the-Loop

Unsupported, ambiguous or high-risk AI requests can be escalated through a human handoff.

This creates:

- A human handoff record
- An operational alert
- An audit record

Managers can then review and resolve the case.

---

## Audit Trail

Important business actions are recorded in the audit log.

Examples include:

- Stock Movement Recorded
- Purchase Request Draft Created
- Purchase Request Submitted
- Purchase Request Approved
- Purchase Request Rejected
- Human Handoff Created
- Human Handoff Resolved

The audit trail provides information about:

- Who performed an action
- What action occurred
- Which business record was affected
- When it occurred
- Relevant transaction details

---

## Dashboard

The Streamlit dashboard currently includes:

- Overview
- Inventory
- Reorder
- Exceptions
- Procurement
- AI Assistant
- Approvals
- Stock Movements
- Activity Log

---

## End-to-End Workflow Tested

The following business scenario has been successfully demonstrated:

Low Stock

→ AI verifies inventory shortage

→ Reorder quantity calculated

→ Purchase request prepared

→ Purchase request submitted

→ Manager approval

→ Goods received

→ Inventory updated

→ Reorder requirement removed

→ Low-stock alert resolved

→ Audit trail verified

---

## Current Demo Environment

The current version is a development and demonstration system.

Current architecture includes:

- SQLite database
- Streamlit dashboard
- FastAPI backend
- Demo user IDs
- OpenAI API integration
- RAG knowledge documents

---

## Production Improvements

A production implementation should include:

- PostgreSQL or integration with an existing ERP/WMS
- Real authentication
- JWT, OAuth or enterprise SSO
- Backend duplicate-procurement protection
- Database concurrency controls
- Automated low-stock alert synchronization
- Rate limiting
- Centralized logging
- Production secret management
- AI usage monitoring
- Document permissions and version governance
- Location-specific reorder rules
- Demand forecasting
- Open purchase order awareness
- In-transit inventory
- Supplier lead-time calculations
- Safety stock

---

## Documentation

Additional documentation:

- `docs/task1_requirements.md`
- `docs/task2_data_model.md`
- `docs/task7_conversation_tests.md`
- `docs/task11_security_review.md`
- `docs/task12_demo_script.md`
- `docs/task12_production_readiness.md`

---

## Project Status

Tasks 1–12 completed.

The local Inventory Agent prototype has successfully passed its end-to-end business workflow demonstration.