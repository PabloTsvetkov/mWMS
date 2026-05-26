import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'warehouse.db')

def line():
    print('-' * 60)

def run():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Товары
    line()
    print('ТОВАРЫ:')
    line()
    rows = conn.execute('SELECT id, sku, name, size, color FROM products').fetchall()
    for r in rows:
        print(f"  [{r['id']}] {r['sku']}  |  {r['name']}  |  {r['size']}  |  {r['color']}")

    # Склады
    line()
    print('СКЛАДЫ:')
    line()
    rows = conn.execute('SELECT id, name, address FROM warehouses').fetchall()
    for r in rows:
        print(f"  [{r['id']}] {r['name']}  —  {r['address']}")

    # Остатки
    line()
    print('ОСТАТКИ (товар / склад / статус / кол-во):')
    line()
    rows = conn.execute('''
        SELECT
            p.name AS product,
            p.sku AS sku,
            w.name AS warehouse,
            s.status AS status,
            s.quantity AS qty
        FROM stock s
        JOIN products p ON s.product_id = p.id
        JOIN warehouses w ON s.warehouse_id = w.id
        ORDER BY p.name, w.name, s.status
    ''').fetchall()
    for r in rows:
        print(f"  {r['product']:<25} | {r['warehouse']:<12} | {r['status']:<10} | {r['qty']} шт.")

    # Отгрузки
    line()
    print('ОТГРУЗКИ:')
    line()
    rows = conn.execute('''
        SELECT
            sh.shipment_number AS num,
            sh.shipment_date AS date,
            w.name AS warehouse,
            sh.destination AS dest,
            sh.status AS status
        FROM shipments sh
        JOIN warehouses w ON sh.warehouse_id = w.id
        ORDER BY sh.shipment_date
    ''').fetchall()
    for r in rows:
        print(f"  {r['num']}  {r['date']}  | {r['warehouse']:<12} -> {r['dest']:<35} | {r['status']}")

    line()
    conn.close()

if __name__ == '__main__':
    run()
