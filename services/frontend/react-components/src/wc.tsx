// assets/react/wc.tsx
import React from "react";
import ReactDOM from "react-dom/client";
import reactToWebComponent from "react-to-webcomponent";

import FacultySelector from "./components/FacultySelector";
import FacultyVisualization from "./components/FacultyVisualization";
import MapboxDashboard from "./components/MapboxDashboard";
import SurveyOverviewWC from "./components/SurveyOverviewWC";

import "./index.css";
import "mapbox-gl/dist/mapbox-gl.css";

// Existing
const FacultyFlowWC = () => {
  const [selected, setSelected] = React.useState<{ name: string; color: string } | null>(null);
  return !selected ? (
    <FacultySelector onFacultySelect={setSelected} />
  ) : (
    <FacultyVisualization faculty={selected} onBack={() => setSelected(null)} />
  );
};

const WcFacultyFlow = reactToWebComponent(FacultyFlowWC, React, ReactDOM);
const WcMapboxDashboard = reactToWebComponent(MapboxDashboard, React, ReactDOM);

// NEW: SurveyOverview as a standalone custom element
const WcSurveyOverview = reactToWebComponent(SurveyOverviewWC, React, ReactDOM);

// Register
if (!customElements.get("ub-faculty-selector")) {
  customElements.define("ub-faculty-selector", WcFacultyFlow);
}
if (!customElements.get("ub-mapbox-dashboard")) {
  customElements.define("ub-mapbox-dashboard", WcMapboxDashboard);
}
if (!customElements.get("ub-survey-overview")) {
  customElements.define("ub-survey-overview", WcSurveyOverview);
}