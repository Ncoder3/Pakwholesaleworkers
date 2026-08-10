// ==========================================
// DYNAMIC BASE URL CONFIGURATION
// ==========================================
const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? ''
    : 'https://pakwholesaleworkers.up.railway.app';


// ==========================================
// DOM INITIALIZATION & EVENT LISTENERS
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
    // Live Search Functionality
    const searchBox = document.getElementById('searchBox') || document.getElementById('searchInput');
    if (searchBox) {
        searchBox.addEventListener('input', function () {
            const term = this.value.toLowerCase().trim();
            const rows = document.querySelectorAll('table tbody tr:not(#noResultsRow)');
            let visibleCount = 0;

            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                if (text.includes(term)) {
                    row.style.display = '';
                    visibleCount++;
                } else {
                    row.style.display = 'none';
                }
            });

            const tbody = document.querySelector('table tbody');
            let noResultsRow = document.getElementById('noResultsRow');

            if (visibleCount === 0 && term !== '') {
                if (!noResultsRow && tbody) {
                    noResultsRow = document.createElement('tr');
                    noResultsRow.id = 'noResultsRow';
                    noResultsRow.innerHTML = `
                        <td colspan="10" style="text-align: center; padding: 20px; color: #64748b; font-size: 14px; background: transparent;">
                            <i class="fa-solid fa-magnifying-glass" style="margin-right: 8px; color: #94a3b8;"></i>
                            No products matching "<strong>${term}</strong>"
                        </td>
                    `;
                    tbody.appendChild(noResultsRow);
                } else if (noResultsRow) {
                    noResultsRow.style.display = '';
                    noResultsRow.querySelector('td').innerHTML = `
                        <i class="fa-solid fa-magnifying-glass" style="margin-right: 8px; color: #94a3b8;"></i>
                        No products matching "<strong>${term}</strong>"
                    `;
                }
            } else if (noResultsRow) {
                noResultsRow.style.display = 'none';
            }
        });
    }

    // Modal Outer Click Close Triggers
    window.addEventListener('click', (event) => {
        if (event.target.classList.contains('modal') || event.target.classList.contains('modal-overlay')) {
            event.target.style.display = 'none';
            event.target.classList.remove('active');
        }

        // Notification Dropdown Close
        const dropdown = document.getElementById('notificationDropdown');
        const notifBtn = document.getElementById('notificationBtn');
        if (dropdown && !dropdown.contains(event.target) && event.target !== notifBtn) {
            dropdown.style.display = 'none';
        }
    });

    // Sidebar Active Link Highlighting
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.sidebar nav a');
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.style.background = 'var(--primary-hover, #046c4e)';
            link.style.color = '#ffffff';
        }
    });
});


// ==========================================
// GENERIC MODAL CONTROLS
// ==========================================
function openModal(id) {
    const target = document.getElementById(id);
    if (target) {
        target.style.display = 'flex';
        target.classList.add('active');
    }
}

function closeModal(id) {
    const target = document.getElementById(id);
    if (target) {
        target.style.display = 'none';
        target.classList.remove('active');
    }
}


// ==========================================
// INVENTORY & STOCK MANAGEMENT
// ==========================================

// Opens Stock Modal and sets active values
function openStockModal(code, name, currentStock) {
    const nameEl = document.getElementById('modalProductName') || document.getElementById('stockModalName');
    const codeEl = document.getElementById('modalProductCode') || document.getElementById('stockModalCode');
    const inputEl = document.getElementById('modalStockInput') || document.getElementById('stockModalInput');

    if (nameEl) nameEl.innerText = name;
    if (codeEl) codeEl.innerText = code;
    if (inputEl) inputEl.value = currentStock;

    openModal('stockModal');
}

// Closes Stock Modal helper alias
function closeStockModal() {
    closeModal('stockModal');
}

// Handles +/- button increments inside Stock Modal
function changeModalStock(delta) {
    const input = document.getElementById('modalStockInput') || document.getElementById('stockModalInput');
    if (!input) return;
    let val = parseInt(input.value) || 0;
    val += delta;
    if (val < 0) val = 0;
    input.value = val;
}

