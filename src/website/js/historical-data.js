document.addEventListener('DOMContentLoaded', function () {
    let lineSelector = document.getElementById('lineSelector');
    let apiUrlBase = 'http://localhost:5000/api/historical-data/';
    let tableTab = document.getElementById('table-tab');
    let tableView = document.getElementById('tableView');

    let startDateTimeFilter = document.getElementById('startDateTimeFilter');
    let endDateTimeFilter = document.getElementById('endDateTimeFilter');

    let table = null;

    let availableColumns = {
        "line4": ["timestamp", "timezone","r01", "r02", "r03", "r04", "r05", "r06", "r07", "r08"],
        "line5": ["timestamp", "timezone", "r01", "r02", "r03", "r04", "r05", "r06", "r07", "r08", "r09", "r10", "r11", "r12", "r13", "r14", "r15", "r16", "r17"]
    };

    // Set default date range (e.g., last 7 days)
    function setDefaultDateRange() {
        let now = new Date();
        let sevenDaysAgo = new Date(now.getTime() - (7 * 24 * 60 * 60 * 1000));
        
        // Format dates for datetime-local input
        startDateTimeFilter.value = formatDateTimeLocal(sevenDaysAgo);
        endDateTimeFilter.value = formatDateTimeLocal(now);
    }

    // Helper function to format date for datetime-local input
    function formatDateTimeLocal(date) {
        const pad = (num) => num.toString().padStart(2, '0');
        return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
    }

    // Set default date range on page load
    setDefaultDateRange();

    // Add event listeners for datetime range filters
    startDateTimeFilter.addEventListener('change', function() {
        console.log("Start datetime changed:", this.value);
        fetchHistoricalData(lineSelector.value);
    });

    endDateTimeFilter.addEventListener('change', function() {
        console.log("End datetime changed:", this.value);
        fetchHistoricalData(lineSelector.value);
    });

    document.getElementById('dateFilter').addEventListener('change', function() {
        console.log("Date filter changed to:", this.value);
        fetchHistoricalData(lineSelector.value);
    });

    function fetchHistoricalData(line) {
        const apiUrl = `${apiUrlBase}${line}`;
        console.log(`Fetching historical data from ${apiUrl}`);

        let columns = availableColumns[line].map(col => {
            if (col === "timestamp") {
                return { data: col, type: "date" };
            }
            return { data: col, type: "num" };
        });

        // Initialize or reset table structure
        if ($.fn.DataTable.isDataTable("#lineTable")) {
            table.destroy();
            $('#lineTable').empty();
        }

        // Create table structure
        $('#lineTable').html(`
            <thead>
                <tr>${columns.map(col => `<th>${col.data}</th>`).join("")}</tr>
            </thead>
            <tbody></tbody>
        `);

        // Initialize DataTable with server-side processing
        table = $('#lineTable').DataTable({
            processing: true,
            serverSide: true,
            searching: false,
            order: [[0, 'desc']], 
            responsive: true,
            autoWidth: false,
            pageLength: -1, 
            lengthChange: false,
            scrollY: '600px', 
            scrollCollapse: true,
            scroller: true, 
            columns: columns,
            ajax: {
                url: apiUrl,
                type: 'POST',
                contentType: "application/json",
                data: function(d) {
                    const requestData = {
                        length: -1, // Request all entries
                        dateFilter: $('#dateFilter').val(),
                        startDateTime: $('#startDateTimeFilter').val(),
                        endDateTime: $('#endDateTimeFilter').val(),
                    };
                    console.log("Request Data:", requestData);
                    
                    return JSON.stringify(requestData);
                },
                error: function(xhr, error, thrown) {
                    console.error("Data fetch error:", xhr.responseText, error, thrown);
                },
                dataSrc: function(response) {
                    if (!response.success) {
                        console.error("API Error:", response.error);
                        return [];
                    }
                    return response.data;
                }
            },
            columns: columns,
            drawCallback: function(settings) {
                const api = this.api();
                const response = api.ajax.json();
                if (response) {
                    api.page.info().recordsTotal = response.recordsTotal;
                    api.page.info().recordsFiltered = response.recordsFiltered;
                }
            }
        });
    }

    // Initial table setup with delay
    setTimeout(() => {
        fetchHistoricalData(lineSelector.value);
    }, 500);

    // Handle line selection changes
    lineSelector.addEventListener("change", function () {
        console.log(`Switching to line: ${this.value}`);
        fetchHistoricalData(lineSelector.value);
    });
});