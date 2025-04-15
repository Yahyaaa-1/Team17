let selectedLine = "line4";
let donutCharts = {};
let currentSlide = 0;
let maxSlides = 0;
let trafficLightChart;
let barChart;
let scatterChart;
let liveScatterData = { normal: [], warning: [], critical: [] };
let forecastThresholds = {};
let trafficLightSystem = false; 

// Helper Functions
async function getSensorsForLine(line) {
    try {
        const response = await fetch(`http://127.0.0.1:5000/api/admin/table-headers?tableID=${line}`);
        const data = await response.json();
        if (data.success) {
            // Filter out non-sensor columns and return
            return data.headers.filter(header => 
                header.startsWith('r') && 
                header !== 'timestamp' && 
                header !== 'timezone'
            ).sort(); // Sort sensors alphabetically
        }
        return [];
    } catch (error) {
        console.error('Error fetching sensors:', error);
        return [];
    }
}

function getTrafficLightStatus(value, lowerBound, upperBound) {
    if (!lowerBound || !upperBound) return 'normal';
    
    if (value < lowerBound) {
        return 'critical';
    } else if (value > upperBound) {
        return 'critical';
    } else if (value < lowerBound + ((upperBound - lowerBound) * 0.1)) {
        return 'warning';
    } else if (value > upperBound - ((upperBound - lowerBound) * 0.1)) {
        return 'warning';
    } else {
        return 'normal';
    }
}

function getTrafficLightColor(sensor, value) {
    if (!trafficLightSystem) return '#808080';
    if (!forecastThresholds[sensor]) return '#00E396';
    
    const { lowerBound, upperBound } = forecastThresholds[sensor];
    const status = getTrafficLightStatus(value, lowerBound, upperBound);
    
    return status === 'normal' ? '#00E396' : 
           status === 'warning' ? '#FFA500' : '#FF0000';
}

