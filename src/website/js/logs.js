document.addEventListener('DOMContentLoaded', function () {
    let apiUrlBase = 'http://localhost:5000/api/logs';
    let logsTable = null;
    const isAdmin = JSON.parse(sessionStorage.getItem('isAdmin'));

    function initializeLogsTable() {
        logsTable = $('#logsTable').DataTable({
            processing: true,
            serverSide: true,
            ajax: {
                url: apiUrlBase,
                type: 'POST',
                contentType: "application/json",
                data: function (d) {
                    return JSON.stringify({
                        length: d.length,
                        dateFilter: $('#dateFilter').val(),
                        searchValue: $('#searchBox').val()
                    });
                },
                dataFilter: function(data) {
                    let json = JSON.parse(data);
                    return JSON.stringify({
                        draw: 1,
                        recordsTotal: json.data.length,
                        recordsFiltered: json.data.length,
                        data: json.data
                    });
                }
            },
            columns: [
                { 
                    data: 'id',
                    width: '50px'
                },
                { 
                    data: 'timestamp',
                    width: '150px'
                },
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
                { 
                    data: 'message',
                    render: function(data) {
                        return data; // Return full message without truncation
                    }
                }
            ],
            order: [[0, 'desc']],
            pageLength: 25,
            lengthMenu: [[10, 25, 50, 100, -1], [10, 25, 50, 100, "All"]],
            responsive: true,
            autoWidth: false
        });

        // Refresh table on search and date filter
        $('#searchBox, #dateFilter').on('change keyup', function () {
            logsTable.ajax.reload();
        });
    }

    // Initialize table on page load
    initializeLogsTable();
});