// Saves stock update to Flask API endpoint
async function saveStockChange(event) {
    if (event) event.preventDefault();

    const codeEl = document.getElementById('modalProductCode') || document.getElementById('stockModalCode');
    const inputEl = document.getElementById('modalStockInput') || document.getElementById('stockModalInput');
    
    if (!codeEl || !inputEl) return;

    const productCode = codeEl.innerText.trim();
    const newStock = parseInt(inputEl.value) || 0;

    try {
        const response = await fetch(`${API_BASE_URL}/api/update-stock`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                product_code: productCode, 
                new_stock: newStock 
            })
        });

        const data = await response.json();

        if (data.success) {
            showToast("Success", "Stock updated successfully!", "success");
            closeStockModal();

            // Dynamic badge update without full page reload
            const badge = document.getElementById(`stock-badge-${productCode}`);
            if (badge) {
                if (newStock === 0) {
                    badge.className = 'badge badge-danger';
                    badge.style.background = '#fee2e2';
                    badge.style.color = '#dc2626';
                    badge.innerHTML = `<i class="fa-solid fa-circle" style="font-size: 8px; color: #dc2626;"></i> Out of Stock (0)`;
                } else if (newStock <= 5) {
                    badge.className = 'badge badge-warning';
                    badge.style.background = '#fef3c7';
                    badge.style.color = '#d97706';
                    badge.innerHTML = `<i class="fa-solid fa-circle" style="font-size: 8px; color: #d97706;"></i> Low Stock (${newStock})`;
                } else {
                    badge.className = 'badge badge-success';
                    badge.style.background = '#dcfce7';
                    badge.style.color = '#16a34a';
                    badge.innerHTML = `<i class="fa-solid fa-circle" style="font-size: 8px; color: #16a34a;"></i> In Stock (${newStock})`;
                }
            } else {
                setTimeout(() => location.reload(), 500);
            }
        } else {
            showToast("Error", data.message || "Failed to update stock", "error");
        }
    } catch (err) {
        console.error("Error updating stock:", err);
        showToast("Error", "Network or server error updating stock.", "error");
    }
}


// ==========================================
// PRODUCT CRUD FUNCTIONS
// ==========================================

// View Product Details
function viewProduct(button) {
    const data = button.dataset;
    if (document.getElementById('modalImage')) document.getElementById('modalImage').src = '/images/' + data.image;
    if (document.getElementById('modalName')) document.getElementById('modalName').innerText = data.name;
    if (document.getElementById('modalCode')) document.getElementById('modalCode').innerText = data.code;
    if (document.getElementById('modalCategory')) document.getElementById('modalCategory').innerText = data.category;
    if (document.getElementById('modalPack')) document.getElementById('modalPack').innerText = data.pack;
    if (document.getElementById('modalPieces')) document.getElementById('modalPieces').innerText = data.pieces;
    if (document.getElementById('modalWholesale')) document.getElementById('modalWholesale').innerText = data.wholesale;
    if (document.getElementById('modalRetail')) document.getElementById('modalRetail').innerText = data.retail;
    if (document.getElementById('modalStock')) document.getElementById('modalStock').innerText = data.stock;
    if (document.getElementById('modalNotes')) document.getElementById('modalNotes').innerText = data.notes || 'None';

    openModal('productModal');
}

// Add New Product
function openAddModal() {
    const form = document.getElementById('addForm');
    if (form) form.reset();
    openModal('addModal');
}

function saveNewProduct(event) {
    event.preventDefault();

    const form = document.getElementById('addForm');
    const submitBtn = form.querySelector('button[type="submit"]');
    const codeInput = document.getElementById('addCode');

    if (codeInput) codeInput.style.borderColor = '';
    if (submitBtn) submitBtn.disabled = true;

    const formData = new FormData(form);

    fetch(`${API_BASE_URL}/add_product`, {
        method: 'POST',
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (submitBtn) submitBtn.disabled = false;

        if (data.success) {
            showToast("Success", data.message, "success");
            closeModal('addModal');
            setTimeout(() => location.reload(), 800);
        } else {
            showToast("Action Required", data.message, "error");
            if (codeInput) {
                codeInput.removeAttribute('readonly');
                codeInput.removeAttribute('disabled');
                codeInput.style.borderColor = '#ef4444';
                codeInput.focus();
                codeInput.select();
            }
        }
    })
    .catch(error => {
        console.error("Error adding product:", error);
        if (submitBtn) submitBtn.disabled = false;
        showToast("System Error", "An unexpected error occurred while saving.", "error");
    });
}

