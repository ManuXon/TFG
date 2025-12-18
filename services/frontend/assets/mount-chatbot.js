// assets/mount-chatbot.js
(function () {
  // Only mount once
  if (document.querySelector("ub-chatbot")) return;

  const el = document.createElement("ub-chatbot");
  // it’s a floating fixed widget, so we can just append to body
  document.body.appendChild(el);
})();
