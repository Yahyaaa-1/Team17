document.addEventListener("DOMContentLoaded", function () {
    const toggleButton = document.getElementById("dark-mode-toggle");
    const body = document.body;

    // Function to apply dark mode
    function applyDarkMode(enabled) {
        if (enabled) {
            body.classList.add("dark-mode");
            localStorage.setItem("darkMode", "enabled");
            if (toggleButton) {
                toggleButton.checked = true; // Ensure the toggle is checked
            }
        } else {
            body.classList.remove("dark-mode");
            localStorage.setItem("darkMode", "disabled");
            if (toggleButton) {
                toggleButton.checked = false; // Ensure the toggle is unchecked
            }
        }
    }

    // Check user preference on page load
    const savedDarkMode = localStorage.getItem("darkMode");
    const isDarkMode = savedDarkMode === "enabled";
    applyDarkMode(isDarkMode);

    // Add event listener to toggle button (only if it exists)
    if (toggleButton) {
        toggleButton.addEventListener("change", function () {
            const isDarkModeNow = body.classList.contains("dark-mode");
            applyDarkMode(!isDarkModeNow);
        });
    }
});