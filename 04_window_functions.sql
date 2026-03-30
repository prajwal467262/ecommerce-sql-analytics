-- ============================================================
-- ADVANCED WINDOW FUNCTIONS REFERENCE
-- ============================================================

-- All major window functions in one query
WITH monthly_customer AS (
    SELECT
        o.customer_id,
        STRFTIME('%Y-%m', o.order_date) AS month,
        ROUND(SUM(oi.revenue), 2)       AS monthly_spend
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.status = 'Delivered'
    GROUP BY o.customer_id, month
)
SELECT
    customer_id, month, monthly_spend,
    ROW_NUMBER() OVER (PARTITION BY month ORDER BY monthly_spend DESC) AS row_num,
    RANK()       OVER (PARTITION BY month ORDER BY monthly_spend DESC) AS rank_with_gaps,
    DENSE_RANK() OVER (PARTITION BY month ORDER BY monthly_spend DESC) AS dense_rank,
    NTILE(4)     OVER (PARTITION BY month ORDER BY monthly_spend DESC) AS quartile,
    LAG(monthly_spend)  OVER (PARTITION BY customer_id ORDER BY month) AS prev_month,
    LEAD(monthly_spend) OVER (PARTITION BY customer_id ORDER BY month) AS next_month,
    ROUND(SUM(monthly_spend) OVER (PARTITION BY customer_id ORDER BY month), 2) AS cumulative,
    ROUND(AVG(monthly_spend) OVER (
        PARTITION BY customer_id ORDER BY month
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 2) AS rolling_3m_avg
FROM monthly_customer
WHERE customer_id IN ('C0001','C0002','C0003')
ORDER BY customer_id, month;
