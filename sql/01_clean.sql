-- STEP 2: reconcile the two POS exports into one clean sales table. SQLite dialect.
-- Inputs (loaded by src/pipeline.py): raw_pos_a_orders, raw_pos_a_items, raw_pos_b_sales, products.

-- 1. Put both systems into one shape ---------------------------------------------------------
--    POS_A: match product by name (case and spaces ignored). Dates are already ISO. Discount is a fraction.
--    POS_B: match product by code. Convert DD/MM/YYYY to ISO. Convert discount from percent to a fraction.
DROP TABLE IF EXISTS lines_all;
CREATE TABLE lines_all AS
SELECT 'POS_A' AS source_system, 'A-' || a.order_id AS order_key, o.order_date AS order_date,
       p.product_id, a.quantity AS qty, a.discount AS discount, a.rowid AS src_row
FROM raw_pos_a_items a
JOIN raw_pos_a_orders o ON o.order_id = a.order_id
LEFT JOIN products p ON lower(trim(a.product_name)) = lower(p.product_name)
UNION ALL
SELECT 'POS_B', 'B-' || b.txn_ref,
       substr(b.sale_dt, 7, 4) || '-' || substr(b.sale_dt, 4, 2) || '-' || substr(b.sale_dt, 1, 2),
       p.product_id, b.units, b.disc_pct / 100.0, b.rowid
FROM raw_pos_b_sales b
LEFT JOIN products p ON p.product_code = b.item_code;

-- 2. Number repeat scans ---------------------------------------------------------------------
--    A repeat scan is an EXACT copy of another line: same order, product, quantity and discount.
--    That is treated as a scanning error. If the same product appears on separate lines with a
--    different quantity or discount, it could be a real second purchase, so those lines are kept
--    and their quantities add up. Both cases are counted in the data-quality log.
DROP TABLE IF EXISTS lines_flagged;
CREATE TABLE lines_flagged AS
SELECT *, ROW_NUMBER() OVER (PARTITION BY order_key, product_id, qty, discount
                             ORDER BY source_system, src_row) AS occurrence
FROM lines_all;

-- 3. Clean sales table: drop repeat scans and zero-quantity lines; missing discount = 0 --------
--    ASSUMPTION: a missing discount means no discount was given. Logged below.
DROP TABLE IF EXISTS sales_clean;
CREATE TABLE sales_clean AS
SELECT l.source_system, l.order_key, l.order_date, substr(l.order_date, 1, 7) AS month,
       pr.product_name AS product, pr.category, l.qty,
       COALESCE(l.discount, 0) AS discount, pr.price, pr.cost,
       ROUND(l.qty * pr.price * (1 - COALESCE(l.discount, 0)), 2) AS revenue,
       ROUND(l.qty * pr.price * (1 - COALESCE(l.discount, 0)) - l.qty * pr.cost, 2) AS gross_profit
FROM lines_flagged l
JOIN products pr ON pr.product_id = l.product_id
WHERE l.occurrence = 1 AND l.qty > 0;

-- 4. Data-quality log: the count behind every rule --------------------------------------------
DROP TABLE IF EXISTS dq_log;
CREATE TABLE dq_log (step INTEGER, check_name TEXT, n INTEGER, treatment TEXT);
INSERT INTO dq_log VALUES
 (1, 'Raw lines loaded (POS_A + POS_B)', (SELECT COUNT(*) FROM lines_all), 'Starting point.'),
 (2, 'POS_B dates converted from DD/MM/YYYY', (SELECT COUNT(*) FROM raw_pos_b_sales), 'Converted to ISO dates so both systems match.'),
 (3, 'POS_B discounts converted from percent to fraction', (SELECT COUNT(*) FROM raw_pos_b_sales WHERE disc_pct IS NOT NULL), 'Divided by 100 so both systems use the same scale.'),
 (4, 'Lines that could not be matched to a product', (SELECT COUNT(*) FROM lines_all WHERE product_id IS NULL), 'None expected; any would be investigated, not dropped silently.'),
 (5, 'Repeat scans removed', (SELECT COUNT(*) FROM lines_flagged WHERE occurrence > 1), 'Removed: exact copy of another line (same order, product, quantity and discount).'),
 (6, 'Same product on separate lines with different quantity or discount',
     (SELECT COUNT(*) FROM (SELECT order_key, product_id FROM lines_flagged WHERE occurrence = 1
                            GROUP BY order_key, product_id HAVING COUNT(*) > 1)),
     'Kept: could be a real second purchase, so the quantities add up.'),
 (7, 'Zero-quantity lines removed', (SELECT COUNT(*) FROM lines_flagged WHERE occurrence = 1 AND qty = 0), 'Removed: nothing was sold.'),
 (8, 'Missing discounts set to zero', (SELECT COUNT(*) FROM lines_flagged WHERE occurrence = 1 AND qty > 0 AND discount IS NULL), 'Assumption: no discount was given.'),
 (9, 'Clean sales lines', (SELECT COUNT(*) FROM sales_clean), 'Used for all analysis.');
