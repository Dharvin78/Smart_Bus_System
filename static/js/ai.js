document.addEventListener("DOMContentLoaded", function () {

    const chart = document.getElementById("forecastChart");

    if (!chart) return;

    const labels = JSON.parse(chart.dataset.labels);

    const actual = JSON.parse(chart.dataset.actual);

    const forecast = JSON.parse(chart.dataset.forecast);

    new Chart(chart, {

        type: "line",

        data: {

            labels: labels,

            datasets: [

                {

                    label: "Actual Revenue",

                    data: actual,

                    borderWidth: 3,

                    tension: .4,

                    fill: false,

                },

                {

                    label: "AI Forecast",

                    data: forecast,

                    borderWidth: 3,

                    borderDash: [8,5],

                    tension: .4,

                    fill: false,

                }

            ]

        },

        options: {

            responsive: true,

            maintainAspectRatio: false,

            interaction: {

                intersect: false,

                mode: "index",

            }

        }

    });

});

const forecastLabels = JSON.parse(
    document.getElementById("forecast-labels").textContent
);

const forecastData = JSON.parse(
    document.getElementById("forecast-data").textContent
);

new Chart(
    document.getElementById("forecastChart"),
    {

        type: "line",

        data: {

            labels: forecastLabels,

            datasets: [{

                label: "Revenue Forecast",

                data: forecastData,

                tension: 0.4,

                fill: false,

                pointRadius: 6,

                borderWidth: 3

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

    }
);

/* Booking Forecast Chart*/

const bookingForecastLabels = JSON.parse(
    document.getElementById(
        "booking-forecast-labels"
    ).textContent
);

const bookingForecastData = JSON.parse(
    document.getElementById(
        "booking-forecast-data"
    ).textContent
);

new Chart(

    document.getElementById(
        "bookingForecastChart"
    ),

    {

        type: "line",

        data: {

            labels: bookingForecastLabels,

            datasets: [{

                label: "Booking Forecast",

                data: bookingForecastData,

                tension: 0.4,

                fill: false,

                pointRadius: 6,

                borderWidth: 3

            }]

        },

        options: {

            responsive: true

        }

    }

);