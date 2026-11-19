BEGIN;

-- Stop if the script is opened in another database.
DO $$
BEGIN
    IF current_database() <> 'production_planning' THEN
        RAISE EXCEPTION 'Open production_planning before running this script';
    END IF;
END;
$$;

SET LOCAL ROLE planner_user;
SET LOCAL search_path TO public;

CREATE TABLE resources (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN ('Сотрудник', 'Станок')),
    r_type TEXT NOT NULL
);

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE operations (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    seq INTEGER NOT NULL CHECK (seq > 0),
    dur INTEGER NOT NULL CHECK (dur > 0),
    worker_type TEXT NOT NULL,
    machine_type TEXT,
    FOREIGN KEY (product_id) REFERENCES products (id),
    UNIQUE (product_id, seq)
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL,
    start_after TIMESTAMP NOT NULL,
    deadline TIMESTAMP NOT NULL,
    penalty NUMERIC NOT NULL DEFAULT 100 CHECK (penalty >= 0),
    FOREIGN KEY (product_id) REFERENCES products (id),
    CHECK (deadline >= start_after)
);

CREATE TABLE schedule (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL,
    operation_id INTEGER NOT NULL,
    worker_id INTEGER NOT NULL,
    machine_id INTEGER,
    start_at TIMESTAMP NOT NULL,
    end_at TIMESTAMP NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders (id),
    FOREIGN KEY (operation_id) REFERENCES operations (id),
    FOREIGN KEY (worker_id) REFERENCES resources (id),
    FOREIGN KEY (machine_id) REFERENCES resources (id),
    CHECK (end_at > start_at)
);

COMMIT;
