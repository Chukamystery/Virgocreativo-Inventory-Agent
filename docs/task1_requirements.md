# Inventory Agent Project Requirements

## 1. Business Scenario

The Inventory Agent is being developed for a small-to-medium business
that stores products in a warehouse.

Employees currently need to manually check inventory records to determine:

- available stock
- low-stock products
- products that need reordering
- supplier information
- incoming and outgoing stock
- purchasing requirements

The Inventory Agent will provide a conversational interface that allows
authorized users to retrieve inventory information and initiate controlled
inventory operations.

## 2. Problem Statement

The business needs a reliable and controlled way for employees to access
inventory information and perform approved inventory-related actions.

Current inventory processes may require employees to search manually through
inventory records, spreadsheets or multiple systems.

This can result in:

- slow access to stock information
- inconsistent inventory information
- delayed identification of low-stock items
- manual reorder calculations
- poor visibility of stock movements
- difficulty finding supplier information
- insufficient audit trails
- risk of unauthorized inventory adjustments

## 3. Source of Truth

The structured inventory database is the source of truth for operational
inventory information.

The following information must come from the database or validated
application tools:

- inventory quantities
- product information
- stock movements
- reorder points
- reorder quantities
- supplier records
- purchase requests
- approvals

The language model must never invent inventory values.

The language model must also never directly modify inventory quantities.

All inventory changes must happen through validated application functions.

## 4. Role of the Language Model

The language model is responsible for:

- understanding user questions
- determining which inventory tool should be used
- calling approved tools
- explaining tool results in natural language
- helping users navigate inventory workflows
- identifying situations that require human intervention

The language model is NOT responsible for:

- creating inventory quantities
- directly changing stock quantities
- independently approving transactions
- inventing suppliers
- inventing purchase orders
- inventing reorder calculations

## 5. Users

### Inventory Staff

Can:

- search products
- check stock quantities
- view inventory information
- request inventory movements

### Inventory Manager

Can:

- review inventory
- review low-stock items
- approve sensitive stock movements
- investigate inventory exceptions

### Procurement Officer

Can:

- view reorder recommendations
- retrieve supplier information
- prepare purchase requests
- review procurement requirements

### Administrator

Can:

- manage system access
- review logs
- manage system configuration

## 6. Inventory Agent Use Cases

### Use Case 1 - Check Stock Quantity

**User Request Example:**

"How many HP keyboards do we have?"

**Agent Action:**

1. Identify the requested product.
2. Call the inventory lookup tool.
3. Retrieve the current stock quantity from the database.
4. Return the verified quantity to the user.

**Source of Truth:** Structured inventory database.

**Approval Required:** No.

---

### Use Case 2 - Search for a Product

**User Request Example:**

"Do we have Logitech wireless mouse?"

**Agent Action:**

1. Search the product database.
2. Find matching products.
3. Return the product name, SKU and availability.

**Source of Truth:** Product database.

**Approval Required:** No.

---

### Use Case 3 - Identify Low-Stock Items

**User Request Example:**

"Which products are running low?"

**Agent Action:**

1. Retrieve inventory quantities.
2. Retrieve the reorder point for each product.
3. Compare the current stock with the defined reorder point.
4. Return products that are below or equal to their reorder threshold.

**Example Rule:**

Current Stock <= Reorder Point

**Source of Truth:** Inventory database and defined business rules.

**Approval Required:** No.

---

### Use Case 4 - Calculate Reorder Quantity

**User Request Example:**

"How many units of USB-C chargers should we reorder?"

**Agent Action:**

1. Retrieve the current stock quantity.
2. Retrieve the reorder point.
3. Retrieve the target or maximum stock level.
4. Send the values to the reorder calculation function.
5. Return the calculated reorder recommendation.

**Example Business Rule:**

Reorder Quantity = Target Stock Level - Current Stock

The language model must not calculate or invent the inventory values itself.

**Source of Truth:** Database and validated reorder calculation function.

**Approval Required:** No for calculation.

Approval may be required before a purchase request is submitted.

---

