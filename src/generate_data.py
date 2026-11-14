"""Step 1: generate SYNTHETIC grocery data exported from two different point-of-sale systems.

Nothing here is real VEETNIC data. Two shopping "themes" (breakfast, cleaning) are planted on purpose,
so the analysis can be tested on whether it recovers them. Fixed seed, so the output is reproducible.
POS_A and POS_B deliberately export in different formats (names vs codes, ISO dates vs DD/MM/YYYY,
discount as a fraction vs a whole percent) so the cleaning step has a real reconciliation job to do.
"""
import numpy as np, pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"; RAW.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(42)

# code, name, category, price, cost  (all invented, USD)
PRODUCTS = [
    ("BRD01", "Bread", "Breakfast", 1.5, 1.0), ("MLK01", "Milk", "Breakfast", 2.0, 1.3),
    ("BTR01", "Butter", "Breakfast", 3.0, 2.0), ("CHS01", "Cheese", "Breakfast", 3.5, 2.5),
    ("PLN01", "Polony", "Breakfast", 2.5, 1.7), ("EGG01", "Eggs", "Breakfast", 3.0, 2.2),
    ("FLC01", "Floor Cleaner", "Cleaning", 4.0, 2.7), ("WLC01", "Wall Cleaner", "Cleaning", 4.5, 3.0),
    ("DSH01", "Dish Soap", "Cleaning", 2.5, 1.6), ("SPG01", "Sponges", "Cleaning", 1.5, 0.8),
    ("RCE01", "Rice", "Grocery & Personal Care", 5.0, 3.7), ("SGR01", "Sugar", "Grocery & Personal Care", 2.0, 1.3),
    ("TEA01", "Tea", "Grocery & Personal Care", 2.5, 1.6), ("OIL01", "Cooking Oil", "Grocery & Personal Care", 4.0, 2.9),
    ("SOP01", "Soap", "Grocery & Personal Care", 1.5, 0.9), ("TPS01", "Toothpaste", "Grocery & Personal Care", 2.5, 1.6),
]
prod = pd.DataFrame(PRODUCTS, columns=["product_code", "product_name", "category", "price", "cost"])
prod.insert(0, "product_id", range(1, len(prod) + 1))
prod.to_csv(ROOT / "data" / "products.csv", index=False)
names = prod.product_name.tolist(); code_of = dict(zip(prod.product_name, prod.product_code))

N_ORDERS = 2400
rows, orders = [], []
for i in range(1, N_ORDERS + 1):
    date = pd.Timestamp("2024-01-01") + pd.Timedelta(days=int(rng.integers(0, 366)))
    system = str(rng.choice(["POS_A", "POS_B"]))
    theme = rng.choice(["breakfast", "cleaning", "other"], p=[.37, .27, .36])
    basket = set()
    if theme == "breakfast":
        basket.add("Bread")
        for item, p in [("Milk", .78), ("Butter", .56), ("Cheese", .35), ("Polony", .30)]:
            if rng.random() < p: basket.add(item)
    elif theme == "cleaning":
        basket.add("Floor Cleaner")
        for item, p in [("Wall Cleaner", .72), ("Dish Soap", .60), ("Sponges", .42)]:
            if rng.random() < p: basket.add(item)
    while len(basket) < int(rng.integers(2, 6)):          # fill small baskets with random items
        basket.add(str(rng.choice(names)))
    orders.append((i, date, system))
    for item in sorted(basket):   # sorted: set order changes between runs, which would break the fixed seed
        rows.append((i, item, int(rng.choice([1, 1, 1, 2, 2, 3])), float(rng.choice([0, 0, 0, .05, .10]))))

# one wholesale-style order (all 16 products, big quantities), kept in the data on purpose
i = N_ORDERS + 1
orders.append((i, pd.Timestamp("2024-06-14"), "POS_A"))
for item in names: rows.append((i, item, int(rng.integers(10, 21)), 0.10))

orders = pd.DataFrame(orders, columns=["oid", "date", "system"])
lines = pd.DataFrame(rows, columns=["oid", "product", "quantity", "discount"])

# inject the data-quality problems the cleaning step must find
lines = pd.concat([lines, lines.sample(12, random_state=4)], ignore_index=True)          # duplicate scans
lines.loc[lines.sample(9, random_state=5).index, "discount"] = np.nan                    # missing discount
lines.loc[lines.sample(6, random_state=6).index, "quantity"] = 0                         # zero-quantity lines
lines = lines.merge(orders, on="oid")

# ---- POS_A export: product NAMES (some typed inconsistently), ISO dates, discount as a fraction
a = lines[lines.system == "POS_A"].copy()
def messy(n):
    r = rng.random()
    return n.upper() if r < .03 else n.lower() if r < .06 else n + " " if r < .08 else n
a["product_name"] = a["product"].map(messy)
a["order_id"] = a.oid.map(lambda x: f"V{x:05d}")
a[["order_id", "product_name", "quantity", "discount"]].to_csv(RAW / "pos_a_items.csv", index=False)
oa = orders[orders.system == "POS_A"].copy(); oa["order_id"] = oa.oid.map(lambda x: f"V{x:05d}")
oa["order_date"] = oa.date.dt.strftime("%Y-%m-%d")
oa[["order_id", "order_date"]].to_csv(RAW / "pos_a_orders.csv", index=False)

# ---- POS_B export: one flat file, product CODES, DD/MM/YYYY dates, discount as a whole percent
b = lines[lines.system == "POS_B"].copy()
b["txn_ref"] = b.oid.map(lambda x: f"TXN-{x:05d}")
b["sale_dt"] = b.date.dt.strftime("%d/%m/%Y")
b["item_code"] = b["product"].map(code_of)
b["units"] = b["quantity"]
b["disc_pct"] = (b["discount"] * 100).round()
b[["txn_ref", "sale_dt", "item_code", "units", "disc_pct"]].to_csv(RAW / "pos_b_sales.csv", index=False)
print(f"orders: {len(orders):,} | raw lines: {len(lines):,} | POS_A lines: {len(a):,} | POS_B lines: {len(b):,}")