// Initialization Functions
async function initializeDonutSlider(line) {
    const slider = document.getElementById('donutSlider');
    slider.innerHTML = '';
    currentSlide = 0;
    donutCharts = {};

    // Get the actual sensors from the database
    const sensors = await getSensorsForLine(line);
    
    sensors.forEach(sensor => {
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
        
        donutCharts[sensor] = new ApexCharts(chartDiv, {
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
    
    // Update the max slides for navigation
    maxSlides = Math.max(0, sensors.length - 1);
}

function initCharts() {
    // Traffic Light Chart
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

    // Bar Chart
    barChart = new ApexCharts(document.querySelector("#barChart"), {
        chart: { type: 'bar', height: '100%', toolbar: { show: false } },
        series: [{ name: 'Temperature', data: [] }],
        xaxis: { categories: [], labels: { style: { fontSize: '12px' } } },
        plotOptions: { bar: { borderRadius: 4, horizontal: false } },
        colors: ['#0066FF'],
        dataLabels: { enabled: false }
    });

    // Scatter Chart
    scatterChart = new ApexCharts(document.querySelector("#scatterChart"), {
        chart: {
            type: 'scatter',
            height: '100%',
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
                formatter: function(value) {
                    const date = new Date(value);
                    return date.toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'});
                }
            },
            tickAmount: 6,
            tickPlacement: 'between',
            tooltip: {
                formatter: function(value) {
                    return new Date(value).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit', second: '2-digit'});
                }
            },
            min: (new Date()).getTime() - (5 * 60 * 1000) - (30 * 1000),
            max: (new Date()).getTime() + (30 * 1000)
        },
        yaxis: {
            title: { text: 'Temperature (°C)' },
            min: 0,
            max: 400,
            tickAmount: 8,
            labels: {
                formatter: function(val) {
                    return val.toFixed(0);
                },
                style: {
                    fontSize: '11px'
                }
            },
            forceNiceScale: true
        },
        colors: ['#00E396', '#FFA500', '#FF0000'],
        markers: { size: 6, strokeWidth: 0, hover: { size: 8 } },
        tooltip: {
            shared: false,
            intersect: true,
            x: {
                format: 'HH:mm:ss'
            },
            y: {
                formatter: function(val) {
                    return val.toFixed(2) + '°C';
                }
            }
        }
    });

    trafficLightChart.render();
    barChart.render();
    scatterChart.render();
}

// Update Functions
async function updateSensorSelector(line) {
    const selector = document.getElementById("sensorSelector");
    const currentSelectedValue = selector.value;
    
    // Clear existing options but keep the default option if it exists
    selector.innerHTML = selector.querySelector('option[value=""]') ? 
        '<option value="">Select Sensor</option>' : '';
    
    const sensors = await getSensorsForLine(line);
    
    if (sensors.length === 0) {
        const option = document.createElement('option');
        option.value = "";
        option.textContent = "No sensors available";
        selector.appendChild(option);
        return;
    }
    
    sensors.forEach(sensor => {
        const option = document.createElement('option');
        option.value = sensor;
        option.textContent = sensor.toUpperCase();
        selector.appendChild(option);
    });
    
    // Restore previous selection if it still exists
    if (sensors.includes(currentSelectedValue)) {
        selector.value = currentSelectedValue;
    } else if (sensors.length > 0) {
        // Select the first sensor by default if previous selection is gone
        selector.value = sensors[0];
    }
    
    liveScatterData = { normal: [], warning: [], critical: [] };
    updateScatterChart();
}

function updateDonutCharts(liveData) {
    Object.keys(donutCharts).forEach(sensor => {
        if (liveData[sensor] !== undefined) {
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

function updateAnalytics(liveData) {
    const sensors = Object.keys(liveData).filter(key => 
        key.startsWith('r') && typeof liveData[key] === 'number'
    );
    
    const totalSensors = sensors.length;
    let totalTemperature = 0;
    let greenCount = 0;
    let amberCount = 0;
    let redCount = 0;
    
    sensors.forEach(sensor => {
        const value = liveData[sensor];
        totalTemperature += value;
        
        if (forecastThresholds[sensor]) {
            const { lowerBound, upperBound } = forecastThresholds[sensor];
            const status = getTrafficLightStatus(value, lowerBound, upperBound);
            
            if (status === 'normal') greenCount++;
            else if (status === 'warning') amberCount++;
            else if (status === 'critical') redCount++;
        } else {
            greenCount++;
        }
    });
    
    const averageTemperature = (totalTemperature / totalSensors).toFixed(2);
    document.getElementById("totalSensors").textContent = totalSensors;
    document.getElementById("averageTemperature").textContent = `${averageTemperature}°C`;
    document.getElementById("optimalSensors").textContent = greenCount;
    document.getElementById("warningSensors").textContent = amberCount + redCount;
    
    if (trafficLightSystem) {
        trafficLightChart.updateSeries([greenCount, amberCount, redCount]);
    }
}

function updateLiveScatterChart(liveData) {
    const selectedSensor = document.getElementById("sensorSelector").value;
    if (!selectedSensor || !liveData[selectedSensor]) return;
    
    const timestamp = liveData.timestamp ? new Date(liveData.timestamp).getTime() : new Date().getTime();
    const temperature = liveData[selectedSensor];
    const point = { x: timestamp, y: temperature };
    
    let status = 'normal';
    if (forecastThresholds[selectedSensor]) {
        const { lowerBound, upperBound } = forecastThresholds[selectedSensor];
        status = getTrafficLightStatus(temperature, lowerBound, upperBound);
    }
    
    liveScatterData[status].push(point);
    
    ['normal', 'warning', 'critical'].forEach(status => {
        if (liveScatterData[status].length > 100) {
            liveScatterData[status].shift();
        }
    });

    scatterChart.updateOptions({
        series: [
            { name: 'Normal', data: liveScatterData.normal },
            { name: 'Warning', data: liveScatterData.warning },
            { name: 'Critical', data: liveScatterData.critical }
        ],
        xaxis: { 
            min: timestamp - (5 * 60 * 1000),
            max: timestamp + (30 * 1000),
            tickAmount: 6
        }
    }, false, true);
}

function updateScatterChart() {
    const selector = document.getElementById("sensorSelector");
    const selectedSensor = selector.value;
    
    // Don't proceed if no valid sensor is selected
    if (!selectedSensor || selector.selectedIndex <= 0) {
        scatterChart.updateOptions({
            series: [
                { name: 'Normal', data: [] },
                { name: 'Warning', data: [] },
                { name: 'Critical', data: [] }
            ]
        });
        return;
    }
    
    liveScatterData = { normal: [], warning: [], critical: [] };
    
    fetch(`http://127.0.0.1:5000/api/historical/${selectedLine}/${selectedSensor}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                data.data.forEach(item => {
                    const point = { x: new Date(item.timestamp).getTime(), y: item.value };
                    let status = 'normal';
                    if (forecastThresholds[selectedSensor]) {
                        const { lowerBound, upperBound } = forecastThresholds[selectedSensor];
                        status = getTrafficLightStatus(item.value, lowerBound, upperBound);
                    }
                    liveScatterData[status].push(point);
                });
                
                scatterChart.updateOptions({
                    series: [
                        { name: 'Normal', data: liveScatterData.normal },
                        { name: 'Warning', data: liveScatterData.warning },
                        { name: 'Critical', data: liveScatterData.critical }
                    ],
                    xaxis: {
                        tickAmount: 6
                    }
                });
            }
        })
        .catch(error => {
            console.error('Error fetching scatter data:', error);
            // If there's an error (like sensor not found), refresh the selector
            updateSensorSelector(selectedLine);
        });
}

// Data Fetching
function fetchLiveData() {
    fetch(`http://127.0.0.1:5000/api/live-data/${selectedLine}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // First ensure our selectors are up to date
                updateSensorSelector(selectedLine).then(() => {
                    updateDonutCharts(data.data);
                    updateBarChart(data.data);
                    updateLiveScatterChart(data.data);
                    updateAnalytics(data.data);
                    fetchForecastedData(data.data);
                });
            }
        })
        .catch(console.error);
}

function fetchForecastedData(liveData) {
    fetch(`http://127.0.0.1:5000/api/forecasted-data/${selectedLine}`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.data?.length > 0) {
                const currentTime = new Date();
                const latestForecastTime = new Date(data.data[0].forecast_time);
                const timeDifference = Math.abs(currentTime - latestForecastTime) / (1000 * 60);
                
                if (timeDifference <= 60) {
                    trafficLightSystem = true;
                    document.getElementById("mlWarningMessage").style.display = "none";
                    processForecastedThresholds(data.data);
                    updateTrafficLightStatus(data.data, liveData);
                } else {
                    handleInoperativeTrafficLightSystem();
                }
            } else {
                handleInoperativeTrafficLightSystem();
            }
        })
        .catch(console.error);
}

function processForecastedThresholds(forecastedData) {
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
    const sensors = Object.keys(donutCharts); // Use only sensors that have donut charts
    let greenCount = 0;
    let amberCount = 0;
    let redCount = 0;
    
    sensors.forEach(sensor => {
        if (liveData[sensor] && forecastThresholds[sensor]) {
            const value = liveData[sensor];
            const { lowerBound, upperBound } = forecastThresholds[sensor];
            const status = getTrafficLightStatus(value, lowerBound, upperBound);
            
            if (status === 'normal') greenCount++;
            else if (status === 'warning') {
                amberCount++;
                logSensorStatus(sensor, value, status, lowerBound, upperBound);
            }
            else if (status === 'critical') {
                redCount++;
                logSensorStatus(sensor, value, status, lowerBound, upperBound);
            }
        }
    });
    
    trafficLightChart.updateSeries([greenCount, amberCount, redCount]);
}

function handleInoperativeTrafficLightSystem() {
    trafficLightSystem = false;
    document.getElementById("mlWarningMessage").style.display = "block";
    trafficLightChart.updateSeries([0, 0, 0]);
    
    Object.keys(donutCharts).forEach(sensor => {
        if (donutCharts[sensor]) {
            donutCharts[sensor].updateOptions({ colors: ['#808080'] });
        }
    });
    
    document.getElementById("optimalSensors").textContent = "N/A";
    document.getElementById("warningSensors").textContent = "N/A";
}

function logSensorStatus(sensor, value, status, lowerBound, upperBound) {
    const message = `Sensor ${sensor} on ${selectedLine} is in ${status} state. Current value: ${value}, Threshold: [${lowerBound}, ${upperBound}]`;
    
    fetch('http://localhost:5000/api/log', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            message: message,
            type: 'WARNING',
            level: 'normal'
        })
    }).catch(console.error);
}

