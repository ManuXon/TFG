console.log("🔎 iframe-resize.js loaded");

window.addEventListener("message", function(e) {
  console.log("📩 message received:", e.data);
  if (!e || !e.data || e.data.source !== "faculty_selector_height") return;
  var iframe = document.getElementById("faculty-selector-iframe");
  console.log("🎯 Found iframe?", iframe);
  if (iframe) {
    iframe.style.height = e.data.height + "px";
  }
}, false);
