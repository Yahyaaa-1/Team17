let selectedLine = "line4";
let donutCharts = {};
let currentSlide = 0;
let trafficLightChart;
let barChart;
let scatterChart;
let liveScatterData = { normal: [], warning: [], critical: [] };

const sensorThresholds = {
    // Line 4
    r01: { min: 129.10 * 0.7, max: 129.10 * 1.3 },
    r02: { min: 264.81 * 0.7, max: 264.81 * 1.3 },
    r03: { min: 255.77 * 0.7, max: 255.77 * 1.3 },
    r04: { min: 309.04 * 0.7, max: 309.04 * 1.3 },
    r05: { min: 253.94 * 0.7, max: 253.94 * 1.3 },
    r06: { min: 268.39 * 0.7, max: 268.39 * 1.3 },
    r07: { min: 263.18 * 0.7, max: 263.18 * 1.3 },
    r08: { min: 210.97 * 0.7, max: 210.97 * 1.3 },
    // Line 5
    r01: { min: 133.31 * 0.7, max: 133.31 * 1.3 },
    r02: { min: 203.01 * 0.7, max: 203.01 * 1.3 },
    r03: { min: 164.63 * 0.7, max: 164.63 * 1.3 },
    r04: { min: 223.17 * 0.7, max: 223.17 * 1.3 },
    r05: { min: 183.02 * 0.7, max: 183.02 * 1.3 },
    r06: { min: 280.04 * 0.7, max: 280.04 * 1.3 },
    r07: { min: 277.71 * 0.7, max: 277.71 * 1.3 },
    r08: { min: 229.20 * 0.7, max: 229.20 * 1.3 },
    r09: { min: 227.06 * 0.7, max: 227.06 * 1.3 },
    r10: { min: 321.24 * 0.7, max: 321.24 * 1.3 },
    r11: { min: 225.51 * 0.7, max: 225.51 * 1.3 },
    r12: { min: 297.59 * 0.7, max: 297.59 * 1.3 },
    r13: { min: 238.31 * 0.7, max: 238.31 * 1.3 },
    r14: { min: 284.27 * 0.7, max: 284.27 * 1.3 },
    r15: { min: 174.30 * 0.7, max: 174.30 * 1.3 },
    r16: { min: 220.43 * 0.7, max: 220.43 * 1.3 },
    r17: { min: 151.66 * 0.7, max: 151.66 * 1.3 }
};

document.addEventListener("DOMContentLoaded", function() {
    initializeDonutSlider(selectedLine);
    initTrafficLightChart();
    initBarChart();
    initScatterChart();
    updateSensorSelector(selectedLine);
    fetchLiveData();

    document.getElementById("lineSelector").addEventListener("change", function () {
        selectedLine = this.value;
        initializeDonutSlider(selectedLine);
        updateSensorSelector(selectedLine);
        fetchLiveData();
    });

    document.getElementById('prevDonut').addEventListener('click', slideDonutsLeft);
    document.getElementById('nextDonut').addEventListener('click', slideDonutsRight);
    document.getElementById("sensorSelector").addEventListener("change", updateScatterChart);

    setInterval(fetchLiveData, 5000);
});

function initializeDonutSlider(line) {
    const slider = document.getElementById('donutSlider');
    slider.innerHTML = '';
    currentSlide = 0;
    donutCharts = {};

    const sensors = getSensorsForLine(line);

    sensors.forEach(sensor => {
        const chartContainer = document.createElement('div');
        chartContainer.className = 'donut-chart-container';
        
        const title = document.createElement('h5');
        title.textContent = sensor.toUpperCase();
        
        const chartDiv = document.createElement('div');
        chartDiv.className = 'donut-chart';
        chartDiv.id = `donut-chart-${sensor}`;

        // Redirect when clicking on the entire chart box
        chartDiv.addEventListener("click", () => {
            window.location.href = `pages/sensor-data.html?sensor=${sensor}&line=${line}`;
        });
        
        chartContainer.appendChild(title);
        chartContainer.appendChild(chartDiv);
        slider.appendChild(chartContainer);
        
        donutCharts[sensor] = new ApexCharts(document.querySelector(`#donut-chart-${sensor}`), {
            series: [0],
            chart: {
                type: 'donut',
                height: 180
            },
            labels: ['Current Value'],
            colors: ['#00E396'],
            plotOptions: {
                pie: {
                    donut: {
                        labels: {
                            show: true,
                            name: {
                                show: true,
                                fontSize: '12px'
                            },
                            value: {
                                show: true,
                                fontSize: '16px',
                                fontWeight: 'bold',
                                formatter: function(val) {
                                    return val.toFixed(2) + '°C';
                                }
                            }
                        }
                    }
                }
            }
        });
        
        donutCharts[sensor].render();
    });
}

