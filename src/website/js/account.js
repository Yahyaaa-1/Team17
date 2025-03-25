document.addEventListener('DOMContentLoaded', () => {
    const user = JSON.parse(sessionStorage.getItem('user'));
    if (!user) window.location.href = '/pages/login.html';

    // Populate account details
    document.getElementById('accountDetails').innerHTML = `
        <p><strong>Operator ID:</strong> ${user.operator_id}</p>
        <p><strong>Email:</strong> ${user.email}</p>
        <p><strong>Full Name:</strong> ${user.fullName || user.full_name}</p>
        <p><strong>Admin Privileges:</strong> ${user.is_admin ? 'Yes' : 'No'}</p>
    `;

    // Initialize dark mode toggle using data-bs-theme
    const darkModeToggle = document.getElementById('darkModeToggle');
    const htmlElement = document.documentElement;

    // Set initial theme
    htmlElement.setAttribute('data-bs-theme', user.dark_mode ? 'dark' : 'light');
    darkModeToggle.checked = user.dark_mode;

    // Dark mode toggle handler
    darkModeToggle.addEventListener('change', () => {
        const isDarkMode = darkModeToggle.checked;
        htmlElement.setAttribute('data-bs-theme', isDarkMode ? 'dark' : 'light');
        updatePreference('dark_mode', isDarkMode ? 1 : 0);
    });

    // Password update handler
    document.getElementById('passwordForm').addEventListener('submit', updatePassword);
});

// Update user preferences
function updatePreference(key, value) {
    const user = JSON.parse(sessionStorage.getItem('user'));
    user[key] = value;
    sessionStorage.setItem('user', JSON.stringify(user));

    fetch('http://localhost:5000/api/update-preference', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            operator_id: user.operator_id,
            [key]: value
        })
    }).catch((error) => {
        console.error(`Failed to update ${key}:`, error);
    });
}

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
    window.location.href = '/pages/login.html';
}
