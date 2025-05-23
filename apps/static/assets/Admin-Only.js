document.addEventListener("DOMContentLoaded", function () {
    const userRole = localStorage.getItem("user_role");
    const adminElements = document.querySelectorAll(".admin-only");

    adminElements.forEach(el => {
        if (userRole !== "Admin") {
            el.style.display = "none";
        }
    });
});