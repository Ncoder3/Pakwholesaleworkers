/*==========================================================
   AL BARAKA TRADERS - DIGITAL CATALOG
   INDEX PAGE JAVASCRIPT ENGINE
==========================================================*/

document.addEventListener("DOMContentLoaded", function () {
    "use strict";

    // ------------------------------------------------------
    // DOM ELEMENTS SETUP
    // ------------------------------------------------------
    const searchBox = document.getElementById("searchBox");
    const filterButtons = document.querySelectorAll(".filter");
    const productCards = document.querySelectorAll(".product-card");

    const cartToggleBtn = document.getElementById("cartToggleBtn");
    const closeCartBtn = document.getElementById("closeCartBtn");
    const cartModal = document.getElementById("cartModal");
    const cartOverlay = document.getElementById("cartOverlay");
    const cartCountEl = document.getElementById("cartCount");
    const cartItemsListEl = document.getElementById("cartItemsList");
    const summaryTotalItemsEl = document.getElementById("summaryTotalItems");
    const summaryTotalPriceEl = document.getElementById("summaryTotalPrice");
    const checkoutForm = document.getElementById("checkoutForm");

    // Dynamic State Management
    let cart = JSON.parse(localStorage.getItem("abt_wholesale_cart")) || [];

    // ------------------------------------------------------
    // UTILITY FUNCTIONS
    // ------------------------------------------------------

    // HTML Escape Helper (Security/XSS Prevention)
    function escapeHtml(str) {
        if (!str) return "";
        return String(str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // Price Parser
    function parsePrice(priceStr) {
        if (!priceStr) return 0;
        return parseFloat(String(priceStr).replace(/,/g, "")) || 0;
    }

    // Non-blocking Toast Notification Component
    function showToast(message, type = "success") {
        let toastContainer = document.getElementById("toastContainer");
        
        if (!toastContainer) {
            toastContainer = document.createElement("div");
            toastContainer.id = "toastContainer";
            Object.assign(toastContainer.style, {
                position: "fixed",
                bottom: "24px",
                right: "24px",
                zIndex: "9999",
                display: "flex",
                flexDirection: "column",
                gap: "10px",
                pointerEvents: "none"
            });
            document.body.appendChild(toastContainer);
        }

        const toast = document.createElement("div");
        toast.className = `toast toast-${type}`;
        toast.innerText = message;
        
        Object.assign(toast.style, {
            background: type === "error" ? "#EF4444" : "#0B7D5A",
            color: "#ffffff",
            padding: "14px 22px",
            borderRadius: "12px",
            boxShadow: "0 10px 25px rgba(0,0,0,0.15)",
            fontSize: "14px",
            fontWeight: "600",
            opacity: "0",
            transform: "translateY(20px)",
            transition: "all 0.3s cubic-bezier(0.16, 1, 0.3, 1)",
            pointerEvents: "auto"
        });

        toastContainer.appendChild(toast);

        // Animate In
        requestAnimationFrame(() => {
            toast.style.opacity = "1";
            toast.style.transform = "translateY(0)";
        });

        // Auto Dismiss
        setTimeout(() => {
            toast.style.opacity = "0";
            toast.style.transform = "translateY(10px)";
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // Debounce Wrapper for Search Input
    function debounce(func, delay = 200) {
        let timeout;
        return (...args) => {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), delay);
        };
    }

    // ------------------------------------------------------
    // 1. SEARCH & CATEGORY FILTER
    // ------------------------------------------------------
    function filterProducts() {
        const query = searchBox ? searchBox.value.toLowerCase().trim() : "";
        const activeFilter = document.querySelector(".filter.active");
        const selectedCategory = activeFilter ? activeFilter.getAttribute("data-category") : "All";

        productCards.forEach(card => {
            const category = card.getAttribute("data-category") || "";
            const name = (card.getAttribute("data-name") || "").toLowerCase();

            const matchesSearch = name.includes(query);
            const matchesCategory = (selectedCategory === "All") || (category === selectedCategory);

            if (matchesSearch && matchesCategory) {
                card.style.display = "flex";
            } else {
                card.style.display = "none";
            }
        });
    }

    if (searchBox) {
        searchBox.addEventListener("input", debounce(filterProducts, 200));
    }

    filterButtons.forEach(button => {
        button.addEventListener("click", function () {
            filterButtons.forEach(btn => btn.classList.remove("active"));
            this.classList.add("active");
            filterProducts();
        });
    });

    // ------------------------------------------------------
    // 2. CART MANAGEMENT & STORAGE
    // ------------------------------------------------------
    function saveCart() {
        localStorage.setItem("abt_wholesale_cart", JSON.stringify(cart));
        renderCart();
    }

    function renderCart() {
        let totalPacks = 0;
        let totalPrice = 0;

        if (!cartItemsListEl) return;
        cartItemsListEl.innerHTML = "";

        if (cart.length === 0) {
            cartItemsListEl.innerHTML = `
                <div style="text-align:center; padding: 40px 10px; color: #64748B;">
                    <p style="font-size: 16px; font-weight:600; margin-bottom:6px;">Your cart is empty</p>
                    <p style="font-size: 13px;">Add products from the catalog to place an order.</p>
                </div>
            `;
        } else {
            cart.forEach((item, index) => {
                const itemPrice = parsePrice(item.price);
                const lineTotal = itemPrice * item.quantity;
                totalPacks += item.quantity;
                totalPrice += lineTotal;

                const itemRow = document.createElement("div");
                itemRow.className = "cart-item-row";
                itemRow.innerHTML = `
                    <img src="${escapeHtml(item.image || 'placeholder.jpg')}" alt="${escapeHtml(item.name)}" class="cart-item-img">
                    <div class="cart-item-details">
                        <h4>${escapeHtml(item.name)}</h4>
                        <p>Rs ${itemPrice.toLocaleString('en-PK', { minimumFractionDigits: 2 })} / pack</p>
                        <div class="cart-qty-ctrl">
                            <button class="cart-qty-btn" data-action="decrease" data-index="${index}">-</button>
                            <span>${item.quantity}</span>
                            <button class="cart-qty-btn" data-action="increase" data-index="${index}">+</button>
                        </div>
                    </div>
                    <div class="cart-item-right">
                        <span class="line-total">Rs ${lineTotal.toLocaleString('en-PK', { minimumFractionDigits: 2 })}</span>
                        <button class="remove-item-btn" data-action="remove" data-index="${index}" title="Remove item">&times;</button>
                    </div>
                `;
                cartItemsListEl.appendChild(itemRow);
            });
        }

        if (cartCountEl) cartCountEl.innerText = totalPacks;
        if (summaryTotalItemsEl) summaryTotalItemsEl.innerText = totalPacks;
        if (summaryTotalPriceEl) {
            summaryTotalPriceEl.innerText = totalPrice.toLocaleString('en-PK', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            });
        }
    }

    // Delegated Cart Actions (Increments, Decrements, Removals)
    if (cartItemsListEl) {
        cartItemsListEl.addEventListener("click", function (e) {
            const target = e.target.closest("[data-action]");
            if (!target) return;

            const action = target.getAttribute("data-action");
            const index = parseInt(target.getAttribute("data-index"), 10);

            if (isNaN(index) || !cart[index]) return;

            if (action === "increase") {
                cart[index].quantity += 1;
            } else if (action === "decrease") {
                cart[index].quantity -= 1;
                if (cart[index].quantity <= 0) {
                    cart.splice(index, 1);
                }
            } else if (action === "remove") {
                cart.splice(index, 1);
            }

            saveCart();
        });
    }

    // Product Card Quantity Controls (+/-)
    document.querySelectorAll(".qty-btn").forEach(btn => {
        btn.addEventListener("click", function (e) {
            e.preventDefault();
            const code = this.getAttribute("data-code");
            const input = document.getElementById(`qty-${code}`);
            if (input) {
                let val = parseInt(input.value, 10) || 1;
                if (this.classList.contains("plus-btn")) {
                    val++;
                } else if (this.classList.contains("minus-btn") && val > 1) {
                    val--;
                }
                input.value = val;
            }
        });
    });

    // Add to Cart Button Handlers
    document.querySelectorAll(".add-to-cart-btn").forEach(btn => {
        btn.addEventListener("click", function (e) {
            e.preventDefault();
            const code = this.getAttribute("data-code");
            const name = this.getAttribute("data-name");
            const price = this.getAttribute("data-price");
            const image = this.getAttribute("data-image");
            const qtyInput = document.getElementById(`qty-${code}`);
            const qty = qtyInput ? (parseInt(qtyInput.value, 10) || 1) : 1;

            const existingIndex = cart.findIndex(item => item.code === code);
            if (existingIndex > -1) {
                cart[existingIndex].quantity += qty;
            } else {
                cart.push({
                    code: code,
                    name: name,
                    price: price,
                    image: image,
                    quantity: qty
                });
            }

            saveCart();
            showToast(`Added ${qty} pack(s) of "${name}" to cart.`, "success");
        });
    });

    // ------------------------------------------------------
    // 3. CART MODAL TOGGLE & ACCESSIBILITY
    // ------------------------------------------------------
    function openCart() {
        if (cartModal) cartModal.classList.add("open");
        if (cartOverlay) cartOverlay.classList.add("active");
        document.body.style.overflow = "hidden"; // Lock background scroll
    }

    function closeCart() {
        if (cartModal) cartModal.classList.remove("open");
        if (cartOverlay) cartOverlay.classList.remove("active");
        document.body.style.overflow = ""; // Restore background scroll
    }

    // Event Bindings
    if (cartOverlay) cartOverlay.addEventListener("click", closeCart);
    if (cartToggleBtn) cartToggleBtn.addEventListener("click", openCart);
    if (closeCartBtn) closeCartBtn.addEventListener("click", closeCart);

    // Close on ESC Key
    document.addEventListener("keydown", function (e) {
        if (e.key === "Escape" && cartModal && cartModal.classList.contains("open")) {
            closeCart();
        }
    });

    // ------------------------------------------------------
    // 4. CHECKOUT FORM SUBMISSION & ADMIN SYNC
    // ------------------------------------------------------
    if (checkoutForm) {
        checkoutForm.addEventListener("submit", async function (e) {
            e.preventDefault();

            if (cart.length === 0) {
                showToast("Your cart is empty. Please add items before placing an order.", "error");
                return;
            }

            const customerDetails = {
                name: document.getElementById("custName") ? document.getElementById("custName").value.trim() : "",
                phone: document.getElementById("custPhone") ? document.getElementById("custPhone").value.trim() : "",
                address: document.getElementById("custAddress") ? document.getElementById("custAddress").value.trim() : ""
            };

            const submitBtn = document.getElementById("submitOrderBtn");
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerText = "Submitting Order...";
            }

            const success = await sendOrderToAdminDashboard(customerDetails, cart);

            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerText = "Place Wholesale Order";
            }

            if (success) {
                cart = [];
                saveCart();
                checkoutForm.reset();
                closeCart();
            }
        });
    }

    // Initial render call
    renderCart();
});

