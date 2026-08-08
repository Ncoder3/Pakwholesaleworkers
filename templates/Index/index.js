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
});