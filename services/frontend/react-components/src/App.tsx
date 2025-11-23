import React, { useState } from "react";
import "mapbox-gl/dist/mapbox-gl.css";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import FacultySelector from "./components/FacultySelector";
import FacultyVisualization from "./components/FacultyVisualization";
import MapboxDashboard from "./components/MapboxDashboard";

interface Faculty {
  name: string;
  color: string;
}

function FacultyFlow() {
  const [selectedFaculty, setSelectedFaculty] = useState<Faculty | null>(null);

  return !selectedFaculty ? (
    <FacultySelector onFacultySelect={setSelectedFaculty} />
  ) : (
    <FacultyVisualization faculty={selectedFaculty} onBack={() => setSelectedFaculty(null)} />
  );
}

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<FacultyFlow />} />
        <Route path="/map" element={<MapboxDashboard />} />
      </Routes>
    </Router>
  );
}
