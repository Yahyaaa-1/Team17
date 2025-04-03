let selectedLine = "line4";
let donutCharts = {};
let currentSlide = 0;
let trafficLightChart;
let barChart;
let scatterChart;
let liveScatterData = { normal: [], warning: [], critical: [] };

// Helper Functions
function getSensorsForLine(line) {
    // add logic here
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
            zoom: { enabled: true, type: 'xy' },
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
            labels: { datetimeFormatter: { hour: 'HH:mm' } }
        },
        yaxis: { title: { text: 'Temperature (°C)' }, min: 0, max: 400 },
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