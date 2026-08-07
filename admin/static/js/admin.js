document.addEventListener('DOMContentLoaded', () => {
    // Live Search Functionality
    const searchBox = document.getElementById('searchBox') || document.getElementById('searchInput');
    if (searchBox) {
        searchBox.addEventListener('input', function () {
            const term = this.value.toLowerCase().trim();
            // Target all table rows except any existing no-results row
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

            // Handle "No Results" cleanly inside the table body (no floating white boxes)
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

    // Modal Close Triggers
    window.addEventListener('click', (event) => {
        if (event.target.classList.contains('modal')) {
            event.target.style.display = 'none';
        }
    });

    // Sidebar active link highlighting
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.sidebar nav a');
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.style.background = 'var(--primary-hover)';
            link.style.color = '#ffffff';
        }
    });
});

function openModal(id) {
    document.getElementById(id).style.display = 'flex';
}

function closeModal(id) {
    document.getElementById(id).style.display = 'none';
}

function viewProduct(button) {
    const data = button.dataset;
    document.getElementById('modalImage').src = '/images/' + data.image;
    document.getElementById('modalName').innerText = data.name;
    document.getElementById('modalCode').innerText = data.code;
    document.getElementById('modalCategory').innerText = data.category;
    document.getElementById('modalPack').innerText = data.pack;
    document.getElementById('modalPieces').innerText = data.pieces;
    document.getElementById('modalWholesale').innerText = data.wholesale;
    document.getElementById('modalRetail').innerText = data.retail;
    document.getElementById('modalStock').innerText = data.stock;
    document.getElementById('modalNotes').innerText = data.notes || 'None';

    openModal('productModal');
}

function openAddModal() {
    document.getElementById('addForm').reset();
    openModal('addModal');
}

function saveNewProduct(event) {
    event.preventDefault();

    const form = document.getElementById('addForm');
    const formData = new FormData(form);

    // Explicitly append the file input if it wasn't captured automatically
    const imageInput = document.getElementById('addImageInput');
    if (imageInput && imageInput.files[0]) {
        formData.append('product_image', imageInput.files[0]);
    }

    fetch('/add_product', {
        method: 'POST',
        body: formData // Sends multipart/form-data with text inputs + image file
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showToast("Success", data.message);
            closeModal('addModal');
            setTimeout(() => location.reload(), 800);
        } else {
            alert(data.message || "Failed to add product");
        }
    })
    .catch(error => {
        console.error("Error adding product:", error);
        alert("An error occurred while saving the product.");
    });
}

// function saveNewProduct(event) {
//     event.preventDefault();

//     const product = {
//         "Product Code": document.getElementById('addCode').value,
//         "Product Name": document.getElementById('addName').value,
//         "Category": document.getElementById('addCategory').value,
//         "Pack / Unit Type": document.getElementById('addPack').value,
//         "Pieces per Pack": document.getElementById('addPieces').value,
//         "Wholesale Price per Pack (Rs)": document.getElementById('addWholesale').value,
//         "Suggested Retail Price per Piece (Rs)": document.getElementById('addRetail').value,
//         "Stock Available (Packs)": document.getElementById('addStock').value,
//         "Notes": document.getElementById('addNotes').value
//     };

//     fetch('/add_product', {
//         method: 'POST',
//         headers: { 'Content-Type': 'application/json' },
//         body: JSON.stringify(product)
//     })
//     .then(res => res.json())
//     .then(data => {
//         if (data.success) {
//             showToast("Success", data.message);
//             closeModal('addModal');
//             setTimeout(() => location.reload(), 800);
//         } else {
//             alert(data.message);
//         }
//     });
// }

function publishLiveSite() {
    if (!confirm("Are you sure you want to regenerate the catalog and publish changes live?")) {
        return;
    }

    showToast("Publishing...", "Regenerating catalog and pushing to Cloudflare. Please wait...", "warning");

    fetch('/publish_site', {
        method: 'POST'
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showToast("Site Published!", data.message, "success");
        } else {
            showToast("Publish Failed", data.message, "error");
        }
    })
    .catch(err => {
        console.error(err);
        showToast("Error", "Failed to connect to backend server.", "error");
    });
}

// Toggle Notifications Dropdown
function toggleNotifications(event) {
    event.stopPropagation();
    const dropdown = document.getElementById('notificationDropdown');
    if (!dropdown) return;

    if (dropdown.style.display === 'none' || dropdown.style.display === '') {
        dropdown.style.display = 'block';
    } else {
        dropdown.style.display = 'none';
    }
}

