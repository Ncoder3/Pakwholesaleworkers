document.addEventListener('DOMContentLoaded', () => {
    // Live Search Functionality
    const searchBox = document.getElementById('searchBox');
    if (searchBox) {
        searchBox.addEventListener('keyup', function () {
            const term = this.value.toLowerCase();
            const rows = document.querySelectorAll('#productTable tbody tr');

            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(term) ? '' : 'none';
            });
        });
    }

    // Modal Close Triggers
    window.addEventListener('click', (event) => {
        if (event.target.classList.contains('modal')) {
            event.target.style.display = 'none';
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

function showToast(title, message) {
    const toast = document.getElementById('toast');
    if (!toast) return;
    document.getElementById('toastTitle').innerText = title;
    document.getElementById('toastMessage').innerText = message;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 3000);
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