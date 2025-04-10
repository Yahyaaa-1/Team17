const urlParams = new URLSearchParams(window.location.search);

// Dynamically fetch line and sensor parameters from URL query string
const line = urlParams.get("line") || "line4";  
const sensor = urlParams.get("sensor") || "r01"; 

if (!line || !sensor) {
  console.error('Line or sensor not specified in the URL');
  alert('Error: Please provide both line and sensor parameters in the URL');
}

const cacheKey = `sensorData_${line}_${sensor}`;
let chartData = [];
let historicalData = [];
let liveData = [];
let temperatureData = [];
let timeRange = 60 * 60 * 1000;
let isZoomed = false;
let currentZoomXaxis = { min: undefined, max: undefined };
let isFirstLiveDataFetch = true;
let forecastThresholds = null;
let trafficLightSystem = false;

document.getElementById("sensorTitle").textContent = `Sensor Data for ${sensor} on ${line}`;

// Initialize time filter buttons - activate 1 hour by default
document.querySelectorAll('.time-filter').forEach(button => {
  button.addEventListener('click', function() {
    document.querySelectorAll('.time-filter').forEach(btn => btn.classList.remove('active'));
    this.classList.add('active');
    updateTimeRange(this.dataset.range);
  });
  
  // Activate 1 hour button by default
  if (button.dataset.range === "hour") {
    button.classList.add('active');
  }
});

// Scatter Chart Configuration
const scatterChartOptions = {
  chart: {
    type: 'scatter',
    height: 400,
    animations: { enabled: false },
    toolbar: { 
      show: true,
      tools: {
        zoomin: true,
        zoomout: true,
        pan: true,
        reset: true,
        selection: true,
      },
      autoSelected: 'zoom',
    },
    zoom: { 
      enabled: true,
      type: 'x',
      autoScaleYaxis: true,
      zoomedArea: {
        fill: {
          color: '#90CAF9',
          opacity: 0.4
        },
        stroke: {
          color: '#0D47A1',
          opacity: 0.4,
          width: 1
        }
      }
    },
    events: {
      zoomed: function(chartContext, { xaxis, yaxis }) {
        isZoomed = true;
        currentZoomXaxis = xaxis;
      },
      scrolled: function(chartContext, { xaxis, yaxis }) {
        if (isZoomed) {
          currentZoomXaxis = xaxis;
        }
      }
    }
  },
  series: [{ name: 'Temperature', data: [] }],
  markers: {
    size: 6,
    strokeWidth: 0,
    hover: { size: 8 }
  },
  xaxis: {
    type: 'datetime',
    title: { text: 'Time' },
    labels: {
      datetimeFormatter: {
        hour: 'HH:mm',
        minute: 'HH:mm',
        second: 'HH:mm:ss'
      },
      datetimeUTC: false // Display in local time
    },
    tooltip: { enabled: true },
    tickAmount: 15,
    min: undefined,
    max: undefined
  },
  yaxis: {
    title: { text: 'Temperature (°C)' },
    tickAmount: 8,
    min: (min) => min - 2,
    max: (max) => max + 2
  },
  tooltip: {
    shared: false,
    intersect: true,
    x: {
      format: 'HH:mm:ss'
    }
  }
};

// Area Chart Configuration
const areaChartOptions = {
  chart: {
    type: 'area',
    height: 400,
    stacked: false,
    animations: { enabled: false },
    toolbar: { show: false },
    zoom: { enabled: false }
  },
  series: [{
    name: 'Temperature',
    data: []
  }],
  dataLabels: { enabled: false },
  stroke: {
    curve: 'smooth',
    width: 2
  },
  fill: {
    type: 'gradient',
    gradient: {
      shadeIntensity: 1,
      opacityFrom: 0.7,
      opacityTo: 0.3,
      stops: [0, 100]
    }
  },
  colors: ['#FF4560'],
  xaxis: {
    type: 'datetime',
    labels: {
      datetimeFormatter: {
        hour: 'HH:mm',
        day: 'MMM dd',
        month: 'MMM'
      },
      datetimeUTC: false // Display in local time
    }
  },
  yaxis: {
    title: { text: 'Temperature (°C)' }
  },
  tooltip: {
    shared: false,
    intersect: true,
    x: {
      format: 'HH:mm:ss'
    }
  }
};

// Initialize charts
const scatterChart = new ApexCharts(document.querySelector("#sensorScatterChart"), scatterChartOptions);
const areaChart = new ApexCharts(document.querySelector("#sensorAreaChart"), areaChartOptions);

scatterChart.render();
areaChart.render();

// Add event listener for the reset button after chart is rendered
setTimeout(() => {
  const resetBtn = document.querySelector('.apexcharts-reset-zoom-icon');
  if (resetBtn) {
    resetBtn.addEventListener('click', resetZoom);
  }
}, 1000);