// Clear Badge and Hide Notifications
function clearNotifications() {
    const badge = document.getElementById('notifBadge');
    if (badge) badge.style.display = 'none';
    showToast("Notifications Read", "All system notifications marked as read.", "success");
}

// Close dropdown when clicking outside
window.addEventListener('click', (event) => {
    const dropdown = document.getElementById('notificationDropdown');
    const notifBtn = document.getElementById('notificationBtn');
    if (dropdown && !dropdown.contains(event.target) && event.target !== notifBtn) {
        dropdown.style.display = 'none';
    }
});

function publishLiveSite() {
    const btn = document.querySelector('.btn-publish-header');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Publishing...';
    }

    fetch('/publish_site', { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '<i class="fa-solid fa-cloud-arrow-up"></i> Publish to Live Site';
            }

            // Update Notification Bell Badge Count & Item
            const notifBadge = document.getElementById('notifBadge');
            const notifDropdown = document.querySelector('#notificationDropdown div[style*="max-height"]');

            if (data.success) {
                showToast("Publish Successful", "All 41 product cards and static assets published successfully!", "success");
                
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
                                <div style="font-size: 11px; color: #64748b; margin-top: 2px;">41 Product cards built & live.</div>
                            </div>
                        </div>` + notifDropdown.innerHTML;
                }
            } else {
                showToast("Validation Error", data.message || "1 or more products missing price or mandatory fields.", "error");

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

function editProduct(button) {
    const data = button.dataset;
    document.getElementById('editCode').value = data.code;
    document.getElementById('editName').value = data.name;
    document.getElementById('editCategory').value = data.category;
    document.getElementById('editPack').value = data.pack;
    document.getElementById('editPieces').value = data.pieces;
    document.getElementById('editWholesale').value = data.wholesale;
    document.getElementById('editRetail').value = data.retail;
    document.getElementById('editStock').value = data.stock;
    document.getElementById('editNotes').value = data.notes;

    openModal('editModal');
}

function saveProductEdit(event) {
    event.preventDefault();

    const product = {
        "Product Code": document.getElementById('editCode').value,
        "Product Name": document.getElementById('editName').value,
        "Category": document.getElementById('editCategory').value,
        "Pack / Unit Type": document.getElementById('editPack').value,
        "Pieces per Pack": document.getElementById('editPieces').value,
        "Wholesale Price per Pack (Rs)": document.getElementById('editWholesale').value,
        "Suggested Retail Price per Piece (Rs)": document.getElementById('editRetail').value,
        "Stock Available (Packs)": document.getElementById('editStock').value,
        "Notes": document.getElementById('editNotes').value
    };

    fetch('/update_product', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(product)
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showToast("Updated", data.message);
            closeModal('editModal');
            setTimeout(() => location.reload(), 800);
        } else {
            alert(data.message);
        }
    });
}

let pendingDeleteCode = null;

// Opens custom delete confirmation modal
function deleteProduct(code) {
    pendingDeleteCode = code;
    document.getElementById('deleteProductCode').innerText = code;
    
    // Bind click event to confirm button dynamically
    const confirmBtn = document.getElementById('confirmDeleteBtn');
    confirmBtn.onclick = executeDeleteProduct;
    
    openModal('deleteModal');
}

// Handles actual deletion via API call
function executeDeleteProduct() {
    if (!pendingDeleteCode) return;

    fetch('/delete_product', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_code: pendingDeleteCode })
    })
    .then(res => res.json())
    .then(data => {
        closeModal('deleteModal');
        if (data.success) {
            showToast("Deleted", data.message);
            setTimeout(() => location.reload(), 800);
        } else {
            alert(data.message);
        }
    })
    .catch(() => {
        closeModal('deleteModal');
        alert("Failed to delete product.");
    });
}

// Opens the Image Zoom Modal with the target image and caption
function openImagePreview(imageSrc, captionText) {
    const modal = document.getElementById('imageZoomModal');
    const zoomImg = document.getElementById('zoomImage');
    const caption = document.getElementById('zoomCaption');

    if (!modal || !zoomImg) {
        console.error("Image zoom modal or image element missing in HTML");
        return;
    }

    zoomImg.src = imageSrc;
    if (caption) {
        caption.innerText = captionText || '';
    }

    // Force display style for modal opening
    modal.style.display = 'flex';
}

// Global modal close helper
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
    }
}

// Close zoom modal when clicking on the dark background
window.addEventListener('click', function(event) {
    const zoomModal = document.getElementById('imageZoomModal');
    if (event.target === zoomModal) {
        closeModal('imageZoomModal');
    }
});


// Function to dynamically render image previews when selecting a new file
function previewFormImage(input, previewElementId) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById(previewElementId).src = e.target.result;
        };
        reader.readAsDataURL(input.files[0]);
    }
}

// Function triggered when clicking the "Edit" button on a product row
function openEditModal(productData) {
    document.getElementById('editOriginalCode').value = productData["Product Code"] || "";
    document.getElementById('editCode').value = productData["Product Code"] || "";
    document.getElementById('editName').value = productData["Product Name"] || "";
    document.getElementById('editCategory').value = productData["Category"] || "";
    document.getElementById('editPack').value = productData["Pack / Unit Type"] || "";
    document.getElementById('editPieces').value = productData["Pieces per Pack"] || 1;
    document.getElementById('editWholesale').value = productData["Wholesale Price per Pack (Rs)"] || 0;
    document.getElementById('editRetail').value = productData["Suggested Retail Price per Piece (Rs)"] || 0;
    document.getElementById('editStock').value = productData["Stock Available (Packs)"] || 0;
    document.getElementById('editNotes').value = productData["Notes"] || "";

    // Set existing image or default placeholder
    const previewImg = document.getElementById('editImgPreview');
    if (productData["Image File"]) {
        previewImg.src = `/images/${productData["Image File"]}?t=${new Date().getTime()}`;
    } else {
        previewImg.src = "https://placehold.co/120x120?text=No+Image";
    }

    // Reset file input selection
    document.getElementById('editImageInput').value = "";

    // Open Modal
    document.getElementById('editModal').style.display = 'block';
}

// Function handling the form submission for updates
function saveProductUpdate(event) {
    event.preventDefault();

    const form = document.getElementById('editForm');
    const formData = new FormData(form);

    fetch('/update_product', {
        method: 'POST',
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showToast("Success", data.message);
            closeModal('editModal');
            setTimeout(() => location.reload(), 800);
        } else {
            alert(data.message || "Failed to update product.");
        }
    })
    .catch(error => {
        console.error("Error updating product:", error);
        alert("An error occurred while updating product.");
    });
}

// Highlight active page link in sidebar based on URL
document.addEventListener('DOMContentLoaded', () => {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.sidebar nav a');

    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.style.background = 'var(--primary-hover)';
            link.style.color = '#ffffff';
        }
    });
});

// Professional Toast Notification Function
function showToast(title, message, type = 'success') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    let iconClass = 'fa-circle-check';
    if (type === 'error') iconClass = 'fa-circle-xmark';
    if (type === 'warning') iconClass = 'fa-triangle-exclamation';

    toast.innerHTML = `
        <div class="toast-icon"><i class="fa-solid ${iconClass}"></i></div>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-message">${message}</div>
        </div>
        <button class="toast-close" onclick="removeToast(this.parentElement)">&times;</button>
    `;

    container.appendChild(toast);

    // Auto-remove toast after 3.5 seconds
    setTimeout(() => {
        removeToast(toast);
    }, 3500);
}

function removeToast(toast) {
    if (!toast) return;
    toast.style.animation = 'toastSlideOut 0.25s forwards';
    setTimeout(() => {
        if (toast.parentElement) {
            toast.remove();
        }
    }, 250);
}

// Fixed saveNewProduct function
function saveNewProduct(event) {
    event.preventDefault();

    const form = document.getElementById('addForm');
    const submitBtn = form.querySelector('button[type="submit"]');
    const codeInput = document.getElementById('addCode');

    // Reset previous error highlighting
    if (codeInput) {
        codeInput.style.borderColor = '';
    }

    // Disable button to prevent double submits during fetch
    if (submitBtn) submitBtn.disabled = true;

    const formData = new FormData(form);

    fetch('/add_product', {
        method: 'POST',
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        // Re-enable submit button immediately
        if (submitBtn) submitBtn.disabled = false;

        if (data.success) {
            showToast("Success", data.message, "success");
            closeModal('addModal');
            setTimeout(() => location.reload(), 800);
        } else {
            // Display professional UI Toast for errors
            showToast("Action Required", data.message, "error");

            // If duplicate product code, highlight input & give focus
            if (codeInput) {
                codeInput.removeAttribute('readonly');
                codeInput.removeAttribute('disabled');
                codeInput.style.borderColor = '#ef4444';
                codeInput.focus();
                codeInput.select(); // Select existing value so user can directly overwrite
            }
        }
    })
    .catch(error => {
        console.error("Error adding product:", error);
        if (submitBtn) submitBtn.disabled = false;
        showToast("System Error", "An unexpected error occurred while saving.", "error");
    });
}