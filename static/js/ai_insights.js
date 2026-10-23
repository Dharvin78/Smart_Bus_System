
document.addEventListener("DOMContentLoaded", function () {

    const dashboard = document.getElementById("aiBusinessInsights");

    if (!dashboard) return;

    const buttons = dashboard.querySelectorAll(".ai-filter-btn");
    const cards = dashboard.querySelectorAll(".ai-insight-card");
    const emptyMessage = document.getElementById("aiNoFilterResults");

    buttons.forEach(function (button) {

        button.addEventListener("click", function () {

            const selectedFilter = button.dataset.filter;

            buttons.forEach(function (btn) {
                btn.classList.remove("active");
            });

            button.classList.add("active");

            let visibleCount = 0;

            cards.forEach(function (card) {

                const category = (card.dataset.category || "").toLowerCase();

                const shouldShow =
                    selectedFilter === "all" ||
                    category.includes(selectedFilter);

                card.hidden = !shouldShow;

                if (shouldShow) {
                    visibleCount++;
                }

            });

            if (emptyMessage) {
                emptyMessage.hidden = visibleCount !== 0;
            }

        });

    });

});
