function formatCompareValue(value, unit) {
  if (value === null || value === undefined) {
    return "--";
  }
  if (unit === "person") {
    const absValue = Math.abs(value);
    if (absValue >= 100000000) {
      return `${(value / 100000000).toFixed(2)} 亿`;
    }
    if (absValue >= 10000) {
      return `${(value / 10000).toFixed(2)} 万`;
    }
    return Number(value).toLocaleString("zh-CN");
  }
  if (unit === "%") {
    return `${Number(value).toFixed(2)}%`;
  }
  return Number(value).toLocaleString("zh-CN");
}

function compareAxisFormatter(unit) {
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

function createComparisonOption(data) {
  return {
    title: { text: data.title, left: "center", textStyle: { fontSize: 16 } },
    tooltip: {
      trigger: "axis",
      formatter: function (params) {
        const lines = [`${params[0].axisValue} 年`];
        params.forEach((point) => {
          lines.push(`${point.seriesName}：${formatCompareValue(point.value, data.axis_unit)}`);
        });
        return lines.join("<br/>");
      },
    },
    legend: { bottom: 8 },
    grid: { left: 86, right: 36, top: 58, bottom: 78 },
    xAxis: { type: "category", data: data.years },
    yAxis: {
      type: "value",
      name: data.metric_label,
      scale: true,
      axisLabel: { formatter: compareAxisFormatter(data.axis_unit) },
    },
    series: data.series.map((item) => ({
      name: item.name,
      type: "line",
      data: item.data,
      smooth: true,
      symbolSize: 8,
      lineStyle: { width: 3 },
    })),
  };
}

function showComparisonMessage(container, message) {
  container.innerHTML = `<div class="muted" style="padding:24px;">${message}</div>`;
}

async function loadComparisonChart() {
  const form = document.getElementById("comparison-filter");
  const container = document.getElementById("comparison-chart");
  if (!form || !container || !window.echarts) {
    return;
  }

  const params = new URLSearchParams(new FormData(form));
  try {
    const response = await fetch(`${form.dataset.endpoint}?${params.toString()}`);
    const payload = await response.json();
    if (!response.ok || !payload.success) {
      showComparisonMessage(container, payload.message || "对比图表加载失败。");
      return;
    }
    const chart = echarts.init(container);
    chart.setOption(createComparisonOption(payload.data));
    window.addEventListener("resize", () => chart.resize());
  } catch (error) {
    showComparisonMessage(container, "对比图表加载失败，请稍后重试。");
  }
}

document.addEventListener("DOMContentLoaded", loadComparisonChart);
