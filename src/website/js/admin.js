document.addEventListener('DOMContentLoaded', function() {
    // Check admin access
    const isAdmin = JSON.parse(sessionStorage.getItem('isAdmin'));
    const user = JSON.parse(sessionStorage.getItem('user'));
    const adminID = user.operator_id;

    if (!isAdmin) {
        alert('Access Denied: Admin privileges required');
        window.location.href = '../home.html';
        return;
    }
    let userAccounts = [];
    async function fetchUserAccounts() {
        try {
            const response = await fetch('http://localhost:5000/api/admin/user-accounts', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    // Add any authentication headers if needed
                    // 'Authorization': `Bearer ${token}`
                }
            });
    
            if (!response.ok) {
                throw new Error('Failed to fetch user accounts');
            }
    
            const data = await response.json();
    
            if (!data.success) {
                throw new Error(data.error || 'Unknown error occurred');
            }
    
            const tableBody = document.getElementById('user-accounts-body');
            tableBody.innerHTML = ''; // Clear existing rows

            // Store the employee data
            userAccounts = data.user_accounts;
    
            data.user_accounts.forEach(user => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td id="operator_id">${user.operator_id}</td>
                    <td>${user.email}</td>
                    <td>${user.full_name}</td>
                    <td>${user.active ? 'Yes' : 'No'}</td>
                    <td>${user.admin ? 'Yes' : 'No'}</td>
                    <td class="action-buttons">
                        <button class="approve-btn" data-id="${user.operator_id}" onclick="toggleUserStatus(this, 'active')">
                            ${user.active ? 'Deactivate' : 'Activate'}
                        </button>
                        <button class="approve-btn" data-id="${user.operator_id}" onclick="toggleAdminStatus(this, 'admin')">
                            ${user.admin ? 'Demote' : 'Promote'}
                        </button>
                        <button class="edit-btn" onclick="openEditModal('${user.operator_id}')">
                            Edit
                        </button>
                        <button class="delete-btn" data-id="${user.operator_id}" onclick="deleteUser(this)">
                            Delete
                        </button>
                    </td>
                `;
                tableBody.appendChild(row);
            });
        } catch (error) {
            console.error('Error fetching user accounts:', error);
            // Optionally show an error message to the user
            alert('Failed to fetch user accounts. Please try again.');
        }

        window.openEditModal = function(operatorId) {
            // Ensure that userAccounts is populated
            if (!userAccounts || userAccounts.length === 0) {
                console.log('User accounts data is empty or not loaded yet.');
                alert('User accounts not loaded.');
                return;
            }
        
            // Convert operatorId to number (if it's a string) to match the type of operator_id in userAccounts
            const user = userAccounts.find(emp => emp.operator_id === Number(operatorId));  // Ensure comparison is between same types
        
            if (user) {
                console.log("Found user data:", user);
                // Populate the form fields
                document.getElementById('edit_operator_id').value = user.operator_id;
                document.getElementById('edit_email').value = user.email;
                document.getElementById('edit_full_name').value = user.full_name;
                document.getElementById('edit_temp_password').value = user.password; // Assuming temp_password is password
                // Show the modal
                const modal = document.getElementById('editModal');
                modal.style.display = "block";
            } else {
                console.log('User not found for operator_id:', operatorId);
                alert('User not found');
            }
            // Close modal when clicking on the close button
            const closeModalButton = document.querySelector('.close');
            closeModalButton.onclick = function() {
                const modal = document.getElementById('editModal');
                modal.style.display = "none";
            }

            // Close modal when clicking outside of the modal content
            window.onclick = function(event) {
                const modal = document.getElementById('editModal');
                if (event.target === modal) {
                    modal.style.display = "none";
                }
            }
        }
    }

    document.getElementById('editEmployeeForm').addEventListener('submit', function(event) {
        event.preventDefault(); // Prevent the default form submission
        savechanges(); // Call the savechanges function
    });

     // Save edit changes
    window.savechanges = async function(button) {

        var operatorId = document.getElementById('edit_operator_id').value
        var email = document.getElementById('edit_email').value
        var fullname = document.getElementById('edit_full_name').value


            try {
                const response = await fetch(`http://localhost:5000/api/admin/update-user-details`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ operator_id: operatorId , Nemail: email, Nfullname:fullname})
                });
                if (!response.ok) {
                    const errorData = await response.json();
                    console.error('Error:', errorData.error);
                    return;
                }
                else{
                    //location.reload();
                }
                const data = await response.json();
                if (data.success) {
                    fetchUserAccounts();
                    document.getElementById('editModal').style.display = "none";
                }
            } catch (error) {
                console.error('Error deleting user:', error);
            }
    }
    

    // Toggle user admin
    window.toggleUserAdmin = async function(button, type) {

        const operatorId = button.dataset.id;

        try {
            const response = await fetch(`http://localhost:5000/api/admin/toggle-user-admin`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ operator_id: operatorId, type: type })
            });
            const data = await response.json();
            if (data.success) {
                fetchUserAccounts(); // Refresh table
            }
        } catch (error) {
            console.error('Error toggling user admin:', error);
        }
    }



    async function fetchTableHeaders(tableId) {
        try {
            const response = await fetch(`http://localhost:5000/api/admin/table-headers?tableID=${tableId}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (!response.ok) {
                throw new Error('Failed to fetch table headers');
            }

            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error || 'Unknown error occurred');
            }

            // Get the table body to populate
            const tableBody = document.getElementById(`${tableId}-headers-body`);
            tableBody.innerHTML = ''; // Clear existing rows

            // Filter out timestamp and timezone columns
            const filteredHeaders = data.headers.filter(header => 
                header !== 'timestamp' && header !== 'timezone'
            );

            // Create a row for each sensor header
            filteredHeaders.forEach(header => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${header}</td>
                    <td>
                        <button class="btn btn-danger btn-sm delete-btn" onclick="deleteSensor('${header}','${tableId}')">
                            <i class="bi bi-trash"></i> Delete
                        </button>
                    </td>
                `;
                tableBody.appendChild(row);
            });

        } catch (error) {
            console.error('Error fetching table headers:', error);
            alert('Failed to fetch table headers. Please try again.');
        }
    }
    window.deleteSensor = async function(sensorName,tableID) {

        if (confirm(`Are you sure you want to delete ${sensorName} sensor?`)) {
            try {
                const response = await fetch(`http://localhost:5000/api/admin/delete-sensor`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ sensorName: sensorName, tableID:tableID })
                });
                const data = await response.json();
                if (data.success) {
                    fetchTableHeaders(tableId); // Refresh table
                }
            } catch (error) {
                console.error('Error deleting sensor:', error);
            }
        }
    }
    
    // Toggle user status
    window.toggleUserStatus = async function(button, type) {

        const operatorId = button.dataset.id;

        try {
            const response = await fetch(`http://localhost:5000/api/admin/toggle-user-status`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ operator_id: operatorId, type: type , admin_ID:adminID})
            });
            const data = await response.json();
            if (data.success) {
                fetchUserAccounts(); // Refresh table
            }
        } catch (error) {
            console.error('Error toggling user status:', error);
        }
    }

    // Toggle admin status
    window.toggleAdminStatus = async function(button, type) {

        const operatorId = button.dataset.id;

        try {
            const response = await fetch(`http://localhost:5000/api/admin/toggle-admin-status`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ operator_id: operatorId, type: type , admin_ID:adminID})
            });
            const data = await response.json();
            if (data.success) {
                fetchUserAccounts(); // Refresh table
            }
        } catch (error) {
            console.error('Error toggling admin status:', error);
        }
    }

    // Delete user
    window.deleteUser = async function(button) {
        const operatorId = button.dataset.id;
        if (confirm(`Are you sure you want to delete user ${operatorId}?`)) {
            try {
                const response = await fetch(`http://localhost:5000/api/admin/delete-user`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ operator_id: operatorId , admin_ID:adminID })
                });
                const data = await response.json();
                if (data.success) {
                    fetchUserAccounts(); // Refresh table
                }
            } catch (error) {
                console.error('Error deleting user:', error);
            }
        }
    }

    // Initial fetch
    fetchUserAccounts();
    fetchTableHeaders('line4');
    fetchTableHeaders('line5');
});
