function formatMapValue(value, metric) {
  if (value === null || value === undefined) return "-";
  if (metric === "total_population") {
    return `${(Number(value) / 10000).toLocaleString("zh-CN", { maximumFractionDigits: 0 })} 万人`;
  }
  return `${Number(value).toFixed(2)}%`;
}

async function loadChinaMap() {
  const container = document.getElementById("china-map");
  if (!container || !window.echarts) return;

  const metricSelect = document.querySelector("[data-map-metric]");
  const yearSelect = document.querySelector("[data-map-year]");
  const detail = document.querySelector("[data-map-detail]");
  const chart = echarts.init(container);

  try {
    const geoResponse = await fetch("/static/js/china.json");
    const chinaGeoJson = await geoResponse.json();
    echarts.registerMap("china", chinaGeoJson);
  } catch (error) {
    container.innerHTML = '<div class="empty-state">中国地图资源加载失败。</div>';
    return;
  }

  async function render() {
    const params = new URLSearchParams({
      metric: metricSelect?.value || "total_population",
      year: yearSelect?.value || "2024",
    });

    const response = await fetch(`${container.dataset.endpoint}?${params.toString()}`);
    const payload = await response.json();
    if (!response.ok || !payload.success) {
      container.innerHTML = `<div class="empty-state">${payload.message || "地图加载失败。"}</div>`;
      return;
    }

    const values = payload.data.items
      .map((item) => item.value)
      .filter((value) => value !== null && value !== undefined);
    const min = values.length ? Math.min(...values) : 0;
    const max = values.length ? Math.max(...values) : 1;

    chart.setOption({
      tooltip: {
        trigger: "item",
        formatter: (item) => {
          const data = item.data || {};
          return `${item.name}<br/>${payload.data.metricLabel}：${formatMapValue(data.value, payload.data.metric)}<br/>出生率：${formatMapValue(data.birthRate, "birth_rate")}<br/>老龄化率：${formatMapValue(data.agingRate, "aging_rate")}`;
        },
      },
      visualMap: {
        min,
        max,
        left: 10,
        bottom: 12,
        text: ["高", "低"],
        calculable: true,
        inRange: { color: ["#dff1f4", "#78b8c2", "#176c7d"] },
      },
      series: [{
        name: payload.data.metricLabel,
        type: "map",
        map: "china",
        roam: true,
        selectedMode: "single",
        emphasis: {
          label: { show: true, color: "#102533", fontWeight: 800 },
          itemStyle: { areaColor: "#f7b955" },
        },
        select: { itemStyle: { areaColor: "#f7b955" } },
        label: { show: true, fontSize: 10, color: "#355564" },
        itemStyle: { borderColor: "#ffffff", borderWidth: 1.4 },
        data: payload.data.items,
      }],
    }, true);
  }

  chart.on("mouseover", (params) => {
    if (!detail || !params.data) return;
    detail.innerHTML = `<strong>${params.name}</strong><span>总人口 ${formatMapValue(params.data.population, "total_population")}，出生率 ${formatMapValue(params.data.birthRate, "birth_rate")}，老龄化率 ${formatMapValue(params.data.agingRate, "aging_rate")}</span>`;
  });

  metricSelect?.addEventListener("change", render);
  yearSelect?.addEventListener("change", render);
  window.addEventListener("resize", () => chart.resize());
  await render();
}

document.addEventListener("DOMContentLoaded", loadChinaMap);
