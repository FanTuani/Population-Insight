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

function formatForecastValue(value, unit) {
  if (value === null || value === undefined) {
    return "";
  }
  if (unit === "person") {
    return formatPopulationValue(value);
  }
  if (unit === "%") {
    return `${Number(value).toFixed(2)}%`;
  }
  return Number(value).toLocaleString("zh-CN");
}

function axisFormatter(unit) {
  return function (value) {
    if (unit === "person") {
      const absValue = Math.abs(value);
      if (absValue >= 100000000) {
        return `${(value / 100000000).toFixed(2)}亿`;
      }
      if (absValue >= 10000) {
        return `${(value / 10000).toFixed(0)}万`;
      }
    }
    if (unit === "%") {
      return `${Number(value).toFixed(1)}%`;
    }
    return Number(value).toLocaleString("zh-CN");
  };
}

function createPredictionOption(data) {
  return {
    title: { text: data.title, left: "center", textStyle: { fontSize: 16 } },
    tooltip: {
      trigger: "axis",
      formatter: function (params) {
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
    grid: { left: 86, right: 36, top: 58, bottom: 72 },
    xAxis: {
      type: "category",
      data: data.xAxis,
      axisLabel: { interval: 0 },
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
        symbolSize: 8,
        lineStyle: { width: 3, color: "#0f7a74" },
        itemStyle: { color: "#0f7a74" },
      },
      {
        name: "预测数据",
        type: "line",
        data: data.prediction,
        smooth: true,
        symbolSize: 8,
        lineStyle: { width: 3, type: "dashed", color: "#095ed2" },
        itemStyle: { color: "#095ed2" },
        areaStyle: { color: "rgba(9, 94, 210, 0.08)" },
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
  container.innerHTML = `<div class="muted" style="padding:24px;">${message}</div>`;
}

async function loadPredictionChart() {
  const form = document.getElementById("prediction-filter");
  const container = document.getElementById("prediction-chart");
  if (!form || !container || !window.echarts) {
    return;
  }
  const params = new URLSearchParams(new FormData(form));
  try {
    const response = await fetch(`${form.dataset.endpoint}?${params.toString()}`);
    const payload = await response.json();
    if (!response.ok || !payload.success) {
      renderPredictionMessage(container, payload.message || "预测图表加载失败。");
      return;
    }
    const chart = echarts.init(container);
    chart.setOption(createPredictionOption(payload.data));
    window.addEventListener("resize", () => chart.resize());
  } catch (error) {
    renderPredictionMessage(container, "预测图表加载失败，请稍后重试。");
  }
}

document.addEventListener("DOMContentLoaded", loadPredictionChart);
