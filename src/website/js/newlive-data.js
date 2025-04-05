let selectedLine = "line4";
let donutCharts = {};
let currentSlide = 0;
let trafficLightChart;
let barChart;
let scatterChart;
let liveScatterData = { normal: [], warning: [], critical: [] };
let forecastThresholds = {};
let trafficLightSystem = false; 

// Helper Functions
function getSensorsForLine(line) {
    return line === "line4" ? 
        ["r01", "r02", "r03", "r04", "r05", "r06", "r07", "r08"] : 
        ["r01", "r02", "r03", "r04", "r05", "r06", "r07", "r08", "r09", "r10", "r11", "r12", "r13", "r14", "r15", "r16", "r17"];
}

function getTrafficLightColor(sensor, value) {
    if (!forecastThresholds[sensor]) return '#00E396'; // Default to green if no thresholds
    
    const { lowerBound, upperBound } = forecastThresholds[sensor];
    const status = getTrafficLightStatus(value, lowerBound, upperBound);
    
    if (status === 'normal') return '#00E396'; // Green
    else if (status === 'warning') return '#FFA500'; // Amber
    else return '#FF0000'; // Red
}


function getTrafficLightStatus(value, lowerBound, upperBound) {
    if (value < lowerBound) {
        return 'critical'; // Below lower bound
    } else if (value > upperBound) {
        return 'critical'; // Above upper bound
    } else if (value < lowerBound + 10) {
        return 'warning'; // Within warning range
    } else {
        return 'normal'; // Within normal range
    }
}

