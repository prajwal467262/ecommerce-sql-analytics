import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="E-Commerce SQL Analytics",
    page_icon="🛍️",
    layout="wide"
)

st.markdown("""
<style>
.sql-box {
    background: #0d1117; border: 1px solid #2a2a3a;
    border-left: 3px solid #c8f04a;
    padding: 1rem 1.25rem; font-family: 'Courier New', monospace;
    font-size: 0.75rem; color: #e8e8f0; margin-bottom: 0.75rem;
    white-space: pre-wrap; line-height: 1.7;
}
.insight-box {
    background: #111118; border-left: 3px solid #7c6af7;
    padding: 0.75rem 1rem; margin: 0.5rem 0; font-size: 0.78rem;
    border-radius: 0 4px 4px 0;
}
.kw { color: #ff7b72; font-weight: bold; }
.fn { color: #d2a8ff; }
.cm { color: #8b949e; font-style: italic; }
.st { color: #a5d6ff; }
.nm { color: #f0c060; }
.badge {
    display: inline-block; font-size: 0.55rem; letter-spacing: 0.1em;
    text-transform: uppercase; padding: 0.15rem 0.45rem;
    border-radius: 2px; margin-right: 0.3rem; font-weight: 700;
}
.badge-hard { background: #ff4a4a22; color: #ff4a4a; border: 1px solid #ff4a4a44; }
.badge-med  { background: #f0c06022; color: #f0c060; border: 1px solid #f0c06044; }
.badge-easy { background: #4af0a022; color: #4af0a0; border: 1px solid #4af0a044; }
.badge-window { background: #c8f04a22; color: #c8f04a; border: 1px solid #c8f04a44; }
.badge-cte    { background: #7c6af722; color: #7c6af7; border: 1px solid #7c6af744; }
</style>
""", unsafe_allow_html=True)

# ── GENERATE & SEED DATABASE ──────────────────────────────
@st.cache_resource
def get_db():
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    np.random.seed(42)

    # --- customers ---
    n_cust = 500
    cities = ['Bengaluru','Mumbai','Delhi','Hyderabad','Chennai','Pune']
    customers = pd.DataFrame({
        'customer_id':   [f'C{i:04d}' for i in range(1, n_cust+1)],
        'name':          [f'Customer_{i}' for i in range(1, n_cust+1)],
        'city':          np.random.choice(cities, n_cust, p=[0.30,0.20,0.18,0.15,0.10,0.07]),
        'signup_date':   pd.date_range('2022-01-01', periods=n_cust, freq='12H').strftime('%Y-%m-%d'),
        'segment':       np.random.choice(['Premium','Regular','Occasional'], n_cust, p=[0.2,0.5,0.3]),
        'age_group':     np.random.choice(['18-25','26-35','36-45','46+'], n_cust, p=[0.25,0.40,0.25,0.10]),
    })

    # --- products ---
    categories = {
        'Electronics':  [('iPhone 15',  85000), ('Samsung TV', 55000), ('Laptop',    72000),
                         ('Earbuds',    3500),  ('Smartwatch', 18000)],
        'Fashion':      [('Kurta Set',  1800),  ('Jeans',      2200),  ('Saree',     4500),
                         ('Sneakers',   5500),  ('Handbag',    3200)],
        'Home':         [('Mixer',      4500),  ('Air Cooler', 8500),  ('Bedsheet',  1200),
                         ('Pressure Cooker',2800),('Wall Shelf',1600)],
        'Beauty':       [('Moisturiser',850),   ('Lipstick',   450),   ('Perfume',   2200),
                         ('Hair Serum', 650),   ('Face Wash',  280)],
        'Grocery':      [('Rice 5kg',   420),   ('Oil 1L',     180),   ('Dal 1kg',   160),
                         ('Tea 500g',   220),   ('Coffee',     480)],
    }
    prod_rows = []
    pid = 1
    for cat, items in categories.items():
        for name, price in items:
            prod_rows.append({'product_id': f'P{pid:03d}', 'product_name': name,
                              'category': cat, 'price': price,
                              'cost': round(price * np.random.uniform(0.45, 0.65), 2)})
            pid += 1
    products = pd.DataFrame(prod_rows)

    # --- orders ---
    n_orders = 8000
    order_dates = pd.date_range('2023-01-01', '2024-12-31', periods=n_orders)
    orders = pd.DataFrame({
        'order_id':    [f'ORD{i:05d}' for i in range(1, n_orders+1)],
        'customer_id': np.random.choice(customers['customer_id'], n_orders),
        'order_date':  order_dates.strftime('%Y-%m-%d'),
        'status':      np.random.choice(['Delivered','Shipped','Cancelled','Returned'],
                                         n_orders, p=[0.72,0.15,0.08,0.05]),
        'payment':     np.random.choice(['UPI','Card','NetBanking','COD','Wallet'],
                                         n_orders, p=[0.45,0.25,0.12,0.12,0.06]),
        'city':        np.random.choice(cities, n_orders, p=[0.30,0.20,0.18,0.15,0.10,0.07]),
    })

    # --- order_items ---
    items_rows = []
    for _, order in orders.iterrows():
        n_items = np.random.choice([1,2,3,4], p=[0.50,0.30,0.15,0.05])
        prods   = products.sample(n_items)
        for _, prod in prods.iterrows():
            qty = np.random.randint(1, 4)
            discount = np.random.choice([0, 0.05, 0.10, 0.15, 0.20], p=[0.40,0.20,0.20,0.12,0.08])
            items_rows.append({
                'item_id':    f'ITEM{len(items_rows)+1:06d}',
                'order_id':   order['order_id'],
                'product_id': prod['product_id'],
                'quantity':   qty,
                'unit_price': prod['price'],
                'discount':   discount,
                'revenue':    round(prod['price'] * qty * (1 - discount), 2),
                'profit':     round((prod['price'] - prod['cost']) * qty * (1 - discount), 2),
            })
    order_items = pd.DataFrame(items_rows)

    # Write to SQLite
    customers.to_sql('customers',   conn, if_exists='replace', index=False)
    products.to_sql('products',     conn, if_exists='replace', index=False)
    orders.to_sql('orders',         conn, if_exists='replace', index=False)
    order_items.to_sql('order_items', conn, if_exists='replace', index=False)
    return conn