### Use Case 5 - Record Stock Received

**User Request Example:**

"We received 50 units of HP keyboards."

**Agent Action:**

1. Identify the product.
2. Validate the quantity.
3. Check the user's permission.
4. Create a stock receipt request.
5. Request approval where required.
6. Call the stock movement function after approval.
7. Record the inventory movement.
8. Update the inventory quantity.
9. Create an audit log.

**Source of Truth:** Inventory database.

**Approval Required:** Yes.

The language model must never directly increase the stock quantity.

---

### Use Case 6 - Record Stock Issued

**User Request Example:**

"Issue 10 Dell keyboards."

**Agent Action:**

1. Identify the product.
2. Retrieve the current stock quantity.
3. Confirm that sufficient stock exists.
4. Validate the requested quantity.
5. Check user permissions.
6. Request approval where required.
7. Call the stock movement function.
8. Reduce the stock through a database transaction.
9. Record the movement in the audit log.

**Source of Truth:** Inventory database.

**Approval Required:** Yes.

The system must reject the transaction if it would cause invalid or unauthorized negative stock.

---

### Use Case 7 - Retrieve Supplier Information

**User Request Example:**

"Who supplies the USB-C chargers?"

**Agent Action:**

1. Identify the product.
2. Search the supplier database.
3. Retrieve approved supplier information.
4. Return the supplier details to the user.

**Possible Information Returned:**

- Supplier name
- Supplier contact
- Supplier email
- Lead time
- Supplier status
- Product supplied

**Source of Truth:** Structured supplier database.

**Approval Required:** No.

---

### Use Case 8 - Prepare a Purchase or Reorder Request

**User Request Example:**

"Prepare a reorder request for all products below minimum stock."

**Agent Action:**

1. Find products below their reorder threshold.
2. Calculate the required reorder quantity using business rules.
3. Retrieve the approved supplier for each product.
4. Prepare a draft purchase/reorder request.
5. Submit the draft for human review or approval.

**Source of Truth:**

- Inventory database
- Supplier database
- Reorder calculation tool

**Approval Required:** Yes before final purchasing action.

The agent may prepare the request but must not automatically purchase products.

---

### Use Case 9 - Generate Inventory Alerts

**Example Situation:**

"USB-C Charger has fallen below its reorder point."

**Agent Action:**

1. Detect that inventory has crossed a defined threshold.
2. Create an alert.
3. Include the product, current quantity and reorder threshold.
4. Send or queue the alert for the appropriate user.

**Possible Alert Channels:**

- Application notification
- Email
- Slack
- Microsoft Teams

**Source of Truth:** Inventory database and alert rules.

**Approval Required:** No for sending an informational alert.

---

### Use Case 10 - Human Handoff

**User Request Example:**

"Remove 5,000 laptops from inventory because they are missing."

**Agent Action:**

1. Detect that the transaction is unusually large or risky.
2. Do not change the inventory.
3. Record the requested transaction as an exception.
4. Notify the Inventory Manager or authorized user.
5. Wait for human review and approval.

**Other Handoff Conditions:**

- User does not have permission.
- Requested quantity exceeds available stock.
- Product cannot be identified.
- Supplier information is missing.
- Conflicting inventory information is detected.
- Database or tool failure occurs.
- Transaction exceeds a defined risk threshold.
- The agent cannot safely determine the user's intention.

**Source of Truth:** Database, application rules and approval system.

**Approval Required:** Yes.

## 7. RAG Boundaries

RAG may be used for unstructured knowledge such as:

- warehouse SOPs
- purchasing procedures
- supplier policies
- product handling instructions
- inventory policies
- procurement rules

RAG must NOT be used as the source of truth for:

- stock quantities
- stock movements
- reorder quantities
- approvals
- live supplier transactions

## 8. Approval Requirements

The Inventory Agent must follow approval rules before performing sensitive
inventory or procurement actions.

The purpose of the approval process is to prevent unauthorized or incorrect
changes to inventory records.

### Approval Matrix

