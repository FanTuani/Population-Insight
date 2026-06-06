const NATIONAL_SUPPORTED_METRICS = new Set([
  "total_population",
  "birth_rate",
  "death_rate",
  "natural_growth_rate",
  "urbanization_rate",
]);

function formatPopulationValue(value) {
  const number = Number(value || 0);
  const absValue = Math.abs(number);
  if (absValue >= 100000000) return `${(number / 100000000).toFixed(2)} 亿`;
  if (absValue >= 10000) return `${(number / 10000).toFixed(2)} 万`;
  return number.toLocaleString("zh-CN");
}

function formatMetricValue(value, unit) {
  if (value === null || value === undefined) return "-";
  if (unit === "%") return `${Number(value).toFixed(2)}%`;
  if (unit === "permille") return `${Number(value).toFixed(2)}‰`;
  if (unit === "person") return formatPopulationValue(value);
  return Number(value).toLocaleString("zh-CN");
}

function buildAxisFormatter(unit) {
  return (value) => {
    if (unit === "person") return formatPopulationValue(value);
    if (unit === "permille") return `${Number(value).toFixed(1)}‰`;
    if (unit === "%") return `${Number(value).toFixed(1)}%`;
    return Number(value).toLocaleString("zh-CN");
  };
}

function buildTrendRange(series, mode) {
  const clean = series.filter((value) => value !== null && value !== undefined);
  if (!clean.length) return { min: 0, max: 1 };
  const minValue = Math.min(...clean);
  const maxValue = Math.max(...clean);
  const span = maxValue - minValue || Math.abs(maxValue) * 0.03 || 1;
  const padding = mode === "absolute" ? span * 0.28 : Math.max(span * 0.25, 0.2);
  return { min: minValue - padding, max: maxValue + padding };
}

const chartInstances = new Map();

function getChart(container) {
  const existing = chartInstances.get(container.id);
  if (existing) return existing;
  const chart = echarts.init(container);
  chartInstances.set(container.id, chart);
  return chart;
}

function createTrendOption(data) {
  const trendRange = buildTrendRange(data.series, data.mode);
  return {
    title: { text: data.title, left: "center", textStyle: { fontSize: 16 } },
    tooltip: {
      trigger: "axis",
      formatter(params) {
        const point = params[0];
        const index = point.dataIndex;
        const lines = [
          `${point.axisValue} 年`,
          `${data.mode === "relative" ? "相对变化" : data.rawMetricLabel}：${formatMetricValue(point.value, data.axisUnit)}`,
        ];
        if (data.mode === "relative") {
          lines.push(`实际值：${formatMetricValue(data.rawSeries[index], data.rawAxisUnit)}`);
          lines.push(`基期值：${formatMetricValue(data.baseValue, data.rawAxisUnit)}`);
        }
        return lines.join("<br/>");
      },
    },
    grid: { left: 86, right: 36, top: 60, bottom: 52 },
    xAxis: {
      type: "category",
      data: data.xAxis,
      axisLabel: { interval: Math.max(0, Math.floor(data.xAxis.length / 12) - 1) },
    },
    yAxis: {
      type: "value",
      name: data.mode === "relative" ? "变化幅度" : data.metricLabel,
      scale: true,
      min: trendRange.min,
      max: trendRange.max,
      axisLabel: { formatter: buildAxisFormatter(data.axisUnit) },
    },
    series: [{
      type: "line",
      data: data.series,
      smooth: true,
      symbolSize: 8,
      lineStyle: { width: 3, color: "#126e82" },
      itemStyle: { color: "#2f67d8" },
      areaStyle: { color: "rgba(47, 103, 216, 0.10)" },
      markLine: data.mode === "relative" ? {
        symbol: "none",
        lineStyle: { type: "dashed", color: "rgba(23,53,61,0.35)" },
        data: [{ yAxis: 0 }],
      } : undefined,
    }],
  };
}

function createBarOption(data) {
  const manyRegions = data.xAxis.length > 18;
  return {
    title: { text: data.title, left: "center", textStyle: { fontSize: 16 } },
    tooltip: {
      trigger: "axis",
      formatter(params) {
        const point = params[0];
        return `${point.axisValue}<br/>${data.metricLabel}：${formatMetricValue(point.value, data.axisUnit)}`;
      },
    },
    grid: { left: 86, right: 28, top: 58, bottom: manyRegions ? 118 : 82 },
    xAxis: {
      type: "category",
      data: data.xAxis,
      axisLabel: {
        interval: 0,
        rotate: manyRegions ? 42 : 20,
        width: manyRegions ? 92 : 110,
        overflow: "break",
        lineHeight: 16,
      },
    },
    yAxis: {
      type: "value",
      name: data.metricLabel,
      axisLabel: { formatter: buildAxisFormatter(data.axisUnit) },
    },
    dataZoom: manyRegions ? [{ type: "inside", xAxisIndex: 0 }] : [],
    series: [{
      type: "bar",
      data: data.series,
      itemStyle: { color: "#126e82", borderRadius: [8, 8, 0, 0] },
    }],
  };
}

function createPieOption(data) {
  return {
    title: { text: data.title, left: "center", textStyle: { fontSize: 16 } },
    tooltip: {
      trigger: "item",
      formatter(params) {
        return `${params.name}<br/>人数：${formatPopulationValue(params.value)}<br/>占比：${params.percent}%`;
      },
    },
    legend: { bottom: 8 },
    series: [{
      type: "pie",
      radius: ["38%", "68%"],
      data: data.labels.map((label, index) => ({ name: label, value: data.series[index] })),
      itemStyle: { color: (params) => ["#2f67d8", "#126e82"][params.dataIndex % 2] },
      label: { formatter: (params) => `${params.name}\n${params.percent}%` },
    }],
  };
}

function renderMessage(container, message) {
  container.innerHTML = `<div class="empty-state">${message}</div>`;
}

function syncNationalMetricOptions(form) {
  const region = form.querySelector('select[name="region"]')?.value;
  const metricSelect = form.querySelector('select[name="metric"]');
  if (!metricSelect) return;
  metricSelect.querySelectorAll("option").forEach((option) => {
    option.disabled = region === "全国" && !NATIONAL_SUPPORTED_METRICS.has(option.value);
  });
  if (region === "全国" && metricSelect.selectedOptions[0]?.disabled) {
    metricSelect.value = "total_population";
  }
}

async function submitChartForm(form) {
  syncNationalMetricOptions(form);
  const endpoint = form.dataset.endpoint;
  const targetId = form.dataset.target;
  const container = document.getElementById(targetId);
  const params = new URLSearchParams(new FormData(form));

  try {
    const response = await fetch(`${endpoint}?${params.toString()}`);
    const payload = await response.json();
    if (!response.ok || !payload.success) {
      renderMessage(container, payload.message || "图表加载失败。");
      return;
    }

    const chart = getChart(container);
    if (targetId === "trend-chart") chart.setOption(createTrendOption(payload.data), true);
    else if (targetId === "bar-chart") chart.setOption(createBarOption(payload.data), true);
    else chart.setOption(createPieOption(payload.data), true);
  } catch (error) {
    renderMessage(container, "图表加载失败，请稍后重试。");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".chart-form").forEach((form) => {
    form.querySelectorAll("select").forEach((select) => {
      select.addEventListener("change", () => submitChartForm(form));
    });
    submitChartForm(form);
  });
  window.addEventListener("resize", () => chartInstances.forEach((chart) => chart.resize()));
});
