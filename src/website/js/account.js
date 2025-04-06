document.addEventListener('DOMContentLoaded', () => {
    const user = JSON.parse(sessionStorage.getItem('user'));
    const admin = JSON.parse(sessionStorage.getItem('isAdmin'));
    if (!user) window.location.href = '/pages/login.html';

    // Populate account details
    document.getElementById('accountDetails').innerHTML = `
        <p><strong>Operator ID:</strong> ${user.operator_id}</p>
        <p><strong>Email:</strong> ${user.email}</p>
        <p><strong>Full Name:</strong> ${user.fullName || user.full_name}</p>
        <p><strong>Admin Privileges:</strong> ${admin ? 'Yes' : 'No'}</p>
    `;

    // Initialize dark mode toggle using data-bs-theme
    const darkModeToggle = document.getElementById('darkModeToggle');
    const htmlElement = document.documentElement;

    // Use either source, prioritizing the dedicated darkMode key if it exists
    const isDarkMode = JSON.parse(sessionStorage.getItem('darkMode')) || user.dark_mode;

    // Set initial theme
    htmlElement.setAttribute('data-bs-theme', isDarkMode ? 'dark' : 'light');
    darkModeToggle.checked = isDarkMode;

    // Dark mode toggle handler
    darkModeToggle.addEventListener('change', () => {
        const isDarkMode = darkModeToggle.checked;
        htmlElement.setAttribute('data-bs-theme', isDarkMode ? 'dark' : 'light');
        user.dark_mode = isDarkMode ? 1 : 0;
        sessionStorage.setItem('user', JSON.stringify(user));
        sessionStorage.setItem('darkMode', JSON.stringify(user.dark_mode));
        

        // updatePreference('dark_mode', isDarkMode ? 1 : 0);
    });

    // Password update handler
    document.getElementById('passwordForm').addEventListener('submit', updatePassword);
});


// Update user password
async function updatePassword(event) {
    event.preventDefault();

    const user = JSON.parse(sessionStorage.getItem('user'));
    const newPass = document.getElementById('newPassword').value;
    const confirmPass = document.getElementById('confirmPassword').value;
    const messageDiv = document.getElementById('passwordMessage');

    messageDiv.style.display = 'block';

    if (newPass !== confirmPass) {
        messageDiv.textContent = 'Passwords do not match';
        messageDiv.style.color = 'red';
        return;
    }

    try {
        const response = await fetch('http://localhost:5000/api/update-password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                operator_id: user.operator_id,
                new_password: newPass
            })
        });

        const result = await response.json();
        if (result.success) {
            messageDiv.textContent = 'Password updated successfully';
            messageDiv.style.color = 'green';
            document.getElementById('passwordForm').reset();
            setTimeout(() => (messageDiv.style.display = 'none'), 3000);
        } else {
            messageDiv.textContent = `Error: ${result.error || 'Failed to update password'}`;
            messageDiv.style.color = 'red';
        }
    } catch (error) {
        console.error('Password update failed:', error);
        messageDiv.textContent = 'Network error - Please try again';
        messageDiv.style.color = 'red';
    }
}

// Logout function
function logout() {
    sessionStorage.clear();
    window.location.href = 'login.html';
}
