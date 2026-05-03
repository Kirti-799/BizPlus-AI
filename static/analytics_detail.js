// static/analytics_detail.js
document.addEventListener('DOMContentLoaded', () => {
    fetchDetailedAnalytics();
    setupScrollReveal();
    setupBackToTop();
});

async function fetchDetailedAnalytics() {
    try {
        const response = await fetch('/api/analytics_detail');
        const data = await response.json();
        
        renderTrending(data.trending);
        renderLeastSold(data.least_sold);
        renderMonthlyChart(data.monthly);
        renderWeeklyChart(data.weekly);
        
        // Trigger reveal check once data is loaded so charts appear if in view
        setTimeout(revealElements, 100);
    } catch (err) {
        console.error("Error fetching analytics details", err);
    }
}

function renderTrending(trending) {
    const container = document.getElementById('trending-container');
    container.innerHTML = '';
    
    if (trending.length === 0) {
        container.innerHTML = '<p>No sales data available yet.</p>';
        return;
    }

    const medals = ['🥇', '🥈', '🥉', '✨', '⭐'];

    trending.forEach((item, index) => {
        const rankBadge = medals[index] || '⭐';
        
        const card = document.createElement('div');
        card.className = 'glass-panel stat-card';
        card.innerHTML = `
            <div class="stat-info">
                <h3 style="color: var(--text-color);">
                    <span style="font-size: 1.5rem;">${rankBadge}</span> 
                    ${item.product_name}
                </h3>
                <p style="color: var(--text-muted); margin-left: 2.5rem; margin-top: 0.25rem;">
                    ${item.total_qty} units sold
                </p>
            </div>
            <div style="text-align: right;">
                <h3 style="color: var(--primary-color);">${formatCurrency(item.revenue)}</h3>
                <span style="font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase;">Revenue</span>
            </div>
        `;
        container.appendChild(card);
    });
}

function renderLeastSold(leastSold) {
    const container = document.getElementById('least-sold-container');
    container.innerHTML = '';
    
    if (leastSold.length === 0) {
        container.innerHTML = '<p>No data available yet.</p>';
        return;
    }

    leastSold.forEach(item => {
        // Warning colors
        const bgColor = 'rgba(239, 68, 68, 0.1)'; // soft red
        const borderColor = 'rgba(239, 68, 68, 0.3)';
        
        const card = document.createElement('div');
        card.className = 'glass-panel stat-card';
        card.style.background = bgColor;
        card.style.border = `1px solid ${borderColor}`;
        card.innerHTML = `
            <div class="stat-info">
                <h3 style="color: var(--danger);">
                    <span style="font-size: 1.5rem;">📉</span> 
                    ${item.product_name}
                </h3>
                <p style="color: var(--text-muted); margin-left: 2.5rem; margin-top: 0.25rem;">
                    ${item.total_qty} units sold
                </p>
            </div>
            <div style="text-align: right;">
                <h3 style="color: var(--text-color);">${item.stock_remaining}</h3>
                <span style="font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase;">In Stock</span>
            </div>
        `;
        container.appendChild(card);
    });
}

function renderMonthlyChart(monthlyData) {
    const ctx = document.getElementById('monthlyChartDetail').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: monthlyData.labels,
            datasets: [{
                label: 'Sales (Last 30 Days)',
                data: monthlyData.data,
                backgroundColor: 'rgba(56, 189, 248, 0.2)', // Sky blue soft
                borderColor: 'rgba(14, 165, 233, 1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4, // Smooth curve
                pointBackgroundColor: 'rgba(14, 165, 233, 1)',
                pointRadius: 3
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: { beginAtZero: true }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

function renderWeeklyChart(weeklyData) {
    const ctx = document.getElementById('weeklyChartDetail').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: weeklyData.labels,
            datasets: [{
                label: 'Sales (Last 7 Days)',
                data: weeklyData.data,
                backgroundColor: 'rgba(244, 114, 182, 0.7)', // Soft pink
                borderColor: 'rgba(219, 39, 119, 1)',
                borderWidth: 1,
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: { beginAtZero: true }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

function revealElements() {
    const reveals = document.querySelectorAll('.reveal');
    const windowHeight = window.innerHeight;
    const elementVisible = 150;
    
    reveals.forEach(reveal => {
        const elementTop = reveal.getBoundingClientRect().top;
        if (elementTop < windowHeight - elementVisible) {
            reveal.classList.add('active');
        }
    });
}

function setupScrollReveal() {
    const wrapper = document.getElementById('analytics-scroll-container');
    wrapper.addEventListener('scroll', revealElements);
    // Initial check
    revealElements();
}

function setupBackToTop() {
    const wrapper = document.getElementById('analytics-scroll-container');
    const backToTop = document.getElementById('backToTop');
    
    wrapper.addEventListener('scroll', () => {
        if (wrapper.scrollTop > 300) {
            backToTop.classList.add('show');
        } else {
            backToTop.classList.remove('show');
        }
    });
}