conn = get_db()

def run_query(sql):
    try:
        return pd.read_sql_query(sql, conn), None
    except Exception as e:
        return None, str(e)

def highlight_sql(sql):
    import re
    keywords = r'\b(SELECT|FROM|WHERE|JOIN|LEFT|RIGHT|INNER|OUTER|ON|GROUP BY|ORDER BY|HAVING|WITH|AS|CASE|WHEN|THEN|ELSE|END|DISTINCT|LIMIT|UNION|ALL|AND|OR|NOT|IN|EXISTS|BETWEEN|LIKE|IS|NULL|COUNT|SUM|AVG|MIN|MAX|RANK|ROW_NUMBER|DENSE_RANK|LAG|LEAD|OVER|PARTITION BY|NTILE|PERCENT_RANK|CUME_DIST|FIRST_VALUE|LAST_VALUE|COALESCE|CAST|ROUND|DATE|STRFTIME|BY|DESC|ASC|INSERT|UPDATE|DELETE|CREATE|TABLE|INDEX)\b'
    sql = re.sub(keywords, lambda m: f'<span class="kw">{m.group()}</span>', sql, flags=re.IGNORECASE)
    sql = re.sub(r"'[^']*'", lambda m: f'<span class="st">{m.group()}</span>', sql)
    sql = re.sub(r'\b\d+\.?\d*\b', lambda m: f'<span class="nm">{m.group()}</span>', sql)
    sql = re.sub(r'--[^\n]*', lambda m: f'<span class="cm">{m.group()}</span>', sql)
    return sql

