import React, { useEffect, useState } from "react";
import Plot from "react-plotly.js";

type Props = { facultyName: string };

const UsesStudentsAdequacyPieChart: React.FC<Props> = ({ facultyName }) => {
  const [data, setData] = useState<{ categories: string[]; values: number[] } | null>(null);
  const [winW, setWinW] = useState<number>(typeof window !== "undefined" ? window.innerWidth : 1024);

  useEffect(() => {
    const onResize = () => setWinW(window.innerWidth);
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  useEffect(() => {
    fetch(
      `http://localhost:8000/api/faculty/${encodeURIComponent(
        facultyName
      )}/students-uses-adequacy-distribution`,
      { cache: "no-store" }
    )
      .then((r) => r.json())
      .then(setData)
      .catch(() => setData({ categories: [], values: [] }));
  }, [facultyName]);

  if (!data) return <p className="text-gray-500">Loading adequacy data...</p>;

  const lt670 = winW < 670;
  const lt600 = winW < 600;
  const pieTitleSize = lt600 ? 12 : lt670 ? 13 : 16;

  // Canonical order to keep bins consistent
  const ORDER = [
    "Unsure",
    "No misuse",
    "Appropriate use",
    "Occasional misuse",
    "Frequent misuse",
  ];

  // Stable purple palette per label (consistent even when some are missing)
  const COLOR_BY_LABEL: Record<string, string> = {
    "Unsure":            "#ddd6fe",
    "No misuse":         "#a78bfa",
    "Appropriate use":   "#7c3aed",
    "Occasional misuse": "#6b21a8",
    "Frequent misuse":   "#4c1d95",
  };

  // Zip → filter zeros → sort by ORDER
  const tuples = (data.categories || []).map((label, i) => ({
    label,
    value: data.values?.[i] ?? 0,
  }));
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

    // After you compute `labels`, `values`, `colors`, add this mapping:
  const SHORT_LABEL: Record<string, string> = {
    "Unsure": "Unsure",
    "No misuse": "None",
    "Appropriate use": "Appropriate",
    "Occasional misuse": "Occasional",
    "Frequent misuse": "Frequent",
  };

  // Text shown INSIDE slices (one word each)
  const sliceText = labels.map((l) => SHORT_LABEL[l] ?? l);

  return (
    <Plot
      data={[
        {
          labels,           // full labels → legend + hover
          values,
          type: "pie",
          sort: false,
          text: sliceText,  // short one-word labels INSIDE slices
          textinfo: "text+percent",
          textposition: "inside",
          insidetextorientation: "auto",
          hovertemplate:
            `<b>%{label}</b><br>Responses: <b>%{value}</b><br>Share: <b>%{percent}</b><extra></extra>`,
          marker: {
            colors,
            line: { color: "#ffffff", width: 2 },
          },
          textfont: { size: 12 }, // keep it compact
        },
      ]}
      layout={{
        title: {
          text: "What's the perception of students AI misuse",
          font: { size: pieTitleSize, color: "#334155" },
          xref: "paper",
          x: -0.11,
          y: 1.05,
        },
        showlegend: true,
        legend: {
          orientation: "h",
          font: { color: "#334155", size: 14 },
          bgcolor: "rgba(255,255,255,0.7)",
          bordercolor: "#e2e8f0",
          borderwidth: 1,
        },
        // Hide slice text if it would overflow
        uniformtext: { mode: "hide", minsize: 10 },
        margin: { t: 90, l: 20, r: 20, b: 5 },
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

export default UsesStudentsAdequacyPieChart;
