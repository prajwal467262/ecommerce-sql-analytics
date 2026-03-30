-- ============================================================
-- REVENUE ANALYSIS QUERIES
-- ============================================================

-- 1. Total Revenue by Category with Profit Margins
SELECT
    p.category,
    COUNT(DISTINCT oi.order_id)                          AS total_orders,
    SUM(oi.quantity)                                     AS units_sold,
    ROUND(SUM(oi.revenue), 2)                            AS total_revenue,
    ROUND(SUM(oi.profit), 2)                             AS total_profit,
    ROUND(SUM(oi.profit)/SUM(oi.revenue)*100, 1)         AS profit_margin_pct
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
JOIN orders o   ON oi.order_id   = o.order_id
WHERE o.status = 'Delivered'
GROUP BY p.category
ORDER BY total_revenue DESC;

-- 2. Monthly Revenue with MoM Growth (LAG Window Function)
WITH monthly_rev AS (
    SELECT
        STRFTIME('%Y-%m', o.order_date)  AS month,
        ROUND(SUM(oi.revenue), 2)        AS revenue,
        COUNT(DISTINCT o.order_id)       AS orders
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.status != 'Cancelled'
    GROUP BY month
)
SELECT
    month, revenue, orders,
    LAG(revenue) OVER (ORDER BY month)   AS prev_month_revenue,
    ROUND(
        (revenue - LAG(revenue) OVER (ORDER BY month))
        / LAG(revenue) OVER (ORDER BY month) * 100, 1
    )                                    AS mom_growth_pct,
    ROUND(AVG(revenue) OVER (
        ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 2)                                AS rolling_3m_avg
FROM monthly_rev
ORDER BY month;

-- 3. Revenue Pivot by City × Payment Method
SELECT
    o.city,
    ROUND(SUM(CASE WHEN o.payment='UPI'  THEN oi.revenue ELSE 0 END), 0) AS upi_revenue,
    ROUND(SUM(CASE WHEN o.payment='Card' THEN oi.revenue ELSE 0 END), 0) AS card_revenue,
    ROUND(SUM(CASE WHEN o.payment='COD'  THEN oi.revenue ELSE 0 END), 0) AS cod_revenue,
    ROUND(SUM(oi.revenue), 0)                                             AS total_revenue
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.status = 'Delivered'
GROUP BY o.city
ORDER BY total_revenue DESC;
