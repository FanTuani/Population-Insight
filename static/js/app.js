document.addEventListener("DOMContentLoaded", () => {
  const body = document.body;
  const mobileBreakpoint = window.matchMedia("(max-width: 1180px)");
  const sidebarToggles = document.querySelectorAll("[data-sidebar-toggle]");
  const sidebarCollapse = document.querySelector("[data-sidebar-collapse]");
  const sidebarBackdrop = document.querySelector("[data-sidebar-backdrop]");

  const syncSidebarBackdrop = () => {
    if (!sidebarBackdrop) {
      return;
    }

    const shouldShow = mobileBreakpoint.matches && body.classList.contains("sidebar-open");
    sidebarBackdrop.hidden = !shouldShow;
  };

  const closeMobileSidebar = () => {
    body.classList.remove("sidebar-open");
    syncSidebarBackdrop();
  };

  sidebarToggles.forEach((button) => {
    button.addEventListener("click", () => {
      body.classList.toggle("sidebar-open");
      syncSidebarBackdrop();
    });
  });

  if (sidebarCollapse) {
    sidebarCollapse.addEventListener("click", () => {
      body.classList.toggle("sidebar-collapsed");
    });
  }

  document.querySelectorAll("[data-nav-group]").forEach((group) => {
    const toggle = group.querySelector("[data-nav-group-toggle]");
    if (!toggle) {
      return;
    }

    toggle.addEventListener("click", () => {
      const willOpen = !group.classList.contains("is-open");

      document.querySelectorAll("[data-nav-group]").forEach((item) => {
        if (item !== group) {
          item.classList.remove("is-open");
          item
            .querySelector("[data-nav-group-toggle]")
            ?.setAttribute("aria-expanded", "false");
        }
      });

      group.classList.toggle("is-open", willOpen);
      toggle.setAttribute("aria-expanded", String(willOpen));
    });
  });

  if (sidebarBackdrop) {
    sidebarBackdrop.addEventListener("click", closeMobileSidebar);
  }

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeMobileSidebar();
    }
  });

  mobileBreakpoint.addEventListener("change", () => {
    if (!mobileBreakpoint.matches) {
      body.classList.remove("sidebar-open");
    }
    syncSidebarBackdrop();
  });

  syncSidebarBackdrop();

  document.querySelectorAll("[data-table-search]").forEach((input) => {
    const table = document.querySelector(input.dataset.tableSearch);
    if (!table) {
      return;
    }

    input.addEventListener("input", () => {
      const query = input.value.trim().toLowerCase();
      table.querySelectorAll("tbody tr").forEach((row) => {
        row.hidden = query && !row.textContent.toLowerCase().includes(query);
      });
    });
  });

  document.querySelectorAll("[data-password-toggle]").forEach((button) => {
    const field = button
      .closest(".password-shell")
      ?.querySelector("[data-password-input]");

    if (!field) {
      return;
    }

    button.addEventListener("click", () => {
      const shouldShow = field.type === "password";
      field.type = shouldShow ? "text" : "password";
      button.classList.toggle("is-visible", shouldShow);
      button.setAttribute("aria-label", shouldShow ? "隐藏密码" : "显示密码");
    });
  });

  const filterToggle = document.querySelector("[data-filter-toggle]");
  const filterPanel = document.querySelector("[data-filter-panel]");
  if (filterToggle && filterPanel) {
    filterToggle.addEventListener("click", () => {
      const collapsed = filterPanel.classList.toggle("is-collapsed");
      filterToggle.setAttribute("aria-expanded", String(!collapsed));
      filterToggle.textContent = collapsed ? "展开筛选条件" : "筛选条件";
    });
  }
});
