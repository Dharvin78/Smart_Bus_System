(() => {
    const panel = document.querySelector("[data-payment-countdowns]");
    if (!panel) return;

    const clockOffset = Number(panel.dataset.serverTime) * 1000 - Date.now();
    const countdowns = Array.from(panel.querySelectorAll("[data-payment-deadline]"), (row) => ({
        deadline: Number(row.dataset.paymentDeadline) * 1000,
        label: row.querySelector("[data-payment-time-left]"),
        payLink: row.querySelector("[data-pay-now]"),
    }));

    function updateCountdowns() {
        const now = Date.now() + clockOffset;
        let hasTimeLeft = false;

        for (const countdown of countdowns) {
            const secondsLeft = Math.ceil((countdown.deadline - now) / 1000);
            if (secondsLeft <= 0) {
                countdown.label.textContent = "Payment deadline passed";
                countdown.payLink.classList.add("d-none");
                continue;
            }

            hasTimeLeft = true;
            const hours = Math.floor(secondsLeft / 3600);
            const minutes = Math.floor(secondsLeft / 60) % 60;
            const seconds = secondsLeft % 60;
            countdown.label.textContent = `${hours}h ${minutes}m ${seconds}s remaining`;
        }

        if (hasTimeLeft) window.setTimeout(updateCountdowns, 1000);
    }

    updateCountdowns();
})();