# ── QUERIES ───────────────────────────────────────────────
QUERIES = {
    "📊 Revenue & Sales": {
        "Total Revenue by Category": {
            "difficulty": "easy",
            "tags": ["GROUP BY","SUM","ORDER BY"],
            "insight": "Electronics dominates revenue due to high ticket size. Grocery has high volume but low revenue — a classic long-tail pattern.",
            "sql": """SELECT
    p.category,
    COUNT(DISTINCT oi.order_id)       AS total_orders,
    SUM(oi.quantity)                  AS units_sold,
    ROUND(SUM(oi.revenue), 2)         AS total_revenue,
    ROUND(AVG(oi.unit_price), 2)      AS avg_price,
    ROUND(SUM(oi.profit), 2)          AS total_profit,
    ROUND(SUM(oi.profit)/SUM(oi.revenue)*100, 1) AS profit_margin_pct
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
JOIN orders o   ON oi.order_id   = o.order_id
WHERE o.status = 'Delivered'
GROUP BY p.category
ORDER BY total_revenue DESC"""
        },
        "Monthly Revenue Trend with MoM Growth": {
            "difficulty": "hard",
            "tags": ["CTE","Window Function","LAG","MoM Growth"],
            "insight": "LAG() window function calculates month-over-month growth without a self-join. Negative growth months signal seasonal dips or operational issues.",
            "sql": """WITH monthly_rev AS (
    SELECT
        STRFTIME('%Y-%m', o.order_date)   AS month,
        ROUND(SUM(oi.revenue), 2)         AS revenue,
        COUNT(DISTINCT o.order_id)        AS orders,
        COUNT(DISTINCT o.customer_id)     AS unique_customers
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.status != 'Cancelled'
    GROUP BY month
)
SELECT
    month,
    revenue,
    orders,
    unique_customers,
    LAG(revenue) OVER (ORDER BY month)    AS prev_month_revenue,
    ROUND(
        (revenue - LAG(revenue) OVER (ORDER BY month))
        / LAG(revenue) OVER (ORDER BY month) * 100, 1
    )                                     AS mom_growth_pct,
    ROUND(AVG(revenue) OVER (
        ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 2)                                 AS rolling_3m_avg
FROM monthly_rev
ORDER BY month"""
        },
        "Top 10 Products by Revenue": {
            "difficulty": "easy",
            "tags": ["JOIN","GROUP BY","LIMIT"],
            "insight": "High-value electronics products dominate top revenue despite lower unit volumes. Useful for inventory prioritisation and promotion strategy.",
            "sql": """SELECT
    p.product_name,
    p.category,
    p.price                           AS list_price,
    SUM(oi.quantity)                  AS units_sold,
    ROUND(SUM(oi.revenue), 2)         AS total_revenue,
    ROUND(SUM(oi.profit), 2)          AS total_profit,
    ROUND(AVG(oi.discount)*100, 1)    AS avg_discount_pct
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
JOIN orders o   ON oi.order_id   = o.order_id
WHERE o.status = 'Delivered'
GROUP BY p.product_id, p.product_name, p.category, p.price
ORDER BY total_revenue DESC
LIMIT 10"""
        },
        "Revenue by City and Payment Method": {
            "difficulty": "med",
            "tags": ["GROUP BY","CASE","PIVOT-style"],
            "insight": "UPI dominance in Bengaluru vs COD preference in Tier-2 cities reveals payment infrastructure gaps. Actionable for targeted payment promotions.",
            "sql": """SELECT
    o.city,
    ROUND(SUM(CASE WHEN o.payment='UPI'        THEN oi.revenue ELSE 0 END), 0) AS upi_revenue,
    ROUND(SUM(CASE WHEN o.payment='Card'       THEN oi.revenue ELSE 0 END), 0) AS card_revenue,
    ROUND(SUM(CASE WHEN o.payment='NetBanking' THEN oi.revenue ELSE 0 END), 0) AS netbanking_revenue,
    ROUND(SUM(CASE WHEN o.payment='COD'        THEN oi.revenue ELSE 0 END), 0) AS cod_revenue,
    ROUND(SUM(CASE WHEN o.payment='Wallet'     THEN oi.revenue ELSE 0 END), 0) AS wallet_revenue,
    ROUND(SUM(oi.revenue), 0)                                                   AS total_revenue
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.status = 'Delivered'
GROUP BY o.city
ORDER BY total_revenue DESC"""
        },
    },
    "👤 Customer Analytics": {
        "Customer Lifetime Value (CLV) Ranking": {
            "difficulty": "hard",
            "tags": ["Window Function","RANK","CTE","CLV"],
            "insight": "RANK() window function assigns CLV rank without losing any rows. Top 20% of customers typically drive 80% of revenue — the classic Pareto principle in action.",
            "sql": """WITH customer_metrics AS (
    SELECT
        c.customer_id,
        c.city,
        c.segment,
        COUNT(DISTINCT o.order_id)        AS total_orders,
        ROUND(SUM(oi.revenue), 2)         AS lifetime_revenue,
        ROUND(AVG(oi.revenue), 2)         AS avg_order_value,
        MIN(o.order_date)                 AS first_order,
        MAX(o.order_date)                 AS last_order,
        CAST(JULIANDAY(MAX(o.order_date)) - JULIANDAY(MIN(o.order_date)) AS INT)
                                          AS customer_lifespan_days
    FROM customers c
    JOIN orders o       ON c.customer_id = o.customer_id
    JOIN order_items oi ON o.order_id    = oi.order_id
    WHERE o.status = 'Delivered'
    GROUP BY c.customer_id, c.city, c.segment
)
SELECT
    customer_id, city, segment,
    total_orders, lifetime_revenue, avg_order_value,
    customer_lifespan_days,
    RANK()       OVER (ORDER BY lifetime_revenue DESC) AS revenue_rank,
    NTILE(4)     OVER (ORDER BY lifetime_revenue DESC) AS revenue_quartile,
    ROUND(lifetime_revenue / NULLIF(customer_lifespan_days, 0) * 30, 2) AS monthly_clv
FROM customer_metrics
ORDER BY revenue_rank
LIMIT 20"""
        },
        "RFM Segmentation with SQL": {
            "difficulty": "hard",
            "tags": ["CTE","CASE","NTILE","Window Function","RFM"],
            "insight": "Full RFM segmentation in pure SQL — no Python needed. NTILE(5) creates quintile buckets. This exact query pattern is used at Meesho and Flipkart for customer targeting.",
            "sql": """WITH rfm_base AS (
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
),
rfm_segments AS (
    SELECT *,
        (r_score + f_score + m_score) AS rfm_total,
        CASE
            WHEN r_score >= 4 AND f_score >= 4            THEN 'Champions'
            WHEN r_score >= 3 AND f_score >= 3            THEN 'Loyal Customers'
            WHEN r_score >= 4 AND f_score < 3             THEN 'Promising'
            WHEN r_score <= 2 AND (r_score+f_score+m_score) >= 8 THEN 'At Risk'
            WHEN r_score <= 2 AND f_score <= 2            THEN 'Lost'
            ELSE 'Needs Attention'
        END AS segment
    FROM rfm_scores
)
SELECT
    segment,
    COUNT(*)                          AS customers,
    ROUND(AVG(recency_days), 0)       AS avg_recency_days,
    ROUND(AVG(frequency), 1)          AS avg_orders,
    ROUND(AVG(monetary), 0)           AS avg_revenue,
    ROUND(SUM(monetary), 0)           AS total_revenue
FROM rfm_segments
GROUP BY segment
ORDER BY total_revenue DESC"""
        },
        "New vs Returning Customer Revenue Split": {
            "difficulty": "med",
            "tags": ["CTE","CASE","SUBQUERY","Cohort"],
            "insight": "Returning customers cost 5-7x less to retain than acquiring new ones. This query quantifies how much revenue is driven by loyalty vs acquisition.",
            "sql": """WITH first_orders AS (
    SELECT customer_id, MIN(order_date) AS first_order_date
    FROM orders
    GROUP BY customer_id
),
order_type AS (
    SELECT
        o.order_id,
        o.customer_id,
        o.order_date,
        CASE
            WHEN o.order_date = f.first_order_date THEN 'New Customer'
            ELSE 'Returning Customer'
        END AS customer_type
    FROM orders o
    JOIN first_orders f ON o.customer_id = f.customer_id
    WHERE o.status = 'Delivered'
)
SELECT
    ot.customer_type,
    STRFTIME('%Y-%m', ot.order_date)   AS month,
    COUNT(DISTINCT ot.order_id)        AS orders,
    COUNT(DISTINCT ot.customer_id)     AS customers,
    ROUND(SUM(oi.revenue), 2)          AS revenue,
    ROUND(AVG(oi.revenue), 2)          AS avg_order_value
FROM order_type ot
JOIN order_items oi ON ot.order_id = oi.order_id
GROUP BY ot.customer_type, month
ORDER BY month, ot.customer_type"""
        },
        "Customer Churn Detection": {
            "difficulty": "hard",
            "tags": ["CTE","DATEDIFF","Window Function","Churn"],
            "insight": "Customers with 90+ days since last order are classified as churned. This query identifies them and their last known spend — essential for win-back campaigns.",
            "sql": """WITH last_activity AS (
    SELECT
        c.customer_id,
        c.city,
        c.segment,
        MAX(o.order_date)              AS last_order_date,
        COUNT(DISTINCT o.order_id)     AS total_orders,
        ROUND(SUM(oi.revenue), 2)      AS total_revenue,
        CAST(JULIANDAY('2025-01-01') - JULIANDAY(MAX(o.order_date)) AS INT)
                                       AS days_since_last_order
    FROM customers c
    JOIN orders o       ON c.customer_id = o.customer_id
    JOIN order_items oi ON o.order_id    = oi.order_id
    WHERE o.status = 'Delivered'
    GROUP BY c.customer_id, c.city, c.segment
)
SELECT
    customer_id, city, segment,
    last_order_date, total_orders, total_revenue,
    days_since_last_order,
    CASE
        WHEN days_since_last_order > 180 THEN 'Churned'
        WHEN days_since_last_order > 90  THEN 'At Risk'
        WHEN days_since_last_order > 30  THEN 'Cooling Off'
        ELSE 'Active'
    END AS churn_status
FROM last_activity
ORDER BY days_since_last_order DESC
LIMIT 25"""
        },
    },
    "🔝 Product Intelligence": {
        "Product Performance with Running Total": {
            "difficulty": "hard",
            "tags": ["Window Function","SUM OVER","Running Total","Market Share"],
            "insight": "SUM() OVER with ORDER BY creates a running total. The cumulative revenue share shows how few products drive majority of sales — Pareto analysis in SQL.",
            "sql": """WITH product_rev AS (
    SELECT
        p.product_name,
        p.category,
        ROUND(SUM(oi.revenue), 2)   AS revenue,
        SUM(oi.quantity)            AS units_sold,
        ROUND(SUM(oi.profit), 2)    AS profit,
        ROUND(AVG(oi.discount)*100, 1) AS avg_discount
    FROM order_items oi
    JOIN products p ON oi.product_id = p.product_id
    JOIN orders o   ON oi.order_id   = o.order_id
    WHERE o.status = 'Delivered'
    GROUP BY p.product_id, p.product_name, p.category
)
SELECT
    product_name, category, revenue, units_sold, profit, avg_discount,
    RANK() OVER (ORDER BY revenue DESC)  AS revenue_rank,
    ROUND(revenue / SUM(revenue) OVER () * 100, 2) AS revenue_share_pct,
    ROUND(SUM(revenue) OVER (
        ORDER BY revenue DESC
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) / SUM(revenue) OVER () * 100, 1)  AS cumulative_revenue_pct
FROM product_rev
ORDER BY revenue DESC
LIMIT 20"""
        },
        "Category Cross-Sell Analysis": {
            "difficulty": "hard",
            "tags": ["Self JOIN","Subquery","Cross-sell"],
            "insight": "Customers buying Electronics often also buy Fashion — cross-sell opportunity. This pattern drives 'Frequently Bought Together' recommendations at Amazon/Flipkart.",
            "sql": """WITH customer_categories AS (
    SELECT DISTINCT
        o.customer_id,
        p.category
    FROM orders o
    JOIN order_items oi ON o.order_id    = oi.order_id
    JOIN products p     ON oi.product_id = p.product_id
    WHERE o.status = 'Delivered'
)
SELECT
    a.category   AS category_a,
    b.category   AS category_b,
    COUNT(DISTINCT a.customer_id) AS customers_bought_both,
    ROUND(
        COUNT(DISTINCT a.customer_id) * 100.0 /
        (SELECT COUNT(DISTINCT customer_id) FROM customer_categories WHERE category = a.category)
    , 1) AS cross_sell_rate_pct
FROM customer_categories a
JOIN customer_categories b
    ON a.customer_id = b.customer_id
    AND a.category < b.category
GROUP BY a.category, b.category
ORDER BY customers_bought_both DESC"""
        },
        "Discount Impact on Profitability": {
            "difficulty": "med",
            "tags": ["CASE","GROUP BY","Profitability"],
            "insight": "High discounts erode margins. This query buckets orders by discount tier to find the optimal discount level — where revenue is maximised without killing profit.",
            "sql": """SELECT
    CASE
        WHEN oi.discount = 0     THEN '0% — No Discount'
        WHEN oi.discount <= 0.05 THEN '1-5% — Minimal'
        WHEN oi.discount <= 0.10 THEN '6-10% — Moderate'
        WHEN oi.discount <= 0.15 THEN '11-15% — Significant'
        ELSE '16-20% — Heavy'
    END                               AS discount_bucket,
    COUNT(*)                          AS line_items,
    COUNT(DISTINCT oi.order_id)       AS orders,
    ROUND(AVG(oi.unit_price), 0)      AS avg_unit_price,
    ROUND(SUM(oi.revenue), 0)         AS total_revenue,
    ROUND(SUM(oi.profit), 0)          AS total_profit,
    ROUND(AVG(oi.profit/oi.revenue)*100, 1) AS avg_margin_pct
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
WHERE o.status = 'Delivered'
  AND oi.revenue > 0
GROUP BY discount_bucket
ORDER BY oi.discount"""
        },
    },
    "⚙️ Operational Metrics": {
        "Order Funnel & Cancellation Analysis": {
            "difficulty": "med",
            "tags": ["CASE","COUNT","Funnel","Conversion"],
            "insight": "High cancellation in specific cities or payment methods signals UX or logistics issues. COD orders typically have 2-3x higher cancellation rates.",
            "sql": """SELECT
    o.city,
    o.payment,
    COUNT(*)                          AS total_orders,
    SUM(CASE WHEN o.status='Delivered'  THEN 1 ELSE 0 END) AS delivered,
    SUM(CASE WHEN o.status='Shipped'    THEN 1 ELSE 0 END) AS in_transit,
    SUM(CASE WHEN o.status='Cancelled'  THEN 1 ELSE 0 END) AS cancelled,
    SUM(CASE WHEN o.status='Returned'   THEN 1 ELSE 0 END) AS returned,
    ROUND(SUM(CASE WHEN o.status='Cancelled' THEN 1.0 ELSE 0 END)
          / COUNT(*) * 100, 1)        AS cancellation_rate_pct,
    ROUND(SUM(CASE WHEN o.status='Returned'  THEN 1.0 ELSE 0 END)
          / COUNT(*) * 100, 1)        AS return_rate_pct,
    ROUND(SUM(CASE WHEN o.status='Delivered' THEN 1.0 ELSE 0 END)
          / COUNT(*) * 100, 1)        AS delivery_success_pct
FROM orders o
GROUP BY o.city, o.payment
ORDER BY total_orders DESC
LIMIT 20"""
        },
        "Peak Sales Hours Analysis": {
            "difficulty": "easy",
            "tags": ["STRFTIME","GROUP BY","Time Analysis"],
            "insight": "Most e-commerce sales happen during lunch (12-2pm) and evening (8-10pm) — this drives flash sale timing decisions and staffing for customer support.",
            "sql": """SELECT
    STRFTIME('%Y', order_date)       AS year,
    STRFTIME('%m', order_date)       AS month,
    CASE CAST(STRFTIME('%m', order_date) AS INT)
        WHEN 1 THEN 'January'   WHEN 2 THEN 'February' WHEN 3 THEN 'March'
        WHEN 4 THEN 'April'     WHEN 5 THEN 'May'       WHEN 6 THEN 'June'
        WHEN 7 THEN 'July'      WHEN 8 THEN 'August'    WHEN 9 THEN 'September'
        WHEN 10 THEN 'October'  WHEN 11 THEN 'November' WHEN 12 THEN 'December'
    END                              AS month_name,
    COUNT(*)                         AS total_orders,
    SUM(CASE WHEN status='Delivered' THEN 1 ELSE 0 END) AS delivered_orders,
    ROUND(COUNT(*) * 1.0 / SUM(COUNT(*)) OVER () * 100, 2) AS pct_of_annual_orders
FROM orders
GROUP BY year, month
ORDER BY year, month"""
        },
        "Cohort Retention Query": {
            "difficulty": "hard",
            "tags": ["CTE","Cohort","Retention","Window Function"],
            "insight": "Cohort analysis is the gold standard for measuring product stickiness. This SQL pattern is asked in DS interviews at Swiggy, Razorpay and Flipkart.",
            "sql": """WITH cohorts AS (
    SELECT
        customer_id,
        STRFTIME('%Y-%m', MIN(order_date)) AS cohort_month
    FROM orders
    WHERE status != 'Cancelled'
    GROUP BY customer_id
),
customer_activity AS (
    SELECT
        o.customer_id,
        c.cohort_month,
        STRFTIME('%Y-%m', o.order_date) AS activity_month,
        CAST(
            (CAST(STRFTIME('%Y', o.order_date) AS INT) - CAST(STRFTIME('%Y', c.cohort_month||'-01') AS INT)) * 12 +
            (CAST(STRFTIME('%m', o.order_date) AS INT) - CAST(STRFTIME('%m', c.cohort_month||'-01') AS INT))
        AS INT) AS months_since_join
    FROM orders o
    JOIN cohorts c ON o.customer_id = c.customer_id
    WHERE o.status != 'Cancelled'
)
SELECT
    cohort_month,
    months_since_join,
    COUNT(DISTINCT customer_id) AS active_customers
FROM customer_activity
WHERE months_since_join BETWEEN 0 AND 6
GROUP BY cohort_month, months_since_join
ORDER BY cohort_month, months_since_join
LIMIT 42"""
        },
    },
    "🏆 Advanced SQL": {
        "Window Functions Showcase": {
            "difficulty": "hard",
            "tags": ["ROW_NUMBER","RANK","DENSE_RANK","LEAD","LAG","NTILE"],
            "insight": "All major window functions in one query — ideal to bookmark. ROW_NUMBER vs RANK vs DENSE_RANK handle ties differently. LEAD/LAG are essential for time-series analysis.",
            "sql": """WITH monthly_customer AS (
    SELECT
        o.customer_id,
        STRFTIME('%Y-%m', o.order_date)  AS month,
        ROUND(SUM(oi.revenue), 2)        AS monthly_spend
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.status = 'Delivered'
    GROUP BY o.customer_id, month
)
SELECT
    customer_id,
    month,
    monthly_spend,
    -- Ranking functions
    ROW_NUMBER() OVER (PARTITION BY month ORDER BY monthly_spend DESC) AS row_num,
    RANK()       OVER (PARTITION BY month ORDER BY monthly_spend DESC) AS rank_with_gaps,
    DENSE_RANK() OVER (PARTITION BY month ORDER BY monthly_spend DESC) AS dense_rank_no_gaps,
    NTILE(4)     OVER (PARTITION BY month ORDER BY monthly_spend DESC) AS spend_quartile,
    -- Lead & Lag
    LAG(monthly_spend)  OVER (PARTITION BY customer_id ORDER BY month) AS prev_month_spend,
    LEAD(monthly_spend) OVER (PARTITION BY customer_id ORDER BY month) AS next_month_spend,
    -- Running aggregates
    ROUND(SUM(monthly_spend)  OVER (PARTITION BY customer_id ORDER BY month), 2) AS cumulative_spend,
    ROUND(AVG(monthly_spend)  OVER (PARTITION BY customer_id ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS rolling_3m_avg
FROM monthly_customer
WHERE customer_id IN ('C0001','C0002','C0003','C0010','C0020')
ORDER BY customer_id, month"""
        },
        "Recursive CTE — Customer Journey": {
            "difficulty": "hard",
            "tags": ["Recursive CTE","Hierarchy","WITH RECURSIVE"],
            "insight": "Recursive CTEs solve hierarchical problems. This example simulates a customer referral chain — essential for multi-level marketing or referral program analysis.",
            "sql": """-- Simulating order sequence journey per customer
WITH RECURSIVE order_sequence AS (
    -- Base: first order per customer
    SELECT
        o.customer_id,
        o.order_id,
        o.order_date,
        ROUND(SUM(oi.revenue), 2) AS order_value,
        1 AS order_number
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.status = 'Delivered'
      AND o.order_date = (
          SELECT MIN(o2.order_date) FROM orders o2
          WHERE o2.customer_id = o.customer_id AND o2.status = 'Delivered'
      )
    GROUP BY o.customer_id, o.order_id, o.order_date

    UNION ALL

    -- Recursive: next order
    SELECT
        o.customer_id,
        o.order_id,
        o.order_date,
        ROUND(SUM(oi.revenue), 2),
        os.order_number + 1
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN order_sequence os ON o.customer_id = os.customer_id
    WHERE o.order_date > os.order_date
      AND o.status = 'Delivered'
      AND os.order_number < 5
    GROUP BY o.customer_id, o.order_id, o.order_date
)
SELECT
    order_number,
    COUNT(DISTINCT customer_id) AS customers,
    ROUND(AVG(order_value), 2)  AS avg_order_value,
    ROUND(SUM(order_value), 2)  AS total_revenue
FROM order_sequence
GROUP BY order_number
ORDER BY order_number"""
        },
    }
}

