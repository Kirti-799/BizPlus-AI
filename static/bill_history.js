// static/bill_history.js
let allBills = [];

document.addEventListener('DOMContentLoaded', () => {
    fetchBills();

    // Setup filter buttons
    const filterBtns = document.querySelectorAll('.filter-btn');
    filterBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            filterBtns.forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            renderBills(e.target.dataset.filter);
        });
    });
});

async function fetchBills() {
    try {
        const response = await fetch('/api/bill_history');
        allBills = await response.json();
        renderBills('today'); // default to today
    } catch (err) {
        console.error('Error fetching bills:', err);
    }
}

function renderBills(filterType) {
    const container = document.getElementById('bills-container');
    container.innerHTML = '';

    const now = new Date();
    
    let filteredBills = allBills.filter(bill => {
        const billDate = new Date(bill.date);
        const timeDiff = now - billDate;
        const daysDiff = timeDiff / (1000 * 3600 * 24);

        if (filterType === 'today') {
            return billDate.toDateString() === now.toDateString();
        } else if (filterType === 'week') {
            return daysDiff <= 7;
        } else if (filterType === 'month') {
            return daysDiff <= 30;
        }
        return true; // all time
    });

    if (filteredBills.length === 0) {
        container.innerHTML = '<p>No bills found for the selected period.</p>';
        return;
    }

    filteredBills.forEach(bill => {
        const customer = bill.customer_name || 'Walk-in Customer';
        const dateStr = new Date(bill.date).toLocaleString();
        
        const card = document.createElement('div');
        card.className = 'glass-panel bill-card';
        card.innerHTML = `
            <div class="bill-header">
                <div>
                    <h3 style="margin-bottom: 0.25rem;">Bill #${bill.id} - ${customer}</h3>
                    <p style="color: var(--text-muted); font-size: 0.9rem;">📅 ${dateStr}</p>
                </div>
                <div style="text-align: right;">
                    <h3 style="color: var(--primary-color); margin-bottom: 0.5rem;">${formatCurrency(bill.total_amount)}</h3>
                    <button class="btn btn-secondary" style="padding: 0.4rem 1rem; font-size: 0.85rem;" onclick="toggleDetails(${bill.id}, this)">View Details</button>
                </div>
            </div>
            <div class="bill-details-container" id="details-${bill.id}">
                <p>Loading items...</p>
            </div>
        `;
        container.appendChild(card);
    });
}

async function toggleDetails(billId, btnElement) {
    const detailsContainer = document.getElementById(`details-${billId}`);
    
    if (detailsContainer.classList.contains('show')) {
        detailsContainer.classList.remove('show');
        btnElement.textContent = 'View Details';
        return;
    }

    // Open and fetch if not loaded
    detailsContainer.classList.add('show');
    btnElement.textContent = 'Hide Details';

    if (detailsContainer.dataset.loaded === 'true') return;

    try {
        const res = await fetch(`/api/bill_history/${billId}`);
        const items = await res.json();
        
        let html = `
            <table style="width: 100%; margin-top: 0.5rem;">
                <tr style="color: var(--text-muted); font-size: 0.85rem; border-bottom: 1px solid rgba(0,0,0,0.1);">
                    <th style="padding-bottom: 0.5rem;">Item</th>
                    <th style="padding-bottom: 0.5rem;">Qty</th>
                    <th style="padding-bottom: 0.5rem;">Unit Price</th>
                    <th style="padding-bottom: 0.5rem; text-align: right;">Total</th>
                </tr>
        `;

        items.forEach(item => {
            html += `
                <tr style="border-bottom: 1px dashed rgba(0,0,0,0.05);">
                    <td style="padding: 0.5rem 0;">${item.product_name}</td>
                    <td style="padding: 0.5rem 0;">${item.quantity}</td>
                    <td style="padding: 0.5rem 0;">${formatCurrency(item.unit_price)}</td>
                    <td style="padding: 0.5rem 0; text-align: right;">${formatCurrency(item.total_price)}</td>
                </tr>
            `;
        });
        
        html += `</table>`;
        detailsContainer.innerHTML = html;
        detailsContainer.dataset.loaded = 'true';

    } catch (err) {
        detailsContainer.innerHTML = '<p style="color: red;">Error loading items.</p>';
        console.error(err);
    }
}
