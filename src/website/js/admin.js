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
    }
    let employeeData = [];
    async function fetchEmployeeRegistry() {
        

        try {
            const response = await fetch('http://localhost:5000/api/admin/employee-reg', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
    
            if (!response.ok) {
                throw new Error('Failed to fetch employee registry');
            }
    
            const data = await response.json();
    
            if (!data.success) {
                throw new Error(data.error || 'Unknown error occurred');
            }
            // Check if employee_registry exists and is an array
            if (!data.employee_registry || !Array.isArray(data.employee_registry)) {
                throw new Error('Invalid or missing employee registry data');
            }

            // Store the employee data
            employeeData = data.employee_registry;
    
            const tableBody = document.getElementById('employee-registry-body');
            tableBody.innerHTML = ''; // Clear existing rows
    
            data.employee_registry.forEach(employee => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${employee.operator_id}</td>
                    <td>${employee.email}</td>
                    <td>${employee.full_name}</td>
                    <td>${employee.temp_password}</td>
                    <td class="action-buttons">
                        <button class="edit-btn" onclick="openEditModal('${employee.operator_id}')">
                            Edit
                        </button>
                        <button class="delete-btn" data-id="${employee.operator_id}" onclick="deleteEmployee(this)">
                            Delete
                        </button>
                    </td>
                `;
                tableBody.appendChild(row);
            });
        } catch (error) {
            console.error('Error fetching employee registry:', error);
            // Optionally show an error message to the user
            alert('Failed to fetch employee registry. Please try again.');
        }


        

         // Modified openEditModal to use stored data
    window.openEditModal = function(operatorId) {
        const employee = employeeData.find(emp => emp.operator_id === operatorId);
        
        if (employee) {

            console.log("Found employee data:", employee);
            // Populate the form
            document.getElementById('edit_operator_id').value = employee.operator_id;
            document.getElementById('edit_email').value = employee.email;
            document.getElementById('edit_full_name').value = employee.full_name;
            document.getElementById('edit_temp_password').value = employee.temp_password;

            // Show the modal
            const modal = document.getElementById('editModal');
            modal.style.display = "block";
        } else {
            alert('Employee not found');
        }
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

    // Delete employee
    window.deleteEmployee = async function(button) {
        const operatorId = button.dataset.id;
        if (confirm(`Are you sure you want to delete employee ${operatorId}?`)) {
            try {
                const response = await fetch(`http://localhost:5000/api/admin/delete-employee`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ operator_id: operatorId , admin_ID:adminID})
                });
                const data = await response.json();
                if (data.success) {
                    fetchEmployeeRegistry(); // Refresh table
                }
            } catch (error) {
                console.error('Error deleting employee:', error);
            }
        }
    }

    // Initial fetch
    fetchUserAccounts();
    fetchEmployeeRegistry();
    fetchTableHeaders('line4');
    fetchTableHeaders('line5');
});