// Initialization Functions
function initializeDonutSlider(line) {
    const slider = document.getElementById('donutSlider');
    slider.innerHTML = '';
    currentSlide = 0;
    donutCharts = {};

    getSensorsForLine(line).forEach(sensor => {
        const chartContainer = document.createElement('div');
        chartContainer.className = 'donut-chart-container';
        
        const title = document.createElement('h5');
        title.textContent = sensor.toUpperCase();
        
        const chartDiv = document.createElement('div');
        chartDiv.className = 'donut-chart';
        chartDiv.id = `donut-chart-${sensor}`;

        chartDiv.addEventListener("click", () => {
            window.location.href = `pages/sensor-data.html?sensor=${sensor}&line=${line}`;
        });
        
        chartContainer.appendChild(title);
        chartContainer.appendChild(chartDiv);
        slider.appendChild(chartContainer);
        
        donutCharts[sensor] = new ApexCharts(document.querySelector(`#donut-chart-${sensor}`), {
            series: [0],
            chart: { type: 'donut', height: 180 },
            labels: ['Current Value'],
            colors: ['#00E396'],
            plotOptions: {
                pie: {
                    donut: {
                        labels: {
                            show: true,
                            name: { show: true, fontSize: '12px' },
                            value: {
                                show: true,
                                fontSize: '16px',
                                fontWeight: 'bold',
                                formatter: (val) => `${val.toFixed(2)}°C`
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
        chart: { type: 'bar', height: '100%', toolbar: { show: false } },
        series: [{ name: 'Temperature', data: [] }],
        xaxis: { categories: [], labels: { style: { fontSize: '12px' } } },
        plotOptions: { bar: { borderRadius: 4, horizontal: false } },
        colors: ['#0066FF'],
        dataLabels: { enabled: false }
    });
    barChart.render();
}

function initScatterChart() {
    scatterChart = new ApexCharts(document.querySelector("#scatterChart"), {
        chart: {
            type: 'scatter',
            height: '100%',
            toolbar: { tools: { download: true, selection: true, zoom: true } },
            animations: { enabled: true, easing: 'linear', dynamicAnimation: { speed: 1000 } }
        },
        series: [
            { name: 'Normal', data: [] },
            { name: 'Warning', data: [] },
            { name: 'Critical', data: [] }
        ],
        xaxis: {
            type: 'datetime',
            title: { text: 'Time' },
            labels: {
                datetimeFormatter: {
                    hour: 'HH:mm',
                    minute: 'HH:mm'
                }
            },
            zoom: {
                enabled: true,
                type: 'x',   // Enable zoom on the x-axis
                autoScaleYaxis: true // Auto scale Y-axis as the X-axis zooms
            },
            // Remove min and max to let zoom dynamically control the range
            // min: Date.now() - 7200000, // Start with 2 hours ago
            // max: Date.now(), // Current time
        },
        yaxis: {
            title: { text: 'Temperature (°C)' },
            min: 0, // Default minimum
            max: 100, // Default maximum
            forceNiceScale: true,
            tickAmount: 6,
            labels: {
                formatter: function(val) {
                    return val.toFixed(1) + '°C';
                }
            }
        },
        colors: ['#00E396', '#FFA500', '#FF0000'],
        markers: { size: 6, strokeWidth: 0, hover: { size: 8 } },
        tooltip: {
            shared: false,
            intersect: true,
            x: { format: 'dd MMM yyyy HH:mm:ss' },
            y: { formatter: (val) => `${val.toFixed(2)}°C` }
        }
    });
    scatterChart.render();
}

function initTrafficLightChart() {
    trafficLightChart = new ApexCharts(document.querySelector("#trafficLightPieChart"), {
        series: [0, 0, 0],
        chart: { type: 'pie', height: '100%' },
        labels: ['Normal', 'Warning', 'Critical'],
        colors: ['#00E396', '#FFA500', '#FF0000'],
        responsive: [{ breakpoint: 480, options: { chart: { width: 200 }, legend: { position: 'bottom' } } }],
        plotOptions: {
            pie: {
                donut: {
                    labels: {
                        show: true,
                        total: {
                            show: true,
                            label: 'Total Sensors',
                            formatter: (w) => w.globals.seriesTotals.reduce((a, b) => a + b, 0)
                        }
                    }
                }
            }
        },
        legend: { position: 'right', offsetY: 0, height: 230 }
    });
    trafficLightChart.render();
}

// Update Functions
function updateSensorSelector(line) {
    const selector = document.getElementById("sensorSelector");
    selector.innerHTML = '';
    getSensorsForLine(line).forEach(sensor => {
        const option = document.createElement('option');
        option.value = sensor;
        option.textContent = sensor.toUpperCase();
        selector.appendChild(option);
    });
    liveScatterData = { normal: [], warning: [], critical: [] };
    if (getSensorsForLine(line).length > 0) updateScatterChart();
}

function updateScatterChart() {
    const selectedSensor = document.getElementById("sensorSelector").value;
    if (!selectedSensor) return;

    fetch(`http://127.0.0.1:5000/api/historical/${selectedLine}/${selectedSensor}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                data.data.forEach(item => {
                    const point = { x: new Date(item.timestamp).getTime(), y: item.value };
                    const status = getTrafficLightStatus(item.value, item.lower_bound, item.upper_bound);
                    liveScatterData[status].push(point);
                });
                scatterChart.updateOptions({ series: [
                    { name: 'Normal', data: liveScatterData.normal },
                    { name: 'Warning', data: liveScatterData.warning },
                    { name: 'Critical', data: liveScatterData.critical }
                ], xaxis: { type: 'datetime' } });
            }
        })
        .catch(console.error);
}

function updateDonutCharts(liveData) {
    Object.keys(liveData).forEach(sensor => {
        if (sensor !== "timestamp" && donutCharts[sensor]) {
            const value = liveData[sensor];
            const color = getTrafficLightColor(sensor, value);
            donutCharts[sensor].updateOptions({ colors: [color] });
            donutCharts[sensor].updateSeries([value]);
        }
    });
}

function updateBarChart(liveData) {
    const sensors = Object.keys(liveData).filter(key => key.startsWith('r'));
    const categories = sensors.map(s => s.toUpperCase());
    const seriesData = sensors.map(s => liveData[s]);
    barChart.updateOptions({ xaxis: { categories } });
    barChart.updateSeries([{ name: 'Temperature', data: seriesData }]);
}

// function updateAnalytics(liveData) {
//     const sensors = Object.keys(liveData).filter(key => key !== "timestamp" && key !== "timezone");
//     const totalSensors = sensors.length;
//     let totalTemperature = 0;
//     let greenCount = 0;
//     let amberCount = 0;
//     let redCount = 0;

//     sensors.forEach(sensor => {
//         const value = liveData[sensor];
//         totalTemperature += value;

//         const color = getTrafficLightColor(sensor, value);
//         if (color === '#00E396') greenCount++;
//         else if (color === '#FFA500') amberCount++;
//         else if (color === '#FF0000') redCount++;
//     });

//     const averageTemperature = (totalTemperature / totalSensors).toFixed(2);
//     document.getElementById("totalSensors").textContent = totalSensors;
//     document.getElementById("averageTemperature").textContent = `${averageTemperature}°C`;
//     document.getElementById("optimalSensors").textContent = greenCount;
//     document.getElementById("warningSensors").textContent = amberCount + redCount;
    
//     trafficLightChart.updateSeries([greenCount, amberCount, redCount]);
// }

// // Navigation Functions
// function slideDonutsLeft() {
//     const slider = document.getElementById('donutSlider');
//     const chartWidth = document.querySelector('.donut-chart-container').offsetWidth;
//     if (currentSlide > 0) {
//         currentSlide--;
//         slider.scrollTo({ left: currentSlide * (chartWidth + 15), behavior: 'smooth' });
//     }
// }

function slideDonutsRight() {
    const slider = document.getElementById('donutSlider');
    const chartWidth = document.querySelector('.donut-chart-container').offsetWidth;
    const maxSlides = (selectedLine === "line4") ? 7 : 16;
    if (currentSlide < maxSlides) {
        currentSlide++;
        slider.scrollTo({ left: currentSlide * (chartWidth + 15), behavior: 'smooth' });
    }
}

// Data Fetching
function fetchLiveData() {
    fetch(`http://127.0.0.1:5000/api/live-data/${selectedLine}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateDonutCharts(data.data);
                updateAnalytics(data.data);
                updateBarChart(data.data);
                fetchForecastedData();
            }
        })
        .catch(console.error);
}

function fetchForecastedData() {
    fetch(`http://127.0.0.1:5000/api/forecasted-data/${selectedLine}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateTrafficLightStatus(data.data); // Update traffic light status using forecasted data
            } else {
                console.error("Failed to fetch forecasted data");
            }
        })
        .catch(error => console.error("Error fetching forecasted data:", error));
}

// Event Listeners
document.addEventListener("DOMContentLoaded", () => {
    initializeDonutSlider(selectedLine);
    initTrafficLightChart();
    initBarChart();
    initScatterChart();
    updateSensorSelector(selectedLine);
    fetchLiveData();

    document.getElementById("lineSelector").addEventListener("change", function() {
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

function fetchLiveData() {
    fetch(`http://127.0.0.1:5000/api/live-data/${selectedLine}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const liveData = data.data;
                updateDonutCharts(liveData);
                updateBarChart(liveData);
                updateLiveScatterChart(liveData);
                
                // Fetch forecasted data for traffic light calculations
                fetchForecastedData(liveData);
            } else {
                console.error("Failed to fetch live data");
            }
        })
        .catch(error => console.error("Error fetching live data:", error));
}

function fetchForecastedData(liveData) {
    fetch(`http://127.0.0.1:5000/api/forecasted-data/${selectedLine}`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.data && data.data.length > 0) {
                // Check if forecasted data is available for the current time
                const currentTime = new Date();
                const latestForecastTime = new Date(data.data[0].forecast_time);
                
                // Calculate time difference in minutes
                const timeDifference = Math.abs(currentTime - latestForecastTime) / (1000 * 60);
                
                // Consider forecasts valid if they're within the last 60 minutes (adjust as needed)
                if (timeDifference <= 60) {
                    trafficLightSystem = true;
                    
                    // Hide the warning message
                    document.getElementById("mlWarningMessage").style.display = "none";
                    
                    // Process forecasted data and update traffic lights
                    processForcastedThresholds(data.data);
                    updateTrafficLightStatus(data.data, liveData);
                    updateAnalytics(liveData);
                } else {
                    handleInoperativeTrafficLightSystem();
                }
            } else {
                handleInoperativeTrafficLightSystem();
            }
        })
        .catch(error => console.error("Error fetching forecasted data:", error));
}

function handleInoperativeTrafficLightSystem() {
    trafficLightSystem = false;
    
    // Show warning message
    document.getElementById("mlWarningMessage").style.display = "block";
    
    // Reset traffic light chart to show system is inoperative
    trafficLightChart.updateSeries([0, 0, 0]);
    
    // Update donut charts to use neutral color
    Object.keys(donutCharts).forEach(sensor => {
        if (donutCharts[sensor]) {
            donutCharts[sensor].updateOptions({
                colors: ['#808080'] // Gray color to indicate system is inoperative
            });
        }
    });
    
    // Update analytics with neutral values
    const sensors = getSensorsForLine(selectedLine);
    document.getElementById("optimalSensors").textContent = "N/A";
    document.getElementById("warningSensors").textContent = "N/A";
}


function processForcastedThresholds(forecastedData) {
    // Process and store thresholds from forecasted data
    forecastThresholds = {};
    
    forecastedData.forEach(record => {
        const sensor = record.sensor;
        if (!forecastThresholds[sensor]) {
            forecastThresholds[sensor] = {
                lowerBound: record.lower_bound,
                upperBound: record.upper_bound
            };
        }
    });
}


function updateTrafficLightStatus(forecastedData, liveData) {
    // Update traffic light status based on forecasted data
    const sensors = getSensorsForLine(selectedLine);
    let greenCount = 0;
    let amberCount = 0;
    let redCount = 0;
    
    sensors.forEach(sensor => {
        if (liveData[sensor] && forecastThresholds[sensor]) {
            const value = liveData[sensor];
            const { lowerBound, upperBound } = forecastThresholds[sensor];
            
            const status = getTrafficLightStatus(value, lowerBound, upperBound);
            
            if (status === 'normal') {
                greenCount++;
            }
            else if (status === 'warning') {
                amberCount++;
                // Log warning status
                logSensorStatus(sensor, value, status, lowerBound, upperBound);
            }
            else if (status === 'critical') {
                redCount++;
                // Log critical status
                logSensorStatus(sensor, value, status, lowerBound, upperBound);
            }
        }
    });
    
    // Update traffic light chart
    trafficLightChart.updateSeries([greenCount, amberCount, redCount]);
}

// Helper function to log sensor status
function logSensorStatus(sensor, value, status, lowerBound, upperBound) {
    const message = `Sensor ${sensor} on ${selectedLine} is in ${status} state. Current value: ${value}, Threshold: [${lowerBound}, ${upperBound}]`;
    
    fetch('http://localhost:5000/api/log', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            message: message,
            type: 'WARNING',
            level: 'normal'
        })
    }).catch(error => {
        console.error('Sensor status logging error:', error);
    });
}

