document.addEventListener("DOMContentLoaded", function () {

    const button = document.getElementById("notificationBtn");
    const dropdown = document.getElementById("notificationDropdown");
    const badge = document.getElementById("notificationCount");
    const list = document.getElementById("notificationList");

    console.log("notifications.js: loaded", { button: !!button, dropdown: !!dropdown });

    if (!dropdown || !button) return;

    // delegated click handling: toggle when clicking the bell, close when clicking outside
    document.addEventListener("click", function (e) {
        const clickedBell = e.target.closest && e.target.closest('#notificationBtn');
        const clickedDropdown = e.target.closest && e.target.closest('#notificationDropdown');

        if (clickedBell) {
            e.preventDefault();
            dropdown.classList.toggle("show");

            // fetch notifications when opening
            if (dropdown.classList.contains("show")) {
                fetch("/notifications/api/")
                    .then(response => response.json())
                    .then(data => {
                        if (badge) {
                            if (data.unread > 0) {
                                badge.style.display = "flex";
                                badge.textContent = data.unread;
                            } else {
                                badge.style.display = "none";
                            }
                        }

                        let html = "";

                        if (!data.notifications || data.notifications.length === 0) {
                            html = '<div class="notification-item">No notifications</div>';
                        } else {
                            data.notifications.forEach(item => {
                                html += `\n<a href="${item.url}" class="notification-item">\n<strong>${item.title}</strong>\n<p>${item.message}</p>\n</a>`;
                            });
                        }

                        if (list) list.innerHTML = html;
                    })
                    .catch(err => console.error('notifications fetch error', err));
            }

            return;
        }

        // if click outside dropdown, close it
        if (!clickedDropdown) {
            dropdown.classList.remove("show");
        }
    });

});