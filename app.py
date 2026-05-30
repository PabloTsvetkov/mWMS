import sqlite3
import os
from datetime import date
from flask import Flask, g, render_template, request, redirect, url_for, flash, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'wms-secret')

DB_PATH = os.environ.get(
    'DB_PATH',
    os.path.join(os.path.dirname(__file__), 'warehouse.db'),
)


# База данных

def get_db():
    if 'db' not in g:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        g.db = conn
    return g.db


@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()


# Маршруты

@app.route('/')
def index():
    return redirect(url_for('products'))


@app.route('/products')
def products():
    db = get_db()
    rows = db.execute('SELECT id, sku, name, size, color FROM products ORDER BY name').fetchall()
    return render_template('products.html', products=rows, form_data=None)


@app.route('/products/add', methods=['POST'])
def product_add():
    sku = request.form['sku'].strip()
    name = request.form['name'].strip()
    size = request.form['size'].strip()
    color = request.form['color'].strip()

    if not sku or not name:
        flash('Артикул и название обязательны', 'error')
        return redirect(url_for('products'))

    db = get_db()
    try:
        db.execute(
            'INSERT INTO products (sku, name, size, color) VALUES (?, ?, ?, ?)',
            (sku, name, size or None, color or None)
        )
        db.commit()
        flash('Товар добавлен', 'success')
        return redirect(url_for('products'))
    except sqlite3.IntegrityError:
        flash(f'Товар с артикулом «{sku}» уже существует', 'error')
        rows = db.execute(
            'SELECT id, sku, name, size, color FROM products ORDER BY name'
        ).fetchall()
        return render_template(
            'products.html',
            products=rows,
            form_data={'sku': sku, 'name': name, 'size': size, 'color': color}
        )


@app.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
def product_edit(product_id):
    db = get_db()

    if request.method == 'POST':
        sku = request.form['sku'].strip()
        name = request.form['name'].strip()
        size = request.form['size'].strip()
        color = request.form['color'].strip()

        if not sku or not name:
            flash('Артикул и название обязательны', 'error')
            product = db.execute('SELECT * FROM products WHERE id=?', (product_id,)).fetchone()
            return render_template('product_edit.html', product=product)

        try:
            db.execute(
                'UPDATE products SET sku=?, name=?, size=?, color=? WHERE id=?',
                (sku, name, size or None, color or None, product_id)
            )
            db.commit()
            flash('Товар обновлен', 'success')
            return redirect(url_for('products'))
        except sqlite3.IntegrityError:
            flash(f'Товар с артикулом «{sku}» уже существует', 'error')
            product = db.execute('SELECT * FROM products WHERE id=?', (product_id,)).fetchone()
            return render_template('product_edit.html', product=product)

    product = db.execute('SELECT * FROM products WHERE id=?', (product_id,)).fetchone()
    return render_template('product_edit.html', product=product)


@app.route('/products/<int:product_id>/delete', methods=['POST'])
def product_delete(product_id):
    db = get_db()
    db.execute('DELETE FROM products WHERE id=?', (product_id,))
    db.commit()
    flash('Товар удален', 'success')
    return redirect(url_for('products'))


@app.route('/warehouses')
def warehouses():
    db = get_db()
    rows = db.execute('SELECT id, name, address, description FROM warehouses ORDER BY name').fetchall()
    return render_template('warehouses.html', warehouses=rows)


@app.route('/warehouses/add', methods=['POST'])
def warehouse_add():
    name = request.form['name'].strip()
    address = request.form['address'].strip()
    description = request.form['description'].strip()

    db = get_db()
    db.execute(
        'INSERT INTO warehouses (name, address, description) VALUES (?, ?, ?)',
        (name, address or None, description or None)
    )
    db.commit()
    flash('Склад добавлен', 'success')
    return redirect(url_for('warehouses'))


@app.route('/warehouses/<int:warehouse_id>/edit', methods=['GET', 'POST'])
def warehouse_edit(warehouse_id):
    db = get_db()

    if request.method == 'POST':
        name = request.form['name'].strip()
        address = request.form['address'].strip()
        description = request.form['description'].strip()

        db.execute(
            'UPDATE warehouses SET name=?, address=?, description=? WHERE id=?',
            (name, address or None, description or None, warehouse_id)
        )
        db.commit()
        flash('Склад обновлен', 'success')
        return redirect(url_for('warehouses'))

    warehouse = db.execute('SELECT * FROM warehouses WHERE id=?', (warehouse_id,)).fetchone()
    return render_template('warehouse_edit.html', warehouse=warehouse)


@app.route('/warehouses/<int:warehouse_id>/delete', methods=['POST'])
def warehouse_delete(warehouse_id):
    db = get_db()
    db.execute('DELETE FROM warehouses WHERE id=?', (warehouse_id,))
    db.commit()
    flash('Склад удален', 'success')
    return redirect(url_for('warehouses'))


