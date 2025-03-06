let selectedLine = "line4";
let charts = {};
let expandedChart = null;

const sensorThresholds = {
    
        // Line 4
        r01: { min: 128.04 * 0.7, max: 128.04 * 1.3 }, // min = 89.63, max = 166.45
        r02: { min: 262.31 * 0.7, max: 262.31 * 1.3 }, // min = 183.62, max = 340.99
        r03: { min: 253.73 * 0.7, max: 253.73 * 1.3 }, // min = 177.61, max = 330.84
        r04: { min: 306.32 * 0.7, max: 306.32 * 1.3 }, // min = 214.42, max = 398.22
        r05: { min: 252.00 * 0.7, max: 252.00 * 1.3 }, // min = 176.40, max = 327.60
        r06: { min: 266.38 * 0.7, max: 266.38 * 1.3 }, // min = 186.47, max = 346.29
        r07: { min: 261.04 * 0.7, max: 261.04 * 1.3 }, // min = 182.73, max = 339.35
        r08: { min: 209.31 * 0.7, max: 209.31 * 1.3 }, // min = 146.51, max = 272.10
    
        // Line 5
        r01: { min: 101.12 * 0.7, max: 101.12 * 1.3 }, // min = 70.78, max = 131.46
        r02: { min: 154.34 * 0.7, max: 154.34 * 1.3 }, // min = 108.04, max = 200.64
        r03: { min: 139.88 * 0.7, max: 139.88 * 1.3 }, // min = 97.92, max = 181.84
        r04: { min: 176.82 * 0.7, max: 176.82 * 1.3 }, // min = 123.77, max = 230.87
        r05: { min: 153.93 * 0.7, max: 153.93 * 1.3 }, // min = 107.75, max = 200.10
        r06: { min: 217.63 * 0.7, max: 217.63 * 1.3 }, // min = 152.34, max = 283.92
        r07: { min: 215.58 * 0.7, max: 215.58 * 1.3 }, // min = 150.91, max = 280.25
        r08: { min: 181.98 * 0.7, max: 181.98 * 1.3 }, // min = 127.39, max = 236.58
        r09: { min: 199.02 * 0.7, max: 199.02 * 1.3 }, // min = 139.31, max = 258.73
        r10: { min: 257.12 * 0.7, max: 257.12 * 1.3 }, // min = 179.98, max = 334.26
        r11: { min: 183.56 * 0.7, max: 183.56 * 1.3 }, // min = 128.49, max = 238.63
        r12: { min: 245.94 * 0.7, max: 245.94 * 1.3 }, // min = 171.16, max = 319.72
        r13: { min: 211.29 * 0.7, max: 211.29 * 1.3 }, // min = 147.90, max = 274.68
        r14: { min: 229.33 * 0.7, max: 229.33 * 1.3 }, // min = 160.53, max = 298.13
        r15: { min: 137.60 * 0.7, max: 137.60 * 1.3 }, // min = 96.32, max = 178.88
        r16: { min: 169.16 * 0.7, max: 169.16 * 1.3 }, // min = 118.41, max = 219.91
        r17: { min: 121.63 * 0.7, max: 121.63 * 1.3 }, // min = 85.14, max = 158.12
    
    
};

document.addEventListener("DOMContentLoaded", function () {
    initializeCharts(selectedLine);
    fetchLiveData();

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
        const div = document.createElement("div");
        div.classList.add("col-md-3", "mb-4", "mini-chart");
        div.innerHTML = `
            <div class="chart-title">${sensor}</div>
            <div id="chart-${sensor}" style="height: 150px;"></div>
        `;
        div.addEventListener("click", () => expandChart(sensor));
        container.appendChild(div);

        charts[sensor] = new ApexCharts(document.querySelector(`#chart-${sensor}`), {
            chart: { type: "line", height: 150, animations: { enabled: false } },
            series: [{ name: sensor, data: [] }],
            colors: ['#00E396'],  // Default to green
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

function getTrafficLightColor(sensor, value) {
    const thresholds = sensorThresholds[sensor];

    if (!thresholds) return '#00E396';  // Green if no thresholds

    const range = thresholds.max - thresholds.min;
    const buffer = range * 0.1;  // 10% buffer around min/max for amber zone

    if (value >= thresholds.min - buffer && value <= thresholds.max + buffer) {
        return '#00E396';  // 🟢 Green: In or close to normal range
    } else if (value >= thresholds.min - 2 * buffer && value <= thresholds.max + 2 * buffer) {
        return '#FFA500';  // 🟠 Amber: Slightly outside the comfort zone
    } else {
        return '#FF0000';  // 🔴 Red: Far outside the normal range
    }
}