// Opens modal and populates form fields defensively
function editProduct(buttonOrData) {
    const data = buttonOrData.dataset ? buttonOrData.dataset : buttonOrData;
    const codeVal = data.code || data["Product Code"] || '';

    if (document.getElementById('editOriginalCode')) document.getElementById('editOriginalCode').value = codeVal;
    if (document.getElementById('editCode')) document.getElementById('editCode').value = codeVal;
    if (document.getElementById('editName')) document.getElementById('editName').value = data.name || data["Product Name"] || '';
    if (document.getElementById('editCategory')) document.getElementById('editCategory').value = data.category || data["Category"] || '';
    if (document.getElementById('editPack')) document.getElementById('editPack').value = data.pack || data["Pack / Unit Type"] || '';
    if (document.getElementById('editPieces')) document.getElementById('editPieces').value = data.pieces || data["Pieces per Pack"] || 1;
    if (document.getElementById('editWholesale')) document.getElementById('editWholesale').value = data.wholesale || data["Wholesale Price per Pack (Rs)"] || 0;
    if (document.getElementById('editRetail')) document.getElementById('editRetail').value = data.retail || data["Suggested Retail Price per Piece (Rs)"] || 0;
    if (document.getElementById('editStock')) document.getElementById('editStock').value = data.stock || data["Stock Available (Packs)"] || 0;
    if (document.getElementById('editNotes')) document.getElementById('editNotes').value = data.notes || data["Notes"] || '';

    const previewImg = document.getElementById('editImgPreview');
    const imageFile = data.image || data["Image File"];
    if (previewImg) {
        previewImg.src = imageFile ? `/images/${imageFile}?t=${new Date().getTime()}` : 'https://placehold.co/120x120?text=No+Image';
    }

    const imgInput = document.getElementById('editImageInput');
    if (imgInput) imgInput.value = "";

    openModal('editModal');
}

// Submits updated product form data safely
async function saveProductUpdate(event) {
    event.preventDefault();

    const form = document.getElementById('editForm');
    const formData = new FormData(form);

    try {
        const response = await fetch(`${API_BASE_URL}/update_product`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok && data.success) {
            showToast("Success", data.message || "Product updated successfully!", "success");
            closeModal('editModal');
            setTimeout(() => location.reload(), 800);
        } else {
            showToast("Error", data.message || "Failed to update product details.", "error");
        }
    } catch (err) {
        console.error("Error updating product:", err);
        showToast("System Error", "Server error occurred while saving product.", "error");
    }
}

// Delete Product Handlers
let pendingDeleteCode = null;

function deleteProduct(code) {
    pendingDeleteCode = code;
    const deleteEl = document.getElementById('deleteProductCode');
    if (deleteEl) deleteEl.innerText = code;

    const confirmBtn = document.getElementById('confirmDeleteBtn');
    if (confirmBtn) confirmBtn.onclick = executeDeleteProduct;

    openModal('deleteModal');
}

function executeDeleteProduct() {
    if (!pendingDeleteCode) return;

    fetch(`${API_BASE_URL}/delete_product`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_code: pendingDeleteCode })
    })
    .then(res => res.json())
    .then(data => {
        closeModal('deleteModal');
        if (data.success) {
            showToast("Deleted", data.message, "success");
            setTimeout(() => location.reload(), 800);
        } else {
            showToast("Error", data.message || "Failed to delete product.", "error");
        }
    })
    .catch(() => {
        closeModal('deleteModal');
        showToast("System Error", "Failed to delete product.", "error");
    });
}


