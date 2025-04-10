document.addEventListener('DOMContentLoaded', function () {
    let apiUrlBase = 'http://localhost:5000/api/logs';
    let logsTable = null;
    const isAdmin = JSON.parse(sessionStorage.getItem('isAdmin')); // Check if the user is an admin

    function initializeLogsTable() {
        logsTable = $('#logsTable').DataTable({
            searching: false,
            processing: true,
            serverSide: true,
            paging: false,      
            info: false,       
            lengthChange: false, 
            ajax: {
                url: apiUrlBase,
                type: 'POST',
                contentType: "application/json",
                data: function (d) {
                    const requestData = {
                        draw: d.draw,
                        start: d.start,
                        length: d.length,
                        
                        searchValue: $('#searchBox').val()
                    };
                    console.log("Sending request data:", requestData); // Debugging line
                    return JSON.stringify(requestData);
                },
                dataFilter: function(data) {
                    console.log("Received response data:", data); // Debugging line
                    let json = JSON.parse(data);
                    let logs = json.data;

                    // Filter the logs if the user is not an admin
                    if (!isAdmin) {
                        logs = logs.filter(log => log.level !== 'admin');
                    }

                    return JSON.stringify({
                        draw: json.draw,
                        recordsTotal: logs.length,
                        recordsFiltered: logs.length,
                        data: logs
                    });
                }
            },
            columns: [
                { data: 'id', width: '50px' },
                { data: 'timestamp', width: '150px' },
                { 
                    data: 'level',
                    render: function(data) {
                        return `<span class="badge bg-secondary">${data}</span>`;
                    },
                    width: '80px'
                },
                { 
                    data: 'type',
                    render: function(data) {
                        const colorMap = {
                            'INFO': 'bg-success',
                            'WARNING': 'bg-warning',
                            'ERROR': 'bg-danger',
                            'CRITICAL': 'bg-dark'
                        };
                        return `<span class="badge ${colorMap[data] || 'bg-secondary'}">${data}</span>`;
                    },
                    width: '80px'
                },
                { data: 'message' }
            ],
            order: [[0, 'desc']],
            pageLength: 25,
            lengthMenu: [[10, 25, 50, 100, -1], [10, 25, 50, 100, "All"]],
            responsive: true,
            autoWidth: false
        });

        // Refresh table on search and date filter
        $('#searchBox').on('change keyup', function () {
            logsTable.ajax.reload();
        });
    }

    // Initialize table on page load
    initializeLogsTable();
});