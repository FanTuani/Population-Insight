function formatPopulationValue(value) {
  const absValue = Math.abs(value);
  if (absValue >= 100000000) {
    return `${(value / 100000000).toFixed(2)} 亿`;
  }
  if (absValue >= 10000) {
    return `${(value / 10000).toFixed(2)} 万`;
  }
  return Number(value).toLocaleString("zh-CN");
}

function formatMetricValue(value, unit) {
  if (unit === "%") {
    return `${Number(value).toFixed(2)}%`;
  }
  if (unit === "person") {
    return formatPopulationValue(value);
  }
  return Number(value).toLocaleString("zh-CN");
}

function buildAxisFormatter(unit) {
  return function (value) {
    if (unit === "%") {
      return `${Number(value).toFixed(2)}%`;
    }
    if (unit === "person") {
      const absValue = Math.abs(value);
      if (absValue >= 100000000) {
        return `${(value / 100000000).toFixed(2)}亿`;
      }
      if (absValue >= 10000) {
        return `${(value / 10000).toFixed(0)}万`;
      }
      return Number(value).toLocaleString("zh-CN");
    }
    return Number(value).toLocaleString("zh-CN");
  };
}

function buildTrendRange(series, mode) {
  const minValue = Math.min(...series);
  const maxValue = Math.max(...series);
  if (mode === "absolute") {
    const span = maxValue - minValue || Math.abs(maxValue) * 0.03 || 1;
    const padding = span * 0.28;
    return {
      min: minValue - padding,
      max: maxValue + padding,
    };
  }

  const span = maxValue - minValue || 1;
  const padding = Math.max(span * 0.25, 0.2);
  return {
    min: minValue - padding,
    max: maxValue + padding,
  };
}

const chartInstances = new Map();

function getChart(container) {
  const existing = chartInstances.get(container.id);
  if (existing) {
    return existing;
  }
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
      formatter: function (params) {
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
    grid: { left: 80, right: 32, top: 60, bottom: 46 },
    xAxis: { type: "category", data: data.xAxis },
    yAxis: {
      type: "value",
      name: data.mode === "relative" ? "变化幅度" : data.metricLabel,
      scale: true,
      min: trendRange.min,
      max: trendRange.max,
      axisLabel: {
        formatter: buildAxisFormatter(data.axisUnit),
      },
    },
    series: [
      {
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
      },
    ],
  };
}

function createBarOption(data) {
  return {
    title: { text: data.title, left: "center", textStyle: { fontSize: 16 } },
    tooltip: {
      trigger: "axis",
      formatter: function (params) {
        const point = params[0];
        return `${point.axisValue}<br/>${data.metricLabel}：${formatMetricValue(point.value, data.axisUnit)}`;
      },
    },
    grid: { left: 80, right: 24, top: 54, bottom: 80 },
    xAxis: {
      type: "category",
      data: data.xAxis,
      axisLabel: { rotate: 20 },
    },
    yAxis: {
      type: "value",
      name: data.metricLabel,
      axisLabel: {
        formatter: buildAxisFormatter(data.axisUnit),
      },
    },
    series: [
      {
        type: "bar",
        data: data.series,
        itemStyle: {
          color: "#126e82",
          borderRadius: [10, 10, 0, 0],
        },
      },
    ],
  };
}

function createPieOption(data) {
  return {
    title: { text: data.title, left: "center", textStyle: { fontSize: 16 } },
    tooltip: {
      trigger: "item",
      formatter: function (params) {
        return `${params.name}<br/>人数：${formatPopulationValue(params.value)}<br/>占比：${params.percent}%`;
      },
    },
    legend: { bottom: 8 },
    series: [
      {
        type: "pie",
        radius: ["38%", "68%"],
        data: data.labels.map((label, index) => ({ name: label, value: data.series[index] })),
        itemStyle: {
          color: function (params) {
            return ["#2f67d8", "#126e82"][params.dataIndex % 2];
          },
        },
        label: {
          formatter: function (params) {
            return `${params.name}\n${params.percent}%`;
          },
        },
      },
    ],
  };
}

function renderMessage(container, message) {
  container.innerHTML = `<div class="muted" style="padding: 24px;">${message}</div>`;
}

async function submitChartForm(form) {
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
    if (targetId === "trend-chart") {
      chart.setOption(createTrendOption(payload.data));
    } else if (targetId === "bar-chart") {
      chart.setOption(createBarOption(payload.data));
    } else {
      chart.setOption(createPieOption(payload.data));
    }
  } catch (error) {
    renderMessage(container, "图表加载失败，请稍后重试。");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".chart-form").forEach((form) => {
    form.querySelectorAll("select").forEach((select) => {
      select.addEventListener("change", () => {
        submitChartForm(form);
      });
    });
    submitChartForm(form);
  });
  window.addEventListener("resize", () => {
    chartInstances.forEach((chart) => chart.resize());
  });
});