# Остатки

@app.route('/stock')
def stock():
    db = get_db()
    query = '''
        SELECT
            s.id,
            p.name AS product,
            p.sku,
            w.name AS warehouse,
            s.status,
            s.quantity
        FROM stock s
        JOIN products p ON s.product_id = p.id
        JOIN warehouses w ON s.warehouse_id = w.id
        ORDER BY p.name, w.name
    '''
    rows = db.execute(query).fetchall()
    products_list = [
        dict(r) for r in db.execute(
            'SELECT id, name, sku FROM products ORDER BY name'
        ).fetchall()
    ]
    warehouses_list = [
        dict(r) for r in db.execute(
            'SELECT id, name FROM warehouses ORDER BY name'
        ).fetchall()
    ]
    return render_template(
        'stock.html',
        stock=rows,
        products=products_list,
        warehouses=warehouses_list
    )


@app.route('/stock/add', methods=['POST'])
def stock_add():
    product_id = request.form['product_id']
    warehouse_id = request.form['warehouse_id']
    status = request.form['status']

    try:
        quantity = int(request.form['quantity'])
        if quantity < 0:
            raise ValueError
    except (ValueError, TypeError):
        flash('Количество должно быть целым числом >= 0', 'error')
        return redirect(url_for('stock'))

    if not product_id or not warehouse_id:
        flash('Выберите товар и склад', 'error')
        return redirect(url_for('stock'))

    db = get_db()

    # если такая запись уже есть, увеличиваем количество
    existing = db.execute(
        'SELECT id FROM stock WHERE product_id=? AND warehouse_id=? AND status=?',
        (product_id, warehouse_id, status)
    ).fetchone()

    if existing:
        db.execute(
            'UPDATE stock SET quantity = quantity + ?, updated_at = datetime("now") WHERE id=?',
            (quantity, existing['id'])
        )
        flash('Количество обновлено (запись объединена с существующей)', 'success')
    else:
        db.execute(
            'INSERT INTO stock (product_id, warehouse_id, status, quantity) VALUES (?, ?, ?, ?)',
            (product_id, warehouse_id, status, quantity)
        )
        flash('Запись добавлена', 'success')

    db.commit()
    return redirect(url_for('stock'))


@app.route('/stock/<int:stock_id>/edit', methods=['GET', 'POST'])
def stock_edit(stock_id):
    db = get_db()

    if request.method == 'POST':
        status = request.form['status']

        try:
            quantity = int(request.form['quantity'])
            if quantity < 0:
                raise ValueError
        except (ValueError, TypeError):
            flash('Количество должно быть целым числом ≥ 0', 'error')
            query = '''
                SELECT s.id, s.status, s.quantity,
                       p.name AS product, p.sku,
                       w.name AS warehouse
                FROM stock s
                JOIN products p ON s.product_id = p.id
                JOIN warehouses w ON s.warehouse_id = w.id
                WHERE s.id = ?
            '''
            row = db.execute(query, (stock_id,)).fetchone()
            return render_template('stock_edit.html', row=row)

        current = db.execute(
            'SELECT id, product_id, warehouse_id, status FROM stock WHERE id=?',
            (stock_id,)
        ).fetchone()

        if not current:
            flash('Запись не найдена', 'error')
            return redirect(url_for('stock'))

        target = None
        if current['status'] != status:
            target = db.execute(
                'SELECT id, quantity FROM stock '
                'WHERE product_id=? AND warehouse_id=? AND status=? AND id!=?',
                (current['product_id'], current['warehouse_id'], status, stock_id)
            ).fetchone()

        if target:
            db.execute(
                'UPDATE stock SET quantity = quantity + ?, updated_at = datetime("now") WHERE id=?',
                (quantity, target['id'])
            )
            db.execute('DELETE FROM stock WHERE id=?', (stock_id,))
            flash('Остаток объединен с существующей записью', 'success')
        else:
            db.execute(
                'UPDATE stock SET status=?, quantity=?, updated_at=datetime("now") WHERE id=?',
                (status, quantity, stock_id)
            )
            flash('Остаток обновлен', 'success')

        db.commit()
        return redirect(url_for('stock'))

    query = '''
        SELECT s.id, s.status, s.quantity,
               p.name AS product, p.sku,
               w.name AS warehouse
        FROM stock s
        JOIN products p ON s.product_id = p.id
        JOIN warehouses w ON s.warehouse_id = w.id
        WHERE s.id = ?
    '''
    row = db.execute(query, (stock_id,)).fetchone()
    return render_template('stock_edit.html', row=row)


