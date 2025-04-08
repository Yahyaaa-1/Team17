document.addEventListener('DOMContentLoaded', function() {
    const headerControls = document.querySelector('.header-controls');
    const mainContent = document.querySelector('.main-content');
    const user = JSON.parse(sessionStorage.getItem('user'));

    // Function to determine the base path
    function getBasePath() {
        console.log("Current Pathname:", window.location.pathname);
        const isInPagesFolder = window.location.pathname.includes('/pages/');
        console.log("Is in Pages Folder:", isInPagesFolder);
        return isInPagesFolder ? '' : 'pages/';
    }

    // Function to create and append buttons
    function updateHeaderButtons() {
        // Check login status
        const isLoggedIn = sessionStorage.getItem('isLoggedIn') === 'true';
        const basePath = getBasePath();
        
        if (!isLoggedIn) {
            // Create login button if not logged in
            const loginButton = document.createElement('a');
            loginButton.href = `${basePath}login.html`;
            loginButton.className = 'btn login-btn';
            loginButton.textContent = 'Login';
            headerControls.appendChild(loginButton);
        } else {

            

            // Retrieve user info
            const admin = JSON.parse(sessionStorage.getItem('isAdmin'));

            // Create account dropdown
            const accountDropdown = document.createElement('div');
            accountDropdown.className = 'account-dropdown';
            
            // Account button
            const accountButton = document.createElement('button');
            accountButton.className = 'btn account-btn';
            accountButton.innerHTML = `
                <i class="fas fa-user"></i> Account
                <i class="fas fa-caret-down"></i>
            `;
            
            // Dropdown content
            const dropdownContent = document.createElement('div');
            dropdownContent.className = 'dropdown-content';
            
            // Account page link
            const accountPageLink = document.createElement('a');
            accountPageLink.href = `${basePath}account.html`;
            accountPageLink.innerHTML = '<i class="fas fa-user-circle"></i> My Account';
            dropdownContent.appendChild(accountPageLink);

             // Add admin link if user is admin
            if (admin === 1) {
                const adminLink = document.createElement('a');
                adminLink.href = `${basePath}admin.html`;
                adminLink.innerHTML = '<i class="fas fa-user-shield"></i> Admin Panel';
                dropdownContent.appendChild(adminLink);
            }
                    
            // Logout link
            const logoutLink = document.createElement('a');
            logoutLink.href = '#';
            logoutLink.innerHTML = '<i class="fas fa-sign-out-alt"></i> Logout';
            logoutLink.addEventListener('click', function(e) {
                e.preventDefault();
                // Remove session storage items
                sessionStorage.removeItem('isLoggedIn');
                sessionStorage.removeItem('user');
                sessionStorage.removeItem('isAdmin');
                sessionStorage.removeItem('darkMode');

                // Log logout event directly to the existing log-message endpoint
                fetch('http://localhost:5000/api/log', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        message: `User ${user.email} logged out`,
                        type: 'INFO',
                        level: 'admin'
                    })
                }).then(response => {                    
                    // Redirect to login page
                    window.location.href = `${basePath}login.html`;
                }).catch(error => {
                    console.error('Logout logging error:', error);
                });
            });
            dropdownContent.appendChild(logoutLink);
            
            // Assemble dropdown
            accountDropdown.appendChild(accountButton);
            accountDropdown.appendChild(dropdownContent);
            
            // Add event listener to toggle dropdown
            accountButton.addEventListener('click', function() {
                dropdownContent.classList.toggle('show');
            });
            
            // Close dropdown when clicking outside
            window.addEventListener('click', function(e) {
                if (!accountDropdown.contains(e.target)) {
                    dropdownContent.classList.remove('show');
                }
            });
            
            headerControls.appendChild(accountDropdown);
            }
    }

    // Initial setup
    updateHeaderButtons();

    // Listen for storage changes (e.g., login/logout in another tab)
    window.addEventListener('storage', function(e) {
        if (e.key === 'isLoggedIn' || e.key === 'user') {
            updateHeaderButtons();
        }
    });
});