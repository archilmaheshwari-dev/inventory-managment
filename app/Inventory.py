"""
inventory.py — Pharmacy stock and billing management
"""

"""
inventory.py — Pharmacy stock and billing management
"""

from app.Db import get_cursor


def add_medicine(name: str, unit_price: float, initial_stock: int = 0) -> dict:
    """Add a new medicine to the catalog"""
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO medicines (name, unit_price, stock_quantity)
               VALUES (%s, %s, %s) RETURNING *""",
            (name, unit_price, initial_stock)
        )
        medicine = cur.fetchone()

        if initial_stock > 0:
            cur.execute(
                """INSERT INTO stock_log (medicine_id, action, quantity_change)
                   VALUES (%s, 'restock', %s)""",
                (medicine["id"], initial_stock)
            )
        return medicine


def restock_medicine(medicine_id: int, quantity: int) -> dict:
    """Add stock to an existing medicine"""
    with get_cursor() as cur:
        cur.execute(
            """UPDATE medicines SET stock_quantity = stock_quantity + %s
               WHERE id = %s RETURNING *""",
            (quantity, medicine_id)
        )
        medicine = cur.fetchone()

        cur.execute(
            """INSERT INTO stock_log (medicine_id, action, quantity_change)
               VALUES (%s, 'restock', %s)""",
            (medicine_id, quantity)
        )
        return medicine


def get_all_medicines() -> list[dict]:
    """List all medicines with current stock"""
    with get_cursor() as cur:
        cur.execute("SELECT * FROM medicines ORDER BY name ASC")
        return cur.fetchall()


def get_medicine_by_name(name: str) -> dict | None:
    """Find a medicine by name (case-insensitive)"""
    with get_cursor() as cur:
        cur.execute("SELECT * FROM medicines WHERE LOWER(name) = LOWER(%s)", (name,))
        return cur.fetchone()


def create_sale(patient_id: int, items: list[dict], discount: float = 0, visit_id: int = None) -> dict:
    """
    Create a new sale with multiple line items.
    items = [{"medicine_id": 1, "quantity": 2}, {"medicine_id": 3, "quantity": 1}]

    Checks stock availability, deducts stock, logs the transaction,
    and returns the full sale + line item details.
    """
    with get_cursor() as cur:
        total = 0
        line_items = []

        # First pass — validate stock and calculate total
        for item in items:
            cur.execute("SELECT * FROM medicines WHERE id = %s", (item["medicine_id"],))
            medicine = cur.fetchone()

            if not medicine:
                raise ValueError(f"Medicine ID {item['medicine_id']} not found")
            if medicine["stock_quantity"] < item["quantity"]:
                raise ValueError(
                    f"Insufficient stock for {medicine['name']}. "
                    f"Available: {medicine['stock_quantity']}, Requested: {item['quantity']}"
                )

            line_total = float(medicine["unit_price"]) * item["quantity"]
            total += line_total
            line_items.append({
                "medicine_id": medicine["id"],
                "name": medicine["name"],
                "quantity": item["quantity"],
                "price_at_sale": medicine["unit_price"],
                "line_total": line_total
            })

        final_amount = total - discount

        # Create the sale record
        cur.execute(
            """INSERT INTO sales (visit_id, patient_id, total_amount, discount, final_amount)
               VALUES (%s, %s, %s, %s, %s) RETURNING *""",
            (visit_id, patient_id, total, discount, final_amount)
        )
        sale = cur.fetchone()

        # Create sale items and deduct stock
        for li in line_items:
            cur.execute(
                """INSERT INTO sale_items (sale_id, medicine_id, quantity, price_at_sale)
                   VALUES (%s, %s, %s, %s)""",
                (sale["id"], li["medicine_id"], li["quantity"], li["price_at_sale"])
            )
            cur.execute(
                """UPDATE medicines SET stock_quantity = stock_quantity - %s
                   WHERE id = %s""",
                (li["quantity"], li["medicine_id"])
            )
            cur.execute(
                """INSERT INTO stock_log (medicine_id, action, quantity_change, reference_sale_id)
                   VALUES (%s, 'sale', %s, %s)""",
                (li["medicine_id"], -li["quantity"], sale["id"])
            )

        sale["items"] = line_items
        return sale


def get_sale_details(sale_id: int) -> dict:
    """Get full details of a sale including line items"""
    with get_cursor() as cur:
        cur.execute("SELECT * FROM sales WHERE id = %s", (sale_id,))
        sale = cur.fetchone()
        if not sale:
            return None

        cur.execute(
            """SELECT si.*, m.name as medicine_name
               FROM sale_items si
               JOIN medicines m ON si.medicine_id = m.id
               WHERE si.sale_id = %s""",
            (sale_id,)
        )
        sale["items"] = cur.fetchall()
        return sale


def get_sales_for_patient(patient_id: int) -> list[dict]:
    """Get all past sales/invoices for a patient"""
    with get_cursor() as cur:
        cur.execute(
            """SELECT * FROM sales WHERE patient_id = %s
               ORDER BY sale_date DESC""",
            (patient_id,)
        )
        return cur.fetchall()


def get_low_stock_medicines(threshold: int = 10) -> list[dict]:
    """Get medicines running low on stock — useful for restock alerts"""
    with get_cursor() as cur:
        cur.execute(
            """SELECT * FROM medicines WHERE stock_quantity <= %s
               ORDER BY stock_quantity ASC""",
            (threshold,)
        )
        return cur.fetchall()