@app.route('/stock/<int:stock_id>/delete', methods=['POST'])
def stock_delete(stock_id):
    db = get_db()
    db.execute('DELETE FROM stock WHERE id=?', (stock_id,))
    db.commit()
    flash('Запись удалена', 'success')
    return redirect(url_for('stock'))


# Отгрузки

@app.route('/shipments')
def shipments():
    db = get_db()
    query = '''
        SELECT
            sh.id,
            sh.shipment_number AS number,
            sh.shipment_date AS date,
            w.name AS warehouse,
            sh.destination,
            sh.status
        FROM shipments sh
        JOIN warehouses w ON sh.warehouse_id = w.id
        ORDER BY sh.shipment_date DESC
    '''
    rows = db.execute(query).fetchall()
    return render_template('shipments.html', shipments=rows)


@app.route('/shipments/new', methods=['GET', 'POST'])
def shipment_new():
    db = get_db()

    def _render_shipment_form(form_data=None, form_items=None, error=None):
        if error:
            flash(error, 'error')

        products_list = db.execute(
            'SELECT id, name, sku FROM products ORDER BY name'
        ).fetchall()
        warehouses_list = db.execute(
            'SELECT id, name FROM warehouses ORDER BY name'
        ).fetchall()
        count = db.execute('SELECT COUNT(*) AS c FROM shipments').fetchone()['c']
        next_number = f'SHP-{count + 1:03d}'

        if form_data is None:
            form_data = {
                'shipment_number': next_number,
                'shipment_date': date.today().isoformat(),
                'warehouse_id': '',
                'destination': '',
                'comment': ''
            }

        if not form_items:
            form_items = [{'product_id': '', 'quantity': ''}]

        return render_template(
            'shipment_new.html',
            products=products_list,
            warehouses=warehouses_list,
            next_number=form_data.get('shipment_number') or next_number,
            today=form_data.get('shipment_date') or date.today().isoformat(),
            form_data=form_data,
            form_items=form_items
        )

    if request.method == 'POST':
        number = request.form['shipment_number'].strip()
        shipment_date = request.form['shipment_date']
        warehouse_id = request.form['warehouse_id']
        destination = request.form['destination'].strip()
        comment = request.form['comment'].strip()

        form_data = {
            'shipment_number': number,
            'shipment_date': shipment_date,
            'warehouse_id': warehouse_id,
            'destination': destination,
            'comment': comment
        }

        # собираем позиции из формы
        product_ids = request.form.getlist('product_id')
        quantities = request.form.getlist('quantity')

        items = []
        for pid, qty in zip(product_ids, quantities):
            if not pid or not qty:
                continue
            try:
                qty_int = int(qty)
                if qty_int > 0:
                    items.append((int(pid), qty_int))
            except (ValueError, TypeError):
                pass

        merged_items = {}
        for product_id, qty in items:
            merged_items[product_id] = merged_items.get(product_id, 0) + qty
        items = list(merged_items.items())
        form_items = [{'product_id': str(pid), 'quantity': qty} for pid, qty in items]

        if not items:
            return _render_shipment_form(form_data, form_items,
                                         'Добавьте хотя бы один товар в отгрузку')

        # проверяем остатки на складе
        for product_id, qty in items:
            query = '''
                SELECT COALESCE(SUM(quantity), 0) AS total
                FROM stock
                WHERE product_id=? AND warehouse_id=? AND status='in_stock'
            '''
            available = db.execute(query, (product_id, warehouse_id)).fetchone()['total']

            if available < qty:
                product_name = db.execute(
                    'SELECT name FROM products WHERE id=?', (product_id,)
                ).fetchone()['name']
                form_items = [
                    item for item in form_items
                    if int(item['product_id']) != product_id
                ]
                return _render_shipment_form(
                    form_data,
                    form_items,
                    f'Недостаточно товара «{product_name}» на складе. '
                    f'Доступно: {available} шт., запрошено: {qty} шт.'
                )

        # создаем отгрузку
        try:
            cursor = db.execute(
                'INSERT INTO shipments '
                '(shipment_number, shipment_date, warehouse_id, destination, status, comment) '
                'VALUES (?, ?, ?, ?, ?, ?)',
                (number, shipment_date, warehouse_id, destination, 'confirmed', comment or None)
            )
        except sqlite3.IntegrityError:
            return _render_shipment_form(
                form_data,
                form_items,
                f'Отгрузка с номером «{number}» уже существует'
            )
        shipment_id = cursor.lastrowid

        # добавляем позиции и списываем остатки
        for product_id, qty in items:
            db.execute(
                'INSERT INTO shipment_items (shipment_id, product_id, quantity) VALUES (?, ?, ?)',
                (shipment_id, product_id, qty)
            )
            # списываем из in_stock
            db.execute(
                'UPDATE stock SET quantity = quantity - ? '
                'WHERE product_id=? AND warehouse_id=? AND status=\'in_stock\'',
                (qty, product_id, warehouse_id)
            )

        db.commit()
        flash(f'Отгрузка {number} создана', 'success')
        return redirect(url_for('shipments'))

    return _render_shipment_form()


