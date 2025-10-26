(function () {
  // Smooth scroll helper
  function scrollToSelector(el) {
    if (!el) return;
    try {
      el.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    } catch (err) {
      const top = el.getBoundingClientRect().top + window.scrollY - 40;
      window.scrollTo(0, top);
    }
  }

  // Given the <ub-faculty-selector> element, get the inner React root div
  // where FacultySelector attached the event listener (id="faculty-visualization")
  function getFacultySelectorInnerRoot(selectorEl) {
    if (!selectorEl) return null;

    // case 1: react-to-webcomponent rendered into a shadow root
    if (selectorEl.shadowRoot) {
      const innerInShadow = selectorEl.shadowRoot.querySelector(
        "#faculty-visualization"
      );
      if (innerInShadow) return innerInShadow;
    }

    // case 2: no shadow DOM, React rendered directly into light DOM
    const innerInLight = selectorEl.querySelector("#faculty-visualization");
    if (innerInLight) return innerInLight;

    return null;
  }

  // Listen for MapboxDashboard's message
  window.addEventListener("message", function (event) {
    const msg = event.data;
    if (!msg || msg.type !== "ub:navigate-to-faculty") return;

    const facultyName = msg.facultyName;
    if (!facultyName) return;

    // Find the custom element hosting the selector / flow
    const selectorEl = document.querySelector("ub-faculty-selector");
    if (!selectorEl) {
      console.warn("[nav-bridge] <ub-faculty-selector> not found on page");
      return;
    }

    // Scroll to it so user sees the visualization area
    scrollToSelector(selectorEl);

    // Find the actual div inside React that we attached the listener to
    const innerRoot = getFacultySelectorInnerRoot(selectorEl);
    if (!innerRoot) {
      console.warn(
        "[nav-bridge] could not locate #faculty-visualization inside <ub-faculty-selector>"
      );
      return;
    }

    // Build the event that FacultySelector is listening for
    const ev = new CustomEvent("external-select-faculty", {
      detail: { facultyName },
      bubbles: true,
      composed: true,
    });

    // Fire it slightly after scroll so the transition feels natural
    setTimeout(() => {
      innerRoot.dispatchEvent(ev);
    }, 300);
  });
})();
