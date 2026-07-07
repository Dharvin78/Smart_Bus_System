document.addEventListener("DOMContentLoaded", function () {

    // Revenue Chart
    const revenueCanvas = document.getElementById("revenueChart");

    if (revenueCanvas) {
        new Chart(revenueCanvas, {
            type: "line",
            data: {
                labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
                datasets: [{
                    label: "Revenue",
                    data: [12000, 19000, 15000, 22000, 27000, 32000],
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }

    // Booking Chart
    const bookingCanvas = document.getElementById("bookingChart");

    if (bookingCanvas) {
        new Chart(bookingCanvas, {
            type: "bar",
            data: {
                labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
                datasets: [{
                    label: "Bookings",
                    data: [12, 18, 14, 22, 27, 35],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }

    // ==========================
    // Notification Dropdown
    // ==========================

    const bell = document.getElementById("notificationToggle");
    const menu = document.getElementById("notificationMenu");

    if (bell && menu) {

        bell.addEventListener("click", function (e) {
            e.stopPropagation();
            menu.classList.toggle("show");
        });

        document.addEventListener("click", function () {
            menu.classList.remove("show");
        });

        menu.addEventListener("click", function (e) {
            e.stopPropagation();
        });

    }

});