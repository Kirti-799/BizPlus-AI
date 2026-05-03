// static/billing.js
let productsData = [];
let billItems = [];

document.addEventListener('DOMContentLoaded', () => {
    fetchProducts();
    
    document.getElementById('add-item-btn').addEventListener('click', addItem);
    document.getElementById('save-bill-btn').addEventListener('click', () => saveBill(false));
    document.getElementById('save-print-btn').addEventListener('click', () => saveBill(true));
});

async function fetchProducts() {
    try {
        const response = await fetch('/api/products');
        productsData = await response.json();
        
        const select = document.getElementById('product-select');
        productsData.forEach(p => {
            const option = document.createElement('option');
            option.value = p.id;
            option.textContent = `${p.name} (₹${p.price} - Qty: ${p.quantity})`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error fetching products:', error);
    }
}

function addItem() {
    const select = document.getElementById('product-select');
    const qtyInput = document.getElementById('quantity-input');
    
    const productId = parseInt(select.value);
    const qty = parseInt(qtyInput.value);
    
    if (!productId || isNaN(qty) || qty <= 0) {
        alert('Please select a valid product and quantity.');
        return;
    }
    
    const product = productsData.find(p => p.id === productId);
    if (!product) return;
    
    if (qty > product.quantity) {
        alert(`Cannot add ${qty} ${product.name}. Only ${product.quantity} in stock!`);
        return;
    }
    
    const total = product.price * qty;
    
    billItems.push({
        product_id: product.id,
        name: product.name,
        unit_price: product.price,
        quantity: qty,
        total_price: total
    });
    
    renderBillTable();
    
    // Reset inputs
    select.value = '';
    qtyInput.value = '1';
}

function renderBillTable() {
    const tbody = document.getElementById('bill-table-body');
    tbody.innerHTML = '';
    
    let grandTotal = 0;
    
    billItems.forEach((item, index) => {
        grandTotal += item.total_price;
        
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${item.name}</td>
            <td>${item.quantity}</td>
            <td>₹${item.unit_price}</td>
            <td>₹${item.total_price}</td>
            <td class="no-print">
                <button class="btn btn-danger" style="padding: 0.25rem 0.5rem;" onclick="removeItem(${index})">X</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
    
    document.getElementById('grand-total').textContent = `₹${grandTotal}`;
}

window.removeItem = function(index) {
    billItems.splice(index, 1);
    renderBillTable();
};

async function saveBill(print = false) {
    if (billItems.length === 0) {
        alert('No items in the bill.');
        return;
    }
    
    const customerName = document.getElementById('customer-name').value;
    
    const payload = {
        customer_name: customerName,
        items: billItems
    };
    
    try {
        const response = await fetch('/api/create_bill', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('print-date').textContent = new Date().toLocaleString();
            
            if (print) {
                window.print();
            } else {
                alert('Bill saved successfully!');
            }
            
            // Reset state
            billItems = [];
            document.getElementById('customer-name').value = '';
            renderBillTable();
            fetchProducts(); // Refresh products to update stock quantities
        } else {
            alert('Error saving bill: ' + data.error);
        }
    } catch (error) {
        console.error('Error saving bill:', error);
    }
}
