(function () {
  function scrollToMap() {
    const target = document.getElementById("mapbox-section");
    if (!target) {
      console.warn("[scroll-bridge] #mapbox-section not found");
      return;
    }

    try {
      target.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    } catch (err) {
      // fallback for older browsers
      const top = target.getBoundingClientRect().top + window.scrollY - 40;
      window.scrollTo({ top: top, left: 0, behavior: "smooth" });
    }
  }

  function wireButton() {
    const btn = document.getElementById("lets-explore-btn");
    if (!btn) {
      // button not in DOM yet; we'll retry shortly
      setTimeout(wireButton, 200);
      return;
    }

    // only attach once
    if (btn.__scrollAttached) return;
    btn.__scrollAttached = true;

    btn.addEventListener("click", function () {
      scrollToMap();
    });
  }

  // run after DOM is interactive
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", wireButton);
  } else {
    wireButton();
  }
})();