# ── UI ────────────────────────────────────────────────────
st.title("🛍️ E-Commerce SQL Analytics")
st.markdown("##### 20+ real SQL queries on a live database | Window Functions · CTEs · Aggregations · Cohort Analysis")
st.markdown("*Built by [Prajwal Markal Puttaswamy](https://prajwalmarkalputtaswamyportfolio.netlify.app/)*")
st.divider()

# Schema overview
with st.expander("📐 Database Schema — click to expand", expanded=False):
    sc1, sc2, sc3, sc4 = st.columns(4)
    sc1.markdown("**customers**\n- customer_id (PK)\n- name\n- city\n- signup_date\n- segment\n- age_group")
    sc2.markdown("**products**\n- product_id (PK)\n- product_name\n- category\n- price\n- cost")
    sc3.markdown("**orders**\n- order_id (PK)\n- customer_id (FK)\n- order_date\n- status\n- payment\n- city")
    sc4.markdown("**order_items**\n- item_id (PK)\n- order_id (FK)\n- product_id (FK)\n- quantity\n- unit_price\n- discount\n- revenue\n- profit")
    st.markdown("**Dataset:** 500 customers · 25 products · 8,000 orders · ~14,000 order items · 2023–2024")

st.divider()

# Main layout
left, right = st.columns([1, 2])