function initBarChart() {
    barChart = new ApexCharts(document.querySelector("#barChart"), {
        chart: {
            type: 'bar',
            height: '100%',
            toolbar: {
                show: false
            }
        },
        series: [{
            name: 'Temperature',
            data: []
        }],
        xaxis: {
            categories: [],
            labels: {
                style: {
                    fontSize: '12px'
                }
            }
        },
        plotOptions: {
            bar: {
                borderRadius: 4,
                horizontal: false
            }
        },
        colors: ['#0066FF'],
        dataLabels: {
            enabled: false
        }
    });
    barChart.render();
}

function initScatterChart() {
    scatterChart = new ApexCharts(document.querySelector("#scatterChart"), {
        chart: {
            type: 'scatter',
            height: '100%',
            zoom: {
                enabled: true,
                type: 'xy'
            },
            toolbar: {
                show: true,
                tools: {
                    download: true,
                    selection: true,
                    zoom: true,
                    zoomin: true,
                    zoomout: true,
                    pan: true,
                    reset: true
                }
            },
            animations: {
                enabled: true,
                easing: 'linear',
                dynamicAnimation: {
                    speed: 1000
                }
            }
        },
        series: [
            { name: 'Normal', data: [] },
            { name: 'Warning', data: [] },
            { name: 'Critical', data: [] }
        ],
        xaxis: {
            type: 'datetime',
            title: {
                text: 'Time'
            },
            labels: {
                datetimeFormatter: {
                    year: 'yyyy',
                    month: "MMM 'yy",
                    day: 'dd MMM',
                    hour: 'HH:mm'
                }
            }
        },
        yaxis: {
            title: {
                text: 'Temperature (°C)'
            },
            min: 0,
            max: 400
        },
        colors: ['#00E396', '#FFA500', '#FF0000'],
        markers: {
            size: 6,
            strokeWidth: 0,
            hover: {
                size: 8
            }
        },
        tooltip: {
            shared: false,
            intersect: true,
            x: {
                format: 'dd MMM yyyy HH:mm:ss'
            },
            y: {
                formatter: function(val) {
                    return val.toFixed(2) + '°C';
                }
            }
        }
    });
    scatterChart.render();
}

function initTrafficLightChart() {
    trafficLightChart = new ApexCharts(document.querySelector("#trafficLightPieChart"), {
        series: [0, 0, 0],
        chart: {
            type: 'pie',
            height: '100%'
        },
        labels: ['Normal', 'Warning', 'Critical'],
        colors: ['#00E396', '#FFA500', '#FF0000'],
        responsive: [{
            breakpoint: 480,
            options: {
                chart: { width: 200 },
                legend: { position: 'bottom' }
            }
        }],
        plotOptions: {
            pie: {
                donut: {
                    labels: {
                        show: true,
                        total: {
                            show: true,
                            label: 'Total Sensors',
                            formatter: function(w) {
                                return w.globals.seriesTotals.reduce((a, b) => a + b, 0);
                            }
                        }
                    }
                }
            }
        },
        legend: { position: 'right', offsetY: 0, height: 230 },
        
    });
    trafficLightChart.render();
}

function getSensorsForLine(line) {
    return line === "line4" 
        ? ["r01", "r02", "r03", "r04", "r05", "r06", "r07", "r08"]
        : ["r01", "r02", "r03", "r04", "r05", "r06", "r07", "r08", "r09", "r10", "r11", "r12", "r13", "r14", "r15", "r16", "r17"];
}

function updateSensorSelector(line) {
    const selector = document.getElementById("sensorSelector");
    selector.innerHTML = '';
    
    const sensors = getSensorsForLine(line);
    sensors.forEach(sensor => {
        const option = document.createElement('option');
        option.value = sensor;
        option.textContent = sensor.toUpperCase();
        selector.appendChild(option);
    });
    
    // Reset live data when changing lines
    liveScatterData = { normal: [], warning: [], critical: [] };
    
    // Trigger initial update if sensors exist
    if (sensors.length > 0) {
        updateScatterChart();
    }
}

