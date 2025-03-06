document.addEventListener('DOMContentLoaded', function () {
    let lineSelector = document.getElementById('lineSelector');
    let apiUrlBase = 'http://localhost:5000/api/historical/';
    // let availableDatesUrlBase = 'http://localhost:5000/api/available-dates/';
    
    let availableColumns = {
        "line4": ["timestamp", "r01", "r02", "r03", "r04", "r05", "r06", "r07", "r08"],
        "line5": ["timestamp", "timezone", "r01", "r02", "r03", "r04", "r05", "r06", "r07", "r08", "r09", "r10", "r11", "r12", "r13", "r14", "r15", "r16", "r17"]
    };

    let table = null;
    let availableDates = [];

    // // Gets list of dates with available data
    // function fetchAvailableDates(line) {
    //     let availableDatesUrl = availableDatesUrlBase + line;
    //     console.log(`Getting dates for: ${availableDatesUrl}`);

    //     fetch(availableDatesUrl)
    //         .then(response => response.json())
    //         .then(data => {
    //             if (data.success) {
    //                 availableDates = data.dates;
    //                 updateDatePicker();
    //             } else {
    //                 console.error("Failed to fetch dates:", data.error);
    //             }
    //         })
    //         .catch(error => console.error("API error:", error));
    // }

    // Populates the date picker dropdown
    function updateDatePicker() {
        let dateInput = document.getElementById('dateFilter');
        dateInput.innerHTML = "";

        availableDates.forEach(date => {
            let option = document.createElement("option");
            option.value = date;
            option.textContent = date;
            dateInput.appendChild(option);
        });

        dateInput.addEventListener('change', function () {
            console.log("Date selected:", this.value);
            table.ajax.reload();
        });

        console.log("Date picker updated with:", availableDates);
    }

    // Sets up the data table with historical data
    function initializeTable(line) {
        let apiUrl = apiUrlBase + line;
        let columns = availableColumns[line].map(col => ({ data: col }));

        console.log(`Setting up table for ${line}`);

        if ($.fn.DataTable.isDataTable("#lineTable")) {
            console.log("Clearing existing table");
            table.destroy();
            $('#lineTable').empty();
        }

        $('#lineTable').html(`<thead><tr>${columns.map(col => `<th>${col.data}</th>`).join("")}</tr></thead><tbody></tbody>`);

        table = $('#lineTable').DataTable({
            processing: true,
            serverSide: true,
            ajax: {
                url: apiUrl,
                type: 'POST',
                contentType: "application/json",
                data: function (d) {
                    return JSON.stringify({
                        length: d.length,
                        dateFilter: $('#dateFilter').val(),
                        searchValue: $('#searchBox').val()
                    });
                },
                error: function (xhr, error, thrown) {
                    console.error("Table error: ", xhr.responseText, error, thrown);
                }
            },
            order: [[0, 'desc']],
            responsive: true,
            autoWidth: false,
            columns: columns
        });

        // Refresh table when filters change
        $('#dateFilter, #searchBox').off('change keyup').on('change keyup', function () {
            console.log("Refreshing table data");
            table.ajax.reload();
        });

        // fetchAvailableDates(line);
    }

    // Initial table setup with delay
    setTimeout(() => {
        initializeTable(lineSelector.value);
    }, 500);

    // Handle line selection changes
    lineSelector.addEventListener("change", function () {
        console.log(`Switching to line: ${this.value}`);
        initializeTable(this.value);
    });
});