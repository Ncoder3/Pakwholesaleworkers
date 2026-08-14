-- Schema for PostgreSQL on Railway / Supabase

CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,

    product_code VARCHAR(50) UNIQUE NOT NULL,
    category VARCHAR(120) NOT NULL DEFAULT 'Miscellaneous',
    product_name VARCHAR(150) NOT NULL,

    pack_unit_type VARCHAR(100),
    pieces_per_pack INTEGER NOT NULL DEFAULT 0,

    wholesale_price_per_pack NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    price_per_piece NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    suggested_retail_price_per_piece NUMERIC(10, 2) NOT NULL DEFAULT 0.00,

    stock_available_packs INTEGER NOT NULL DEFAULT 0,

    notes TEXT,
    image_file VARCHAR(255),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(30) UNIQUE NOT NULL,
    customer_name VARCHAR(120) NOT NULL,
    customer_phone VARCHAR(20) NOT NULL,
    customer_city VARCHAR(80),
    customer_address TEXT,
    customer_notes TEXT,
    total_amount NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    status VARCHAR(30) NOT NULL DEFAULT 'Pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(30) REFERENCES orders(order_id) ON DELETE CASCADE,
    product_code VARCHAR(50) NOT NULL,
    product_name VARCHAR(150) NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    unit_price NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    subtotal NUMERIC(12, 2) NOT NULL DEFAULT 0.00
);

CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    customer_id VARCHAR(30) UNIQUE NOT NULL,
    name VARCHAR(120) NOT NULL,
    store_name VARCHAR(120),
    phone VARCHAR(20) UNIQUE NOT NULL,
    address TEXT,
    tier VARCHAR(20) DEFAULT 'Standard',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS deleted_orders (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(30) NOT NULL,
    customer_name VARCHAR(120),
    customer_phone VARCHAR(20),
    customer_city VARCHAR(80),
    customer_address TEXT,
    total_amount NUMERIC(12, 2),
    source VARCHAR(20),
    order_data JSONB,
    deleted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);