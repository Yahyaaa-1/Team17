document.addEventListener('DOMContentLoaded', function() {
    const registerForm = document.getElementById('register-form');
    const messageDiv = document.getElementById('message');
    const submitButton = document.querySelector('.register-btn');
    const newPasswordInput = document.getElementById('newPassword');
    const confirmPasswordInput = document.getElementById('confirmPassword');
    const passwordMatchMessage = document.getElementById('passwordMatch');
    const emailInput = document.getElementById('email');
    const fullNameInput = document.getElementById('fullname');


    function togglePasswordVisibility(toggleButtonId, passwordFieldId) {
        const toggleButton = document.querySelector(toggleButtonId);
        const passwordField = document.querySelector(passwordFieldId);
    
        toggleButton.addEventListener("click", function () {
            const isPassword = passwordField.getAttribute("type") === "password";
            passwordField.setAttribute("type", isPassword ? "text" : "password");
            this.classList.toggle("fa-eye-slash");
            this.classList.toggle("fa-eye");
        });
    }
    
    document.addEventListener("DOMContentLoaded", function () {
        togglePasswordVisibility("#toggleNewPassword", "#newPassword");
        togglePasswordVisibility("#toggleConfirmPassword", "#confirmPassword");
    });
    

    // Function to show messages
    function showMessage(message, isError = false) {
        if (messageDiv) {
            messageDiv.textContent = message;
            messageDiv.className = isError ? 'error-message' : 'success-message';
            messageDiv.style.display = 'block';
        }
    }

    // Password match validation
    function validatePasswordMatch() {
        if (!confirmPasswordInput || !newPasswordInput || !passwordMatchMessage) return;

        if (confirmPasswordInput.value === '') {
            passwordMatchMessage.textContent = '';
            return;
        }

        if (newPasswordInput.value === confirmPasswordInput.value) {
            passwordMatchMessage.textContent = 'Passwords match';
            passwordMatchMessage.className = 'match-message success';
        } else {
            passwordMatchMessage.textContent = 'Passwords do not match';
            passwordMatchMessage.className = 'match-message error';
        }
    }

    // Event Listeners
    if (confirmPasswordInput) {
        confirmPasswordInput.addEventListener('input', validatePasswordMatch);
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
    if (registerForm) {
        registerForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            if (submitButton) {
                submitButton.classList.add('loading');
                submitButton.disabled = true;
            }

            const fullName = fullNameInput?.value;
            const email = emailInput?.value;
            const newPassword = newPasswordInput?.value;
            const confirmPassword = confirmPasswordInput?.value;

            if (!fullName || !email || !newPassword || !confirmPassword) {
                showMessage('Please fill in all fields', true);
                if (submitButton) {
                    submitButton.classList.remove('loading');
                    submitButton.disabled = false;
                }
                return;
            }

            // Validation
            if (newPassword !== confirmPassword) {
                showMessage('New passwords do not match', true);
                if (submitButton) {
                    submitButton.classList.remove('loading');
                    submitButton.disabled = false;
                }
                return;
            }

            try {
                // Proceed with registration
                const registerResponse = await fetch('http://localhost:5000/api/register', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        full_name: fullName,
                        email: email,
                        new_password: newPassword
                    })
                });
        
                if (!registerResponse.ok) {
                    const errorData = await registerResponse.json();
                    throw new Error(errorData.error || `HTTP error! status: ${registerResponse.status}`);
                }
        
                const registerData = await registerResponse.json();
        
                if (registerData.success) {
                    showMessage('Registration successful! Waiting for admin approval. Redirecting to login...');
                    registerForm.reset();
                    
                    setTimeout(() => {
                        window.location.href = '../pages/login.html';
                    }, 3000);
                } else {
                    showMessage(registerData.error || 'Registration failed', true);
                }
            } catch (error) {
                console.error('Error:', error);
                showMessage(error.message || 'An error occurred. Please try again later.', true);
            } finally {
                if (submitButton) {
                    submitButton.classList.remove('loading');
                    submitButton.disabled = false;
                }
            }
        });
    }
});