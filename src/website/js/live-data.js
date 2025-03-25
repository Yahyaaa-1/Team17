let selectedLine = "line4";
let charts = {};
let expandedChart = null;

const sensorThresholds = {
    
        // Line 4
        r01: { min: 129.10 * 0.7, max: 129.10 * 1.3 }, // min = 89.63, max = 166.45
        r02: { min: 264.81 * 0.7, max: 264.81 * 1.3 }, // min = 183.62, max = 340.99
        r03: { min: 255.77 * 0.7, max: 255.77 * 1.3 }, // min = 177.61, max = 330.84
        r04: { min: 309.04 * 0.7, max: 309.04 * 1.3 }, // min = 214.42, max = 398.22
        r05: { min: 253.94 * 0.7, max: 253.94 * 1.3 }, // min = 176.40, max = 327.60
        r06: { min: 268.39 * 0.7, max: 268.39 * 1.3 }, // min = 186.47, max = 346.29
        r07: { min: 263.18 * 0.7, max: 263.18 * 1.3 }, // min = 182.73, max = 339.35
        r08: { min: 210.97 * 0.7, max: 210.97 * 1.3 }, // min = 146.51, max = 272.10
    
        // Line 5
        r01: { min: 133.31 * 0.7, max: 133.31 * 1.3 }, // min = 70.78, max = 131.46
        r02: { min: 203.01 * 0.7, max: 203.01 * 1.3 }, // min = 108.04, max = 200.64
        r03: { min: 164.63 * 0.7, max: 164.63 * 1.3 }, // min = 97.92, max = 181.84
        r04: { min: 223.17 * 0.7, max: 223.17 * 1.3 }, // min = 123.77, max = 230.87
        r05: { min: 183.02 * 0.7, max: 183.02 * 1.3 }, // min = 107.75, max = 200.10
        r06: { min: 280.04 * 0.7, max: 280.04 * 1.3 }, // min = 152.34, max = 283.92
        r07: { min: 277.71 * 0.7, max: 277.71 * 1.3 }, // min = 150.91, max = 280.25
        r08: { min: 229.20 * 0.7, max: 229.20 * 1.3 }, // min = 127.39, max = 236.58
        r09: { min: 227.06 * 0.7, max: 227.06 * 1.3 }, // min = 139.31, max = 258.73
        r10: { min: 321.24 * 0.7, max: 321.24 * 1.3 }, // min = 179.98, max = 334.26
        r11: { min: 225.51 * 0.7, max: 225.51 * 1.3 }, // min = 128.49, max = 238.63
        r12: { min: 297.59 * 0.7, max: 297.59 * 1.3 }, // min = 171.16, max = 319.72
        r13: { min: 238.31 * 0.7, max: 238.31 * 1.3 }, // min = 147.90, max = 274.68
        r14: { min: 284.27 * 0.7, max: 284.27 * 1.3 }, // min = 160.53, max = 298.13
        r15: { min: 174.30 * 0.7, max: 174.30 * 1.3 }, // min = 96.32, max = 178.88
        r16: { min: 220.43 * 0.7, max: 220.43 * 1.3 }, // min = 118.41, max = 219.91
        r17: { min: 151.66 * 0.7, max: 151.66 * 1.3 }, // min = 85.14, max = 158.12
    
    
};

document.addEventListener("DOMContentLoaded", function () {
    initializeCharts(selectedLine);
    fetchLiveData();
    // Initial chart creation 
    function initTrafficLightChart() {
        updateTrafficLightPieChart(0, 0, 0);
    }

    // Call this when the page loads
    document.addEventListener('DOMContentLoaded', initTrafficLightChart);


    document.getElementById("lineSelector").addEventListener("change", function () {
        selectedLine = this.value;
        initializeCharts(selectedLine);
        fetchLiveData();
    });

    setInterval(fetchLiveData, 5000); // Poll every 5 seconds
});

