document.addEventListener('DOMContentLoaded', function () {
    let lineSelector = document.getElementById('lineSelector');
    let apiUrlBase = 'http://localhost:5000/api/historical-data/';
    let tableTab = document.getElementById('table-tab');
    let graphTab = document.getElementById('graph-tab');
    let tableView = document.getElementById('tableView');
    let graphView = document.getElementById('graphView');
    let graphCanvas = document.getElementById('dataChart');
    let chartTypeSelector = document.getElementById('chartTypeSelector');

    if (!graphCanvas) {
        console.error("Graph canvas not found!");
        return;
    }

    let startDateTimeFilter = document.getElementById('startDateTimeFilter');
    let endDateTimeFilter = document.getElementById('endDateTimeFilter');

    let graphContext = graphCanvas.getContext('2d');
    let graphInstance = null;
    let currentGraphData = null; // Store the fetched data

    // Event listeners to toggle views
    tableTab.addEventListener('click', function () {
        tableView.classList.add('show', 'active');
        graphView.classList.remove('show', 'active');
    });

    graphTab.addEventListener('click', function () {
        graphView.classList.add('show', 'active');
        tableView.classList.remove('show', 'active');
        if (!currentGraphData) {
            // fetchGraphData(lineSelector.value); // Fetch only if no data yet
            fetchHistoricalData(lineSelector.value);
        } else {
            plotGraph(currentGraphData); // Re-plot with existing data
        }
    });

    document.getElementById('dateFilter').addEventListener('change', function() {
        console.log("Date filter changed to:", this.value);
        // fetchGraphData(lineSelector.value);
        fetchHistoricalData(lineSelector.value);
    });

    // Chart type change listener
    chartTypeSelector.addEventListener('change', function () {
        if (currentGraphData) {
            plotGraph(currentGraphData); // Immediately re-plot with stored data
        } else {
            // fetchGraphData(lineSelector.value); // Fetch if no data yet
            fetchHistoricalData(lineSelector.value);
        }
    });

    
    let availableColumns = {
        "line4": ["timestamp", "r01", "r02", "r03", "r04", "r05", "r06", "r07", "r08"],
        "line5": ["timestamp", "timezone", "r01", "r02", "r03", "r04", "r05", "r06", "r07", "r08", "r09", "r10", "r11", "r12", "r13", "r14", "r15", "r16", "r17"]
    };

    let table = null;
    // let availableDates = [];

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
    table.ajax.reload();
});

startDateTimeFilter.addEventListener('change', function() {
    console.log("Start datetime changed:", this.value);
    table.ajax.reload();
});

