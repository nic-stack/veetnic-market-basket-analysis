"""Steps 2-4: load the raw POS exports into SQLite, run the SQL files in order,
export the results, then rebuild the pair rules in pandas to check the SQL."""
import itertools
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)
MIN_ORDERS = 30  # must match the threshold in sql/03_market_basket.sql

# --- 1. Load raw data into a fresh database ------------------------------------------------
db_path = ROOT / "veetnic.sqlite"
if db_path.exists():
    db_path.unlink()
con = sqlite3.connect(db_path)

raw_tables = {
    "raw_pos_a_orders": "data/raw/pos_a_orders.csv",
    "raw_pos_a_items": "data/raw/pos_a_items.csv",
    "raw_pos_b_sales": "data/raw/pos_b_sales.csv",
    "products": "data/products.csv",
}
for table, path in raw_tables.items():
    pd.read_csv(ROOT / path).to_sql(table, con, index=False)

# --- 2. Run the SQL steps in order (01_clean, 02_sales_performance, 03_market_basket) -------
for sql_file in sorted((ROOT / "sql").glob("0*.sql")):
    con.executescript(sql_file.read_text())


def query(sql):
    return pd.read_sql(sql, con)


# --- 3. Export results ---------------------------------------------------------------------
result_tables = ["dq_log", "monthly_sales", "category_sales", "product_sales",
                 "system_compare", "discount_impact", "pair_rules", "pair_rules_no_large"]
for table in result_tables:
    query(f"SELECT * FROM {table}").to_csv(RESULTS / f"{table}.csv", index=False)
query("SELECT * FROM sales_clean").to_csv(ROOT / "data/sales_clean.csv", index=False)

# --- 4. Cross-check: rebuild the pair rules in pandas and compare with SQL -----------------
baskets = query("SELECT DISTINCT order_key, product FROM sales_clean")
total_orders = baskets.order_key.nunique()
orders_per_product = baskets.groupby("product").size()

pair_counts = {}
for _, order in baskets.groupby("order_key"):
    for a, b in itertools.combinations(sorted(order["product"]), 2):
        pair_counts[(a, b)] = pair_counts.get((a, b), 0) + 1

pandas_rules = {}
for (a, b), together in pair_counts.items():
    if together >= MIN_ORDERS:
        confidence = together / orders_per_product[a]
        lift = confidence / (orders_per_product[b] / total_orders)
        pandas_rules[(a, b)] = (together, lift)

sql_rules = query("SELECT * FROM pair_rules")
assert len(sql_rules) == len(pandas_rules), (len(sql_rules), len(pandas_rules))
for r in sql_rules.itertuples():
    together, lift = pandas_rules[(r.product_a, r.product_b)]
    assert together == r.orders_together and abs(lift - r.lift) < 0.002, (r.product_a, r.product_b)
print(f"SQL and pandas agree on {len(sql_rules)} pairs; {total_orders} clean orders\n")

# --- 5. Print a summary --------------------------------------------------------------------
summaries = {
    "Data-quality log": "SELECT * FROM dq_log",
    "POS_A vs POS_B after cleaning": "SELECT * FROM system_compare",
    "Sales by category": "SELECT * FROM category_sales",
    "Discount cost": "SELECT * FROM discount_impact",
    "Top pairs by lift": "SELECT * FROM pair_rules ORDER BY lift DESC LIMIT 12",
    "Sensitivity: largest lift change without large orders": """
        SELECT MAX(ABS(r.lift - n.lift)) AS max_lift_change
        FROM pair_rules r JOIN pair_rules_no_large n USING (product_a, product_b)""",
    "Large orders flagged": "SELECT COUNT(*) AS large_orders FROM order_size WHERE large_order = 1",
    "Pairs passing the filter / with lift of 1.5 or more":
        "SELECT COUNT(*) AS pairs, SUM(lift >= 1.5) AS strong FROM pair_rules",
}
for title, sql in summaries.items():
    print(f"{title}:\n{query(sql).to_string()}\n")

con.close()