function fetchLiveData() {
    fetch(`http://127.0.0.1:5000/api/live-data/${selectedLine}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateCharts(data.data);
                updateAnalytics(data.data);
            } else {
                console.error("Failed to fetch live data");
            }
        })
        .catch(error => console.error("Error fetching data:", error));
}

function initializeCharts(line) {
    const container = document.getElementById("chartsContainer");
    container.innerHTML = "";
    charts = {};

    const sensors = (line === "line4") 
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

function updateCharts(liveData) {
    Object.keys(liveData).forEach(sensor => {
        if (sensor !== "timestamp" && charts[sensor]) {
            const timestamp = new Date().toLocaleTimeString();
            const value = liveData[sensor];
            const newData = { x: timestamp, y: value };

            const color = getTrafficLightColor(sensor, value);

            // Update chart color
            charts[sensor].updateOptions({
                colors: [color]
            });

            // Add new data point, keeping only the last 50 points
            const updatedData = [...(charts[sensor].w.config.series[0].data), newData].slice(-50);
            charts[sensor].updateSeries([{ name: sensor, data: updatedData }]);

            // If expanded view is open for this sensor, update it too
            if (expandedChart && expandedChart.sensor === sensor) {
                updateExpandedChart(sensor, newData, color);
            }
        }
    });
}

function expandChart(sensor) {
    const expandedContainer = document.getElementById("expandedChartContainer");
    const expandedChartDiv = document.getElementById("expandedChart");

    expandedContainer.style.display = "flex";
    expandedChartDiv.innerHTML = "";

    expandedChart = {
        sensor: sensor,
        instance: new ApexCharts(expandedChartDiv, {
            chart: { type: "line", height: 400, animations: { enabled: false } },
            series: [{ name: sensor, data: charts[sensor].w.config.series[0].data }],
            colors: charts[sensor].w.config.colors,
            xaxis: { type: "datetime", labels: { format: "HH:mm:ss" } },
            yaxis: { title: { text: sensor } }
        })
    };

    expandedChart.instance.render();
}

function updateExpandedChart(sensor, newData, color) {
    if (!expandedChart || expandedChart.sensor !== sensor) return;

    expandedChart.instance.updateOptions({
        colors: [color]
    });

    const updatedData = [...(expandedChart.instance.w.config.series[0].data), newData].slice(-50);
    expandedChart.instance.updateSeries([{ name: sensor, data: updatedData }]);
}

function closeExpandedChart() {
    document.getElementById("expandedChartContainer").style.display = "none";
    expandedChart = null;
}
let trafficLightChart;

function updateAnalytics(liveData) {
    // Filter out non-sensor fields
    const sensors = Object.keys(liveData).filter(key => key !== "timestamp" && key !== "timezone");
    const totalSensors = sensors.length;
    let totalTemperature = 0;
    let greenCount = 0;
    let amberCount = 0;
    let redCount = 0;

    sensors.forEach(sensor => {
        const value = liveData[sensor];
        totalTemperature += value;

        const color = getTrafficLightColor(sensor, value);
        if (color === '#00E396') greenCount++;
        else if (color === '#FFA500') amberCount++;
        else if (color === '#FF0000') redCount++;
    });

    const averageTemperature = (totalTemperature / totalSensors).toFixed(2);

    document.getElementById("totalSensors").textContent = totalSensors;
    document.getElementById("averageTemperature").textContent = `${averageTemperature}°C`;
    updateTrafficLightPieChart(greenCount, amberCount, redCount);
}


function updateTrafficLightPieChart(greenCount, amberCount, redCount) {
    const options = {
        series: [greenCount, amberCount, redCount],
        chart: {
            type: 'pie',
            height: 300,
        },
        labels: ['Green', 'Amber', 'Red'], colors: ['#00E396', '#FFA500', '#FF0000'],
        responsive: [{ breakpoint: 480, options: { chart: { width: 200 }, legend: { position: 'bottom' } } }],
        plotOptions: {
            pie: {
                donut: {
                    labels: {
                        show: true,
                        total: {
                            show: true,
                            label: 'Total Sensors',
                            formatter: function (w) {
                                return w.globals.seriesTotals.reduce((a, b) => a + b, 0);
                            }
                        }
                    }
                }
            }
        },
        legend: { position: 'right', offsetY: 0, height: 230, }, title: { text: 'Sensor Status Distribution', align: 'center' }
    };

    // If chart doesn't exist, create it
    if (!trafficLightChart) {
        trafficLightChart = new ApexCharts(
            document.querySelector("#trafficLightPieChart"), 
            options
        );
        trafficLightChart.render();
    } else {
        // Update existing chart
        trafficLightChart.updateSeries([greenCount, amberCount, redCount]);
    }
}



function getTrafficLightColor(sensor, value) {
    const thresholds = sensorThresholds[sensor];

    if (!thresholds) return '#00E396';  // Green if no thresholds

    const range = thresholds.max - thresholds.min;
    const buffer = range * 0.1;  // 10% buffer around min/max for amber zone

    if (value >= thresholds.min - buffer && value <= thresholds.max + buffer) {
        return '#00E396';  //  Green: In or close to normal range
    } else if (value >= thresholds.min - 2 * buffer && value <= thresholds.max + 2 * buffer) {
        return '#FFA500';  // Amber: Slightly outside the comfort zone
    } else {
        return '#FF0000';  //  Red: Far outside the normal range
    }
}

function fetchAverageTemperature(line, period) {
    const apiUrl = `http://localhost:5000/api/average-temperature/${line}`;
    
    fetch(apiUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ period: period })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displayAverages(data.averages);
        } else {
            console.error("Failed to fetch average temperature:", data.error);
        }
    })
    .catch(error => console.error("API error:", error));
}

function displayAverages(averages) {
    const averageContainer = document.getElementById('averageContainer');
    averageContainer.innerHTML = '';

    for (const [sensor, avg] of Object.entries(averages)) {
        const card = document.createElement('div');
        card.classList.add('average-card');

        // Format sensor name
        const sensorName = document.createElement('h4');
        sensorName.textContent = sensor.replace('avg_', '').toUpperCase();

        const avgValue = document.createElement('p');
        avgValue.textContent = `${avg.toFixed(2)}°C`;

        card.appendChild(sensorName);
        card.appendChild(avgValue);
        averageContainer.appendChild(card);
    }
}

document.addEventListener('DOMContentLoaded', function () {
    const lineSelector = document.getElementById('lineSelector');
    const periodSelector = document.getElementById('periodSelector');

    lineSelector.addEventListener('change', function () {
        fetchAverageTemperature(this.value, periodSelector.value);
    });

    periodSelector.addEventListener('change', function () {
        fetchAverageTemperature(lineSelector.value, this.value);
    });

    // Initial fetch
    fetchAverageTemperature(lineSelector.value, periodSelector.value);
});