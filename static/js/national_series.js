function formatNationalPopulation(value) {
  const number = Number(value || 0);
  if (Math.abs(number) >= 100000000) {
    return `${(number / 100000000).toFixed(2)} 亿人`;
  }
  if (Math.abs(number) >= 10000) {
    return `${(number / 10000).toFixed(0)} 万人`;
  }
  return number.toLocaleString("zh-CN");
}

function formatNationalMetric(value, unit) {
  if (value === null || value === undefined) {
    return "-";
  }
  if (unit === "person") {
    return formatNationalPopulation(value);
  }
  if (unit === "permille") {
    return `${Number(value).toFixed(2)}‰`;
  }
  if (unit === "%") {
    return `${Number(value).toFixed(2)}%`;
  }
  return Number(value).toLocaleString("zh-CN");
}

function buildNationalAxisFormatter(unit) {
  return function (value) {
    if (unit === "person") {
      return formatNationalPopulation(value);
    }
    if (unit === "permille") {
      return `${Number(value).toFixed(1)}‰`;
    }
    if (unit === "%") {
      return `${Number(value).toFixed(1)}%`;
    }
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
      formatter: function (params) {
        const point = params[0];
        return `${point.axisValue} 年<br/>${data.metricLabel}：${formatNationalMetric(point.value, data.axisUnit)}`;
      },
    },
    grid: { left: 84, right: 34, top: 58, bottom: 54 },
    xAxis: {
      type: "category",
      data: data.xAxis,
      axisLabel: { interval: 5 },
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

async function loadNationalTrend(form) {
  const container = document.getElementById("national-trend-chart");
  if (!container || !window.echarts) {
    return;
  }
  renderNationalMessage(container, "正在加载全国长序列图表...");
  const params = new URLSearchParams(new FormData(form));
  try {
    const response = await fetch(`${form.dataset.endpoint}?${params.toString()}`);
    const payload = await response.json();
    if (!response.ok || !payload.success) {
      renderNationalMessage(container, payload.message || "图表加载失败。");
      return;
    }
    container.innerHTML = "";
    nationalTrendChart = echarts.getInstanceByDom(container) || echarts.init(container);
    nationalTrendChart.setOption(createNationalTrendOption(payload.data), true);
    if (!nationalTrendResizeBound) {
      window.addEventListener("resize", () => {
        if (nationalTrendChart) {
          nationalTrendChart.resize();
        }
      });
      nationalTrendResizeBound = true;
    }
  } catch (error) {
    renderNationalMessage(container, "图表加载失败，请稍后重试。");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("[data-national-trend-form]");
  if (!form) {
    return;
  }
  form.querySelectorAll("select").forEach((field) => {
    field.addEventListener("change", () => loadNationalTrend(form));
  });
  loadNationalTrend(form);
});
