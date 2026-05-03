import datetime
from database import get_db

def predict_sales(user_id):
    conn = get_db()
    c = conn.cursor()
    
    # Get last 30 days of sales grouped by date
    today = datetime.date.today()
    thirty_days_ago = today - datetime.timedelta(days=30)
    
    c.execute('''
        SELECT date(date) as sale_date, SUM(total_revenue) as daily_total
        FROM sales
        WHERE user_id = ? AND date(date) >= date(?)
        GROUP BY sale_date
        ORDER BY sale_date ASC
    ''', (user_id, thirty_days_ago.isoformat()))
    
    rows = c.fetchall()
    conn.close()
    
    if not rows:
        return {
            "moving_average": 0,
            "linear_regression": 0,
            "final_prediction": 0,
            "trend": "stable"
        }
    
    # Create a dense array for the last 30 days, filling missing days with 0
    date_dict = {row['sale_date']: row['daily_total'] for row in rows}
    
    daily_sales = []
    for i in range(30):
        # Days from 30 days ago to yesterday
        d = (thirty_days_ago + datetime.timedelta(days=i)).isoformat()
        daily_sales.append(date_dict.get(d, 0.0))
        
    # Method 1 - Moving Average (last 7 days)
    last_7_days = daily_sales[-7:]
    moving_average = sum(last_7_days) / len(last_7_days) if last_7_days else 0
    
    # Method 2 - Linear Regression (pure python)
    n = len(daily_sales)
    x = list(range(n))
    y = daily_sales
    
    if n > 1:
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(i * j for i, j in zip(x, y))
        sum_x2 = sum(i**2 for i in x)
        
        denominator = n * sum_x2 - sum_x**2
        if denominator == 0:
            slope = 0
            intercept = sum_y / n
        else:
            slope = (n * sum_xy - sum_x * sum_y) / denominator
            intercept = (sum_y - slope * sum_x) / n
            
        # Predict for tomorrow (index 30)
        linear_regression_pred = slope * 30 + intercept
    else:
        linear_regression_pred = daily_sales[0] if daily_sales else 0
        slope = 0
        
    # Final prediction (weighted)
    # Ensure no negative predictions
    moving_average = max(0, moving_average)
    linear_regression_pred = max(0, linear_regression_pred)
    
    final_prediction = (moving_average * 0.4) + (linear_regression_pred * 0.6)
    
    # Determine trend
    if slope > 5: # Threshold for upward
        trend = "upward"
    elif slope < -5:
        trend = "downward"
    else:
        trend = "stable"
        
    return {
        "moving_average": round(moving_average, 2),
        "linear_regression": round(linear_regression_pred, 2),
        "final_prediction": round(final_prediction, 2),
        "trend": trend
    }
