-- STEP 4: which products are bought together? SQLite dialect.
-- support    = orders with both products / all orders
-- confidence = orders with both / orders with the first product
-- lift       = confidence / share of all orders containing the second product (above 1 = more than chance)

DROP TABLE IF EXISTS basket_items;
CREATE TABLE basket_items AS SELECT DISTINCT order_key, product FROM sales_clean;

-- Flag unusually large orders (over 10 different products). They are KEPT; a sensitivity run excludes them.
DROP TABLE IF EXISTS order_size;
CREATE TABLE order_size AS
SELECT order_key, COUNT(*) AS items, CASE WHEN COUNT(*) > 10 THEN 1 ELSE 0 END AS large_order
FROM basket_items GROUP BY order_key;

DROP TABLE IF EXISTS item_counts;
CREATE TABLE item_counts AS SELECT product, COUNT(*) AS orders FROM basket_items GROUP BY product;

DROP TABLE IF EXISTS pair_counts;
CREATE TABLE pair_counts AS
SELECT a.product AS product_a, b.product AS product_b, COUNT(*) AS orders_together
FROM basket_items a JOIN basket_items b ON a.order_key = b.order_key AND a.product < b.product
GROUP BY a.product, b.product;

DROP TABLE IF EXISTS pair_rules;
CREATE TABLE pair_rules AS
WITH n AS (SELECT COUNT(DISTINCT order_key) AS total FROM basket_items)
SELECT p.product_a, p.product_b, p.orders_together, ca.orders AS orders_a, cb.orders AS orders_b, n.total AS total_orders,
       ROUND(1.0 * p.orders_together / n.total, 4) AS support,
       ROUND(1.0 * p.orders_together / ca.orders, 4) AS confidence_a_to_b,
       ROUND(1.0 * p.orders_together / cb.orders, 4) AS confidence_b_to_a,
       ROUND((1.0 * p.orders_together / ca.orders) / (1.0 * cb.orders / n.total), 3) AS lift
FROM pair_counts p
JOIN item_counts ca ON ca.product = p.product_a
JOIN item_counts cb ON cb.product = p.product_b, n
WHERE p.orders_together >= 30;      -- ignore pairs seen in fewer than 30 orders

-- Sensitivity: same lifts without the large orders
DROP TABLE IF EXISTS pair_rules_no_large;
CREATE TABLE pair_rules_no_large AS
WITH bi AS (SELECT b.* FROM basket_items b JOIN order_size s USING (order_key) WHERE s.large_order = 0),
     n  AS (SELECT COUNT(DISTINCT order_key) AS total FROM bi),
     ic AS (SELECT product, COUNT(*) AS orders FROM bi GROUP BY product),
     pc AS (SELECT a.product AS product_a, b.product AS product_b, COUNT(*) AS orders_together
            FROM bi a JOIN bi b ON a.order_key = b.order_key AND a.product < b.product GROUP BY 1, 2)
SELECT pc.product_a, pc.product_b, pc.orders_together,
       ROUND((1.0 * pc.orders_together / ca.orders) / (1.0 * cb.orders / n.total), 3) AS lift
FROM pc JOIN ic ca ON ca.product = pc.product_a JOIN ic cb ON cb.product = pc.product_b, n
WHERE pc.orders_together >= 30;