// Navigation Functions
function slideDonutsLeft() {
    const slider = document.getElementById('donutSlider');
    const chartWidth = document.querySelector('.donut-chart-container').offsetWidth;
    if (currentSlide > 0) {
        currentSlide--;
        slider.scrollTo({ left: currentSlide * (chartWidth + 15), behavior: 'smooth' });
    }
}

function slideDonutsRight() {
    const slider = document.getElementById('donutSlider');
    const chartWidth = document.querySelector('.donut-chart-container').offsetWidth;
    if (currentSlide < maxSlides) {
        currentSlide++;
        slider.scrollTo({ left: currentSlide * (chartWidth + 15), behavior: 'smooth' });
    }
}

// Event Listeners
document.addEventListener("DOMContentLoaded", async () => {
    await initializeDonutSlider(selectedLine);
    initCharts();
    await updateSensorSelector(selectedLine);
    fetchLiveData();

    document.getElementById("lineSelector").addEventListener("change", async function() {
        selectedLine = this.value;
        await initializeDonutSlider(selectedLine);
        await updateSensorSelector(selectedLine);
        fetchLiveData();
    });

    document.getElementById('prevDonut').addEventListener('click', slideDonutsLeft);
    document.getElementById('nextDonut').addEventListener('click', slideDonutsRight);
    document.getElementById("sensorSelector").addEventListener("change", updateScatterChart);
    setInterval(fetchLiveData, 5000);
});