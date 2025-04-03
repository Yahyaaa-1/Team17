document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('login-form');
    const messageDiv = document.getElementById('message');
    const submitButton = document.querySelector('.register-btn');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const forgotPasswordLink = document.querySelector('.forgot-password-link');
    const forgotPasswordModal = new bootstrap.Modal(document.getElementById('forgotPasswordModal'));
    const validateButton = document.getElementById('validateForgotPassword');
    const darkModeToggle = document.getElementById('dark-mode-toggle');
    const togglePassword = document.getElementById('togglePassword');

    togglePassword.addEventListener('click', function () {
        // Toggle the type attribute
        const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
        passwordInput.setAttribute('type', type);

        // Toggle the eye icon emoji (optional)
        this.textContent = type === 'password' ? '👁️' : '🙈';
    });

    // Function to show messages
    function showMessage(message, isError = false) {
        if (messageDiv) {
            messageDiv.textContent = message;
            messageDiv.className = isError ? 'error-message' : 'success-message';
            messageDiv.style.display = 'block';
        }
    }
    function toggleDarkMode() {
        const isDarkMode = document.body.classList.toggle('dark-mode');
        // Save the preference in sessionStorage
        sessionStorage.setItem('darkMode', isDarkMode ? 'enabled' : 'disabled');

        // Optionally, send the preference to the backend (if needed)
        fetch('/toggle_dark_mode', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ dark_mode: isDarkMode ? 'enabled' : 'disabled' }),
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.success) {
                    console.log('Dark mode preference saved:', isDarkMode ? 'enabled' : 'disabled');
                }
            })
            .catch((error) => {
                console.error('Error saving dark mode preference:', error);
            });
    }

    // Event listener for dark mode toggle button
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', toggleDarkMode);
    }


    // if (emailInput) {
    //     emailInput.addEventListener('input', function() {
    //         const emailPattern = /^[a-zA-Z]+\.[a-zA-Z]+@rakusens\.co\.uk$/;
    //         if (!emailPattern.test(this.value)) {
    //             this.setCustomValidity('Email must be in format firstname.lastname@rakusens.co.uk');
    //         } else {
    //             this.setCustomValidity('');
    //         }
    //     });
    // }

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
                    // Store user info in session storage
                    sessionStorage.setItem('isLoggedIn', 'true');
                    sessionStorage.setItem('isAdmin', data.is_admin);
                    sessionStorage.setItem('user', JSON.stringify({
                        operator_id: data.operator_id,
                        email: data.email,
                        fullName: data.full_name
                    }));
                    
                    // Set dark mode preference from database response
                    const darkModePreference = data.dark_mode || 'disabled';
                    sessionStorage.setItem('darkMode', darkModePreference);
                    localStorage.setItem('darkMode', darkModePreference);
                
                    // Apply immediately
                    if (darkModePreference === 'enabled') {
                        document.body.classList.add('dark-mode');
                        document.documentElement.setAttribute('data-bs-theme', 'dark');
                    }
                    // Apply dark mode preference immediately
                    if (darkModePreference === 'enabled') {
                        document.body.classList.add('dark-mode');
                    } else {
                        document.body.classList.remove('dark-mode');
                    }


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
    if (forgotPasswordLink) {
        forgotPasswordLink.addEventListener('click', function(e) {
            e.preventDefault();
            forgotPasswordModal.show();
        });
    }

    validateButton.addEventListener('click', async function() {
        // Get input values
        const operatorId = document.getElementById('operatorId').value;
        const email = document.getElementById('Femail').value;
    
        try {
    
            // Show confirmation modal or proceed with password reset
            Swal.fire({
                title: 'Confirm Password Reset',
                text: 'Are you sure you want to reset your password? This will remove all your account preferences.',
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#3085d6',
                cancelButtonColor: '#d33',
                confirmButtonText: 'Yes, reset my password'
            }).then(async (result) => {
                if (result.isConfirmed) {
                    // Proceed with password reset
                    try {
                        const resetResponse = await fetch('http://localhost:5000/api/forgot-password', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                operator_id: operatorId,
                                email: email
                            })
                        });

                        const resetData = await resetResponse.json();

                        if (resetData.success) {
                            Swal.fire({
                                title: 'Password Reset',
                                text: 'Your password has been reset. Please contact and admin for your temporary credentials.',
                                icon: 'success'
                            });
                            forgotPasswordModal.hide();
                        } else {
                            Swal.fire({
                                title: 'Error',
                                text: resetData.error || 'Failed to reset password',
                                icon: 'error'
                            });
                        }
                    } catch (error) {
                        console.error('Password reset error:', error);
                        Swal.fire({
                            title: 'Error',
                            text: 'An unexpected error occurred',
                            icon: 'error'
                        });
                    }
                }
            });
        } catch (error) {
            console.error('Validation error:', error);
            Swal.fire({
                title: 'Error',
                text: 'An unexpected error occurred',
                icon: 'error'
            });
        }
    });
});
