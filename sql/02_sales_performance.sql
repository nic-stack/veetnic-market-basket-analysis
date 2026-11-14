-- STEP 3: is the business making money? Revenue, gross profit and discounts. SQLite dialect.
-- Gross profit = revenue minus product cost. It excludes rent, wages and other operating costs.

DROP TABLE IF EXISTS monthly_sales;
CREATE TABLE monthly_sales AS
SELECT month, COUNT(DISTINCT order_key) AS orders, ROUND(SUM(revenue), 2) AS revenue,
       ROUND(SUM(gross_profit), 2) AS gross_profit,
       ROUND(100.0 * SUM(gross_profit) / SUM(revenue), 1) AS margin_pct
FROM sales_clean GROUP BY month ORDER BY month;

DROP TABLE IF EXISTS category_sales;
CREATE TABLE category_sales AS
SELECT category, SUM(qty) AS units, ROUND(SUM(revenue), 2) AS revenue, ROUND(SUM(gross_profit), 2) AS gross_profit,
       ROUND(100.0 * SUM(gross_profit) / SUM(revenue), 1) AS margin_pct
FROM sales_clean GROUP BY category ORDER BY revenue DESC;

DROP TABLE IF EXISTS product_sales;
CREATE TABLE product_sales AS
SELECT product, category, SUM(qty) AS units, ROUND(SUM(revenue), 2) AS revenue, ROUND(SUM(gross_profit), 2) AS gross_profit,
       ROUND(100.0 * SUM(gross_profit) / SUM(revenue), 1) AS margin_pct
FROM sales_clean GROUP BY product ORDER BY revenue DESC;

-- Reconciliation check: do the two systems tell the same story once cleaned?
DROP TABLE IF EXISTS system_compare;
CREATE TABLE system_compare AS
SELECT source_system, COUNT(DISTINCT order_key) AS orders, ROUND(SUM(revenue), 2) AS revenue,
       ROUND(SUM(revenue) / COUNT(DISTINCT order_key), 2) AS avg_order_value,
       ROUND(100.0 * SUM(gross_profit) / SUM(revenue), 1) AS margin_pct
FROM sales_clean GROUP BY source_system;

-- What discounts cost: revenue given up versus list price
DROP TABLE IF EXISTS discount_impact;
CREATE TABLE discount_impact AS
SELECT ROUND(SUM(qty * price), 2) AS revenue_at_list_price, ROUND(SUM(revenue), 2) AS revenue_after_discount,
       ROUND(SUM(qty * price) - SUM(revenue), 2) AS discount_cost,
       ROUND(100.0 * (SUM(qty * price) - SUM(revenue)) / SUM(qty * price), 1) AS discount_pct_of_list
FROM sales_clean;
