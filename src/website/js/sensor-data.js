let selectedLine = "line4"; // Default line
let selectedSensor = "r01"; // Default sensor
let sensorChart = null; // Chart instance
 
document.addEventListener("DOMContentLoaded", function () {
    // Extract sensor & line from URL params
    const urlParams = new URLSearchParams(window.location.search);
    selectedSensor = urlParams.get("sensor") || "r01";
    selectedLine = urlParams.get("line") || "line4";
 
    console.log(`Selected Line: ${selectedLine}, Sensor: ${selectedSensor}`);
 
    initializeChart();
    fetchSensorData(); // Fetch initial data
    setInterval(fetchSensorData, 5000); // Fetch new data every 5 seconds
});
 
// Fetch real-time sensor data from Flask API
function fetchSensorData() {
    console.log(`Fetching data for ${selectedSensor} on ${selectedLine}...`);
 
    fetch(`http://127.0.0.1:5000/api/sensor-data/${selectedLine}/${selectedSensor}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP Error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                console.log(`Received data:`, data.data);
                updateChart(data.data);
            } else {
                console.error("No data available for this sensor.");
            }
        })
        .catch(error => console.error("Error fetching sensor data:", error));
}
 
// Initialize chart
function initializeChart() {
    const chartContainer = document.getElementById("sensorChart");
    chartContainer.innerHTML = ""; // Clear previous chart
 
    sensorChart = new ApexCharts(chartContainer, {
        chart: { type: "line", height: 400, animations: { enabled: false } },
        series: [{ name: selectedSensor, data: [] }],
        xaxis: { type: "datetime", labels: { format: "HH:mm:ss" } },
        yaxis: { title: { text: selectedSensor } }
    });
 
    sensorChart.render();
}
 
// Update chart with new sensor data
function updateChart(sensorData) {
    let timestamp = new Date(sensorData.timestamp).getTime(); // Convert timestamp to JS format
    let value = sensorData[selectedSensor];
 
    if (!value) {
        console.warn(`No value for sensor ${selectedSensor}`);
        return;
    }
 
    let newData = { x: timestamp, y: value };
 
    sensorChart.updateSeries([{
        name: selectedSensor,
        data: [...(sensorChart.w.config.series[0].data || []), newData].slice(-50)
    }]);
}
 