| Action | Approval Required | Authorized Role |
|---|---|---|
| Check stock quantity | No | Inventory Staff |
| Search products | No | Inventory Staff |
| View low-stock items | No | Inventory Staff |
| View supplier information | No | Inventory Staff / Procurement Officer |
| Calculate reorder quantity | No | Inventory Staff / Procurement Officer |
| Prepare purchase request | No | Procurement Officer |
| Submit purchase request | Yes | Procurement Manager / Authorized Manager |
| Receive stock into inventory | Yes | Inventory Manager |
| Issue stock from inventory | Yes | Inventory Manager |
| Adjust stock quantity | Yes | Inventory Manager |
| Delete inventory record | Yes | Administrator |
| Large or unusual stock movement | Yes | Inventory Manager |
| Override inventory rules | Yes | Administrator / Authorized Manager |

### Approval Rules

1. Read-only actions such as checking stock or viewing supplier information
   do not require approval.

2. The agent may calculate reorder recommendations without approval because
   the calculation does not change inventory.

3. The agent may prepare a draft purchase request, but the final purchasing
   action must require human approval.

4. Any action that changes inventory quantities must pass through a validated
   stock movement function.

5. Sensitive inventory movements must be approved by an authorized user.

6. The language model must never approve its own transaction.

7. The language model must never directly modify inventory quantities.

8. If approval is required but has not been received, the transaction must
   remain pending.

9. If the user does not have permission to perform an action, the agent must
   reject the request or escalate it to an authorized person.

10. All approved inventory-changing actions must create an audit record.

## 8. Human Handoff Conditions

The agent should request human intervention when:

- the requested transaction is unusually large
- the user does not have permission
- inventory would become negative
- required inventory data is missing
- supplier information is missing
- conflicting data is detected
- approval is required
- an unexpected system error occurs
- the agent is uncertain about the requested transaction

## 9. Success Criteria

The Inventory Agent will be considered successful when:

1. Stock quantities returned by the agent exactly match the database.

2. The agent never invents missing inventory quantities.

3. Low-stock detection follows defined business rules.

4. Reorder calculations are performed by validated business logic.

5. Inventory values cannot be directly changed by the language model.

6. Stock movements are recorded with an audit trail.

7. Sensitive stock movements require appropriate authorization.

8. Supplier information comes from approved data sources.

9. Procurement requests can be prepared without automatically purchasing products.

10. Risky or exceptional transactions are escalated to a human.

11. System errors do not cause unauthorized inventory changes.

12. Every inventory-changing transaction can be traced back to its user and action.

## 10. Expected Inventory Agent Behaviour

The completed Inventory Agent should be able to handle common inventory
questions and controlled inventory actions through natural language.

### Example 1 - Check Stock

**User:**

How many Dell keyboards do we have?

**Expected Agent Behaviour:**

1. Identify the requested product.
2. Call the inventory lookup tool.
3. Retrieve the live quantity from the database.
4. Return the verified result.

**Example Response:**

"There are currently 48 Dell keyboards in stock."

**Important Rule:**

The quantity must come from the structured inventory database.
The language model must not guess or invent the quantity.

---

### Example 2 - Check Low-Stock Items

**User:**

Which items need reordering?

**Expected Agent Behaviour:**

1. Retrieve the relevant inventory records.
2. Compare current stock against each product's reorder point.
3. Use the defined reorder business rules.
4. Return only the products that meet the low-stock condition.

**Example Response:**

"Three products are currently below their reorder points:

1. Wireless Mouse - 8 available - Reorder Point: 15
2. USB-C Charger - 12 available - Reorder Point: 20
3. HDMI Cable - 4 available - Reorder Point: 10"

**Important Rule:**

The quantities and reorder points must come from the database.

The low-stock decision must come from defined business logic.

---

### Example 3 - Calculate Reorder Quantity

**User:**

How many USB-C chargers should we reorder?

**Expected Agent Behaviour:**

1. Retrieve the current stock quantity.
2. Retrieve the reorder point and target stock level.
3. Pass the values to the reorder calculation function.
4. Return the calculated recommendation.

