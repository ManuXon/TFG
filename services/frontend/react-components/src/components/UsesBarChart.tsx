// UsesBarChart.tsx
import React, { useState, useEffect } from "react";
import Plot from "react-plotly.js";
import { useWindowWidth } from "./useWindowWidthHook"; // we'll define this tiny hook

const UsesBarChart = ({ facultyName }: { facultyName: string }) => {
  const [selected, setSelected] = useState<string[]>(["gender", "experience"]);
  const [data, setData] = useState<any | null>(null);

  const winW = useWindowWidth();
  const lt684 = winW < 684;

  // responsive font sizes
  const barTitleSize = lt684 ? 15 : 18;
  const barLegendSize = lt684 ? 11 : 14;

  const toggleSelection = (value: string) => {
    setSelected((prev) => {
      if (prev.includes(value)) return prev.filter((v) => v !== value);
      if (prev.length < 2) return [...prev, value];
      return [prev[0], value];
    });
  };

  useEffect(() => {
    if (selected.length === 0) return;
    const [d1, d2] = selected;
    const url = d2
      ? `http://localhost:8000/api/faculty/${facultyName}/uses-distribution?demographic1=${d1}&demographic2=${d2}`
      : `http://localhost:8000/api/faculty/${facultyName}/uses-distribution?demographic1=${d1}`;

    fetch(url)
      .then((res) => res.json())
      .then(setData)
      .catch((err) =>
        console.error("Error fetching uses data:", err)
      );
  }, [facultyName, selected]);

  if (!data) {
    return <p className="text-gray-500">Loading AI uses data...</p>;
  }

  // --- SINGLE DEMOGRAPHIC VIEW ---
  if (data.mode === "single") {
    return (
      <div>
        <div className="flex justify-center gap-6 mb-4">
          {["gender", "experience", "profile"].map((opt) => (
            <label
              key={opt}
              className="flex items-center space-x-2 text-slate-700"
            >
              <input
                type="checkbox"
                checked={selected.includes(opt)}
                onChange={() => toggleSelection(opt)}
                className="accent-purple-700 w-4 h-4 cursor-pointer"
              />
              <span className="capitalize cursor-pointer">{opt}</span>
            </label>
          ))}
        </div>

        <Plot
          data={[
            {
              x: data.categories,
              y: data.values,
              type: "bar",
              marker: { color: "#6b21a8", opacity: 0.9 },
              text: data.values.map((v: number) => v.toFixed(1)),
              textposition: "auto",
              hovertemplate:
                `<b>%{x}</b><br>Avg Usage Level: <b>%{y:.2f}</b><extra></extra>`,
            },
          ]}
          layout={{
            title: {
              text: `AI Usage Level by ${data.demographics[0]}`,
              font: { size: barTitleSize, color: "#334155" },
              y: 0.95,
            },
            xaxis: {
              title: `${data.demographics[0]} categories`,
              tickfont: { size: 10 },
            },
            yaxis: {
              title: {
                text: "Avg Usage Level (1–4)",
                tickfont: { size: 10 },
              },
              range: [0, 4],
            },
            margin: { t: 80, l: 70, r: 20, b: 80 },
            paper_bgcolor: "rgba(0,0,0,0)",
            plot_bgcolor: "rgba(0,0,0,0)",
          }}
          style={{ width: "100%", height: "100%" }}
          config={{ displayModeBar: false }}
        />
      </div>
    );
  }

  // --- TWO DEMOGRAPHICS VIEW ---
  // same contract as KnowledgeBarChart
  const mainGroups = Array.from(new Set(data.data.map((d: any) => d.main))) as string[];
  const subGroups = Array.from(new Set(data.data.map((d: any) => d.sub))) as string[];
  const mainAvgMap: Record<string, number> = {};
  data.data.forEach((r: any) => {
    if (mainAvgMap[r.main] == null) mainAvgMap[r.main] = r.main_avg;
  });

  const purplePalette = [
    "#4c1d95",
    "#5b21b6",
    "#6b21a8",
    "#7e22ce",
    "#9333ea",
    "#a855f7",
    "#c084fc",
  ];

  const traces = subGroups.map((sub, idx) => {
    const yValues = mainGroups.map((m) => {
      const rec = data.data.find(
        (d: any) => d.main === m && d.sub === sub
      );
      return rec ? rec.contribution : 0;
    });

    const subAvg = mainGroups.map(
      (m) =>
        data.data.find(
          (d: any) => d.main === m && d.sub === sub
        )?.mean_sub ?? 0
    );
    const counts = mainGroups.map(
      (m) =>
        data.data.find(
          (d: any) => d.main === m && d.sub === sub
        )?.n_sub ?? 0
    );
    const percentages = mainGroups.map((m, i) => {
      const mainAvg = mainAvgMap[m] || 0;
      const val = yValues[i] || 0;
      return mainAvg > 0
        ? ((val / mainAvg) * 100).toFixed(1)
        : "0.0";
    });

    return {
      x: mainGroups,
      y: yValues,
      name: sub,
      type: "bar",
      marker: {
        color: purplePalette[idx % purplePalette.length],
      },
      customdata: yValues.map((_, i) => [
        subAvg[i],
        counts[i],
        percentages[i],
      ]),
      hovertemplate:
        `<b>%{x}</b><br>${data.demographics[1]}: <b>${sub}</b><br>` +
        `Sub avg: %{customdata[0]:.2f} (n=%{customdata[1]})<br>` +
        `Contribution to main avg: <b>%{y:.2f}</b><br>` +
        `Share: <b>%{customdata[2]}%</b><extra></extra>`,
    };
  });

  return (
    <div>
      <div className="flex justify-center gap-6 mb-4">
        {["gender", "experience", "profile"].map((opt) => (
          <label
            key={opt}
            className="flex items-center space-x-2 text-slate-700"
          >
            <input
              type="checkbox"
              checked={selected.includes(opt)}
              onChange={() => toggleSelection(opt)}
              className="accent-purple-700 w-4 h-4 cursor-pointer"
            />
            <span className="capitalize cursor-pointer">{opt}</span>
          </label>
        ))}
      </div>

      <Plot
        data={traces}
        layout={{
          barmode: "stack",
          title: {
            text: `AI Usage Level by: ${data.demographics[0]} × ${data.demographics[1]}`,
            font: { size: barTitleSize, color: "#334155" },
            y: 0.95,
          },
          xaxis: { title: data.demographics[0], tickfont: { size: 10 } },
          yaxis: {
            title: { text: "Avg Usage Level (1–4)" },
            tickfont: { size: 10 },
            range: [0, 4],
          },
          legend: {
            orientation: "h",
            y: -0.25,
            x: 0.071,
            font: { size: barLegendSize },
            bordercolor: "#e2e8f0",
            borderwidth: 1,
          },
          margin: { t: 80, l: 70, r: 20, b: 80 },
          paper_bgcolor: "rgba(0,0,0,0)",
          plot_bgcolor: "rgba(0,0,0,0)",
          hoverlabel: {
            bgcolor: "rgba(255,255,255,0.95)",
            bordercolor: "#cbd5e1",
            font: { color: "#1e293b", size: 12 },
            align: "left",
          },
        }}
        style={{ width: "100%", height: "100%" }}
        config={{ displayModeBar: false }}
      />
    </div>
  );
};

export default UsesBarChart;
