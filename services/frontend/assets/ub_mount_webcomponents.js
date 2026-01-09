// assets/ub_mount_webcomponents.js
(function () {
  const OBSERVED = new WeakSet();

  function ensureResizeObserver(host) {
    if (typeof ResizeObserver === "undefined") return;
    if (OBSERVED.has(host)) return;
    OBSERVED.add(host);

    const ro = new ResizeObserver(() => {
      // Mapbox/Plotly often need a resize tick after DOM changes
      window.dispatchEvent(new Event("resize"));
    });
    ro.observe(host);
  }

  function mountOnce(hostId, tagName) {
    const host = document.getElementById(hostId);
    if (!host) return false;

    // already mounted
    if (host.querySelector(tagName)) return true;

    const el = document.createElement(tagName);
    el.style.display = "block";
    el.style.width = "100%";
    host.appendChild(el);

    ensureResizeObserver(host);
    return true;
  }

  function mountAll() {
    const a = mountOnce("ub-faculty-selector-host", "ub-faculty-selector");
    const b = mountOnce("ub-mapbox-dashboard-host", "ub-mapbox-dashboard");
    const c = mountOnce("ub-survey-overview-host", "ub-survey-overview");
    const d = mountOnce("ub-auth-modal-host", "ub-auth-modal");

  return a && b && c && d;
  }

  // Retry a few times because Dash can insert the layout after scripts run
  function retryMounts(maxMs = 5000, intervalMs = 100) {
    const start = Date.now();
    const tick = () => {
      if (mountAll()) return;
      if (Date.now() - start >= maxMs) return;
      setTimeout(tick, intervalMs);
    };
    tick();
  }

  // Watch for Dash inserting/replacing nodes
  function observeDomForHosts() {
    if (typeof MutationObserver === "undefined") return;

    const mo = new MutationObserver(() => {
      // cheap + safe; mountOnce prevents duplicates
      mountAll();
    });

    mo.observe(document.documentElement, {
      childList: true,
      subtree: true,
    });
  }

  // Kick everything off
  function init() {
    mountAll();
    retryMounts();
    observeDomForHosts();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  // Extra hooks (harmless)
  window.addEventListener("load", mountAll);
  document.addEventListener("dash:rendered", mountAll);
})();
