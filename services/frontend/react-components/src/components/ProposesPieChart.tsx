// ProposesPieChart.tsx
import React, { useState, useEffect } from "react";
import Plot from "react-plotly.js";
import { useWindowWidth } from "./useWindowWidthHook";

const ProposesPieChart = ({ facultyName }: { facultyName: string }) => {
  const [data, setData] = useState<{
    categories: string[];
    values: number[];
  } | null>(null);

  const winW = useWindowWidth();
  const lt670 = winW < 670;
  const lt600 = winW < 600;

  const pieTitleSize = lt600 ? 14 : lt670 ? 15 : 18;

  useEffect(() => {
    fetch(
      `http://localhost:8000/api/faculty/${facultyName}/proposes-distribution`
    )
      .then((res) => res.json())
      .then(setData)
      .catch((err) =>
        console.error("Error fetching proposes-to-students data:", err)
      );
  }, [facultyName]);

  if (!data) {
    return <p className="text-gray-500">Loading proposal data...</p>;
  }

  const labels = data.categories;
  const values = data.values;
  const total = values.reduce((acc, v) => acc + v, 0);

  // Build custom text so slices with 0 don't render anything on the pie.
  // For non-zero slices we inline "Label 12.3%" etc.
  const text = labels.map((lbl, idx) => {
    const v = values[idx];
    if (!v || v === 0 || total === 0) return "";
    return `${lbl}`;
  });

  // Purple-ish range
  const pieColors = [
    "#4c1d95", // darkest
    "#6b21a8",
    "#9333ea",
    "#c084fc", // lightest
  ];

  return (
    <Plot
      data={[
        {
          labels,
          values,
          text,
          textinfo: "text", // <- we control the text fully now
          type: "pie",
          hovertemplate:
            `<b>%{label}</b><br>Responses: <b>%{value}</b>` +
            `<br>Share: <b>%{percent}</b><extra></extra>`,
          marker: {
            colors: pieColors,
            line: { color: "#ffffff", width: 2 },
          },
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
        showlegend: true,
        legend: {
          orientation: "h",
          x: 0.15,
          font: { color: "#334155", size: 14 },
          bgcolor: "rgba(255,255,255,0.7)",
          bordercolor: "#e2e8f0",
          borderwidth: 1,
        },
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