with left:
    st.markdown("### Query Library")
    category = st.selectbox("Category", list(QUERIES.keys()))
    query_name = st.selectbox("Query", list(QUERIES[category].keys()))
    q = QUERIES[category][query_name]

    diff_color = {'easy':'badge-easy','med':'badge-med','hard':'badge-hard'}[q['difficulty']]
    badges = f'<span class="badge {diff_color}">{q["difficulty"]}</span>'
    for tag in q['tags'][:3]:
        tag_class = 'badge-window' if tag in ['Window Function','LAG','LEAD','RANK','ROW_NUMBER','NTILE','DENSE_RANK','SUM OVER'] else 'badge-cte' if 'CTE' in tag else 'badge-easy'
        badges += f'<span class="badge {tag_class}">{tag}</span>'
    st.markdown(badges, unsafe_allow_html=True)

    st.markdown(f"""<div class="insight-box">💡 <b>Business Insight</b><br/>{q['insight']}</div>""",
                unsafe_allow_html=True)

    st.markdown("### Try Your Own SQL")
    custom_sql = st.text_area("Write any SQL query:", height=120,
        placeholder="SELECT * FROM customers LIMIT 5",
        help="Tables: customers, products, orders, order_items")
    run_custom = st.button("▶ Run Query", use_container_width=True)

    st.markdown("**Quick reference:**")
    st.code("SELECT * FROM customers LIMIT 5\nSELECT * FROM orders LIMIT 5\nSELECT * FROM products\nSELECT * FROM order_items LIMIT 5", language='sql')

