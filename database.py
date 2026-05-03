import sqlite3
import datetime
import random
import os

DB_NAME = os.path.join(os.getcwd(), "bizplus.db")

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    
    # Drop existing tables to enforce schema update
    tables = ['users', 'products', 'sales', 'bills', 'bill_items']
    for table in tables:
        c.execute(f"DROP TABLE IF EXISTS {table}")
        
    # Create users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            shop_name TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create products table
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            emoji TEXT,
            cost_price REAL NOT NULL,
            selling_price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            expiry_date DATE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    # Create sales table
    c.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            cost_price REAL NOT NULL,
            selling_price REAL NOT NULL,
            total_revenue REAL NOT NULL,
            total_cost REAL NOT NULL,
            profit REAL NOT NULL,
            date TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    # Create bills table
    c.execute('''
        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            customer_name TEXT,
            total_amount REAL NOT NULL,
            date TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    # Create bill_items table
    c.execute('''
        CREATE TABLE IF NOT EXISTS bill_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            bill_id INTEGER,
            product_id INTEGER,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            total_price REAL NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(bill_id) REFERENCES bills(id)
        )
    ''')
    
    conn.commit()
    conn.close()

def load_sample_data(user_id):
    conn = get_db()
    c = conn.cursor()
    
    # Clear existing data for this user
    c.execute('DELETE FROM products WHERE user_id = ?', (user_id,))
    c.execute('DELETE FROM sales WHERE user_id = ?', (user_id,))
    c.execute('DELETE FROM bills WHERE user_id = ?', (user_id,))
    c.execute('DELETE FROM bill_items WHERE user_id = ?', (user_id,))
    
    today = datetime.date.today()
    
    # Insert Sample Products (Furniture Store)
    sample_products = [
        ("Wooden Dining Table", "🪑", 8500, 14999, 2, today - datetime.timedelta(days=5)),
        ("Sofa Set (3+1+1)", "🛋️", 22000, 38999, 1, today + datetime.timedelta(days=18)),
        ("Queen Size Bed Frame", "🛏️", 12000, 21999, 3, today + datetime.timedelta(days=45)),
        ("Office Chair (Ergonomic)", "💺", 4500, 8499, 0, today + datetime.timedelta(days=90)),
        ("Bookshelf (5 Tier)", "📚", 3200, 5999, 2, today + datetime.timedelta(days=25)),
        ("Wardrobe (3 Door)", "🚪", 15000, 26999, 5, today + datetime.timedelta(days=180)),
        ("Coffee Table (Glass Top)", "☕", 5500, 9999, 3, today + datetime.timedelta(days=120)),
        ("Study Table with Drawer", "📖", 3800, 6999, 1, today + datetime.timedelta(days=60)),
        ("Recliner Chair", "🪑", 18000, 31999, 2, today + datetime.timedelta(days=200)),
        ("Shoe Rack (Wooden)", "👟", 1800, 3499, 1, today + datetime.timedelta(days=90))
    ]
    
    product_ids = {}
    for prod in sample_products:
        c.execute('''
            INSERT INTO products (user_id, name, emoji, cost_price, selling_price, quantity, expiry_date) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, prod[0], prod[1], prod[2], prod[3], prod[4], prod[5].isoformat()))
        product_ids[prod[0]] = c.lastrowid
        
    # Generate 30 days of realistic random sales (1-3 items per day)
    for i in range(30):
        # Go back from 30 days ago up to today
        sale_date = (today - datetime.timedelta(days=(30-i-1))).strftime('%Y-%m-%d %H:%M:%S')
        
        # 1 to 3 sales per day
        num_sales_today = random.randint(1, 3)
        for _ in range(num_sales_today):
            prod_name = random.choice(list(product_ids.keys()))
            prod_id = product_ids[prod_name]
            
            # Find product price
            for p in sample_products:
                if p[0] == prod_name:
                    cost = p[2]
                    sell = p[3]
                    break
                    
            qty = random.randint(1, 2)
            total_revenue = qty * sell
            total_cost = qty * cost
            profit = total_revenue - total_cost
            
            c.execute('''
                INSERT INTO sales (user_id, product_id, product_name, quantity, cost_price, selling_price, total_revenue, total_cost, profit, date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, prod_id, prod_name, qty, cost, sell, total_revenue, total_cost, profit, sale_date))
            
            
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