function loadInitialData() {
  // First load any cached data
  const cached = JSON.parse(localStorage.getItem(cacheKey) || "[]");
  const now = new Date();
  const periodStart = now.getTime() - timeRange;
  
  liveData = cached.filter(p => p.x >= periodStart).sort((a, b) => a.x - b.x);
  
  // Fetch forecast data for this sensor
  fetchForecastData();
  
  // Then fetch historical data with appropriate length for initial time range
  fetchHistoricalData(getDataPointsForTimeRange(timeRange));
  
  // Start live updates
  setInterval(fetchLiveData, 8000);
  // Refresh forecast data periodically
  setInterval(fetchForecastData, 60000); // Every minute
}

// Helper function to determine how many data points to fetch based on time range
function getDataPointsForTimeRange(range) {
  // Assuming data points come approximately every 10 seconds
  const pointsPerHour = 360; // 360 points per hour (1 every 10 seconds)
  
  if (range <= 60 * 60 * 1000) { // 1 hour
    return pointsPerHour;
  } else if (range <= 2 * 60 * 60 * 1000) { // 2 hours
    return pointsPerHour * 2;
  } else if (range <= 24 * 60 * 60 * 1000) { // 1 day
    return pointsPerHour * 24;
  } else { // 1 week
    return pointsPerHour * 24 * 7;
  }
}

function fetchHistoricalData(pointsToFetch) {
  fetch(`http://127.0.0.1:5000/api/historical/${line}/${sensor}?length=${pointsToFetch}`)
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        historicalData = data.data.map(item => ({
          // Parse timestamp as local time
          x: new Date(item.timestamp).getTime(),
          y: item.value
        })).sort((a, b) => a.x - b.x);
        
        // Combine with any existing live data
        chartData = [...historicalData, ...liveData]
          .sort((a, b) => a.x - b.x)
          .filter((v, i, a) => a.findIndex(t => t.x === v.x) === i);
        
        temperatureData = chartData.map(p => p.y);
        // Combine with live data
        // updateCombinedData();
        updateCharts();
        updateStatistics();
      }
    })
    .catch(err => console.error("Historical data error:", err));
}

function fetchLiveData() {
  fetch(`http://localhost:5000/api/live-data/${line}`)
    .then(res => res.json())
    .then(data => {
      if (data.success && data.data && data.data[sensor] !== undefined) {
        // Parse timestamp as local time
        const timestamp = new Date(data.data.timestamp).getTime();
        const value = parseFloat(data.data[sensor]);
        const newData = { x: timestamp, y: value };
        
        liveData.push(newData);
        
        if (isFirstLiveDataFetch) {
          // On first fetch, combine historical + live data
          chartData = [...historicalData, ...liveData]
            .sort((a, b) => a.x - b.x)
            .filter((v, i, a) => a.findIndex(t => t.x === v.x) === i);
          
          isFirstLiveDataFetch = false;
        } else {
          // Subsequent updates just append new data
          chartData.push(newData);
        }
        
        // Filter to current time range
        const now = new Date().getTime();
        const periodStart = now - timeRange;
        chartData = chartData.filter(p => p.x >= periodStart).sort((a, b) => a.x - b.x);
        temperatureData = chartData.map(p => p.y);
        
        updateCharts();
        updateStatistics();
        
        // Cache the data
        localStorage.setItem(cacheKey, JSON.stringify(liveData));
        
        // Restore zoom state if zoomed
        if (isZoomed && currentZoomXaxis.min && currentZoomXaxis.max) {
          setTimeout(() => {
            scatterChart.zoomX(
              currentZoomXaxis.min,
              currentZoomXaxis.max
            );
          }, 100);
        }
      }
    })
    .catch(err => console.error("Live update error:", err));
}

function updateCharts() {
  const now = new Date().getTime();
  const periodStart = now - timeRange;
  
  // Prepare data with colors for scatter chart
  const scatterData = chartData.map(point => ({
    x: point.x,
    y: point.y,
    fillColor: getPointColor(point.y)
  }));
  
  // Update Scatter Chart
  scatterChart.updateSeries([{
    name: 'Temperature',
    data: scatterData
  }], false);
  
  if (!isZoomed) {
    scatterChart.updateOptions({
      xaxis: {
        min: periodStart,
        max: now
      }
    }, false, false);
  }

  // Update Area Chart with gradient based on traffic light system
  let areaColor = '#FF4560'; // Default color
  if (trafficLightSystem) {
    // Use the color of the latest data point
    const latestPoint = chartData[chartData.length - 1];
    if (latestPoint) {
      areaColor = getPointColor(latestPoint.y);
    }
  }
  
  areaChart.updateOptions({
    colors: [areaColor],
    fill: {
      type: 'gradient',
      gradient: {
        shadeIntensity: 1,
        opacityFrom: 0.7,
        opacityTo: 0.3,
        stops: [0, 100]
      }
    }
  }, false, false);
  
  areaChart.updateSeries([{
    name: 'Temperature',
    data: chartData
  }]);
  
  // Update current temperature display color
  if (temperatureData.length > 0) {
    const latestTemp = temperatureData[temperatureData.length - 1];
    const tempDisplay = document.getElementById("temperatureDisplay");
    tempDisplay.textContent = `${latestTemp.toFixed(1)} °C`;
    
    if (trafficLightSystem) {
      tempDisplay.style.color = getPointColor(latestTemp);
    } else {
      tempDisplay.style.color = ''; // Reset to default
    }
  }
}


