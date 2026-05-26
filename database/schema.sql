-- Удаляем таблицы если существуют
DROP TABLE IF EXISTS shipment_items;
DROP TABLE IF EXISTS shipments;
DROP TABLE IF EXISTS stock;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS warehouses;

--  Товары
CREATE TABLE products (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    sku        TEXT    NOT NULL UNIQUE,   -- артикул
    name       TEXT    NOT NULL,
    size       TEXT,                      -- размер: S, M, L, XL и т.п.
    color      TEXT,                      -- цвет
    image_url  TEXT,                      -- ссылка на картинку (заполним потом)
    created_at TEXT    DEFAULT (date('now'))
);


--  Склады

CREATE TABLE warehouses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    address     TEXT,
    description TEXT
);


--  Остатки: сколько какого товара на каком складе и в каком состоянии
--
--  Статусы:
--    incoming  — товар едет / ещё не принят
--    in_stock  — товар принят, лежит на складе
--    packing   — товар снят со склада, идёт упаковка
--
--  UNIQUE(product_id, warehouse_id, status) гарантирует, что для
--  одной комбинации (товар, склад, статус) всегда ровно одна строка.
--  При добавлении дублирующей записи количество суммируется (upsert).

CREATE TABLE stock (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id   INTEGER NOT NULL REFERENCES products(id),
    warehouse_id INTEGER NOT NULL REFERENCES warehouses(id),
    status       TEXT    NOT NULL CHECK(status IN ('incoming', 'in_stock', 'packing')),
    quantity     INTEGER NOT NULL DEFAULT 0 CHECK(quantity >= 0),
    updated_at   TEXT    DEFAULT (datetime('now')),
    UNIQUE(product_id, warehouse_id, status)
);


--  Отгрузки
--
--  Статусы отгрузки:
--    confirmed  — подтверждена, товар уже списан с остатков
--    in_transit — отправлена, в пути
--    delivered  — доставлена, получатель принял товар
--    archived   — в архиве, не показывается по умолчанию

CREATE TABLE shipments (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    shipment_number  TEXT NOT NULL UNIQUE,
    shipment_date    TEXT NOT NULL DEFAULT (date('now')),
    warehouse_id     INTEGER NOT NULL REFERENCES warehouses(id),
    destination      TEXT NOT NULL,
    status           TEXT NOT NULL DEFAULT 'confirmed'
                         CHECK(status IN ('confirmed', 'in_transit', 'delivered', 'archived')),
    comment          TEXT
);


--  Состав отгрузки: какие товары и в каком количестве

CREATE TABLE shipment_items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    shipment_id INTEGER NOT NULL REFERENCES shipments(id),
    product_id  INTEGER NOT NULL REFERENCES products(id),
    quantity    INTEGER NOT NULL CHECK(quantity > 0)
);
