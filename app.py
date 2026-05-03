from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from database import init_db, get_db, load_sample_data
from ml_model import predict_sales
import datetime
from functools import wraps
import hashlib
import os

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "fallback_secret")

# Initialize DB on startup
try:
    init_db()
except:
    pass

# ----- AUTHENTICATION LOGIC -----

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.json
        username = data.get('username', '').strip().lower()
        password = hash_password(data.get('password', ''))
        
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = c.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['shop_name'] = user['shop_name']
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Invalid username or password"}), 401
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.json
        username = data.get('username', '').strip().lower()
        email = data.get('email', '').strip().lower()
        password = hash_password(data.get('password', ''))
        shop_name = data.get('shop_name')
        
        conn = get_db()
        c = conn.cursor()
        
        try:
            c.execute('INSERT INTO users (username, email, password, shop_name) VALUES (?, ?, ?, ?)',
                      (username, email, password, shop_name))
            conn.commit()
            user_id = c.lastrowid
            
            session['user_id'] = user_id
            session['username'] = username
            session['shop_name'] = shop_name
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 400
        finally:
            conn.close()
            
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/guest_login')
def guest_login():
    session.clear()
    session['user_id'] = 'guest'
    session['username'] = 'Guest'
    session['shop_name'] = 'Demo Shop'
    return redirect(url_for('dashboard'))

# ----- HTML ROUTES -----

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/stocks')
@login_required
def stocks():
    return render_template('stocks.html')

@app.route('/billing')
@login_required
def billing():
    return render_template('billing.html')

@app.route('/analytics')
@login_required
def analytics():
    return render_template('analytics.html')

@app.route('/bill_history')
@login_required
def bill_history():
    return render_template('bill_history.html')

@app.route('/analytics_detail')
@login_required
def analytics_detail():
    return render_template('analytics_detail.html')

# ----- API ENDPOINTS -----

@app.route('/api/products', methods=['GET'])
@login_required
def get_products():
    user_id = session['user_id']
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM products WHERE user_id = ? ORDER BY name ASC', (user_id,))
    products = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(products)

