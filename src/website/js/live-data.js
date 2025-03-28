let selectedLine = "line4";
let charts = {};
let chartMeta = {};
let expandedChart = null;

// Show/hide loading spinner
function setLoading(isLoading) {
  const spinner = document.getElementById("loading");
  if (spinner) {
    spinner.style.display = isLoading ? "block" : "none";
  }
}

document.addEventListener("DOMContentLoaded", function () {
  console.log("Dashboard loading for:", selectedLine);
  setLoading(true);

  initializeCharts(selectedLine)
    .then(() => {
      setLoading(false);
      fetchLiveData(); // first pull
    })
    .catch(err => {
      console.error("Init error:", err);
      setLoading(false);
    });

  document.getElementById("lineSelector").addEventListener("change", function () {
    selectedLine = this.value;
    console.log("Switched to:", selectedLine);
    setLoading(true);

    initializeCharts(selectedLine)
      .then(() => {
        setLoading(false);
        fetchLiveData();
      })
      .catch(err => {
        console.error("Switching error:", err);
        setLoading(false);
      });
  });

  setInterval(fetchLiveData, 5000);
});

// LocalStorage helpers
function getStorageKey() {
  return `sensorData_${selectedLine}`;
}
function loadChartData(sensor) {
  const stored = JSON.parse(localStorage.getItem(getStorageKey()) || "{}");
  return stored[sensor] || [];
}
function saveChartData(sensor, newPoint) {
  const key = getStorageKey();
  const stored = JSON.parse(localStorage.getItem(key) || "{}");
  const now = Date.now();
  if (!stored[sensor]) stored[sensor] = [];
  stored[sensor].push(newPoint);
  stored[sensor] = stored[sensor].filter(d => new Date(d.x).getTime() >= now - 60 * 60 * 1000);
  localStorage.setItem(key, JSON.stringify(stored));
}

// Only create chart if missing
function initializeCharts(line) {
  return new Promise((resolve, reject) => {
    const container = document.getElementById("chartsContainer");
    if (!container) return reject("Missing chart container");
    container.innerHTML = "";
    charts = {};
    chartMeta = {};

    fetch(`http://127.0.0.1:5000/api/live-data/${line}`)
      .then(response => response.json())
      .then(data => {
        if (!data.success) return reject("No sensors found");
        const sensors = Object.keys(data.data).filter(k => k.startsWith("r"));
        if (!sensors.length) return reject("No sensor keys");

        const renderPromises = sensors.map(sensor => {
          chartMeta[sensor] = line;

          const wrapper = document.createElement("div");
          wrapper.id = `chart-wrapper-${sensor}`;
          wrapper.classList.add("col-md-3", "mb-4", "mini-chart");

          wrapper.innerHTML = `
            <div class="chart-title">
              <a href="pages/sensor-data.html?sensor=${sensor}&line=${line}" class="sensor-link">${sensor}</a>
            </div>
            <div id="chart-${sensor}" style="height: 150px;"></div>
          `;

          wrapper.addEventListener("click", () => {
            window.location.href = `pages/sensor-data.html?sensor=${sensor}&line=${line}`;
          });

          container.appendChild(wrapper);

          const historical = loadChartData(sensor);
          const chartOptions = {
            chart: {
              type: "line",
              height: 150,
              animations: { enabled: false },
              toolbar: { show: false }
            },
            stroke: { curve: "smooth", width: 2 },
            series: [{ name: sensor, data: historical }],
            colors: ['#00E396'],
            xaxis: {
              type: "datetime",
              labels: { show: true, datetimeUTC: false, format: "HH:mm:ss" },
              tickAmount: 4,
              title: { text: "Time" }
            },
            yaxis: {
              title: { text: "Temperature (°C)" },
              labels: { show: true }
            }
          };

          charts[sensor] = new ApexCharts(document.querySelector(`#chart-${sensor}`), chartOptions);
          return charts[sensor].render();
        });

        Promise.all(renderPromises)
          .then(() => resolve())
          .catch(err => reject(err));
      })
      .catch(err => reject(err));
  });
}

// Update charts from backend data
function fetchLiveData() {
  fetch(`http://127.0.0.1:5000/api/live-data/${selectedLine}`)
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        updateCharts(data.data);
        updateAnalytics(data.data);
      } else {
        console.warn("Fetch failed:", data.error);
      }
    })
    .catch(err => console.error("Fetch error:", err));
}

// Smooth chart updates
function updateCharts(liveData) {
  const timestamp = new Date();
  Object.keys(liveData).forEach(sensor => {
    if (!sensor.startsWith("r")) return;

    const chart = charts[sensor];
    if (!chart) return console.warn("No chart for:", sensor);

    const { value, status } = liveData[sensor];
    const newPoint = { x: timestamp.toISOString(), y: value };

    chart.updateOptions({ colors: [getColorFromStatus(status)] });

    const current = chart.w.config.series[0].data;
    const updated = [...current, newPoint].slice(-50);
    chart.updateSeries([{ name: sensor, data: updated }]);

    saveChartData(sensor, newPoint);
  });
}

// Chart colors
function getColorFromStatus(status) {
  switch (status) {
    case "green": return "#00E396";
    case "amber": return "#FFA500";
    case "red": return "#FF0000";
    default: return "#888888";
  }
}

// Analytics + Pie chart
function updateAnalytics(data) {
  const sensors = Object.keys(data).filter(k => k.startsWith("r"));
  let total = sensors.length, sum = 0, green = 0, amber = 0, red = 0;

  sensors.forEach(s => {
    const { value, status } = data[s];
    sum += value;
    if (status === "green") green++;
    else if (status === "amber") amber++;
    else if (status === "red") red++;
  });

  document.getElementById("totalSensors").textContent = total;
  document.getElementById("averageTemperature").textContent = `${(sum / total).toFixed(2)}°C`;
  updateTrafficLightPieChart(green, amber, red);
}

function updateTrafficLightPieChart(green, amber, red) {
  const options = {
    series: [green, amber, red],
    chart: { type: "pie", height: 300 },
    labels: ["Green", "Amber", "Red"],
    colors: ["#00E396", "#FFA500", "#FF0000"],
    legend: { position: "right" },
    title: { text: "Sensor Status Distribution", align: "center" }
  };

  if (!window.trafficLightChart) {
    window.trafficLightChart = new ApexCharts(document.querySelector("#trafficLightPieChart"), options);
    window.trafficLightChart.render();
  } else {
    window.trafficLightChart.updateSeries([green, amber, red]);
  }
}