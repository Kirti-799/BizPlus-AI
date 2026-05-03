// static/dashboard.js
document.addEventListener('DOMContentLoaded', () => {
    fetchDashboardData();
});

async function fetchDashboardData() {
    try {
        const response = await fetch('/api/dashboard_data');
        const data = await response.json();
        // ===== NEW INSIGHTS DATA =====
    if (data.top_product) {
        document.getElementById('top-product').textContent = data.top_product;
    }
    if (data.least_product) {
        document.getElementById('least-product').textContent = data.least_product;
    }
    if (data.best_category) {
        document.getElementById('best-category').textContent = data.best_category;
    }
        
        // Update Stats
        document.getElementById('today-sales').textContent = formatCurrency(data.today_sales);
        document.getElementById('weekly-sales').textContent = formatCurrency(data.weekly_sales);
        document.getElementById('monthly-sales').textContent = formatCurrency(data.monthly_sales);
        document.getElementById('predicted-sales').textContent = formatCurrency(data.predicted_sales);
        
        // Update Alerts
        const alertsContainer = document.getElementById('alerts-container');
        alertsContainer.innerHTML = ''; // Clear loading
        
        if (data.alerts && data.alerts.length > 0) {
            data.alerts.forEach(alert => {
                const alertDiv = document.createElement('div');
                alertDiv.className = 'glass-panel alert-box';
                alertDiv.style.padding = '1rem';
                alertDiv.style.marginBottom = '1rem';
                alertDiv.style.display = 'flex';
                alertDiv.style.alignItems = 'center';
                alertDiv.style.gap = '1rem';
                
                if (alert.quantity === 0) {
                    alertDiv.style.borderLeft = '4px solid var(--danger)';
                    alertDiv.innerHTML = `<span>🚨</span> <strong>${alert.name}</strong> is out of stock!`;
                } else {
                    alertDiv.style.borderLeft = '4px solid var(--warning)';
                    alertDiv.innerHTML = `<span>⚠️</span> <strong>${alert.name}</strong> is low on stock (Quantity: ${alert.quantity})`;
                }
                
                alertsContainer.appendChild(alertDiv);
            });
        } else {
            alertsContainer.innerHTML = '<p>No alerts at this time. Stock levels are good.</p>';
        }
        
    } catch (error) {
        console.error('Error fetching dashboard data:', error);
    }
}
