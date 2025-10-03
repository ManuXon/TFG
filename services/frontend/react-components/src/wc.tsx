// src/wc.tsx
import React from "react";
import ReactDOM from "react-dom/client";
import FacultySelector from "./components/FacultySelector";
import reactToWebComponent from "react-to-webcomponent";
import "./index.css"; // Importa Tailwind para que quede empaquetado

// Envuelve el componente React como Web Component
const Elem = reactToWebComponent(FacultySelector, React, ReactDOM);

// Registra el custom element (nombre en kebab-case)
if (!customElements.get("ub-faculty-selector")) {
  customElements.define("ub-faculty-selector", Elem);
}
