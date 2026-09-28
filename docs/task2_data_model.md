# Task 2 - Inventory Data Model

## Core Rule

Structured operational facts come from the database.

The language model may request inventory information through
validated tools/functions, but it must not invent or directly
overwrite inventory values.

## Core Tables

The Inventory Agent will initially use the following structured tables:

1. users
2. products
3. locations
4. suppliers
5. product_suppliers
6. inventory


## Products Table

The products table stores the basic information about every item
managed by the inventory system.

Fields:

- product_id
- sku
- name
- category
- unit_of_measure
- reorder_point
- target_stock
- active

Example:

product_id: 1
sku: SKU-001
name: USB-C Charger 65W
category: Electronics
unit_of_measure: unit
reorder_point: 20
target_stock: 60
active: true


## Locations Table

The locations table identifies where inventory is physically stored.

Fields:

- location_id
- code
- name
- location_type
- active

Example:

location_id: 1
code: WH-MAIN
name: Main Warehouse
location_type: WAREHOUSE
active: true


## Suppliers Table

The suppliers table stores information about approved suppliers.

Fields:

- supplier_id
- supplier_code
- name
- email
- phone
- lead_time_days
- currency
- active


## Product Suppliers Table

A product can have more than one supplier.

A supplier can also provide more than one product.

The product_suppliers table connects products and suppliers.

Fields:

- product_id
- supplier_id
- supplier_sku
- unit_cost
- minimum_order_qty
- preferred


## Inventory Table

The inventory table stores the current quantity of each product
at each location.

Fields:

- inventory_id
- product_id
- location_id
- quantity_on_hand
- reserved_quantity

Available quantity will be calculated as:

available_quantity =
quantity_on_hand - reserved_quantity


## Users Table

The users table identifies people who may interact with the
Inventory Agent.

Fields:

- user_id
- full_name
- role
- active

Initial roles:

- INVENTORY_STAFF
- INVENTORY_MANAGER
- PROCUREMENT_OFFICER
- ADMIN


## Table Relationships

PRODUCTS ----< INVENTORY >---- LOCATIONS

PRODUCTS ----< PRODUCT_SUPPLIERS >---- SUPPLIERS

One product can exist at multiple locations.

One location can contain multiple products.

One product can have multiple suppliers.

One supplier can provide multiple products.


## Future Tables

The following tables will be added in later tasks:

- stock_movements
- purchase_requests
- purchase_request_lines
- alerts
- audit_logs


## Data Integrity Rules

1. SKU must be unique.

2. Supplier code must be unique.

3. Location code must be unique.

4. quantity_on_hand cannot be negative.

5. reserved_quantity cannot be negative.

6. reserved_quantity cannot be greater than quantity_on_hand.

7. reorder_point cannot be negative.

8. target_stock must be greater than or equal to reorder_point.

9. unit_cost cannot be negative.

10. There should not be duplicate inventory records for the same
product and location.

11. Products with transaction history should be marked inactive
instead of being deleted.


## Source of Truth Rule

The structured database will be the source of truth for:

- products
- locations
- inventory quantities
- suppliers
- reorder information
- stock movements
- approvals

The language model must not invent these values.

The language model must access them through validated tools/functions.


## RAG Boundary

RAG will only be used for unstructured information such as:

- inventory SOPs
- warehouse procedures
- supplier policies
- product handling instructions
- purchasing procedures

RAG must not be used as the source of truth for live inventory
quantities.