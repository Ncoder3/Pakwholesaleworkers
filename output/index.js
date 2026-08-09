document.addEventListener("DOMContentLoaded", function () {
    const searchBox = document.getElementById("searchBox");
    const filterButtons = document.querySelectorAll(".filter");
    const productCards = document.querySelectorAll(".product-card");

    function filterProducts() {
        const query = searchBox ? searchBox.value.toLowerCase().trim() : "";
        const activeFilter = document.querySelector(".filter.active");
        const selectedCategory = activeFilter ? activeFilter.getAttribute("data-category") : "All";

        productCards.forEach(card => {
            const category = card.getAttribute("data-category") || "";
            const name = card.getAttribute("data-name") || "";

            const matchesSearch = name.includes(query);
            const matchesCategory = (selectedCategory === "All") || (category === selectedCategory);

            if (matchesSearch && matchesCategory) {
                card.style.display = "flex";
            } else {
                card.style.display = "none";
            }
        });
    }

    // Attach search input event
    if (searchBox) {
        searchBox.addEventListener("input", filterProducts);
    }

    // Attach category filter button events
    filterButtons.forEach(button => {
        button.addEventListener("click", function () {
            filterButtons.forEach(btn => btn.classList.remove("active"));
            this.classList.add("active");
            filterProducts();
        });
    });
    // EXAMPLE: Attach this call inside your checkout form submit event handler
    // const checkoutForm = document.getElementById("checkoutForm");
    // if (checkoutForm) {
    //     checkoutForm.addEventListener("submit", async function (e) {
    //         e.preventDefault();
    //         const customerDetails = {
    //             name: document.getElementById("custName").value,
    //             phone: document.getElementById("custPhone").value,
    //             address: document.getElementById("custAddress").value
    //         };
    //         // Pass customer details and cart items array to the API sync function
    //         await sendOrderToAdminDashboard(customerDetails, cartItems);
    //     });
    // }
});

// ==========================================================
// ADMIN DASHBOARD SYNC FUNCTION
// ==========================================================
async function sendOrderToAdminDashboard(customerDetails, cartItems) {
    // Replace with your Flask server URL or Cloudflare Tunnel endpoint
    const ADMIN_API_URL = "https://your-admin-domain.com/api/orders/create";

    const payload = {
        customer: {
            name: customerDetails.name,
            phone: customerDetails.phone,
            address: customerDetails.address
        },
        items: cartItems.map(item => ({
            product_code: item.code, // Matches ABT-001 format
            packs: item.quantity
        }))
    };

    try {
        const response = await fetch(ADMIN_API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await response.json();
        if (data.success) {
            alert("Order placed successfully! Order ID: " + data.order_id);
        } else {
            alert("Order failed: " + data.message);
        }
    } catch (error) {
        console.error("Sync error:", error);
        alert("Could not communicate with store server.");
    }
}