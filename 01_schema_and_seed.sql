-- ============================================================
-- E-Commerce SQL Analytics
-- Author: Prajwal Markal Puttaswamy
-- Schema: customers, products, orders, order_items
-- ============================================================

CREATE TABLE IF NOT EXISTS customers (
    customer_id   TEXT PRIMARY KEY,
    name          TEXT,
    city          TEXT,
    signup_date   DATE,
    segment       TEXT CHECK(segment IN ('Premium','Regular','Occasional')),
    age_group     TEXT
);

CREATE TABLE IF NOT EXISTS products (
    product_id    TEXT PRIMARY KEY,
    product_name  TEXT,
    category      TEXT,
    price         DECIMAL(10,2),
    cost          DECIMAL(10,2)
);

CREATE TABLE IF NOT EXISTS orders (
    order_id      TEXT PRIMARY KEY,
    customer_id   TEXT REFERENCES customers(customer_id),
    order_date    DATE,
    status        TEXT CHECK(status IN ('Delivered','Shipped','Cancelled','Returned')),
    payment       TEXT,
    city          TEXT
);

CREATE TABLE IF NOT EXISTS order_items (
    item_id       TEXT PRIMARY KEY,
    order_id      TEXT REFERENCES orders(order_id),
    product_id    TEXT REFERENCES products(product_id),
    quantity      INT,
    unit_price    DECIMAL(10,2),
    discount      DECIMAL(4,2),
    revenue       DECIMAL(10,2),
    profit        DECIMAL(10,2)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_orders_customer   ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_date       ON orders(order_date);
CREATE INDEX IF NOT EXISTS idx_items_order       ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_items_product     ON order_items(product_id);
