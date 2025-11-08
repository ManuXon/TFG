// This file is auto-loaded by Dash
if (!window.dash_clientside) { window.dash_clientside = {}; }

window.dash_clientside.survey = {
  open: function(n_clicks) {
    if (!n_clicks) { return window.dash_clientside.no_update; }
    window.dispatchEvent(new CustomEvent('mapai:openSurvey'));
    return 0; // store payload unused
  }
};
