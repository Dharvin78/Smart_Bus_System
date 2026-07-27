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