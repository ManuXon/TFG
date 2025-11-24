// Auto-loaded by Dash
if (!window.dash_clientside) window.dash_clientside = {};

window.dash_clientside.auth = {
  open: function(n_clicks_analyst, n_clicks_signin) {
    const clicks = (n_clicks_analyst || 0) + (n_clicks_signin || 0);
    if (!clicks) return window.dash_clientside.no_update;
    window.dispatchEvent(new CustomEvent("mapai:openAuth"));
    return 0;
  }
};
