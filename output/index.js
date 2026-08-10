/*==========================================================
   AL BARAKA TRADERS - DIGITAL CATALOG
   INDEX PAGE JAVASCRIPT ENGINE
==========================================================*/
// templates/Index/index.js & output/index.js

const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://127.0.0.1:5000'
    : 'https://pakwholesaleworkers.up.railway.app';

// ------------------------------------------------------
// UTILITY HELPERS (GLOBAL SCOPE)
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

// Price Parser Helper
function parsePrice(priceStr) {
    if (!priceStr) return 0;
    return parseFloat(String(priceStr).replace(/,/g, "")) || 0;
}

// ------------------------------------------------------
// CUSTOM SUCCESS MODAL & WHATSAPP INTEGRATION
// ------------------------------------------------------
function showOrderSuccessModal(orderId, customerDetails, cartItems) {
    // 1. Calculate Total Amount
    let totalAmount = 0;
    cartItems.forEach(item => {
        const price = parsePrice(item.price);
        totalAmount += price * item.quantity;
    });

    // 2. Format WhatsApp Order Summary Message
    let itemDetailsText = cartItems.map((item, idx) => 
        `${idx + 1}. *${item.name}* (Qty: ${item.quantity} packs) - Rs ${item.price}`
    ).join("\n");

    const whatsappMessage = 
`*NEW ORDER PAYMENT REQUEST - AL BARAKA TRADERS*
----------------------------------
*Order ID:* ${orderId}
*Customer:* ${customerDetails.name}
*Phone:* ${customerDetails.phone}
${customerDetails.city ? `*City:* ${customerDetails.city}\n` : ""}${customerDetails.state ? `*State/Province:* ${customerDetails.state}\n` : ""}*Address:* ${customerDetails.address}

*Order Items:*
${itemDetailsText}

*Total Amount:* Rs ${totalAmount.toLocaleString('en-PK')}
----------------------------------
Hello, I would like to proceed with payment for my order *${orderId}*. Please share online payment details.`;

    const encodedMessage = encodeURIComponent(whatsappMessage);
    const whatsappPhone = "923231551535";
    const whatsappUrl = `https://wa.me/${whatsappPhone}?text=${encodedMessage}`;

    // 3. Create or Reuse Modal Element
    let modalOverlay = document.getElementById("orderSuccessModal");
    if (!modalOverlay) {
        modalOverlay = document.createElement("div");
        modalOverlay.id = "orderSuccessModal";
        modalOverlay.className = "abt-modal-overlay";
        document.body.appendChild(modalOverlay);
    }

    // Dynamic location row formatting for the modal
    const locationString = [customerDetails.city, customerDetails.state].filter(Boolean).join(", ");

    // 4. Inject Modal Markup
    modalOverlay.innerHTML = `
        <div class="abt-modal-card">
            <div class="abt-modal-icon">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#0B7D5A" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
            </div>
            <h2 class="abt-modal-title">Order Placed Successfully!</h2>
            <p class="abt-modal-subtitle">Thank you for your order. Your Order ID is <strong>${escapeHtml(orderId)}</strong>.</p>
            
            <div class="abt-modal-summary">
                <div class="abt-summary-row">
                    <span>Customer:</span>
                    <strong>${escapeHtml(customerDetails.name)}</strong>
                </div>
                ${locationString ? `
                <div class="abt-summary-row">
                    <span>Location:</span>
                    <strong>${escapeHtml(locationString)}</strong>
                </div>
                ` : ""}
                <div class="abt-summary-row">
                    <span>Total Amount:</span>
                    <strong>Rs ${totalAmount.toLocaleString('en-PK', { minimumFractionDigits: 2 })}</strong>
                </div>
            </div>

            <div class="abt-modal-actions">
                <a href="${whatsappUrl}" target="_blank" class="abt-btn-whatsapp" onclick="closeOrderSuccessModal()">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M.057 24l1.687-6.163c-1.041-1.804-1.588-3.849-1.587-5.946.003-6.556 5.338-11.891 11.893-11.891 3.181.001 6.167 1.24 8.413 3.488 2.245 2.248 3.481 5.236 3.48 8.414-.003 6.557-5.338 11.892-11.893 11.892-1.99-.001-3.951-.5-5.688-1.448l-6.305 1.654zm6.597-3.807c1.676.995 3.276 1.591 5.392 1.592 5.448 0 9.886-4.434 9.889-9.885.002-5.462-4.415-9.89-9.881-9.892-5.452 0-9.887 4.434-9.889 9.884-.001 2.225.651 3.891 1.746 5.634l-.999 3.648 3.742-.981zm11.387-5.464c-.074-.124-.272-.198-.57-.347-.297-.149-1.758-.868-2.031-.967-.272-.099-.47-.149-.669.149-.198.297-.768.967-.941 1.165-.173.198-.347.223-.644.074-.297-.149-1.255-.462-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.297-.347.446-.521.151-.172.2-.296.3-.495.099-.198.05-.372-.025-.521-.075-.148-.669-1.611-.916-2.206-.242-.579-.487-.501-.669-.51l-.57-.01c-.198 0-.52.074-.792.372s-1.04 1.016-1.04 2.479 1.065 2.876 1.213 3.074c.149.198 2.095 3.2 5.076 4.487.709.306 1.263.489 1.694.626.712.226 1.36.194 1.872.118.571-.085 1.758-.719 2.006-1.413.248-.695.248-1.29.173-1.414z"/>
                    </svg>
                    Proceed to Pay via WhatsApp
                </a>
                <button type="button" class="abt-btn-secondary" onclick="closeOrderSuccessModal()">Close</button>
            </div>
        </div>
    `;

    requestAnimationFrame(() => {
        modalOverlay.classList.add("active");
    });
}

function closeOrderSuccessModal() {
    const modalOverlay = document.getElementById("orderSuccessModal");
    if (modalOverlay) {
        modalOverlay.classList.remove("active");
    }
}

// ------------------------------------------------------
// MAIN APPLICATION ENGINE
// ------------------------------------------------------
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
                        <button class="remove-item-btn" data-action="remove" data-index="${index}" title="Remove item">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <polyline points="3 6 5 6 21 6"></polyline>
                                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                                <line x1="10" y1="11" x2="10" y2="17"></line>
                                <line x1="14" y1="11" x2="14" y2="17"></line>
                            </svg>
                        </button>
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
                city: document.getElementById("custCity") ? document.getElementById("custCity").value.trim() : "",
                state: document.getElementById("custState") ? document.getElementById("custState").value.trim() : "",
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
        showOrderSuccessModal("ORD-LOCAL-TEST", customerDetails, cartItems);
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
        const response = await fetch(`${API_BASE_URL}/api/orders/create`, {
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
            showOrderSuccessModal(data.order_id || "ORD-SUCCESS", customerDetails, cartItems);
            return true;
        } else {
            showToast("Order submission failed: " + (data.message || "Unknown error occurred."), "error");
            return false;
        }
    } catch (error) {
        console.error("Backend Communication Error:", error);
        showToast("Unable to communicate with the store server. Please check your network connection.", "error");
        return false;
    }
}