**Example Response:**

"There are currently 12 USB-C chargers in stock.
The target stock level is 50 units.
Based on the defined reorder rule, the recommended reorder quantity is
38 units."

**Important Rule:**

The language model must not invent or independently calculate the
inventory values.

The reorder quantity must be produced using validated business logic.

---

### Example 4 - Retrieve Supplier Information

**User:**

Who supplies the USB-C chargers?

**Expected Agent Behaviour:**

1. Identify the product.
2. Search the structured supplier records.
3. Return the approved supplier information.

**Example Response:**

"The approved supplier for USB-C chargers is ABC Supplies Ltd.
The recorded lead time is 5 working days."

**Important Rule:**

Supplier information must come from an approved data source.

---

### Example 5 - Prepare Reorder Request

**User:**

Prepare a reorder request for everything below minimum stock.

**Expected Agent Behaviour:**

1. Identify all products below their reorder thresholds.
2. Calculate the required reorder quantities.
3. Retrieve approved suppliers.
4. Prepare a draft purchase/reorder request.
5. Send the draft for human review where required.

**Example Response:**

"I prepared a draft reorder request for 3 products.
The request is awaiting procurement review."

**Important Rule:**

Preparing a draft does not mean the agent is authorized to purchase
the products automatically.

---

### Example 6 - Record Stock Receipt

**User:**

We received 50 units of Dell keyboards.

**Expected Agent Behaviour:**

1. Identify the product.
2. Validate the quantity.
3. Check the user's permission.
4. Request approval where required.
5. Call the approved stock movement function.
6. Update the inventory only after validation and approval.
7. Create an audit record.

**Example Response Before Approval:**

"A request to receive 50 Dell keyboards has been prepared and is
awaiting approval."

**Example Response After Approval:**

"The approved stock receipt has been recorded successfully.
50 Dell keyboards were added to inventory and the transaction was
logged."

**Important Rule:**

The language model must never directly increase the inventory quantity.

---

### Example 7 - Risky Stock Movement

**User:**

Remove 5,000 laptops from inventory because they are missing.

**Expected Agent Behaviour:**

1. Recognize the request as unusually large or risky.
2. Do not modify the inventory.
3. Create an exception or approval request.
4. Notify the appropriate human reviewer.

**Example Response:**

"This transaction has been flagged for human review because the
requested stock adjustment exceeds the allowed risk threshold.
No inventory quantities have been changed."

**Important Rule:**

High-risk transactions must not be executed automatically.

---

### Example 8 - Missing or Unverified Information

**User:**

How many units of Product XYZ do we have?

**Expected Agent Behaviour:**

If Product XYZ cannot be found in the approved inventory records, the
agent must not invent an answer.

**Example Response:**

"I could not verify Product XYZ in the inventory database.
No stock quantity can be confirmed from the available records."

**Important Rule:**

When the system cannot verify inventory information, it must say so
rather than guessing.




                    USER
                      │
                      ▼
              INVENTORY AGENT
               (LLM / Chat)
                      │
          ┌───────────┴───────────┐
          │                       │
          ▼                       ▼
   INVENTORY TOOLS            RAG SYSTEM
          │                       │
          ▼                       ▼
 STRUCTURED DATABASE        SOPs / Policies
          │
          ▼
 Products
 Inventory
 Movements
 Suppliers
 Purchase Requests
 Approvals
 Audit Logs

 ## 11. Non-Negotiable System Rules

RULE 1:
The database is the source of truth for inventory quantities.

RULE 2:
The language model cannot directly change inventory values.

RULE 3:
Stock changes must happen through validated application functions.

RULE 4:
Every stock movement must create an audit record.

RULE 5:
Reorder calculations must use defined business rules.

RULE 6:
RAG cannot provide live inventory quantities.

RULE 7:
Sensitive transactions require authorization.

RULE 8:
The system must reject invalid inventory transactions.

RULE 9:
High-risk situations must be escalated to a human.

RULE 10:
When inventory information cannot be verified, the agent must say that
it cannot verify the information rather than invent an answer.