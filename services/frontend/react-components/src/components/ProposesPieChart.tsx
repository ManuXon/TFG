// ProposesPieChart.tsx
import React, { useState, useEffect } from "react";
import Plot from "react-plotly.js";
import { useWindowWidth } from "./useWindowWidthHook";

const ProposesPieChart = ({ facultyName }: { facultyName: string }) => {
  const [data, setData] = useState<{ categories: string[]; values: number[] } | null>(null);

  const winW = useWindowWidth();
  const lt670 = winW < 670;
  const lt600 = winW < 600;
  const pieTitleSize = lt600 ? 14 : lt670 ? 15 : 18;

  useEffect(() => {
    fetch(`http://localhost:8000/api/faculty/${facultyName}/proposes-distribution`)
      .then((res) => res.json())
      .then(setData)
      .catch((err) => console.error("Error fetching proposes-to-students data:", err));
  }, [facultyName]);

  if (!data) return <p className="text-gray-500">Loading proposal data...</p>;

  // Canonical order from backend
  const ORDER = ["Never", "Sometimes", "Often", "Very often"];

  // Stable color per label (Uses = purple palette)
  const COLOR_BY_LABEL: Record<string, string> = {
    "Never": "#4c1d95",
    "Sometimes": "#6b21a8",
    "Often": "#9333ea",
    "Very often": "#c084fc",
  };

  // Zip, filter zeros, and keep ORDER
  const tuples = data.categories.map((label, i) => ({ label, value: data.values[i] ?? 0 }));
  const filtered = tuples
    .filter((t) => (t.value ?? 0) > 0)
    .sort((a, b) => ORDER.indexOf(a.label) - ORDER.indexOf(b.label));

  const labels = filtered.map((t) => t.label);
  const values = filtered.map((t) => t.value);
  const colors = labels.map((l) => COLOR_BY_LABEL[l] ?? "#7e22ce");

  const total = values.reduce((s, v) => s + (v || 0), 0);
  if (!filtered.length || total === 0) {
    return (
      <div className="h-[470px] flex items-center justify-center text-slate-400">
        No responses for this question in this faculty.
      </div>
    );
  }

  // Optional: short text INSIDE slices; legend/hover still show full label
  const SHORT_LABEL: Record<string, string> = {
    "Never": "Never",
    "Sometimes": "Sometimes",
    "Often": "Often",
    "Very often": "Very",
  };
  const sliceText = labels.map((l) => SHORT_LABEL[l] ?? l);

  return (
    <Plot
      data={[
        {
          labels,               // legend only shows these (non-zero)
          values,
          type: "pie",
          sort: false,          // keep canonical order
          text: sliceText,      // compact text inside slices
          textinfo: "text+percent",
          textposition: "inside",
          hovertemplate:
            `<b>%{label}</b><br>Responses: <b>%{value}</b><br>Share: <b>%{percent}</b><extra></extra>`,
          marker: { colors, line: { color: "#ffffff", width: 2 } },
        },
      ]}
      layout={{
        title: {
          text: "Do they propose AI use to students?",
          font: { size: pieTitleSize, color: "#334155" },
          xref: "paper",
          x: 0.0,
          y: 1.05,
        },
        showlegend: true, // legend now only lists used labels
        legend: {
          orientation: "h",
          x: 0.05,
          font: { color: "#334155", size: 14 },
          bgcolor: "rgba(255,255,255,0.7)",
          bordercolor: "#e2e8f0",
          borderwidth: 1,
        },
        uniformtext: { mode: "hide", minsize: 10 }, // avoid overflow in slices
        margin: { t: 90, l: 20, r: 20, b: 0 },
        paper_bgcolor: "rgba(0,0,0,0)",
        plot_bgcolor: "rgba(0,0,0,0)",
        hoverlabel: {
          bgcolor: "rgba(255,255,255,0.95)",
          bordercolor: "#cbd5e1",
          font: { color: "#1e293b", size: 12 },
          align: "left",
        },
      }}
      style={{ width: "100%", height: "470px" }}
      config={{ displayModeBar: false }}
    />
  );
};

export default ProposesPieChart;