@app.route('/shipments/<int:shipment_id>')
def shipment_detail(shipment_id):
    db = get_db()
    query = '''
        SELECT sh.*, w.name AS warehouse_name
        FROM shipments sh
        JOIN warehouses w ON sh.warehouse_id = w.id
        WHERE sh.id = ?
    '''
    shipment = db.execute(query, (shipment_id,)).fetchone()

    query = '''
        SELECT p.name AS product, p.sku, si.quantity
        FROM shipment_items si
        JOIN products p ON si.product_id = p.id
        WHERE si.shipment_id = ?
    '''
    items = db.execute(query, (shipment_id,)).fetchall()

    return render_template('shipment_detail.html', shipment=shipment, items=items)


@app.route('/shipments/<int:shipment_id>/delete', methods=['POST'])
def shipment_delete(shipment_id):
    db = get_db()
    db.execute('DELETE FROM shipment_items WHERE shipment_id=?', (shipment_id,))
    db.execute('DELETE FROM shipments WHERE id=?', (shipment_id,))
    db.commit()
    flash('Отгрузка удалена', 'success')
    return redirect(url_for('shipments'))


# API

@app.route('/api/stock')
def api_stock():
    warehouse_ids = request.args.getlist('warehouse_id')
    statuses = request.args.getlist('status')
    product_ids = request.args.getlist('product_id')

    conditions = []
    params = []

    if warehouse_ids:
        placeholders = ','.join('?' * len(warehouse_ids))
        conditions.append(f's.warehouse_id IN ({placeholders})')
        params.extend(warehouse_ids)
    if statuses:
        placeholders = ','.join('?' * len(statuses))
        conditions.append(f's.status IN ({placeholders})')
        params.extend(statuses)
    if product_ids:
        placeholders = ','.join('?' * len(product_ids))
        conditions.append(f's.product_id IN ({placeholders})')
        params.extend(product_ids)

    where = ('WHERE ' + ' AND '.join(conditions)) if conditions else ''

    query = f'''
        SELECT s.id, p.name AS product, p.sku,
               w.name AS warehouse, s.status, s.quantity
        FROM stock s
        JOIN products p ON s.product_id = p.id
        JOIN warehouses w ON s.warehouse_id = w.id
        {where}
        ORDER BY p.name, w.name
    '''

    db = get_db()
    rows = db.execute(query, params).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route('/api/stock/<int:stock_id>/status', methods=['POST'])
def api_stock_status(stock_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON'}), 400
    new_status = data.get('status', '')
    if new_status not in ('incoming', 'in_stock', 'packing'):
        return jsonify({'error': 'Invalid status'}), 400

    db = get_db()
    current = db.execute(
        'SELECT id, product_id, warehouse_id, status, quantity FROM stock WHERE id=?',
        (stock_id,)
    ).fetchone()
    if not current:
        return jsonify({'error': 'Not found'}), 404

    if current['status'] == new_status:
        return jsonify({'ok': True, 'merged': False, 'status': new_status})

    # ищем строку с новым статусом
    target = db.execute(
        'SELECT id, quantity FROM stock '
        'WHERE product_id=? AND warehouse_id=? AND status=? AND id!=?',
        (current['product_id'], current['warehouse_id'], new_status, stock_id)
    ).fetchone()

    if target:
        # объединяем записи
        new_qty = target['quantity'] + current['quantity']
        db.execute(
            'UPDATE stock SET quantity=?, updated_at=datetime("now") WHERE id=?',
            (new_qty, target['id'])
        )
        db.execute('DELETE FROM stock WHERE id=?', (stock_id,))
        db.commit()
        return jsonify({
            'ok': True,
            'merged': True,
            'target_id': target['id'],
            'new_quantity': new_qty,
            'new_status': new_status
        })
    else:
        db.execute(
            'UPDATE stock SET status=?, updated_at=datetime("now") WHERE id=?',
            (new_status, stock_id)
        )
        db.commit()
        return jsonify({'ok': True, 'merged': False, 'status': new_status})


@app.route('/api/shipments/<int:shipment_id>/status', methods=['POST'])
def api_shipment_status(shipment_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON'}), 400
    new_status = data.get('status', '')
    valid = ('confirmed', 'in_transit', 'delivered', 'archived')
    if new_status not in valid:
        return jsonify({'error': 'Invalid status'}), 400
    db = get_db()
    db.execute('UPDATE shipments SET status=? WHERE id=?', (new_status, shipment_id))
    db.commit()
    return jsonify({'ok': True, 'status': new_status})
    return jsonify({'ok': True, 'status': new_status})


# Запуск

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