with right:
    st.markdown(f"### {query_name}")

    # Highlighted SQL
    st.markdown(f'<div class="sql-box">{highlight_sql(q["sql"])}</div>', unsafe_allow_html=True)

    # Run query
    df_result, err = run_query(q['sql'])

    if err:
        st.error(f"Query error: {err}")
    elif df_result is not None:
        st.markdown(f"**{len(df_result):,} rows returned**")
        st.dataframe(df_result, use_container_width=True, hide_index=True)

        # Auto-visualise
        if len(df_result) > 1 and len(df_result.columns) >= 2:
            num_cols = df_result.select_dtypes(include='number').columns.tolist()
            cat_cols = df_result.select_dtypes(include='object').columns.tolist()

            if num_cols and cat_cols:
                try:
                    x_col = cat_cols[0]
                    y_col = num_cols[0]
                    if len(df_result) <= 30:
                        fig = px.bar(df_result, x=x_col, y=y_col,
                                     color=y_col, color_continuous_scale=['#2a2a3a','#7c6af7','#c8f04a'],
                                     title=f"{y_col} by {x_col}")
                    else:
                        fig = px.line(df_result, x=df_result.columns[0], y=y_col,
                                      title=f"{y_col} over {df_result.columns[0]}",
                                      markers=True)
                        fig.update_traces(line_color='#c8f04a')
                    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)',
                                      plot_bgcolor='rgba(0,0,0,0.05)',
                                      coloraxis_showscale=False)
                    st.plotly_chart(fig, use_container_width=True)
                except:
                    pass

    # Custom query result
    if run_custom and custom_sql.strip():
        st.divider()
        st.markdown("### Custom Query Result")
        df_custom, err_custom = run_query(custom_sql)
        if err_custom:
            st.error(f"Error: {err_custom}")
        elif df_custom is not None:
            st.markdown(f"**{len(df_custom):,} rows returned**")
            st.dataframe(df_custom, use_container_width=True, hide_index=True)

st.divider()
st.caption("E-Commerce SQL Analytics | Built by Prajwal Markal Puttaswamy | "
           "[Portfolio](https://prajwalmarkalputtaswamyportfolio.netlify.app/) | "
           "[GitHub](https://github.com/prajwal467262)")