function getTrafficLightStatus(value, lowerBound, upperBound) {
    if (!lowerBound || !upperBound) return 'normal';
    
    if (value < lowerBound) {
        return 'critical'; // Below lower bound
    } else if (value > upperBound) {
        return 'critical'; // Above upper bound
    } else if (value < lowerBound + ((upperBound - lowerBound) * 0.2)) {
        return 'warning'; // Within warning range (20% buffer from lower bound)
    } else if (value > upperBound - ((upperBound - lowerBound) * 0.2)) {
        return 'warning'; // Within warning range (20% buffer from upper bound)
    } else {
        return 'normal'; // Within normal range
    }
}

function getTrafficLightColor(sensor, value) {
    if (!trafficLightSystem) return '#808080'; // Gray if system is inoperative
    
    if (!forecastThresholds[sensor]) return '#00E396'; // Default to green if no thresholds
    
    const { lowerBound, upperBound } = forecastThresholds[sensor];
    const status = getTrafficLightStatus(value, lowerBound, upperBound);
    
    if (status === 'normal') return '#00E396'; // Green
    else if (status === 'warning') return '#FFA500'; // Amber
    else return '#FF0000'; // Red
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
    
    // Get thresholds from forecasted data
    const thresholds = forecastThresholds[selectedSensor];
    
    // Categorize the point using forecasted thresholds
    let status = 'normal';
    if (thresholds) {
        status = getTrafficLightStatus(temperature, thresholds.lowerBound, thresholds.upperBound);
    }
    
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

    // Calculate y-axis min/max based on all data points
    const allPoints = [...liveScatterData.normal, ...liveScatterData.warning, ...liveScatterData.critical];
    let yMin = 0;
    let yMax = 100;

    if (allPoints.length > 0) {
        const values = allPoints.map(p => p.y);
        const dataMin = Math.min(...values);
        const dataMax = Math.max(...values);
        
        // Add 10% buffer to the min/max
        const range = dataMax - dataMin;
        yMin = Math.max(0, dataMin - range * 0.1);
        yMax = dataMax + range * 0.1;
        
        // Ensure we have at least 20 degrees range
        if ((yMax - yMin) < 20) {
            const center = (yMin + yMax) / 2;
            yMin = center - 10;
            yMax = center + 10;
        }
    }
    
    // Update the chart
    scatterChart.updateOptions({
        series: [
            { name: 'Normal', data: liveScatterData.normal },
            { name: 'Warning', data: liveScatterData.warning },
            { name: 'Critical', data: liveScatterData.critical }
        ],
        xaxis: {
            type: 'datetime',
            min: timestamp - 7200000, // 2 hours ago
            max: timestamp + 60000 // 1 minute in future (small buffer)
        },
        yaxis: {
            min: yMin,
            max: yMax
        }
    });
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
        
        // Use forecasted thresholds for traffic light status
        if (forecastThresholds[sensor]) {
            const { lowerBound, upperBound } = forecastThresholds[sensor];
            const status = getTrafficLightStatus(value, lowerBound, upperBound);
            
            if (status === 'normal') greenCount++;
            else if (status === 'warning') amberCount++;
            else if (status === 'critical') redCount++;
        } else {
            // Default to green if no thresholds
            greenCount++;
        }
    });
    
    const averageTemperature = (totalTemperature / totalSensors).toFixed(2);
    document.getElementById("totalSensors").textContent = totalSensors;
    document.getElementById("averageTemperature").textContent = `${averageTemperature}°C`;
    document.getElementById("optimalSensors").textContent = greenCount;
    document.getElementById("warningSensors").textContent = amberCount + redCount;
}

function updateScatterChart() {
    const selectedSensor = document.getElementById("sensorSelector").value;
    if (!selectedSensor) return;
    
    // Reset scatter data
    liveScatterData = { normal: [], warning: [], critical: [] };
    
    // First load historical data
    fetch(`http://127.0.0.1:5000/api/historical/${selectedLine}/${selectedSensor}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Categorize historical data using forecasted thresholds
                data.data.forEach(item => {
                    const point = {
                        x: new Date(item.timestamp).getTime(),
                        y: item.value
                    };
                    
                    // Use forecasted thresholds if available
                    let status = 'normal';
                    if (forecastThresholds[selectedSensor]) {
                        const { lowerBound, upperBound } = forecastThresholds[selectedSensor];
                        status = getTrafficLightStatus(item.value, lowerBound, upperBound);
                    }
                    
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
