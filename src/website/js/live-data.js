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

function getTrafficLightStatus(value, lowerBound, upperBound) {
    if (!lowerBound || !upperBound) return 'normal';
    
    if (value < lowerBound) {
        return 'critical';
    } else if (value > upperBound) {
        return 'critical';
    } else if (value < lowerBound + ((upperBound - lowerBound) * 0.2)) {
        return 'warning';
    } else if (value > upperBound - ((upperBound - lowerBound) * 0.2)) {
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
            labels: { datetimeFormatter: { hour: 'HH:mm', minute: 'HH:mm' } },
            zoom: { enabled: true, type: 'x', autoScaleYaxis: true }
        },
        yaxis: {
            title: { text: 'Temperature (°C)' },
            min: 0,
            max: 100,
            forceNiceScale: true,
            tickAmount: 6,
            labels: { formatter: (val) => `${val.toFixed(1)}°C` }
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

    trafficLightChart.render();
    barChart.render();
    scatterChart.render();
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

function updateAnalytics(liveData) {
    // Filter out non-sensor keys
    const sensors = Object.keys(liveData).filter(key => 
        key.startsWith('r') && typeof liveData[key] === 'number'
    );
    
    // if (sensors.length === 0) {
    //     // No valid sensor data case
    //     document.getElementById("totalSensors").textContent = "0";
    //     document.getElementById("averageTemperature").textContent = "0°C";
    //     document.getElementById("optimalSensors").textContent = "N/A";
    //     document.getElementById("warningSensors").textContent = "N/A";
    //     return;
    // }

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
            // Default to green if no thresholds available
            greenCount++;
        }
    });
    
    const averageTemperature = (totalTemperature / totalSensors).toFixed(2);
    document.getElementById("totalSensors").textContent = totalSensors;
    document.getElementById("averageTemperature").textContent = `${averageTemperature}°C`;
    document.getElementById("optimalSensors").textContent = greenCount;
    document.getElementById("warningSensors").textContent = amberCount + redCount;
    
    // Update traffic light chart only if system is active
    if (trafficLightSystem) {
        trafficLightChart.updateSeries([greenCount, amberCount, redCount]);
    }
}

function updateLiveScatterChart(liveData) {
    const selectedSensor = document.getElementById("sensorSelector").value;
    if (!selectedSensor || !liveData[selectedSensor]) return;
    
    const timestamp = new Date().getTime();
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

    const allPoints = [...liveScatterData.normal, ...liveScatterData.warning, ...liveScatterData.critical];
    let yMin = 0;
    let yMax = 100;

    if (allPoints.length > 0) {
        const values = allPoints.map(p => p.y);
        const dataMin = Math.min(...values);
        const dataMax = Math.max(...values);
        const range = dataMax - dataMin;
        yMin = Math.max(0, dataMin - range * 0.1);
        yMax = dataMax + range * 0.1;
        
        if ((yMax - yMin) < 20) {
            const center = (yMin + yMax) / 2;
            yMin = center - 10;
            yMax = center + 10;
        }
    }
    
    scatterChart.updateOptions({
        series: [
            { name: 'Normal', data: liveScatterData.normal },
            { name: 'Warning', data: liveScatterData.warning },
            { name: 'Critical', data: liveScatterData.critical }
        ],
        xaxis: { min: timestamp - 7200000, max: timestamp + 60000 },
        yaxis: { min: yMin, max: yMax }
    });
}

function updateScatterChart() {
    const selectedSensor = document.getElementById("sensorSelector").value;
    if (!selectedSensor) return;
    
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
                    ]
                });
            }
        })
        .catch(console.error);
}

// Data Fetching
function fetchLiveData() {
    fetch(`http://127.0.0.1:5000/api/live-data/${selectedLine}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateDonutCharts(data.data);
                updateBarChart(data.data);
                updateLiveScatterChart(data.data);
                updateAnalytics(data.data);
                fetchForecastedData(data.data);
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
    const sensors = getSensorsForLine(selectedLine);
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
    
    const sensors = getSensorsForLine(selectedLine);
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
    const maxSlides = (selectedLine === "line4") ? 7 : 16;
    if (currentSlide < maxSlides) {
        currentSlide++;
        slider.scrollTo({ left: currentSlide * (chartWidth + 15), behavior: 'smooth' });
    }
}

// Event Listeners
document.addEventListener("DOMContentLoaded", () => {
    initializeDonutSlider(selectedLine);
    initCharts();
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