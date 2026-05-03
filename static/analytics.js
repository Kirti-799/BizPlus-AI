// static/analytics.js
document.addEventListener('DOMContentLoaded', () => {
    fetchAnalyticsData();
});

async function fetchAnalyticsData() {
    try {
        const response = await fetch('/api/analytics_data');
        const data = await response.json();
        
        // Update Profit Overview
        document.getElementById('total-revenue').textContent = formatCurrency(data.profit.revenue);
        document.getElementById('total-cost').textContent = formatCurrency(data.profit.cost);
        document.getElementById('net-profit').textContent = formatCurrency(data.profit.net_profit);
        
        // Populate Trending Products
        const trendingList = document.getElementById('trending-list');
        data.trending.forEach(item => {
            const li = document.createElement('li');
            li.style.padding = '0.5rem 0';
            li.style.borderBottom = '1px solid var(--glass-border)';
            li.innerHTML = `<strong>${item.name}</strong> - ${item.quantity} units sold`;
            trendingList.appendChild(li);
        });
        
        // Render Charts
        renderWeeklyChart(data.weekly);
        renderMonthlyChart(data.monthly);
        
    } catch (error) {
        console.error('Error fetching analytics data:', error);
    }
}

function renderWeeklyChart(weeklyData) {
    const ctx = document.getElementById('weeklyChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: weeklyData.labels,
            datasets: [{
                label: 'Sales (Last 7 Days)',
                data: weeklyData.data,
                backgroundColor: 'rgba(244, 114, 182, 0.6)', // Soft pink
                borderColor: 'rgba(244, 114, 182, 1)',
                borderWidth: 1,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

function renderMonthlyChart(monthlyData) {
    const ctx = document.getElementById('monthlyChart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: monthlyData.labels,
            datasets: [{
                label: 'Sales (Last 30 Days)',
                data: monthlyData.data,
                backgroundColor: 'rgba(186, 230, 253, 0.2)', // Sky blue soft
                borderColor: 'rgba(56, 189, 248, 1)',
                borderWidth: 2,
                fill: true,
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}