@app.route('/api/add_product', methods=['POST'])
@login_required
def add_product():
    user_id = session['user_id']
    data = request.json
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        INSERT INTO products (user_id, name, emoji, cost_price, selling_price, quantity, expiry_date) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, data.get('name'), data.get('emoji'), data.get('cost_price'), data.get('selling_price'), data.get('quantity'), data.get('expiry_date')))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/edit_product/<int:id>', methods=['PUT'])
@login_required
def edit_product(id):
    user_id = session['user_id']
    data = request.json
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        UPDATE products 
        SET name=?, emoji=?, cost_price=?, selling_price=?, quantity=?, expiry_date=? 
        WHERE id=? AND user_id=?
    ''', (data.get('name'), data.get('emoji'), data.get('cost_price'), data.get('selling_price'), data.get('quantity'), data.get('expiry_date'), id, user_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/add_stock/<int:id>', methods=['POST'])
@login_required
def add_stock(id):
    user_id = session['user_id']
    data = request.json
    qty_to_add = int(data.get('quantity', 0))
    expiry_date = data.get('expiry_date')
    
    if qty_to_add <= 0:
        return jsonify({"success": False, "error": "Quantity must be positive"}), 400
        
    conn = get_db()
    c = conn.cursor()
    
    if expiry_date:
        c.execute('''
            UPDATE products 
            SET quantity = quantity + ?, expiry_date = ? 
            WHERE id = ? AND user_id = ?
        ''', (qty_to_add, expiry_date, id, user_id))
    else:
        c.execute('''
            UPDATE products 
            SET quantity = quantity + ? 
            WHERE id = ? AND user_id = ?
        ''', (qty_to_add, id, user_id))
        
    c.execute('SELECT quantity FROM products WHERE id = ?', (id,))
    new_qty = c.fetchone()['quantity']
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "new_quantity": new_qty})

@app.route('/api/delete_product/<int:id>', methods=['DELETE'])
@login_required
def delete_product(id):
    user_id = session['user_id']
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM products WHERE id=? AND user_id=?', (id, user_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/load_sample_data', methods=['POST'])
@login_required
def load_sample():
    user_id = session['user_id']
    load_sample_data(user_id)
    return jsonify({"success": True})

@app.route('/api/create_bill', methods=['POST'])
@login_required
def create_bill():
    user_id = session['user_id']
    data = request.json
    customer_name = data.get('customer_name', '')
    items = data.get('items', [])
    
    if not items:
        return jsonify({"success": False, "error": "No items provided"}), 400
        
    date_now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    conn = get_db()
    c = conn.cursor()
    
    # Calculate totals from current product prices
    total_bill_amount = 0
    bill_records = []
    
    for item in items:
        c.execute('SELECT name, cost_price, selling_price FROM products WHERE id = ? AND user_id = ?', (item['product_id'], user_id))
        prod = c.fetchone()
        if not prod:
            continue
            
        qty = int(item['quantity'])
        cost = prod['cost_price']
        sell = prod['selling_price']
        
        total_rev = qty * sell
        total_cost = qty * cost
        profit = total_rev - total_cost
        
        total_bill_amount += total_rev
        
        bill_records.append({
            "product_id": item['product_id'],
            "product_name": prod['name'],
            "quantity": qty,
            "cost_price": cost,
            "selling_price": sell,
            "total_revenue": total_rev,
            "total_cost": total_cost,
            "profit": profit
        })
    
    # Create bill record
    c.execute('INSERT INTO bills (user_id, customer_name, total_amount, date) VALUES (?, ?, ?, ?)',
              (user_id, customer_name, total_bill_amount, date_now))
    bill_id = c.lastrowid
    
    for rec in bill_records:
        # Add to bill_items
        c.execute('''
            INSERT INTO bill_items (user_id, bill_id, product_id, quantity, unit_price, total_price) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, bill_id, rec['product_id'], rec['quantity'], rec['selling_price'], rec['total_revenue']))
                  
        # Reduce stock
        c.execute('UPDATE products SET quantity = quantity - ? WHERE id = ? AND user_id = ?',
                  (rec['quantity'], rec['product_id'], user_id))
                  
        # Record sale for analytics
        c.execute('''
            INSERT INTO sales (user_id, product_id, product_name, quantity, cost_price, selling_price, total_revenue, total_cost, profit, date) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, rec['product_id'], rec['product_name'], rec['quantity'], rec['cost_price'], rec['selling_price'], rec['total_revenue'], rec['total_cost'], rec['profit'], date_now))
                  
    conn.commit()
    conn.close()
    return jsonify({"success": True, "bill_id": bill_id})

@app.route('/api/dashboard_data', methods=['GET'])
@login_required
def get_dashboard_data():
    user_id = session['user_id']
    conn = get_db()
    c = conn.cursor()
    
    today = datetime.date.today()
    today_str = today.isoformat()
    seven_days_ago = (today - datetime.timedelta(days=6))
    thirty_days_ago = (today - datetime.timedelta(days=29))
    
    # ---------- TODAY ----------
    c.execute('''
        SELECT SUM(total_revenue) as rev, SUM(profit) as prof 
        FROM sales 
        WHERE user_id = ? AND date(date) = ?
    ''', (user_id, today_str))
    row = c.fetchone()
    today_revenue = row['rev'] if row['rev'] else 0
    today_profit = row['prof'] if row['prof'] else 0
    
    # ---------- WEEKLY ----------
    c.execute('''
        SELECT SUM(total_revenue) as rev, SUM(profit) as prof 
        FROM sales 
        WHERE user_id = ? AND date(date) >= ?
    ''', (user_id, seven_days_ago.isoformat()))
    row = c.fetchone()
    weekly_revenue = row['rev'] if row['rev'] else 0
    weekly_profit = row['prof'] if row['prof'] else 0
    
    # ---------- MONTHLY ----------
    c.execute('''
        SELECT SUM(total_revenue) as rev, SUM(profit) as prof 
        FROM sales 
        WHERE user_id = ? AND date(date) >= ?
    ''', (user_id, thirty_days_ago.isoformat()))
    row = c.fetchone()
    monthly_revenue = row['rev'] if row['rev'] else 0
    monthly_profit = row['prof'] if row['prof'] else 0
    
    # ---------- ALERTS ----------
    c.execute('SELECT name, quantity, expiry_date FROM products WHERE user_id = ?', (user_id,))
    all_products = c.fetchall()
    
    raw_alerts = []
    for p in all_products:
        qty = p['quantity']
        expiry_str = p['expiry_date']
        
        days_until_expiry = 9999
        if expiry_str:
            try:
                exp_date = datetime.date.fromisoformat(expiry_str)
                days_until_expiry = (exp_date - today).days
            except:
                pass
                
        if days_until_expiry < 0 and qty > 0:
            raw_alerts.append({"type": "overdue_review", "product": p['name'], "quantity": qty, "priority": 1})
        elif qty == 0:
            raw_alerts.append({"type": "out_of_stock", "product": p['name'], "quantity": qty, "priority": 2})
        elif 0 <= days_until_expiry <= 30 and qty > 0:
            raw_alerts.append({"type": "review_soon", "product": p['name'], "quantity": qty, "priority": 3})
        elif 1 <= qty <= 3:
            raw_alerts.append({"type": "low_stock", "product": p['name'], "quantity": qty, "priority": 4})
    
    raw_alerts.sort(key=lambda x: x['priority'])
    
    # ---------- WEEKLY CHART ----------
    c.execute('''
        SELECT date(date) as sd, SUM(total_revenue) as total 
        FROM sales 
        WHERE user_id = ? AND date(date) >= ? 
        GROUP BY sd ORDER BY sd ASC
    ''', (user_id, seven_days_ago.isoformat()))
    
    weekly_rows = c.fetchall()
    weekly_dict = {row['sd']: row['total'] for row in weekly_rows}
    
    weekly_labels = []
    weekly_data = []
    for i in range(7):
        d = (seven_days_ago + datetime.timedelta(days=i)).isoformat()
        weekly_labels.append(d)
        weekly_data.append(weekly_dict.get(d, 0))
    
    # ---------- INSIGHTS (FIXED POSITION) ----------
    c.execute('''
        SELECT product_name, SUM(quantity) as total_qty
        FROM sales
        WHERE user_id = ? AND date(date) >= ?
        GROUP BY product_name
        ORDER BY total_qty DESC
    ''', (user_id, thirty_days_ago.isoformat()))

    product_sales = c.fetchall()

    top_product = "N/A"
    least_product = "N/A"

    if product_sales:
        top_product = product_sales[0]['product_name']
        least_product = product_sales[-1]['product_name']

    best_category = "General"

    # ---------- PREDICTION ----------
    prediction = predict_sales(user_id)

    # ✅ CLOSE CONNECTION AT END (CRITICAL FIX)
    conn.close()

    return jsonify({
        "today_revenue": round(today_revenue, 2),
        "today_profit": round(today_profit, 2),
        "weekly_revenue": round(weekly_revenue, 2),
        "weekly_profit": round(weekly_profit, 2),
        "monthly_revenue": round(monthly_revenue, 2),
        "monthly_profit": round(monthly_profit, 2),
        "predicted_sales": prediction['final_prediction'],
        "weekly_chart": {
            "labels": weekly_labels,
            "data": weekly_data
        },
        "top_product": top_product,
        "least_product": least_product,
        "best_category": best_category,
        "alerts": raw_alerts
    })

@app.route('/api/analytics_data', methods=['GET'])    
@login_required
def get_analytics_data():
    user_id = session['user_id']
    conn = get_db()
    c = conn.cursor()
    
    today = datetime.date.today()
    seven_days_ago = (today - datetime.timedelta(days=6))
    thirty_days_ago = (today - datetime.timedelta(days=29))
    
    # Weekly Chart Data
    c.execute('''
        SELECT date(date) as sd, SUM(total_revenue) as rev, SUM(profit) as prof 
        FROM sales 
        WHERE user_id = ? AND date(date) >= ? 
        GROUP BY sd ORDER BY sd ASC
    ''', (user_id, seven_days_ago.isoformat()))
    
    weekly_rows = c.fetchall()
    weekly_rev_dict = {row['sd']: row['rev'] for row in weekly_rows}
    weekly_prof_dict = {row['sd']: row['prof'] for row in weekly_rows}
    
    weekly_labels = []
    weekly_rev_data = []
    weekly_prof_data = []
    for i in range(7):
        d = (seven_days_ago + datetime.timedelta(days=i)).isoformat()
        weekly_labels.append(d)
        weekly_rev_data.append(weekly_rev_dict.get(d, 0))
        weekly_prof_data.append(weekly_prof_dict.get(d, 0))
        
    # Monthly Chart Data
    c.execute('''
        SELECT date(date) as sd, SUM(total_revenue) as rev, SUM(profit) as prof 
        FROM sales 
        WHERE user_id = ? AND date(date) >= ? 
        GROUP BY sd ORDER BY sd ASC
    ''', (user_id, thirty_days_ago.isoformat()))
    
    monthly_rows = c.fetchall()
    monthly_rev_dict = {row['sd']: row['rev'] for row in monthly_rows}
    monthly_prof_dict = {row['sd']: row['prof'] for row in monthly_rows}
    
    monthly_labels = []
    monthly_rev_data = []
    monthly_prof_data = []
    for i in range(30):
        d = (thirty_days_ago + datetime.timedelta(days=i)).isoformat()
        monthly_labels.append(d)
        monthly_rev_data.append(monthly_rev_dict.get(d, 0))
        monthly_prof_data.append(monthly_prof_dict.get(d, 0))
        
    # Trending Products
    c.execute('''
        SELECT product_name, SUM(quantity) as total_qty
        FROM sales
        WHERE user_id = ? AND date(date) >= ?
        GROUP BY product_name
        ORDER BY total_qty DESC
        LIMIT 5
    ''', (user_id, thirty_days_ago.isoformat()))
    trending = [{"name": row['product_name'], "quantity": row['total_qty']} for row in c.fetchall()]
    
    # Profit Overview
    c.execute('''
        SELECT SUM(total_revenue) as rev, SUM(total_cost) as cost, SUM(profit) as prof
        FROM sales
        WHERE user_id = ? AND date(date) >= ?
    ''', (user_id, thirty_days_ago.isoformat()))
    profit_row = c.fetchone()
    revenue = profit_row['rev'] if profit_row and profit_row['rev'] else 0
    cost = profit_row['cost'] if profit_row and profit_row['cost'] else 0
    net_profit = profit_row['prof'] if profit_row and profit_row['prof'] else 0

    conn.close()
    
    return jsonify({
        "weekly": {"labels": weekly_labels, "data": weekly_rev_data, "profit": weekly_prof_data},
        "monthly": {"labels": monthly_labels, "data": monthly_rev_data, "profit": monthly_prof_data},
        "trending": trending,
        "profit": {
            "revenue": round(revenue, 2),
            "cost": round(cost, 2),
            "net_profit": round(net_profit, 2)
        }
    })

@app.route('/api/predict', methods=['GET'])
@login_required
def get_prediction():
    user_id = session['user_id']
    return jsonify(predict_sales(user_id))

@app.route('/api/bill_history', methods=['GET'])
@login_required
def get_bill_history():
    user_id = session['user_id']
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM bills WHERE user_id = ? ORDER BY date DESC', (user_id,))
    bills = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(bills)

@app.route('/api/bill_history/<int:bill_id>', methods=['GET'])
@login_required
def get_single_bill(bill_id):
    user_id = session['user_id']
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM bill_items WHERE bill_id = ? AND user_id = ?', (bill_id, user_id))
    items = []
    for row in c.fetchall():
        item = dict(row)
        c.execute('SELECT name FROM products WHERE id = ? AND user_id = ?', (item['product_id'], user_id))
        prod = c.fetchone()
        item['product_name'] = prod['name'] if prod else 'Unknown Product'
        items.append(item)
    conn.close()
    return jsonify(items)

@app.route('/api/analytics_detail', methods=['GET'])
@login_required
def get_analytics_detail():
    user_id = session['user_id']
    conn = get_db()
    c = conn.cursor()
    
    today = datetime.date.today()
    thirty_days_ago = (today - datetime.timedelta(days=29))
    seven_days_ago = (today - datetime.timedelta(days=6))
    
    c.execute('''
        SELECT product_name, SUM(quantity) as total_qty, SUM(total_revenue) as revenue
        FROM sales
        WHERE user_id = ? AND date(date) >= ?
        GROUP BY product_name
        ORDER BY total_qty DESC
        LIMIT 5
    ''', (user_id, thirty_days_ago.isoformat()))
    trending = [dict(row) for row in c.fetchall()]
    
    c.execute('''
        SELECT p.name as product_name, IFNULL(SUM(s.quantity), 0) as total_qty, p.quantity as stock_remaining
        FROM products p
        LEFT JOIN sales s ON p.id = s.product_id AND date(s.date) >= ? AND s.user_id = ?
        WHERE p.user_id = ?
        GROUP BY p.id
        ORDER BY total_qty ASC
        LIMIT 5
    ''', (thirty_days_ago.isoformat(), user_id, user_id))
    least_sold = [dict(row) for row in c.fetchall()]
    
    c.execute('''
        SELECT date(date) as sd, SUM(total_revenue) as total 
        FROM sales 
        WHERE user_id = ? AND date(date) >= ? 
        GROUP BY sd ORDER BY sd ASC
    ''', (user_id, thirty_days_ago.isoformat()))
    monthly_rows = c.fetchall()
    monthly_dict = {row['sd']: row['total'] for row in monthly_rows}
    monthly_labels = []
    monthly_data = []
    for i in range(30):
        d = (thirty_days_ago + datetime.timedelta(days=i)).isoformat()
        monthly_labels.append(d)
        monthly_data.append(monthly_dict.get(d, 0))
        
    c.execute('''
        SELECT date(date) as sd, SUM(total_revenue) as total 
        FROM sales 
        WHERE user_id = ? AND date(date) >= ? 
        GROUP BY sd ORDER BY sd ASC
    ''', (user_id, seven_days_ago.isoformat()))
    weekly_rows = c.fetchall()
    weekly_dict = {row['sd']: row['total'] for row in weekly_rows}
    weekly_labels = []
    weekly_data = []
    for i in range(7):
        d = (seven_days_ago + datetime.timedelta(days=i)).isoformat()
        weekly_labels.append(d)
        weekly_data.append(weekly_dict.get(d, 0))
        
    conn.close()
    
    return jsonify({
        "trending": trending,
        "least_sold": least_sold,
        "monthly": {"labels": monthly_labels, "data": monthly_data},
        "weekly": {"labels": weekly_labels, "data": weekly_data}
    })

if __name__ == '__main__':
    app.run()
