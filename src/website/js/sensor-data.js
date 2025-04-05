let selectedLine = "line4";
let selectedSensor = "r01";
let historicalData = [];
let liveData = []; // Added missing declaration
let isFirstLiveDataFetch = true;
let sensorChart = null;
let initialTimeRange = 20000;


document.addEventListener("DOMContentLoaded", function () {
    const urlParams = new URLSearchParams(window.location.search);
    selectedSensor = urlParams.get("sensor") || "r01";
    selectedLine = urlParams.get("line") || "line4";
    const cacheKey = `sensorData_${selectedLine}_${selectedSensor}`;

    document.getElementById("sensorTitle").textContent = `Sensor Data for ${selectedSensor} on ${selectedLine}`;

    // Initialize charts
    initializeChart();
    sensorScatterChart.render();
    sensorAreaChart.render();


    // Questionable code??? is it neeeded?
    // // Load cached data
    // const cached = JSON.parse(localStorage.getItem(cacheKey) || "[]");
    // const now = Date.now();
    // const oneDayAgo = now - 24 * 60 * 60 * 1000;
    // liveData = cached.filter(p => p.x >= oneDayAgo).sort((a, b) => a.x - b.x);

    // Fetch historical data from API and fill charts
    fetchHistoricalData(selectedLine, selectedSensor);

    setInterval(fetchLiveData, 8000);
});

function initializeChart() {
  const chartContainer = document.getElementById("sensorChart");
  chartContainer.innerHTML = "";

  //const timeRange = getTimeRange(2); // Get 2-hour range

  sensorChart = new ApexCharts(chartContainer, {
    chart: { 
      type: "line", 
      height: 400, 
      animations: { enabled: true },
      zoom: { enabled: true,
        type: 'x',
        autoScaleYaxis: true
       }
    },
    series: [{ name: selectedSensor, data: [] }],
    xaxis: {
      type: "datetime",
      labels: {
        datetimeFormatter: {
          hour: "HH:mm",
          minute: "HH:mm",
          second: "HH:mm:ss"
        }
      },
      range: 3500000
    },
    yaxis: { title: { text: "Temperature (°C)" } },
    stroke: { curve: 'straight', width: 2 }
  });

  sensorChart.render();
}
// Initialize scatter chart with time range
const sensorScatterChart = new ApexCharts(document.querySelector("#sensorScatterChart"), {
    chart: { 
      type: "scatter", 
      height: 400, 
      animations: { enabled: true },
      zoom: { enabled: true,
        type: 'x',
        autoScaleYaxis: true
       }
    },
    series: [],
    xaxis: { 
      type: "datetime", 
      labels: { format: "HH:mm:ss" },
      range: 3500000
    },
    yaxis: { 
      title: { text: "Temperature (°C)" } 
    },
    markers: { 
      size: 5, 
      colors: ["#FF4560"] 
    }
  });
  
  // Initialize area chart with time range
  const sensorAreaChart = new ApexCharts(document.querySelector("#sensorAreaChart"), {
    chart: { 
      type: "area", 
      height: 400, 
      animations: { enabled: true },
      zoom: { enabled: true,
        type: 'x',
        autoScaleYaxis: true
       }
    },
    series: [],
    xaxis: { 
      type: "datetime", 
      labels: { format: "HH:mm:ss" },
      range: 3500000
    },
    yaxis: { 
      title: { text: "Temperature (°C)" } 
    },
    fill: {
      type: "gradient",
      gradient: { 
        shadeIntensity: 0.5, 
        opacityFrom: 0.6, 
        opacityTo: 0.2, 
        stops: [0, 90, 100] 
      }
    },
    stroke: {
      curve: 'straight',
      width: 2
    }
  });

function fetchLiveData() {
  fetch(`http://localhost:5000/api/live-data/${selectedLine}`)
    .then(res => res.json())
    .then(data => {
      if (data.success && data.data && data.data[selectedSensor] !== undefined) {
        const timestamp = new Date(data.data.timestamp).getTime();
        const value = parseFloat(data.data[selectedSensor]);
        const newData = { x: timestamp, y: value };
        
        liveData.push(newData);
        
        if (isFirstLiveDataFetch) {
          // On first fetch, combine historical + live data
          const combinedData = [...historicalData, ...liveData]
            .sort((a, b) => a.x - b.x)
            .filter((v, i, a) => a.findIndex(t => t.x === v.x) === i);
          
          sensorChart.updateSeries([{
            name: selectedSensor,
            data: combinedData
          }]);
          
          updateSecondaryCharts(combinedData);
          updateStatistics(combinedData);
          
          isFirstLiveDataFetch = false;
        } else {
          // Subsequent updates just append new data
          sensorChart.appendData([{
            id: selectedSensor,
            data: [newData]
          }]);
          
          updateCombinedData();
        }
        
        // Cache the data
        localStorage.setItem(`sensorData_${selectedLine}_${selectedSensor}`, JSON.stringify(liveData));
      }
    })
    .catch(err => console.error("Live data error:", err));
}

function fetchHistoricalData(line, sensor) {
  const url = `http://127.0.0.1:5000/api/historical/${line}/${sensor}?length=100`;
  fetch(url)
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        historicalData = data.data.map(item => ({
          x: new Date(item.timestamp).getTime(),
          y: item.value
        })).sort((a, b) => a.x - b.x);
        
        sensorChart.updateSeries([{
          name: selectedSensor,
          data: historicalData
        }]);
        
        updateSecondaryCharts(historicalData);
        updateStatistics(historicalData);
      }
    })
    .catch(err => console.error("Historical data error:", err));
}

function updateCombinedData() {
  const combinedData = [...historicalData, ...liveData]
    .sort((a, b) => a.x - b.x)
    .filter((v, i, a) => a.findIndex(t => t.x === v.x) === i);
  
  updateSecondaryCharts(combinedData);
  updateStatistics(combinedData);
}

function updateSecondaryCharts(data) {
  const seriesData = [{ name: selectedSensor, data }];
  sensorScatterChart.updateSeries(seriesData);
  sensorAreaChart.updateSeries(seriesData);
}

function updateStatistics(data) {
  const tempData = data.map(p => p.y);
  if (!tempData.length) return;
  
  const latest = tempData[tempData.length - 1].toFixed(1);
  const mean = (tempData.reduce((a, b) => a + b, 0) / tempData.length).toFixed(1);
  const min = Math.min(...tempData).toFixed(1);
  const max = Math.max(...tempData).toFixed(1);

  document.getElementById("temperatureDisplay").textContent = `${latest} °C`;
  document.getElementById("meanTemperature").textContent = `${mean} °C`;
  document.getElementById("minTemperature").textContent = `${min} °C`;
  document.getElementById("maxTemperature").textContent = `${max} °C`;
}

function getTimeRange(hours) {
    const now = new Date();
    const past = new Date(now.getTime() - (hours * 60 * 60 * 1000));
    return {
      min: past.getTime(),
      max: now.getTime() + (5 * 60 * 1000) // Add 5 minutes buffer
    };
  }