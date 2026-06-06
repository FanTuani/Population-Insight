function formatNationalPopulation(value) {
  const number = Number(value || 0);
  if (Math.abs(number) >= 100000000) return `${(number / 100000000).toFixed(2)} 亿人`;
  if (Math.abs(number) >= 10000) return `${(number / 10000).toFixed(0)} 万人`;
  return number.toLocaleString("zh-CN");
}

function formatNationalMetric(value, unit) {
  if (value === null || value === undefined) return "-";
  if (unit === "person") return formatNationalPopulation(value);
  if (unit === "permille") return `${Number(value).toFixed(2)}‰`;
  if (unit === "%") return `${Number(value).toFixed(2)}%`;
  return Number(value).toLocaleString("zh-CN");
}

function buildNationalAxisFormatter(unit) {
  return (value) => {
    if (unit === "person") return formatNationalPopulation(value);
    if (unit === "permille") return `${Number(value).toFixed(1)}‰`;
    if (unit === "%") return `${Number(value).toFixed(1)}%`;
    return Number(value).toLocaleString("zh-CN");
  };
}

function renderNationalMessage(container, message) {
  container.innerHTML = `<div class="empty-state">${message}</div>`;
}

let nationalTrendChart = null;
let nationalTrendResizeBound = false;

function createNationalTrendOption(data) {
  return {
    title: {
      text: data.title,
      left: "center",
      textStyle: { fontSize: 16, color: "#163042", fontWeight: 700 },
    },
    tooltip: {
      trigger: "axis",
      formatter(params) {
        const point = params[0];
        return `${point.axisValue} 年<br/>${data.metricLabel}：${formatNationalMetric(point.value, data.axisUnit)}`;
      },
    },
    grid: { left: 88, right: 36, top: 62, bottom: 58 },
    xAxis: {
      type: "category",
      data: data.xAxis,
      axisLabel: { interval: Math.max(0, Math.floor(data.xAxis.length / 12) - 1) },
    },
    yAxis: {
      type: "value",
      name: data.metricLabel,
      scale: true,
      axisLabel: { formatter: buildNationalAxisFormatter(data.axisUnit) },
      splitLine: { lineStyle: { color: "rgba(111, 136, 157, 0.18)" } },
    },
    series: [
      {
        name: data.metricLabel,
        type: "line",
        data: data.series,
        smooth: true,
        showSymbol: false,
        symbolSize: 6,
        lineStyle: { width: 3, color: "#176c7d" },
        itemStyle: { color: "#176c7d" },
        areaStyle: {
          color: {
            type: "linear",
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: "rgba(23,108,125,0.18)" },
              { offset: 1, color: "rgba(23,108,125,0.02)" },
            ],
          },
        },
      },
    ],
  };
}

async function loadNationalTrend(metric) {
  const container = document.getElementById("national-trend-chart");
  if (!container || !window.echarts) return;
  try {
    const response = await fetch(`/api/national-series/trend?metric=${encodeURIComponent(metric)}`);
    const payload = await response.json();
    if (!response.ok || !payload.success) {
      renderNationalMessage(container, payload.message || "全国长序列加载失败。");
      return;
    }
    nationalTrendChart = nationalTrendChart || echarts.init(container);
    nationalTrendChart.setOption(createNationalTrendOption(payload.data), true);
    if (!nationalTrendResizeBound) {
      nationalTrendResizeBound = true;
      window.addEventListener("resize", () => nationalTrendChart?.resize());
    }
  } catch (error) {
    renderNationalMessage(container, "全国长序列加载失败，请稍后重试。");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const selector = document.querySelector("[data-national-metric]");
  const initialMetric = selector?.value || "total_population";
  selector?.addEventListener("change", (event) => loadNationalTrend(event.target.value));
  loadNationalTrend(initialMetric);
});