function updateScatterChart() {
    const selectedSensor = document.getElementById("sensorSelector").value;
    if (!selectedSensor) return;

    // Reset live data when switching sensors
    liveScatterData = { normal: [], warning: [], critical: [] };

    // First load historical data
    fetch(`http://127.0.0.1:5000/api/historical/${selectedLine}/${selectedSensor}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Categorize historical data
                data.data.forEach(item => {
                    const point = {
                        x: new Date(item.timestamp).getTime(),
                        y: item.value
                    };
                    const status = getTrafficLightStatus(selectedSensor, item.value);
                    
                    if (status === 'normal') liveScatterData.normal.push(point);
                    else if (status === 'warning') liveScatterData.warning.push(point);
                    else liveScatterData.critical.push(point);
                });

                scatterChart.updateOptions({
                    series: [
                        { name: 'Normal', data: liveScatterData.normal },
                        { name: 'Warning', data: liveScatterData.warning },
                        { name: 'Critical', data: liveScatterData.critical }
                    ],
                    xaxis: {
                        type: 'datetime'
                    }
                });
            } else {
                console.error("Failed to fetch historical data");
            }
        })
        .catch(error => console.error("Error fetching historical data:", error));
}

function updateLiveScatterChart(liveData) {
    const selectedSensor = document.getElementById("sensorSelector").value;
    if (!selectedSensor || !liveData[selectedSensor]) return;

    // Get current timestamp and value
    const timestamp = new Date().getTime();
    const temperature = liveData[selectedSensor];
    
    // Create new point
    const point = {
        x: timestamp,
        y: temperature
    };
    
    // Categorize the point
    const status = getTrafficLightStatus(selectedSensor, temperature);
    
    // Add to appropriate series
    if (status === 'normal') liveScatterData.normal.push(point);
    else if (status === 'warning') liveScatterData.warning.push(point);
    else liveScatterData.critical.push(point);

    // Keep only the last 100 points in each series
    ['normal', 'warning', 'critical'].forEach(status => {
        if (liveScatterData[status].length > 100) {
            liveScatterData[status].shift();
        }
    });

    // Update the chart
    scatterChart.updateOptions({
        series: [
            { name: 'Normal', data: liveScatterData.normal },
            { name: 'Warning', data: liveScatterData.warning },
            { name: 'Critical', data: liveScatterData.critical }
        ],
        xaxis: {
            type: 'datetime'
        }
    });
}

function getTrafficLightStatus(sensor, value) {
    const thresholds = sensorThresholds[sensor];
    if (!thresholds) return 'normal';

    const range = thresholds.max - thresholds.min;
    const buffer = range * 0.1;

    if (value >= thresholds.min - buffer && value <= thresholds.max + buffer) {
        return 'normal';
    } else if (value >= thresholds.min - 2 * buffer && value <= thresholds.max + 2 * buffer) {
        return 'warning';
    } else {
        return 'critical';
    }
}

function slideDonutsLeft() {
    const slider = document.getElementById('donutSlider');
    const chartWidth = document.querySelector('.donut-chart-container').offsetWidth;
    if (currentSlide > 0) {
        currentSlide--;
        slider.scrollTo({
            left: currentSlide * (chartWidth + 15),
            behavior: 'smooth'
        });
    }
}

function slideDonutsRight() {
    const slider = document.getElementById('donutSlider');
    const chartWidth = document.querySelector('.donut-chart-container').offsetWidth;
    const maxSlides = (selectedLine === "line4") ? 7 : 16;
    if (currentSlide < maxSlides) {
        currentSlide++;
        slider.scrollTo({
            left: currentSlide * (chartWidth + 15),
            behavior: 'smooth'
        });
    }
}

function fetchLiveData() {
    fetch(`http://127.0.0.1:5000/api/live-data/${selectedLine}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateDonutCharts(data.data);
                updateAnalytics(data.data);
                updateBarChart(data.data);
                updateLiveScatterChart(data.data);
            } else {
                console.error("Failed to fetch live data");
            }
        })
        .catch(error => console.error("Error fetching data:", error));
}

function updateDonutCharts(liveData) {
    Object.keys(liveData).forEach(sensor => {
        if (sensor !== "timestamp" && donutCharts[sensor]) {
            const value = liveData[sensor];
            const color = getTrafficLightColor(sensor, value);
            
            donutCharts[sensor].updateOptions({
                colors: [color]
            });
            
            donutCharts[sensor].updateSeries([value]);
        }
    });
}

function updateBarChart(liveData) {
    const sensors = Object.keys(liveData).filter(key => key.startsWith('r'));
    const categories = sensors.map(s => s.toUpperCase());
    const seriesData = sensors.map(s => liveData[s]);
    
    barChart.updateOptions({
        xaxis: { categories }
    });
    barChart.updateSeries([{
        name: 'Temperature',
        data: seriesData
    }]);
}

function updateAnalytics(liveData) {
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
    document.getElementById("optimalSensors").textContent = greenCount;
    document.getElementById("warningSensors").textContent = amberCount + redCount;
    
    trafficLightChart.updateSeries([greenCount, amberCount, redCount]);
}

function getTrafficLightColor(sensor, value) {
    const thresholds = sensorThresholds[sensor];
    if (!thresholds) return '#00E396';

    const range = thresholds.max - thresholds.min;
    const buffer = range * 0.1;

    if (value >= thresholds.min - buffer && value <= thresholds.max + buffer) {
        return '#00E396';
    } else if (value >= thresholds.min - 2 * buffer && value <= thresholds.max + 2 * buffer) {
        return '#FFA500';
    } else {
        return '#FF0000';
    }
}

function closeExpandedChart() {
    document.getElementById("expandedChartContainer").style.display = "none";

}