import React from "react";
import ReactDOM from "react-dom/client";
import reactToWebComponent from "react-to-webcomponent";
import FacultySelector from "./components/FacultySelector";
import FacultyVisualization from "./components/FacultyVisualization";
import MapboxDashboard from "./components/MapboxDashboard";
import "./index.css";
import "mapbox-gl/dist/mapbox-gl.css";


// Faculty flow: selector → visualization
const FacultyFlowWC = () => {
  const [selected, setSelected] = React.useState<{ name: string; color: string } | null>(null);
  return !selected ? (
    <FacultySelector onFacultySelect={setSelected} />
  ) : (
    <FacultyVisualization faculty={selected} onBack={() => setSelected(null)} />
  );
};

// Convert to custom elements
const WcFacultyFlow = reactToWebComponent(FacultyFlowWC, React, ReactDOM);
const WcMapboxDashboard = reactToWebComponent(MapboxDashboard, React, ReactDOM);

// Register them globally — this runs automatically when Dash serves assets/react/ub-components.iife.js
if (!customElements.get("ub-faculty-selector")) {
  customElements.define("ub-faculty-selector", WcFacultyFlow);
}
if (!customElements.get("ub-mapbox-dashboard")) {
  customElements.define("ub-mapbox-dashboard", WcMapboxDashboard);
}