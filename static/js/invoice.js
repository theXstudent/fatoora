/* ========================================================================
   Fatoora — Dynamic Invoice Form Logic
   ======================================================================== */

document.addEventListener('DOMContentLoaded', function () {
    const itemsBody = document.getElementById('invoice-items-body');
    const addRowBtn = document.getElementById('add-row-btn');
    const productSelect = document.getElementById('product-select');

    // Totals display
    const totalHTDisplay = document.getElementById('total-ht-display');
    const totalTVADisplay = document.getElementById('total-tva-display');
    const netAPayerDisplay = document.getElementById('net-a-payer-display');

    let rowCounter = document.querySelectorAll('.item-row').length || 0;

    // ---- Add Row ----
    if (addRowBtn) {
        addRowBtn.addEventListener('click', function () {
            addRow();
        });
    }

    // ---- Add from product selector ----
    if (productSelect) {
        productSelect.addEventListener('change', function () {
            const productId = this.value;
            if (!productId) return;

            fetch(`/api/products/${productId}`)
                .then(r => r.json())
                .then(data => {
                    addRow(data.name, data.default_tva, 1, 0, data.default_price);
                    productSelect.value = '';
                })
                .catch(err => console.error('Error fetching product:', err));
        });
    }

    function addRow(name = '', tva = 19, nbrco = 1, qty = 0, price = 0) {
        rowCounter++;
        const tr = document.createElement('tr');
        tr.className = 'item-row';
        tr.innerHTML = `
            <td>
                <input type="text" name="product_name[]" value="${escapeHtml(name)}"
                       class="form-control" placeholder="Nom du produit" required>
            </td>
            <td>
                <input type="number" name="tva_rate[]" value="${tva}" step="0.01" min="0"
                       class="form-control text-center" style="width:80px">
            </td>
            <td>
                <input type="number" name="nbr_co[]" value="${nbrco}" min="1"
                       class="form-control text-center" style="width:70px">
            </td>
            <td>
                <input type="number" name="quantity[]" value="${qty}" step="0.001" min="0"
                       class="form-control" style="width:110px" required>
            </td>
            <td>
                <input type="number" name="unit_price[]" value="${price}" step="0.01" min="0"
                       class="form-control" style="width:120px" required>
            </td>
            <td class="row-total" data-total="0">0.00</td>
            <td>
                <button type="button" class="btn btn-danger btn-icon btn-sm remove-row-btn"
                        title="Supprimer la ligne">✕</button>
            </td>
        `;
        itemsBody.appendChild(tr);

        // Bind events
        bindRowEvents(tr);
        recalculate();
    }

    function bindRowEvents(row) {
        const inputs = row.querySelectorAll('input[name="quantity[]"], input[name="unit_price[]"], input[name="tva_rate[]"]');
        inputs.forEach(input => {
            input.addEventListener('input', recalculate);
        });

        const removeBtn = row.querySelector('.remove-row-btn');
        if (removeBtn) {
            removeBtn.addEventListener('click', function () {
                row.remove();
                recalculate();
            });
        }
    }

    // Bind events on existing rows (for edit mode)
    document.querySelectorAll('.item-row').forEach(row => bindRowEvents(row));

    // ---- Recalculate Totals ----
    function recalculate() {
        let grandTotalHT = 0;
        let grandTotalTVA = 0;

        document.querySelectorAll('.item-row').forEach(row => {
            const qty = parseFloat(row.querySelector('input[name="quantity[]"]').value) || 0;
            const price = parseFloat(row.querySelector('input[name="unit_price[]"]').value) || 0;
            const tva = parseFloat(row.querySelector('input[name="tva_rate[]"]').value) || 0;

            const lineTotal = qty * price;
            const lineTVA = lineTotal * (tva / 100);

            const totalCell = row.querySelector('.row-total');
            totalCell.textContent = formatNumber(lineTotal);
            totalCell.dataset.total = lineTotal;

            grandTotalHT += lineTotal;
            grandTotalTVA += lineTVA;
        });

        const netAPayer = grandTotalHT + grandTotalTVA;

        if (totalHTDisplay)   totalHTDisplay.textContent = formatNumber(grandTotalHT);
        if (totalTVADisplay)  totalTVADisplay.textContent = formatNumber(grandTotalTVA);
        if (netAPayerDisplay) netAPayerDisplay.textContent = formatNumber(netAPayer);
    }

    // ---- Helpers ----
    function formatNumber(num) {
        return num.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.appendChild(document.createTextNode(text));
        return div.innerHTML;
    }

    // Initial calculation
    recalculate();
});
