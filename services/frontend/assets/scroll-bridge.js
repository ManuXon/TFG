(function () {
  function scrollToMap() {
    const target = document.getElementById("mapbox-section");
    if (!target) {
      console.warn("[scroll-bridge] #mapbox-section not found");
      return;
    }

    // Where is the element right now on the page?
    const absoluteTop = target.getBoundingClientRect().top + window.scrollY;

    // 1. header offset so it doesn't hide under sticky stuff
    const headerOffset = 80; // px

    // 2. extra downward bump so the map ends up closer to center
    //    ~20% of viewport height feels like "scroll one more notch"
    const extraBump = window.innerHeight * 0.12;

    // Final Y position we want to land on
    const finalTop = absoluteTop - headerOffset + extraBump;

    // Smooth scroll there
    window.scrollTo({
      top: finalTop,
      left: 0,
      behavior: "smooth",
    });
  }

  function wireButton() {
    const btn = document.getElementById("lets-explore-btn");
    if (!btn) {
      // button may not be in DOM yet if Dash hasn't rendered, retry soon
      setTimeout(wireButton, 200);
      return;
    }

    if (btn.__scrollAttached) return; // don't double-bind
    btn.__scrollAttached = true;

    btn.addEventListener("click", function () {
      scrollToMap();
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", wireButton);
  } else {
    wireButton();
  }
})();
