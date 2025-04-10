document.addEventListener('DOMContentLoaded', function() {
    const registerForm = document.getElementById('register-form');
    const messageDiv = document.getElementById('message');
    const submitButton = document.querySelector('.register-btn');
    const newPasswordInput = document.getElementById('newPassword');
    const confirmPasswordInput = document.getElementById('confirmPassword');
    const passwordMatchMessage = document.getElementById('passwordMatch');
    const emailInput = document.getElementById('email');
    const fullNameInput = document.getElementById('fullname');
    const togglePassword = document.getElementById('toggleNewPassword');
    const toggleConfirmPassword = document.getElementById('toggleConfirmPassword');
    
    document.getElementById('darkModeToggle').addEventListener('click', function() {
        const body = document.body;
        const icon = this.querySelector('i');
    
        body.classList.toggle('dark-mode');
    
        // Change icon based on the mode
        if (body.classList.contains('dark-mode')) {
            icon.classList.remove('fa-moon');
            icon.classList.add('fa-sun');
        } else {
            icon.classList.remove('fa-sun');
            icon.classList.add('fa-moon');
        }
    });

    togglePassword.addEventListener('click', function () {
        const type = newPasswordInput.getAttribute('type') === 'password' ? 'text' : 'password';
        newPasswordInput.setAttribute('type', type);

        // Toggle the icon (optional visual feedback)
        this.classList.toggle('fa-eye');
        this.classList.toggle('fa-eye-slash');
    });

    toggleConfirmPassword.addEventListener('click', function () {
        const type = confirmPasswordInput.getAttribute('type') === 'password' ? 'text' : 'password';
        confirmPasswordInput.setAttribute('type', type);

        // Toggle the icon (optional visual feedback)
        this.classList.toggle('fa-eye');
        this.classList.toggle('fa-eye-slash');
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
            const passwordValidation = /^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$/
            if(!passwordValidation.test(newPassword) || !passwordValidation.test(confirmPassword)){
                showMessage('Passwords must be Minimum eight characters, at least one letter, one number and one special character:', true);
                if (submitButton) {
                    submitButton.classList.remove('loading');
                    submitButton.disabled = false;
                }
                return;
            }
            // Email validation
            const emailValidation = /^.+@rakusens\.com$/;
            if (!emailValidation.test(email)) {
                showMessage('Email must end with @rakusens.com', true);
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
                    showMessage('Registration successful! Waiting for production manager approval. Redirecting to login...');
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