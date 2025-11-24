// Overwritten by entrypoint in prod if you want. Default works locally:
// services/frontend/assets/config.js
window.__API_BASE__ =
  (location.hostname === 'localhost' || location.hostname === '127.0.0.1')
    ? 'http://localhost:8000'            // dev
    : 'http://localhost:8000';       // prod

