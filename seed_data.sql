BEGIN;
SET LOCAL ROLE planner_user;
SET LOCAL search_path TO public;

DO $$
BEGIN
    IF current_database() <> 'production_planning' THEN
        RAISE EXCEPTION 'Open production_planning first';
    END IF;
END;
$$;

-- Этот набор предназначен для первого заполнения пустой базы.
LOCK TABLE resources, products, operations, orders, schedule IN SHARE ROW EXCLUSIVE MODE;
DO $$
BEGIN
    IF EXISTS (SELECT FROM resources) OR EXISTS (SELECT FROM products) THEN
        RAISE EXCEPTION 'Данные уже есть. Повторная загрузка отменена.';
    END IF;
END;
$$;

INSERT INTO resources (name, category, r_type) VALUES
    ('Иванов', 'Сотрудник', 'Токарь'),
    ('Петров', 'Сотрудник', 'Фрезеровщик'),
    ('Смирнов', 'Сотрудник', 'Слесарь'),
    ('Т-01', 'Станок', 'Токарный'),
    ('Ф-01', 'Станок', 'Фрезерный');

INSERT INTO products (name) VALUES ('Вал'), ('Фланец'), ('Кронштейн');

INSERT INTO operations (product_id, seq, name, dur, worker_type, machine_type)
SELECT p.id, v.seq, v.name, v.dur, v.worker_type, v.machine_type
FROM (VALUES
    ('Вал', 1, 'Точение заготовки', 40, 'Токарь', 'Токарный'),
    ('Вал', 2, 'Фрезерование паза', 25, 'Фрезеровщик', 'Фрезерный'),
    ('Вал', 3, 'Зачистка кромок', 10, 'Слесарь', NULL),
    ('Фланец', 1, 'Точение торца', 30, 'Токарь', 'Токарный'),
    ('Фланец', 2, 'Расточка отверстия', 20, 'Токарь', 'Токарный'),
    ('Фланец', 3, 'Контроль размеров', 10, 'Слесарь', NULL),
    ('Кронштейн', 1, 'Разметка', 15, 'Слесарь', NULL),
    ('Кронштейн', 2, 'Фрезерование плоскости', 35, 'Фрезеровщик', 'Фрезерный'),
    ('Кронштейн', 3, 'Снятие заусенцев', 10, 'Слесарь', NULL)
) AS v(product, seq, name, dur, worker_type, machine_type)
JOIN products p ON p.name = v.product;

INSERT INTO orders (product_id, start_after, deadline)
SELECT p.id, TIMESTAMP '2026-11-23 08:00', TIMESTAMP '2026-11-23 16:00' + v.days * INTERVAL '1 day'
FROM (VALUES ('Вал', 0), ('Фланец', 1), ('Кронштейн', 2), ('Вал', 3),
             ('Фланец', 4), ('Кронштейн', 5), ('Вал', 6), ('Фланец', 7),
             ('Кронштейн', 8), ('Вал', 9)) AS v(product, days)
JOIN products p ON p.name = v.product;

-- Назначаем первую операцию самого срочного заказа на время начала заказа.
INSERT INTO schedule (order_id, operation_id, worker_id, machine_id, start_at, end_at)
SELECT o.id, op.id, w.id, m.id, o.start_after, o.start_after + op.dur * INTERVAL '1 minute'
FROM orders o
JOIN operations op ON op.product_id = o.product_id AND op.seq = 1
JOIN resources w ON w.category = 'Сотрудник' AND w.r_type = op.worker_type
LEFT JOIN resources m ON m.category = 'Станок' AND m.r_type = op.machine_type
ORDER BY o.deadline
LIMIT 1;

COMMIT;

SELECT 'resources' AS "Таблица", COUNT(*) AS "Количество записей" FROM public.resources
UNION ALL SELECT 'products', COUNT(*) FROM public.products
UNION ALL SELECT 'operations', COUNT(*) FROM public.operations
UNION ALL SELECT 'orders', COUNT(*) FROM public.orders
UNION ALL SELECT 'schedule', COUNT(*) FROM public.schedule;
