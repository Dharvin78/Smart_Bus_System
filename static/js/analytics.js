/*! Revenue Trend Chart (Revenue by Month) */

const labels = JSON.parse(
    document.getElementById("chart-labels").textContent
);

const revenue = JSON.parse(
    document.getElementById("chart-data").textContent
);

new Chart(document.getElementById("revenueTrendChart"), {

    type: "line",

    data: {

        labels: labels,

        datasets: [{

            label: "Revenue (RM)",

            data: revenue,

            borderWidth: 3,

            fill: true,

            tension: 0.4

        }]

    },

    options: {

        responsive: true,

        plugins: {

            legend: {

                display: true

            }

        }

    }

});

/*! Booking Trend Chart (Bookings by Month) */

const bookingLabels = JSON.parse(
    document.getElementById("booking-labels").textContent
);

const bookingData = JSON.parse(
    document.getElementById("booking-data").textContent
);

new Chart(document.getElementById("bookingTrendChart"), {

    type: "bar",

    data: {

        labels: bookingLabels,

        datasets: [{

            label: "Bookings",

            data: bookingData,

            borderWidth: 1

        }]

    },

    options: {

        responsive: true,

        plugins: {

            legend: {

                display: true

            }

        }

    }

});

/*! Vehicle Revenue Chart (Revenue by Vehicle) */

const vehicleLabels = JSON.parse(
    document.getElementById("vehicle-labels").textContent
);

const vehicleData = JSON.parse(
    document.getElementById("vehicle-data").textContent
);

new Chart(document.getElementById("vehicleRevenueChart"), {

    type: "bar",

    data: {

        labels: vehicleLabels,

        datasets: [{

            label: "Revenue (RM)",

            data: vehicleData,

            borderWidth: 1

        }]

    },

    options: {

        indexAxis: "y",

        responsive: true,

        plugins: {

            legend: {

                display: true

            }

        }

    }

});

/* Revenue by Vehicle*/

const driverLabels = JSON.parse(
    document.getElementById("driver-labels").textContent
);

const driverData = JSON.parse(
    document.getElementById("driver-data").textContent
);

new Chart(document.getElementById("driverRevenueChart"), {

    type: "bar",

    data: {

        labels: driverLabels,

        datasets: [{

            label: "Revenue (RM)",

            data: driverData,

            borderWidth: 1

        }]

    },

    options: {

        responsive: true,

        indexAxis: "y",

        plugins: {

            legend: {

                display: true

            }

        }

    }

});

/* Revenue by Customer*/
const customerLabels = JSON.parse(
    document.getElementById("customer-labels").textContent
);

const customerData = JSON.parse(
    document.getElementById("customer-data").textContent
);

new Chart(document.getElementById("customerChart"), {

    type: "bar",

    data: {

        labels: customerLabels,

        datasets: [{

            label: "Total Spending (RM)",

            data: customerData,

            borderWidth: 1

        }]

    },

    options: {

        responsive: true,

        indexAxis: "y",

        plugins: {

            legend: {

                display: true

            }

        }

    }

});

/* Popular Routes Chart (Bookings by Route) */

const routeLabels = JSON.parse(
    document.getElementById("route-labels").textContent
);

const routeData = JSON.parse(
    document.getElementById("route-data").textContent
);

new Chart(document.getElementById("routeChart"), {

    type: "doughnut",

    data: {

        labels: routeLabels,

        datasets: [{

            data: routeData

        }]

    },

    options: {

        responsive: true,

        plugins: {

            legend: {

                position: "bottom"

            }

        }

    }

});

/* Payment Methods Chart (Revenue by Payment Method) */

const paymentLabels = JSON.parse(
    document.getElementById("payment-labels").textContent
);

const paymentData = JSON.parse(
    document.getElementById("payment-data").textContent
);

new Chart(document.getElementById("paymentChart"), {

    type: "pie",

    data: {

        labels: paymentLabels,

        datasets: [{

            data: paymentData

        }]

    },

    options: {

        responsive: true,

        plugins: {

            legend: {

                position: "bottom"

            }

        }

    }

});

/* Booking Status Chart (Bookings by Status) */

const statusLabels = JSON.parse(
    document.getElementById("status-labels").textContent
);

const statusData = JSON.parse(
    document.getElementById("status-data").textContent
);

new Chart(document.getElementById("statusChart"), {

    type: "doughnut",

    data: {

        labels: statusLabels,

        datasets: [{

            data: statusData

        }]

    },

    options: {

        responsive: true,

        plugins: {

            legend: {

                position: "bottom"

            }

        }

    }

});