// ==========================================
// BULK SELECTION & ZIP EXPORT
// ==========================================
function toggleSelectAll(masterCheckbox) {
    const checkboxes = document.querySelectorAll('.product-checkbox');
    checkboxes.forEach(cb => cb.checked = masterCheckbox.checked);
    updateBulkExportButton();
}

function updateBulkExportButton() {
    const selected = document.querySelectorAll('.product-checkbox:checked');
    const bulkBtn = document.getElementById('bulkExportBtn');
    if (bulkBtn) {
        if (selected.length > 0) {
            bulkBtn.style.display = 'inline-flex';
            bulkBtn.innerHTML = `<i class="fa-solid fa-file-zipper"></i> Export Selected (${selected.length})`;
        } else {
            bulkBtn.style.display = 'none';
        }
    }
}

async function exportSelectedPNGs() {
    const selectedCheckboxes = document.querySelectorAll('.product-checkbox:checked');
    const selectedCodes = Array.from(selectedCheckboxes).map(cb => cb.value);

    if (selectedCodes.length === 0) {
        showToast("Warning", "Please select at least one product.", "warning");
        return;
    }

    const bulkBtn = document.getElementById('bulkExportBtn');
    if (bulkBtn) {
        bulkBtn.disabled = true;
        bulkBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Zipping Cards...`;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/api/export-pngs`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ product_codes: selectedCodes })
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.message || "Failed to generate ZIP archive.");
        }

        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = `product_cards_${new Date().toISOString().slice(0, 10)}.zip`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(downloadUrl);

        showToast("Success", "ZIP archive downloaded successfully!", "success");
    } catch (err) {
        console.error(err);
        showToast("Export Failed", err.message, "error");
    } finally {
        if (bulkBtn) {
            bulkBtn.disabled = false;
            updateBulkExportButton();
        }
    }
}


// ==========================================
// SITE PUBLISHING & NOTIFICATIONS
// ==========================================
function publishLiveSite() {
    const btn = document.querySelector('.btn-publish-header');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Publishing...';
    }

    fetch(`${API_BASE_URL}/publish_site`, { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '<i class="fa-solid fa-cloud-arrow-up"></i> Publish to Live Site';
            }

            const notifBadge = document.getElementById('notifBadge');
            const notifDropdown = document.querySelector('#notificationDropdown div[style*="max-height"]');

            if (data.success) {
                showToast("Publish Successful", "Product cards and static assets published successfully!", "success");

                if (notifBadge) {
                    notifBadge.textContent = "1";
                    notifBadge.style.display = "flex";
                }

                if (notifDropdown) {
                    notifDropdown.innerHTML = `
                        <div class="notif-item" style="padding: 12px 16px; border-bottom: 1px solid #f1f5f9; display: flex; gap: 12px; align-items: flex-start; background: #f0fdf4;">
                            <i class="fa-solid fa-circle-check" style="color: #16a34a; margin-top: 3px;"></i>
                            <div>
                                <div style="font-size: 12px; font-weight: 600; color: #0f172a;">Publish Success</div>
                                <div style="font-size: 11px; color: #64748b; margin-top: 2px;">Product cards built & live.</div>
                            </div>
                        </div>` + notifDropdown.innerHTML;
                }
            } else {
                showToast("Validation Error", data.message || "1 or more products missing mandatory fields.", "error");

                if (notifBadge) {
                    notifBadge.textContent = "1";
                    notifBadge.style.display = "flex";
                }

                if (notifDropdown) {
                    notifDropdown.innerHTML = `
                        <div class="notif-item" style="padding: 12px 16px; border-bottom: 1px solid #f1f5f9; display: flex; gap: 12px; align-items: flex-start; background: #fef2f2;">
                            <i class="fa-solid fa-circle-xmark" style="color: #dc2626; margin-top: 3px;"></i>
                            <div>
                                <div style="font-size: 12px; font-weight: 600; color: #991b1b;">Publish Failed</div>
                                <div style="font-size: 11px; color: #64748b; margin-top: 2px;">Product missing selling price in Excel.</div>
                            </div>
                        </div>` + notifDropdown.innerHTML;
                }
            }
        })
        .catch(err => {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '<i class="fa-solid fa-cloud-arrow-up"></i> Publish to Live Site';
            }
            showToast("System Error", "Failed to reach publish endpoint.", "error");
        });
}

