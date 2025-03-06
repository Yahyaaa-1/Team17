let selectedLine = "line4";
let charts = {};
let expandedChart = null;

document.addEventListener("DOMContentLoaded", function () {
    initializeCharts(selectedLine);
    fetchLiveData();

    document.getElementById("lineSelector").addEventListener("change", function () {
        selectedLine = this.value;
        console.log(`Switching to line: ${selectedLine}`);
        initializeCharts(selectedLine);
        fetchLiveData();
    });

    setInterval(fetchLiveData, 5000); // Update every 5 seconds
});

// Gets the latest sensor readings from the API
function fetchLiveData() {
    console.log(`Getting latest data for ${selectedLine}`);

    fetch(`http://127.0.0.1:5000/api/live-data/${selectedLine}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP Error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                console.log(`Latest readings:`, data.data);
                updateCharts(data.data);
            } else {
                console.error("Failed to get live data");
            }
        })
        .catch(error => console.error("API Error:", error));
}

// Sets up the initial chart layout
function initializeCharts(line) {
    const chartsContainer = document.getElementById("chartsContainer");
    chartsContainer.innerHTML = "";

    let sensors = line === "line4"
        ? ["r01", "r02", "r03", "r04", "r05", "r06", "r07", "r08"]
        : ["r01", "r02", "r03", "r04", "r05", "r06", "r07", "r08", "r09", "r10", "r11", "r12", "r13", "r14", "r15", "r16", "r17"];

    sensors.forEach(sensor => {
        const chartDiv = document.createElement("div");
        chartDiv.classList.add("col-md-3", "mb-4", "mini-chart");
        chartDiv.innerHTML = `
            <div class="chart-title">
                <a href="pages/sensor-data.html?sensor=${sensor}&line=${line}" class="sensor-link">${sensor}</a>
            </div>
            <div id="chart-${sensor}" style="height: 150px;"></div>
        `;

        // Redirect when clicking on the entire chart box
        chartDiv.addEventListener("click", () => {
            window.location.href = `pages/sensor-data.html?sensor=${sensor}&line=${line}`;
        });

        chartsContainer.appendChild(chartDiv);

        charts[sensor] = new ApexCharts(document.querySelector(`#chart-${sensor}`), {
            chart: { type: "line", height: 150, animations: { enabled: false } },
            series: [{ name: sensor, data: [] }],
            colors: ['#00E396'],
            xaxis: { labels: { show: false } },
            yaxis: { labels: { show: false } }
        });

        charts[sensor].render();
    });
}


// Updates all charts with new sensor data
function updateCharts(liveData) {
    Object.keys(liveData).forEach(sensor => {
        if (sensor !== "timestamp" && charts[sensor]) {
            let timestamp = new Date().toLocaleTimeString();
            let newData = { x: timestamp, y: liveData[sensor] };

            // Update mini chart
            charts[sensor].updateSeries([{ 
                name: sensor, 
                data: [...(charts[sensor].w.config.series[0].data || []), newData].slice(-50)
            }]);

            // Update expanded view if active
            if (expandedChart && expandedChart.sensor === sensor) {
                updateExpandedChart(sensor, newData);
            }
        }
    });
}

// Shows detailed view when clicking a chart
function expandChart(sensor) {
    console.log(`Opening detailed view for ${sensor}`);

    const expandedContainer = document.getElementById("expandedChartContainer");
    const expandedChartDiv = document.getElementById("expandedChart");

    expandedContainer.style.display = "flex";
    expandedChartDiv.innerHTML = "";

    expandedChart = {
        instance: new ApexCharts(expandedChartDiv, {
            chart: { type: "line", height: 400, animations: { enabled: false } },
            series: [{ name: sensor, data: [] }],
            xaxis: { type: "datetime", labels: { format: "HH:mm:ss" } },
            yaxis: { title: { text: sensor } }
        }),
        sensor: sensor
    };

    expandedChart.instance.render();
}

// Updates the expanded chart view
function updateExpandedChart(sensor, newData) {
    if (!expandedChart || expandedChart.sensor !== sensor) return;

    expandedChart.instance.updateSeries([{ 
        name: sensor, 
        data: [...(expandedChart.instance.w.config.series[0].data || []), newData].slice(-50)
    }]);
}

// Closes the detailed view
function closeExpandedChart() {
    document.getElementById("expandedChartContainer").style.display = "none";
    expandedChart = null;
}