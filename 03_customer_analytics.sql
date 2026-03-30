-- ============================================================
-- CUSTOMER ANALYTICS QUERIES
-- ============================================================

-- 1. Customer Lifetime Value with Window Ranking
WITH customer_metrics AS (
    SELECT
        c.customer_id, c.city, c.segment,
        COUNT(DISTINCT o.order_id)    AS total_orders,
        ROUND(SUM(oi.revenue), 2)     AS lifetime_revenue,
        MIN(o.order_date)             AS first_order,
        MAX(o.order_date)             AS last_order
    FROM customers c
    JOIN orders o       ON c.customer_id = o.customer_id
    JOIN order_items oi ON o.order_id    = oi.order_id
    WHERE o.status = 'Delivered'
    GROUP BY c.customer_id, c.city, c.segment
)
SELECT *,
    RANK()   OVER (ORDER BY lifetime_revenue DESC) AS revenue_rank,
    NTILE(4) OVER (ORDER BY lifetime_revenue DESC) AS revenue_quartile
FROM customer_metrics
ORDER BY revenue_rank
LIMIT 20;

-- 2. Full RFM Segmentation in Pure SQL
WITH rfm_base AS (
    SELECT
        o.customer_id,
        CAST(JULIANDAY('2025-01-01') - JULIANDAY(MAX(o.order_date)) AS INT) AS recency_days,
        COUNT(DISTINCT o.order_id)                                           AS frequency,
        ROUND(SUM(oi.revenue), 2)                                            AS monetary
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.status = 'Delivered'
    GROUP BY o.customer_id
),
rfm_scores AS (
    SELECT *,
        NTILE(5) OVER (ORDER BY recency_days ASC)  AS r_score,
        NTILE(5) OVER (ORDER BY frequency DESC)    AS f_score,
        NTILE(5) OVER (ORDER BY monetary DESC)     AS m_score
    FROM rfm_base
)
SELECT
    CASE
        WHEN r_score >= 4 AND f_score >= 4 THEN 'Champions'
        WHEN r_score >= 3 AND f_score >= 3 THEN 'Loyal Customers'
        WHEN r_score >= 4 AND f_score < 3  THEN 'Promising'
        WHEN r_score <= 2 AND (r_score+f_score+m_score) >= 8 THEN 'At Risk'
        WHEN r_score <= 2 AND f_score <= 2 THEN 'Lost'
        ELSE 'Needs Attention'
    END AS segment,
    COUNT(*)                     AS customers,
    ROUND(AVG(monetary), 0)      AS avg_revenue,
    ROUND(SUM(monetary), 0)      AS total_revenue
FROM rfm_scores
GROUP BY segment
ORDER BY total_revenue DESC;

-- 3. Customer Churn Detection
WITH last_activity AS (
    SELECT
        c.customer_id, c.city, c.segment,
        MAX(o.order_date) AS last_order_date,
        CAST(JULIANDAY('2025-01-01') - JULIANDAY(MAX(o.order_date)) AS INT) AS days_inactive
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    WHERE o.status = 'Delivered'
    GROUP BY c.customer_id
)
SELECT *,
    CASE
        WHEN days_inactive > 180 THEN 'Churned'
        WHEN days_inactive > 90  THEN 'At Risk'
        WHEN days_inactive > 30  THEN 'Cooling Off'
        ELSE 'Active'
    END AS churn_status
FROM last_activity
ORDER BY days_inactive DESC;
