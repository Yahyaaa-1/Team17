let selectedLine = "line4";
let donutCharts = {};
let currentSlide = 0;
let trafficLightChart;
let barChart;
let scatterChart;
let liveScatterData = { normal: [], warning: [], critical: [] };


async function getSensorStatus(line, sensor, currentValue) {
    try {
        // Call API to get latest forecast for this sensor
        const response = await fetch(`http://127.0.0.1:5000/api/latest-forecast/${line}/${sensor}`);
        const data = await response.json();
        
        if (data.success && data.forecast) {
            const forecast = data.forecast;
            const lower = forecast.lower_bound;
            const upper = forecast.upper_bound;
            const range = upper - lower;
            
            // Calculate 20% buffer zone
            const buffer = range * 0.2;
            
            if (currentValue >= lower && currentValue <= upper) {
                return { status: 'normal', color: '#00E396' };
            } 
            else if (currentValue >= (lower - buffer) && currentValue <= (upper + buffer)) {
                return { status: 'warning', color: '#FFA500' };
            } 
            else {
                return { status: 'critical', color: '#FF0000' };
            }
        }
    } catch (error) {
        console.error("Error checking sensor status:", error);
        // Default to normal if there's an error
        return { status: 'normal', color: '#00E396' };
    }
}

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

async function getTrafficLightStatus(sensor, value) {
    const forecast = await getCachedForecast(selectedLine, sensor);
    
    if (!forecast) return 'normal'; // Default if no forecast --------------- no forecast
    
    const { lower_bound: lower, upper_bound: upper } = forecast;
    const range = upper - lower;
    const buffer = range * 0.2;
    
    if (value >= lower && value <= upper) return 'normal';
    if (value >= (lower - buffer) && value <= (upper + buffer)) return 'warning';
    return 'critical';
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

const forecastCache = {
    data: {},
    lastUpdated: null,
    ttl: 30000, // 30 seconds cache
    inProgress: {}
};

async function getCachedForecast(line, sensor) {
    // Include line in the cache key
    const cacheKey = `${line}-${sensor}`;
    
    if (forecastCache.data[cacheKey] && 
        Date.now() - forecastCache.lastUpdated < forecastCache.ttl) {
        return forecastCache.data[cacheKey];
    }
    
    if (forecastCache.inProgress[cacheKey]) {
        return forecastCache.inProgress[cacheKey];
    }
    
    try {
        forecastCache.inProgress[cacheKey] = fetch(
            `http://127.0.0.1:5000/api/latest-forecast/${line}/${sensor}`
        ).then(response => response.json());
        
        const data = await forecastCache.inProgress[cacheKey];
        
        if (data.success) {
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
        const response = await fetch(`http://127.0.0.1:5000/api/bulk-forecast/${line}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ sensors })
        });
        
        const data = await response.json();
        
        if (data.success) {
            Object.entries(data.data).forEach(([sensor, forecast]) => {
                const cacheKey = `${line}-${sensor}`;
                forecastCache.data[cacheKey] = forecast;
            });
            forecastCache.lastUpdated = Date.now();
        }
    } catch (error) {
        console.error(`Error fetching bulk forecasts for ${line}:`, error);
    }
}

async function fetchLiveData() {
    try {
        const response = await fetch(`http://127.0.0.1:5000/api/live-data/${selectedLine}`);
        const data = await response.json();
        
        if (data.success) {
            const liveData = data.data;
            const sensors = Object.keys(liveData).filter(key => key.startsWith('r'));
            
            // Process sensors sequentially to avoid API flooding
            for (const sensor of sensors) {
                try {
                    const value = liveData[sensor];
                    
                    // Skip if value is invalid
                    if (typeof value !== 'number' || isNaN(value)) {
                        console.warn(`Invalid value for ${sensor}:`, value);
                        continue;
                    }
                    
                    // Get status with fallback
                    const statusInfo = await getSensorStatus(selectedLine, sensor, value) || {
                        status: 'normal',
                        color: '#00E396'
                    };
                    
                    // Update donut chart if exists
                    if (donutCharts[sensor]) {
                        donutCharts[sensor].updateOptions({
                            colors: [statusInfo.color]
                        });
                        donutCharts[sensor].updateSeries([value]);
                    }
                } catch (sensorError) {
                    console.error(`Error processing ${sensor}:`, sensorError);
                }
            }
            
            // Update other charts
            await updateAnalytics(liveData);
            updateBarChart(liveData);
            updateLiveScatterChart(liveData);
        } else {
            console.error("Failed to fetch live data:", data);
        }
    } catch (error) {
        console.error("Error fetching live data:", error);
    }
}

// async function fetchLiveData() {
//     try {
//         const response = await fetch(`http://127.0.0.1:5000/api/live-data/${selectedLine}`);
//         const data = await response.json();
//             if (data.success) {
//                 const liveData = data.data;
//                 const sensors = Object.keys(liveData).filter(key => key.startsWith('r'));
//                // Update all charts with forecast-based colors
//                 for (const sensor of sensors) {
//                     const value = liveData[sensor];
//                     const statusInfo = await getSensorStatus(selectedLine, sensor, value);
                    
//                     if (donutCharts[sensor]) {
//                         donutCharts[sensor].updateOptions({
//                             colors: [statusInfo.color]
//                         });
//                         donutCharts[sensor].updateSeries([value]);
//                     }
//                 }
            
//             updateAnalytics(liveData);
//             updateBarChart(liveData);
//             updateLiveScatterChart(liveData);
//             } else {
//                 console.error("Failed to fetch live data");
//             }
//         }
//     catch (error) {
//         console.error("Error fetching live data:", error);
//     }
// }

async function calculateTrafficLightStatus(sensor, value) {
    try {
        // Always use the currently selected line
        const forecast = await getCachedForecast(selectedLine, sensor);
        
        if (!forecast) {
            return { 
                status: 'normal', 
                color: '#00E396',
                lowerBound: null,
                upperBound: null
            };
        }
        
        const { lower_bound: lower, upper_bound: upper } = forecast;
        const range = upper - lower;
        const buffer = range * 0.2;
        
        if (value >= lower && value <= upper) {
            return { 
                status: 'normal', 
                color: '#00E396',
                lowerBound: lower,
                upperBound: upper
            };
        } 
        else if (value >= (lower - buffer) && value <= (upper + buffer)) {
            return { 
                status: 'warning', 
                color: '#FFA500',
                lowerBound: lower,
                upperBound: upper
            };
        } 
        else {
            return { 
                status: 'critical', 
                color: '#FF0000',
                lowerBound: lower,
                upperBound: upper
            };
        }
    } catch (error) {
        console.error(`Error calculating status for ${selectedLine}-${sensor}:`, error);
        return { 
            status: 'normal', 
            color: '#00E396',
            lowerBound: null,
            upperBound: null
        };
    }
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

async function updateAnalytics(liveData) {
    try {
        const sensors = getSensorsForLine(selectedLine);
        const totalSensors = sensors.length;
        let totalTemperature = 0;
        let greenCount = 0;
        let amberCount = 0;
        let redCount = 0;
        let validSensors = 0;

        // Process sensors sequentially for better error handling
        for (const sensor of sensors) {
            try {
                const value = liveData[sensor];
                
                // Skip if value is invalid
                if (typeof value !== 'number' || isNaN(value)) {
                    console.warn(`Invalid temperature value for ${sensor}:`, value);
                    continue;
                }

                validSensors++;
                totalTemperature += value;
                
                // Get status with fallback
                const statusInfo = await getSensorStatus(selectedLine, sensor, value) || {
                    status: 'normal',
                    color: '#00E396'
                };

                // Count statuses
                switch (statusInfo.status) {
                    case 'normal':
                        greenCount++;
                        break;
                    case 'warning':
                        amberCount++;
                        break;
                    case 'critical':
                        redCount++;
                        break;
                    default:
                        console.warn(`Unknown status for ${sensor}:`, statusInfo.status);
                        greenCount++; // Default to normal
                }
            } catch (sensorError) {
                console.error(`Error processing sensor ${sensor}:`, sensorError);
            }
        }

        // Calculate average (protected against division by zero)
        const averageTemperature = validSensors > 0 
            ? (totalTemperature / validSensors).toFixed(2)
            : '0.00';

        // Safely update UI elements
        const updateIfExists = (id, value) => {
            const el = document.getElementById(id);
            if (el) el.textContent = value;
        };

        updateIfExists("totalSensors", totalSensors);
        updateIfExists("averageTemperature", `${averageTemperature}°C`);
        updateIfExists("optimalSensors", greenCount);
        updateIfExists("warningSensors", amberCount + redCount);
        
        if (trafficLightChart) {
            trafficLightChart.updateSeries([greenCount, amberCount, redCount]);
        }
    } catch (error) {
        console.error("Error in updateAnalytics:", error);
    }
}

async function getTrafficLightColor(sensor, value) {
    const status = await getTrafficLightStatus(sensor, value);
    return {
        normal: '#00E396',
        warning: '#FFA500',
        critical: '#FF0000'
    }[status];
}

function closeExpandedChart() {
    document.getElementById("expandedChartContainer").style.display = "none";

}