function toggleNotifications(event) {
    if (event) event.stopPropagation();
    const dropdown = document.getElementById('notificationDropdown');
    if (!dropdown) return;

    dropdown.style.display = (dropdown.style.display === 'none' || dropdown.style.display === '') ? 'block' : 'none';
}

function clearNotifications() {
    const badge = document.getElementById('notifBadge');
    if (badge) badge.style.display = 'none';
    showToast("Notifications Read", "All system notifications marked as read.", "success");
}


// ==========================================
// UI HELPER & UTILITY FUNCTIONS
// ==========================================
function openImagePreview(imageSrc, captionText) {
    const modal = document.getElementById('imageZoomModal');
    const zoomImg = document.getElementById('zoomImage');
    const caption = document.getElementById('zoomCaption');

    if (!modal || !zoomImg) return;

    zoomImg.src = imageSrc;
    if (caption) caption.innerText = captionText || '';

    openModal('imageZoomModal');
}

function previewFormImage(input, previewElementId) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const previewEl = document.getElementById(previewElementId);
            if (previewEl) previewEl.src = e.target.result;
        };
        reader.readAsDataURL(input.files[0]);
    }
}

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const toggleIcon = document.querySelector('#sidebarToggle i');
    if (!sidebar) return;

    sidebar.classList.toggle('collapsed');
    if (toggleIcon) {
        toggleIcon.className = sidebar.classList.contains('collapsed') 
            ? 'fa-solid fa-chevron-right' 
            : 'fa-solid fa-chevron-left';
    }
}

function updateCalculatedPrice() {
    const wholesale = parseFloat(document.getElementById('wholesale_price')?.value) || 0;
    const pieces = parseFloat(document.getElementById('pieces_per_pack')?.value) || 0;
    const outputField = document.getElementById('price_per_piece');

    if (!outputField) return;

    if (pieces <= 0 || wholesale <= 0) {
        outputField.value = "0.00";
        return;
    }

    outputField.value = (wholesale / pieces).toFixed(2);
}

function showToast(title, message, type = 'success') {
    let container = document.getElementById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.style.cssText = `
            position: fixed;
            bottom: 24px;
            right: 24px;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            gap: 10px;
            max-width: 350px;
        `;
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    const isSuccess = type === 'success';
    const isWarning = type === 'warning';
    
    let bgColor = '#10b981';
    let iconClass = 'fa-circle-check';

    if (type === 'error') {
        bgColor = '#ef4444';
        iconClass = 'fa-circle-xmark';
    } else if (isWarning) {
        bgColor = '#f59e0b';
        iconClass = 'fa-triangle-exclamation';
    }

    toast.style.cssText = `
        background: #ffffff;
        border-left: 4px solid ${bgColor};
        padding: 14px 18px;
        border-radius: 8px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        display: flex;
        align-items: flex-start;
        gap: 12px;
        color: #1e293b;
        font-family: inherit;
        font-size: 13px;
        transition: all 0.3s ease;
    `;

    toast.innerHTML = `
        <i class="fa-solid ${iconClass}" style="color: ${bgColor}; font-size: 18px; margin-top: 2px;"></i>
        <div style="flex: 1;">
            <div style="font-weight: 600; color: #0f172a; margin-bottom: 2px;">${title}</div>
            <div style="color: #64748b; font-size: 12px; line-height: 1.4;">${message}</div>
        </div>
        <button onclick="removeToast(this.parentElement)" style="background: none; border: none; color: #94a3b8; cursor: pointer; padding: 0;">
            <i class="fa-solid fa-xmark"></i>
        </button>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        removeToast(toast);
    }, 3500);
}

function removeToast(toast) {
    if (!toast) return;
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => {
        if (toast.parentElement) {
            toast.remove();
        }
    }, 250);
}