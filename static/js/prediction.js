function formatPopulationValue(value) {
  const number = Number(value || 0);
  const absValue = Math.abs(number);
  if (absValue >= 100000000) return `${(number / 100000000).toFixed(2)} 亿`;
  if (absValue >= 10000) return `${(number / 10000).toFixed(2)} 万`;
  return number.toLocaleString("zh-CN");
}

function formatForecastValue(value, unit) {
  if (value === null || value === undefined) return "";
  if (unit === "person") return formatPopulationValue(value);
  if (unit === "%") return `${Number(value).toFixed(2)}%`;
  if (unit === "permille") return `${Number(value).toFixed(2)}‰`;
  return Number(value).toLocaleString("zh-CN");
}

function axisFormatter(unit) {
  return (value) => {
    if (unit === "person") return formatPopulationValue(value);
    if (unit === "%") return `${Number(value).toFixed(1)}%`;
    if (unit === "permille") return `${Number(value).toFixed(1)}‰`;
    return Number(value).toLocaleString("zh-CN");
  };
}

function createPredictionOption(data) {
  return {
    title: { text: data.title, left: "center", textStyle: { fontSize: 16 } },
    tooltip: {
      trigger: "axis",
      formatter(params) {
        const lines = [`${params[0].axisValue} 年`];
        params.forEach((point) => {
          if (point.value !== null && point.value !== undefined) {
            lines.push(`${point.seriesName}：${formatForecastValue(point.value, data.axisUnit)}`);
          }
        });
        return lines.join("<br/>");
      },
    },
    legend: { bottom: 8 },
    grid: { left: 90, right: 38, top: 62, bottom: 76 },
    xAxis: {
      type: "category",
      data: data.xAxis,
      axisLabel: { interval: Math.max(0, Math.floor(data.xAxis.length / 12) - 1) },
    },
    yAxis: {
      type: "value",
      name: data.metricLabel,
      scale: true,
      axisLabel: { formatter: axisFormatter(data.axisUnit) },
    },
    series: [
      {
        name: "历史数据",
        type: "line",
        data: data.history,
        smooth: true,
        symbolSize: 6,
        lineStyle: { width: 3, color: "#126e82" },
        itemStyle: { color: "#126e82" },
      },
      {
        name: "预测数据",
        type: "line",
        data: data.prediction,
        smooth: true,
        symbolSize: 7,
        lineStyle: { width: 3, type: "dashed", color: "#2f67d8" },
        itemStyle: { color: "#2f67d8" },
        areaStyle: { color: "rgba(47, 103, 216, 0.10)" },
        markLine: {
          symbol: "none",
          lineStyle: { color: "rgba(23,53,61,0.35)", type: "dashed" },
          data: [{ xAxis: String(data.splitYear) }],
        },
      },
    ],
  };
}

function renderPredictionMessage(container, message) {
  container.innerHTML = `<div class="empty-state">${message}</div>`;
}

function syncPredictionMetricOptions(form) {
  const region = form.querySelector('select[name="region"]')?.value;
  const metricSelect = form.querySelector('select[name="metric"]');
  if (!metricSelect) return;
  metricSelect.querySelectorAll("option").forEach((option) => {
    option.disabled = region === "全国" && option.value !== "total_population";
  });
  if (region === "全国") metricSelect.value = "total_population";
}

async function loadPredictionChart() {
  const form = document.getElementById("prediction-filter");
  const container = document.getElementById("prediction-chart");
  if (!form || !container || !window.echarts) return;
  syncPredictionMetricOptions(form);
  const params = new URLSearchParams(new FormData(form));
  try {
    const response = await fetch(`${form.dataset.endpoint}?${params.toString()}`);
    const payload = await response.json();
    if (!response.ok || !payload.success) {
      renderPredictionMessage(container, payload.message || "预测图表加载失败。");
      return;
    }
    const chart = echarts.getInstanceByDom(container) || echarts.init(container);
    chart.setOption(createPredictionOption(payload.data), true);
    window.addEventListener("resize", () => chart.resize(), { once: true });
  } catch (error) {
    renderPredictionMessage(container, "预测图表加载失败，请稍后重试。");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("prediction-filter");
  form?.querySelectorAll("select").forEach((select) => {
    select.addEventListener("change", loadPredictionChart);
  });
  loadPredictionChart();
});