endDateTimeFilter.addEventListener('change', function() {
    console.log("End datetime changed:", this.value);
    table.ajax.reload();
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
            columns: columns,
            ajax: {
                url: apiUrl,
                type: 'POST',
                contentType: "application/json",
                data: function(d) {
                    const requestData = {
                        length: d.length,
                        dateFilter: $('#dateFilter').val(),
                        startDateTime: $('#startDateTimeFilter').val(),
                        endDateTime: $('#endDateTimeFilter').val(),
                    };
                    console.log("Request Data:", requestData);
                    
                    // Fetch graph data when table data is requested
                    fetchAndUpdateGraph(apiUrl, requestData);
                    
                    return JSON.stringify(requestData);
                },
                error: function(xhr, error, thrown) {
                    console.error("Data fetch error:", xhr.responseText, error, thrown);
                    alert("Error fetching data. Please try again.");
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
    
    // Separate function to fetch and update graph
    function fetchAndUpdateGraph(apiUrl, requestData) {
        fetch(apiUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        })
        .then(response => response.json())
        .then(response => {
            if (!response.success || !Array.isArray(response.data)) {
                throw new Error("Invalid data format received");
            }
    
            currentGraphData = response.data;
    
            if (currentGraphData.length === 0) {
                console.warn("No data available for graph");
                // Clear or reset graph if needed
                return;
            }
    
            plotGraph(currentGraphData);
        })
        .catch(error => {
            console.error("Graph update error:", error);
            // Handle graph error (maybe show placeholder or error message)
        });
    }
    
    function plotGraph(data) {
        if (!graphContext) {
            console.error("Graph context is null!");
            return;
        }

        const chartType = chartTypeSelector.value;

        if (graphInstance) {
            graphInstance.destroy();
        }

        if (chartType === 'line') {
            let timestamps = data.map(item => item.timestamp);
            let sensors = Object.keys(data[0]).filter(key => key.startsWith('r'));

            let datasets = sensors.map(sensor => ({
                label: sensor.toUpperCase(),
                data: data.map(item => item[sensor] || 0),
                borderColor: getRandomColor(),
                fill: false
            }));

            graphInstance = new Chart(graphContext, {
                type: 'line',
                data: { labels: timestamps, datasets },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: { title: { display: true, text: 'Timestamp' }, ticks: { maxRotation: 45, minRotation: 45 } },
                        y: { title: { display: true, text: 'Sensor Value' }, beginAtZero: true, suggestedMax: Math.max(...datasets.flatMap(d => d.data)) * 1.1 }
                    }
                }
            });
        } else if (chartType === 'pie') {
            let sensors = Object.keys(data[0]).filter(key => key.startsWith('r'));
            let averages = sensors.map(sensor => {
                const total = data.reduce((sum, item) => sum + (item[sensor] || 0), 0);
                return total / data.length;
            });

            graphInstance = new Chart(graphContext, {
                type: 'pie',
                data: {
                    labels: sensors.map(sensor => sensor.toUpperCase()),
                    datasets: [{ data: averages, backgroundColor: sensors.map(() => getRandomColor()), borderColor: '#fff', borderWidth: 2 }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'top', labels: { font: { size: 14 }, color: '#333' } },
                        tooltip: { callbacks: { label: context => `${context.label}: ${context.raw.toFixed(2)}` } }
                    }
                }
            });
        } else if (chartType === 'bar') {
            let sensors = Object.keys(data[0]).filter(key => key.startsWith('r'));
            let averages = sensors.map(sensor => {
                const total = data.reduce((sum, item) => sum + (item[sensor] || 0), 0);
                return total / data.length;
            });

            graphInstance = new Chart(graphContext, {
                type: 'bar',
                data: {
                    labels: sensors.map(sensor => sensor.toUpperCase()),
                    datasets: [{ label: 'Average Sensor Values', data: averages, backgroundColor: sensors.map(() => getRandomColor()), borderColor: '#333', borderWidth: 1 }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: { title: { display: true, text: 'Sensors' }, ticks: { color: '#333' } },
                        y: { title: { display: true, text: 'Average Value' }, beginAtZero: true, ticks: { color: '#333' } }
                    },
                    plugins: {
                        legend: { position: 'top', labels: { font: { size: 14 }, color: '#333' } },
                        tooltip: { callbacks: { label: context => `${context.label}: ${context.raw.toFixed(2)}` } }
                    }
                }
            });
        } else if (chartType === 'area') {
            let timestamps = data.map(item => item.timestamp);
            let sensors = Object.keys(data[0]).filter(key => key.startsWith('r'));

            let datasets = sensors.map(sensor => ({
                label: sensor.toUpperCase(),
                data: data.map(item => item[sensor] || 0),
                backgroundColor: getRandomColor(), // Fill color
                borderColor: getRandomColor(), // Line color
                fill: true, // Enable area fill
                tension: 0.3 // Smooth lines
            }));

            graphInstance = new Chart(graphContext, {
                type: 'line', // Area chart is a line chart with fill
                data: { labels: timestamps, datasets },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: { title: { display: true, text: 'Timestamp' }, ticks: { maxRotation: 45, minRotation: 45 } },
                        y: { 
                            title: { display: true, text: 'Sensor Value' }, 
                            beginAtZero: true, 
                            suggestedMax: Math.max(...datasets.flatMap(d => d.data)) * 1.1,
                            stacked: true // Stack areas (optional, set to false for overlap)
                        }
                    },
                    plugins: {
                        legend: { position: 'top', labels: { font: { size: 14 }, color: '#333' } },
                        tooltip: { callbacks: { label: context => `${context.dataset.label}: ${context.raw.toFixed(2)}` } }
                    }
                }
            });
        } else if (chartType === 'scatter') {
            let timestamps = data.map(item => item.timestamp);
            let sensors = Object.keys(data[0]).filter(key => key.startsWith('r'));

            let datasets = sensors.map(sensor => ({
                label: sensor.toUpperCase(),
                data: data.map(item => ({
                    x: item.timestamp,
                    y: item[sensor] || 0
                })),
                backgroundColor: getRandomColor(),
                pointRadius: 5, // Size of points
                pointHoverRadius: 7 // Size on hover
            }));

            graphInstance = new Chart(graphContext, {
                type: 'scatter',
                data: { datasets }, // No labels here, timestamps are in data points
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: { 
                            type: 'category', // Treat timestamps as categories
                            title: { display: true, text: 'Timestamp' }, 
                            ticks: { maxRotation: 45, minRotation: 45 } 
                        },
                        y: { 
                            title: { display: true, text: 'Sensor Value' }, 
                            beginAtZero: true, 
                            suggestedMax: Math.max(...datasets.flatMap(d => d.data.map(p => p.y))) * 1.1 
                        }
                    },
                    plugins: {
                        legend: { position: 'top', labels: { font: { size: 14 }, color: '#333' } },
                        tooltip: { callbacks: { label: context => `${context.dataset.label}: ${context.raw.y.toFixed(2)}` } }
                    }
                }
            });
        }

        console.log(`${chartType} chart updated successfully!`);
    }

    function getRandomColor() {
        return `rgba(${Math.floor(Math.random() * 255)}, ${Math.floor(Math.random() * 255)}, ${Math.floor(Math.random() * 255)}, 1)`;
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