function updateStatistics() {
  if (!temperatureData.length) return;
  
  const mean = (temperatureData.reduce((a, b) => a + b, 0) / temperatureData.length).toFixed(1);
  const min = Math.min(...temperatureData).toFixed(1);
  const max = Math.max(...temperatureData).toFixed(1);
  const latest = temperatureData[temperatureData.length - 1].toFixed(1);

  document.getElementById("temperatureDisplay").textContent = `${latest} °C`;
  document.getElementById("meanTemperature").textContent = `${mean} °C`;
  document.getElementById("minTemperature").textContent = `${min} °C`;
  document.getElementById("maxTemperature").textContent = `${max} °C`;
}

function updateTimeRange(selectedPeriod) {
  const now = new Date().getTime();
  
  switch (selectedPeriod) {
    case "hour":
      timeRange = 60 * 60 * 1000;
      break;
    case "2hours":
      timeRange = 2 * 60 * 60 * 1000;
      break;
    case "day":
      timeRange = 24 * 60 * 60 * 1000;
      break;
    case "week":
      timeRange = 7 * 24 * 60 * 60 * 1000;
      break;
    default:
      timeRange = 60 * 60 * 1000;
  }

  // Fetch new historical data appropriate for the selected time range
  fetchHistoricalData(getDataPointsForTimeRange(timeRange));
  
  // Filter data to new time range
  const periodStart = now - timeRange;
  chartData = [...historicalData, ...liveData]
    .filter(p => p.x >= periodStart)
    .sort((a, b) => a.x - b.x);
  temperatureData = chartData.map(p => p.y);

  // Reset zoom state when time range changes
  isZoomed = false;
  currentZoomXaxis = { min: undefined, max: undefined };

  // Update charts with new x-axis range
  scatterChart.updateOptions({
    xaxis: {
      min: periodStart,
      max: now
    }
  }, false, false);

  scatterChart.updateSeries([{
    name: 'Temperature',
    data: chartData
  }]);

  areaChart.updateSeries([{
    name: 'Temperature',
    data: chartData
  }]);

  updateStatistics();
}

function resetZoom() {
  isZoomed = false;
  currentZoomXaxis = { min: undefined, max: undefined };
  
  const now = new Date().getTime();
  const periodStart = now - timeRange;
  
  scatterChart.updateOptions({
    xaxis: {
      min: periodStart,
      max: now
    }
  }, false, false);
  
  scatterChart.resetSeries();
  updateCharts();
}

// Add this function to fetch forecast data for the specific sensor
function fetchForecastData() {
  fetch(`http://127.0.0.1:5000/api/forecasted-data/${line}`)
    .then(response => response.json())
    .then(data => {
      if (data.success && data.data?.length > 0) {
        const currentTime = new Date();
        const sensorForecasts = data.data.filter(item => item.sensor === sensor);
        
        if (sensorForecasts.length > 0) {
          const latestForecast = sensorForecasts[0];
          const latestForecastTime = new Date(latestForecast.forecast_time);
          const timeDifference = Math.abs(currentTime - latestForecastTime) / (1000 * 60);
          
          if (timeDifference <= 60) {
            trafficLightSystem = true;
            forecastThresholds = {
              lowerBound: latestForecast.lower_bound,
              upperBound: latestForecast.upper_bound
            };
            
            // Update charts with traffic light colors
            updateCharts();
            
            // Show threshold information
            document.getElementById('thresholdInfo').style.display = 'block';
            document.getElementById('lowerThreshold').textContent = forecastThresholds.lowerBound.toFixed(1);
            document.getElementById('upperThreshold').textContent = forecastThresholds.upperBound.toFixed(1);
          } else {
            handleInoperativeTrafficLightSystem();
          }
        } else {
          handleInoperativeTrafficLightSystem();
        }
      } else {
        handleInoperativeTrafficLightSystem();
      }
    })
    .catch(err => {
      console.error("Forecast data error:", err);
      handleInoperativeTrafficLightSystem();
    });
}

function handleInoperativeTrafficLightSystem() {
  trafficLightSystem = false;
  forecastThresholds = null;
  document.getElementById('thresholdInfo').style.display = 'none';
  
  // Update charts with default colors
  updateCharts();
}

// Helper function to determine point color based on traffic light system
function getPointColor(value) {
  if (!trafficLightSystem || !forecastThresholds) return '#FF4560'; // Default color
  
  const { lowerBound, upperBound } = forecastThresholds;
  
  if (value < lowerBound) {
    return '#FF0000'; // Critical (below lower bound)
  } else if (value > upperBound) {
    return '#FF0000'; // Critical (above upper bound)
  } else if (value < lowerBound + ((upperBound - lowerBound) * 0.1)) {
    return '#FFA500'; // Warning (near lower bound)
  } else if (value > upperBound - ((upperBound - lowerBound) * 0.1)) {
    return '#FFA500'; // Warning (near upper bound)
  } else {
    return '#00E396'; // Normal
  }
}

// Start the application
loadInitialData();