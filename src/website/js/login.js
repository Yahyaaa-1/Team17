document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('login-form');
    const messageDiv = document.getElementById('message');
    const submitButton = document.querySelector('.register-btn');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');

    // Function to show messages
    function showMessage(message, isError = false) {
        if (messageDiv) {
            messageDiv.textContent = message;
            messageDiv.className = isError ? 'error-message' : 'success-message';
            messageDiv.style.display = 'block';
        }
    }

    if (emailInput) {
        emailInput.addEventListener('input', function() {
            const emailPattern = /^[a-zA-Z]+\.[a-zA-Z]+@rakusens\.co\.uk$/;
            if (!emailPattern.test(this.value)) {
                this.setCustomValidity('Email must be in format firstname.lastname@rakusens.co.uk');
            } else {
                this.setCustomValidity('');
            }
        });
    }

    // Form submission
    if (loginForm) {
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            // Disable submit button and show loading state
            if (submitButton) {
                submitButton.classList.add('loading');
                submitButton.disabled = true;
            }

            const email = emailInput.value;
            const password = passwordInput.value;

            // Basic validation
            if (!email || !password) {
                showMessage('Please fill in all fields', true);
                resetSubmitButton();
                return;
            }

            try {
                const response = await fetch('http://localhost:5000/api/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        email: email,
                        password: password
                    })
                });

                const data = await response.json();

                if (data.success) {
                    // Successful login
                    showMessage('Login successful! Redirecting...');
                    
                     // Store user info in session storage
                     sessionStorage.setItem('isLoggedIn', 'true');
                     sessionStorage.setItem('isAdmin', data.is_admin);
                     sessionStorage.setItem('user', JSON.stringify({
                         operator_id: data.operator_id,
                         email: data.email,
                         fullName: data.full_name
                     })                    
                    );

                    // Redirect to dashboard
                    setTimeout(() => {
                        window.location.href = '../home.html';
                    }, 2000);
                } else {
                    // Handle different error scenarios
                    if (data.active === false) {
                        // Account not approved
                        showMessage('Your account is pending admin approval. Please contact the administrator.', true);
                    } else {
                        // Other login errors
                        showMessage(data.error || 'Login failed', true);
                    }
                    resetSubmitButton();
                }
            } catch (error) {
                console.error('Login error:', error);
                showMessage('An error occurred. Please try again.', true);
                resetSubmitButton();
            }
        });
    }

    // Helper function to reset submit button
    function resetSubmitButton() {
        if (submitButton) {
            submitButton.classList.remove('loading');
            submitButton.disabled = false;
        }
    }

    // Forgot Password Link
    const forgotPasswordLink = document.querySelector('.forgot-password-link');
    if (forgotPasswordLink) {
        forgotPasswordLink.addEventListener('click', function(e) {
            e.preventDefault();
            alert('Password reset functionality coming soon!');
        });
    }
});