function openAboutModal() {
    alert("Al Baraka Traders\n\nYour trusted wholesale distributor for high-quality items in Shah Alam Market, Lahore.");
}

// ==========================================================
// ADMIN DASHBOARD SYNC FUNCTION
// ==========================================================
async function sendOrderToAdminDashboard(customerDetails, cartItems) {
    // Local Testing Fallback
    if (window.location.protocol === "file:") {
        console.log("Local Order Test Payload:", { customer: customerDetails, items: cartItems });
        alert(`Order Placed Locally!\n\nCustomer: ${customerDetails.name}\nTotal Unique Items: ${cartItems.length}`);
        return true;
    }

    const payload = {
        customer: customerDetails,
        items: cartItems.map(item => ({
            product_code: item.code,
            product_name: item.name,
            packs: item.quantity,
            price: item.price
        }))
    };

    try {
        const response = await fetch("/api/orders/create", {
            method: "POST",
            headers: { 
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error(`Server responded with status code ${response.status}`);
        }

        const data = await response.json();

        if (data.success) {
            alert("Order placed successfully! Order ID: " + (data.order_id || "N/A"));
            return true;
        } else {
            alert("Order submission failed: " + (data.message || "Unknown error occurred."));
            return false;
        }
    } catch (error) {
        console.error("Backend Communication Error:", error);
        alert("Unable to communicate with the store server. Please check your network connection.");
        return false;
    }
}