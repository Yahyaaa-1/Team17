let selectedLine = "line4";
let donutCharts = {};
let currentSlide = 0;
let trafficLightChart;
let barChart;
let scatterChart;
let liveScatterData = { normal: [], warning: [], critical: [] };

// Cache configuration
const forecastCache = {
    data: {},
    lastUpdated: null,
    ttl: 30000, // 30 seconds cache
    inProgress: {}
};

document.addEventListener("DOMContentLoaded", function() {
    initializeDonutSlider(selectedLine);
    initTrafficLightChart();
    initBarChart();
    initScatterChart();
    updateSensorSelector(selectedLine);
    fetchLiveData();

    // Event listeners
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

// Core Functions ======================================================

async function fetchLiveData() {
    try {
        const response = await fetch(`http://127.0.0.1:5000/api/live-data/${selectedLine}`);
        const data = await response.json();
        
        if (data.success) {
            const liveData = data.data;
            const sensors = await getSensorsForLine(selectedLine);
            
            // Fetch all forecasts once
            const forecasts = await fetchAllForecasts(selectedLine, sensors);
            
            // Process sensors in parallel
            await Promise.all(sensors.map(async sensor => {
                try {
                    const value = liveData[sensor];
                    
                    if (typeof value !== 'number' || isNaN(value)) {
                        console.warn(`Invalid value for ${sensor}:`, value);
                        return;
                    }
                    
                    // Pass forecasts to getSensorStatus
                    const statusInfo = await getSensorStatus(selectedLine, sensor, value, forecasts);
                    
                    if (donutCharts[sensor]) {
                        donutCharts[sensor].updateOptions({
                            colors: [statusInfo.color]
                        });
                        donutCharts[sensor].updateSeries([value]);
                    }
                } catch (sensorError) {
                    console.error(`Error processing ${sensor}:`, sensorError);
                }
            }));
            
            await updateAnalytics(liveData, sensors, forecasts);
            updateBarChart(liveData);
            updateLiveScatterChart(liveData, forecasts);
        } else {
            console.error("Failed to fetch live data:", data);
        }
    } catch (error) {
        console.error("Error fetching live data:", error);
    }
}

// Modify getSensorStatus to not fetch sensors again
async function getSensorStatus(line, sensor, currentValue, forecasts) {
    try {
        const forecast = forecasts?.[sensor];
        let previousStatus = null;
        
        // Try to get previous status from donutCharts if it exists
        if (donutCharts[sensor]) {
            const currentColor = donutCharts[sensor].opts.colors[0];
            previousStatus = currentColor === '#00E396' ? 'normal' : 
                           currentColor === '#FFA500' ? 'warning' : 'critical';
        }
        
        if (!forecast) {
            return { status: 'normal', color: '#00E396' };
        }
        
        const { lower_bound: lower, upper_bound: upper } = forecast;
        const range = upper - lower;
        const buffer = range * 0.2;
        
        let newStatus;
        let color;
        
        if (currentValue >= lower && currentValue <= upper) {
            newStatus = 'normal';
            color = '#00E396';
        } 
        else if (currentValue >= (lower - buffer) && currentValue <= (upper + buffer)) {
            newStatus = 'warning';
            color = '#FFA500';
        } 
        else {
            newStatus = 'critical';
            color = '#FF0000';
        }

        // If status has changed, log it
        if (previousStatus && previousStatus !== newStatus) {
            const message = `Sensor ${sensor.toUpperCase()} on ${line.toUpperCase()} changed state from ${previousStatus} to ${newStatus} (Value: ${currentValue.toFixed(2)}°C)`;
            
            // Log the state change
            fetch('http://127.0.0.1:5000/api/log', {
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
                console.error('Error logging sensor state change:', error);
            });
        }
        
        return { status: newStatus, color: color };
    } catch (error) {
        console.error(`Error checking sensor status for ${line}-${sensor}:`, error);
        return { status: 'normal', color: '#00E396' };
    }
}
// Cache Management ====================================================

async function getCachedForecast(line, sensor) {
    const cacheKey = `${line}-${sensor}`;
    
    // Return cached data if valid
    if (forecastCache.data[cacheKey] && 
        Date.now() - forecastCache.lastUpdated < forecastCache.ttl) {
        return forecastCache.data[cacheKey];
    }
    
    // Return in-progress request if exists
    if (forecastCache.inProgress[cacheKey]) {
        return forecastCache.inProgress[cacheKey];
    }
    
    try {
        // Create new request promise
        forecastCache.inProgress[cacheKey] = fetch(
            `http://127.0.0.1:5000/api/latest-forecast/${line}/${sensor}`
        ).then(response => response.json());
        
        const data = await forecastCache.inProgress[cacheKey];
        
        if (data.success && data.forecast) {
            forecastCache.data[cacheKey] = data.forecast;
            forecastCache.lastUpdated = Date.now();
            return data.forecast;
        }
        return null;
    } catch (error) {
        console.error(`Error fetching forecast for ${line}-${sensor}:`, error);
        return null;
    } finally {
        delete forecastCache.inProgress[cacheKey];
    }
}

async function fetchAllForecasts(line, sensors) {
    try {
        // Check if cache is still valid
        if (forecastCache.lastUpdated && 
            Date.now() - forecastCache.lastUpdated < forecastCache.ttl) {
            return forecastCache.data;
        }

        const response = await fetch(`http://127.0.0.1:5000/api/bulk-forecast/${line}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sensors })
        });
        
        const data = await response.json();
        
        if (data.success) {
            forecastCache.data = data.data;
            forecastCache.lastUpdated = Date.now();
            return forecastCache.data;
        }
        throw new Error('Failed to fetch bulk forecasts');
    } catch (error) {
        console.error(`Error fetching bulk forecasts for ${line}:`, error);
        return null;
    }
}


// Chart Updates =======================================================

async function updateAnalytics(liveData, sensors, forecasts) {
    try {
        const statusCounts = { normal: 0, warning: 0, critical: 0 };
        let totalTemperature = 0;
        let validSensors = 0;

        await Promise.all(sensors.map(async sensor => {
            const value = liveData[sensor];
            
            if (typeof value !== 'number' || isNaN(value)) {
                console.warn(`Invalid value for ${sensor}:`, value);
                return;
            }

            validSensors++;
            totalTemperature += value;
            
            // Use the passed forecasts
            const statusInfo = await getSensorStatus(selectedLine, sensor, value, forecasts);
            statusCounts[statusInfo.status]++;
        }));

        // Update UI
        document.getElementById("totalSensors").textContent = sensors.length;
        document.getElementById("averageTemperature").textContent = 
            validSensors > 0 ? `${(totalTemperature / validSensors).toFixed(2)}°C` : '0.00°C';
        document.getElementById("optimalSensors").textContent = statusCounts.normal;
        document.getElementById("warningSensors").textContent = statusCounts.warning + statusCounts.critical;
        
        if (trafficLightChart) {
            trafficLightChart.updateSeries([
                statusCounts.normal, 
                statusCounts.warning, 
                statusCounts.critical
            ]);
        }
    } catch (error) {
        console.error("Error in updateAnalytics:", error);
    }
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

function updateLiveScatterChart(liveData, forecasts) {
    const selectedSensor = document.getElementById("sensorSelector").value;
    if (!selectedSensor || !liveData[selectedSensor]) return;

    const timestamp = new Date().getTime();
    const temperature = liveData[selectedSensor];
    const point = { x: timestamp, y: temperature };
    
    // Use the passed forecasts
    getSensorStatus(selectedLine, selectedSensor, temperature, forecasts)
        .then(statusInfo => {
            const status = statusInfo.status;
            liveScatterData[status].push(point);
            
            // Keep only the last 100 points
            if (liveScatterData[status].length > 100) {
                liveScatterData[status].shift();
            }

            scatterChart.updateOptions({
                series: [
                    { name: 'Normal', data: liveScatterData.normal },
                    { name: 'Warning', data: liveScatterData.warning },
                    { name: 'Critical', data: liveScatterData.critical }
                ]
            });
        });
}

async function getSensorsForLine(line) {
    try {
        const response = await fetch(`http://127.0.0.1:5000/api/admin/table-headers?tableID=${line}`);
        const data = await response.json();
        
        if (data.success) {
            // Filter headers to only include those starting with 'r'
            return data.headers.filter(header => header.startsWith('r'));
        } else {
            console.error("Failed to fetch table headers:", data.error);
            // Return default values as fallback
            return line === "line4" 
                ? ["r01", "r02", "r03", "r04", "r05", "r06", "r07", "r08"]
                : ["r01", "r02", "r03", "r04", "r05", "r06", "r07", "r08", "r09", "r10", "r11", "r12", "r13", "r14", "r15", "r16", "r17"];
        }
    } catch (error) {
        console.error("Error fetching table headers:", error);
        // Return default values as fallback
        return line === "line4" 
            ? ["r01", "r02", "r03", "r04", "r05", "r06", "r07", "r08"]
            : ["r01", "r02", "r03", "r04", "r05", "r06", "r07", "r08", "r09", "r10", "r11", "r12", "r13", "r14", "r15", "r16", "r17"];
    }
}

async function initializeDonutSlider(line) {
    const slider = document.getElementById('donutSlider');
    slider.innerHTML = '';
    currentSlide = 0;
    donutCharts = {};

    const sensors = await getSensorsForLine(line);

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

function updateScatterChart() {
    const selectedSensor = document.getElementById("sensorSelector").value;
    if (!selectedSensor) return;
    
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
                    const status = getSensorStatus(selectedLine, selectedSensor, item.value);
                    
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

async function updateSensorSelector(line) {
    const selector = document.getElementById("sensorSelector");
    selector.innerHTML = '';
    
    const sensors = await getSensorsForLine(line);
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
