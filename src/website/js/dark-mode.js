document.addEventListener("DOMContentLoaded", function () {
    const toggleButton = document.getElementById("dark-mode-toggle");
    const body = document.body;
    const htmlElement = document.documentElement;

    // Function to apply dark mode and update storage
    async function applyDarkMode(enabled) {
        const darkModeValue = enabled ? 1 : 0;
        
        if (enabled) {
            body.classList.add("dark-mode");
            htmlElement.setAttribute("data-bs-theme", "dark");
            localStorage.setItem("darkMode", "1");
            sessionStorage.setItem("darkMode", "1");
            if (toggleButton) {
                toggleButton.checked = true;
            }
        } else {
            body.classList.remove("dark-mode");
            htmlElement.setAttribute("data-bs-theme", "light");
            localStorage.setItem("darkMode", "0");
            sessionStorage.setItem("darkMode", "0");
            if (toggleButton) {
                toggleButton.checked = false;
            }
        }

        // Update the database with the new preference
        try {
            const user = JSON.parse(sessionStorage.getItem('user'));
            if (user && user.operator_id) {
                await fetch('http://localhost:5000/api/update-dark-mode', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${sessionStorage.getItem('token')}`
                    },
                    body: JSON.stringify({
                        operator_id: user.operator_id,
                        dark_mode: darkModeValue
                    })
                });
            }
        } catch (error) {
            console.error('Error updating dark mode preference:', error);
        }
    }

    // Check user preference on page load (priority: sessionStorage > localStorage)
    const sessionDarkMode = sessionStorage.getItem("darkMode");
    const localDarkMode = localStorage.getItem("darkMode");
    const isDarkMode = (sessionDarkMode ? sessionDarkMode : localDarkMode) === "1";
    applyDarkMode(isDarkMode);

    // Add event listener to toggle button
    if (toggleButton) {
        toggleButton.addEventListener("change", function () {
            applyDarkMode(this.checked);
        });
    }
});