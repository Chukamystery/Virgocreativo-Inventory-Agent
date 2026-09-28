import csv
from pathlib import Path

from app.database import Base, SessionLocal, engine
from app.models import (
    Inventory,
    Location,
    Product,
    ProductSupplier,
    Supplier,
    User,
)


DATA_DIR = Path("data/sample")


def read_csv(filename):
    with open(
        DATA_DIR / filename,
        newline="",
        encoding="utf-8"
    ) as file:
        return list(csv.DictReader(file))


def seed():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # Prevent accidental duplicate seeding
        if db.query(Product).count() > 0:
            print("Database already contains products. Seed skipped.")
            return

        # -------------------------
        # USERS
        # -------------------------
        for row in read_csv("users.csv"):
            db.add(
                User(
                    user_id=int(row["user_id"]),
                    full_name=row["full_name"],
                    role=row["role"],
                    active=bool(int(row["active"])),
                )
            )

        # -------------------------
        # PRODUCTS
        # -------------------------
        for row in read_csv("products.csv"):
            db.add(
                Product(
                    product_id=int(row["product_id"]),
                    sku=row["sku"],
                    name=row["name"],
                    category=row["category"],
                    unit_of_measure=row["unit_of_measure"],
                    reorder_point=int(row["reorder_point"]),
                    target_stock=int(row["target_stock"]),
                    active=bool(int(row["active"])),
                )
            )

        # -------------------------
        # LOCATIONS
        # -------------------------
        for row in read_csv("locations.csv"):
            db.add(
                Location(
                    location_id=int(row["location_id"]),
                    code=row["code"],
                    name=row["name"],
                    location_type=row["location_type"],
                    active=bool(int(row["active"])),
                )
            )

        # -------------------------
        # SUPPLIERS
        # -------------------------
        for row in read_csv("suppliers.csv"):
            db.add(
                Supplier(
                    supplier_id=int(row["supplier_id"]),
                    supplier_code=row["supplier_code"],
                    name=row["name"],
                    email=row["email"],
                    phone=row["phone"],
                    lead_time_days=int(row["lead_time_days"]),
                    currency=row["currency"],
                    active=bool(int(row["active"])),
                )
            )

        # Save parent records before bridge/child records
        db.flush()

        # -------------------------
        # PRODUCT SUPPLIERS
        # -------------------------
        for row in read_csv("product_suppliers.csv"):
            db.add(
                ProductSupplier(
                    product_id=int(row["product_id"]),
                    supplier_id=int(row["supplier_id"]),
                    supplier_sku=row["supplier_sku"],
                    unit_cost=float(row["unit_cost"]),
                    minimum_order_qty=int(row["minimum_order_qty"]),
                    preferred=bool(int(row["preferred"])),
                )
            )

        # -------------------------
        # INVENTORY
        # -------------------------
        for row in read_csv("inventory.csv"):
            db.add(
                Inventory(
                    inventory_id=int(row["inventory_id"]),
                    product_id=int(row["product_id"]),
                    location_id=int(row["location_id"]),
                    quantity_on_hand=int(row["quantity_on_hand"]),
                    reserved_quantity=int(row["reserved_quantity"]),
                )
            )

        db.commit()

        print("Sample data seeded successfully.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed()