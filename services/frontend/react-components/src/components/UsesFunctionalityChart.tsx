import React, { useState, useEffect, useCallback, useMemo } from "react";
import Plot from "react-plotly.js";
import { useWindowWidth } from "./useWindowWidthHook";

const UsesFunctionalityChart: React.FC<{
  facultyName: string;
  facultyColor: string; // use faculty.color to tint "no data" box
}> = ({ facultyName, facultyColor }) => {
  // chart "family" dropdown
  const [chartFamily, setChartFamily] =
    useState<"bar" | "heatmap" | "spider">("spider");

  // spider variant toggle (area vs bars)
  const [spiderMode, setSpiderMode] = useState<"area" | "bars">("area");

  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [noData, setNoData] = useState<boolean>(false);

  const [gender, setGender] = useState<string>("All");
  const [experience, setExperience] = useState<string | null>(null);
  const [profile, setProfile] = useState<string | null>(null);

  const winW = useWindowWidth();
  const lt740 = winW < 740;
  const lt684 = winW < 684;
  const lt600 = winW < 600;

  const baseTitleFont = lt600 ? 14 : lt740 ? 18 : 21;
  const barTitleSize = lt600 ? 14 : lt684 ? 15 : baseTitleFont;
  const barLegendSize = lt684 ? 11 : 14;
  const radarLegendSize = lt740 ? 12 : 14;
  const radarTickFontSize = lt740 ? 10 : 13;

  // helper to tint "no data"
  const rgba = (input: string, a = 1) => {
    const s = input.trim();
    if (/^rgba?\(/i.test(s)) {
      const [r, g, b] = s
        .replace(/[^\d.,]/g, "")
        .split(",")
        .slice(0, 3)
        .map(Number);
      return `rgba(${r},${g},${b},${a})`;
    }
    if (s[0] === "#") {
      let r = 0,
        g = 0,
        b = 0;
      if (s.length === 4) {
        r = parseInt(s[1] + s[1], 16);
        g = parseInt(s[2] + s[2], 16);
        b = parseInt(s[3] + s[3], 16);
      } else {
        r = parseInt(s.slice(1, 3), 16);
        g = parseInt(s.slice(3, 5), 16);
        b = parseInt(s.slice(5, 7), 16);
      }
      return `rgba(${r},${g},${b},${a})`;
    }
    return input;
  };
  const tintBg = rgba(facultyColor, 0.06);
  const tintBorder = `1px solid ${rgba(facultyColor, 0.25)}`;
  const tintText = facultyColor;

  const fetchData = useCallback(() => {
    setLoading(true);
    setNoData(false);

    const params = new URLSearchParams();
    if (gender && gender !== "All") params.append("gender", gender);
    if (experience) params.append("experience", experience);
    if (profile) params.append("profile", profile);

    fetch(
      `http://localhost:8000/api/faculty/${encodeURIComponent(
        facultyName
      )}/uses-functionality-correlation?${params.toString()}`,
      { cache: "no-store" }
    )
      .then((res) => res.json())
      .then((json) => {
        const arr = Array.isArray(json) ? json : [];
        setData(arr);
        setNoData(arr.length === 0);
      })
      .catch(() => {
        setData([]);
        setNoData(true);
      })
      .finally(() => setLoading(false));
  }, [facultyName, gender, experience, profile]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // STABLE task axis labels
  const funcLabels = useMemo(
    () => [
      "Text Creation",
      "Multimedia Creation",
      "Class Planning",
      "Material Design",
      "Activity Design",
      "Evaluation",
      "Research Management",
      "Data Collection",
      "Transcription / Translation",
      "Data Analysis",
      "Technical Support",
      "AI Experiments",
      "Inclusion Support",
    ],
    []
  );

  // STABLE canonical usage ordering
  const canonicalUsageOrder = useMemo(
    () => ["No use", "Low use", "Moderate use", "Advanced use"],
    []
  );

  // 1. Drop any usage row that's all zeros (ghost rows)
  const filteredData = useMemo(() => {
    return data.filter((row) => {
      const vals = funcLabels.map((task) => row[task]);
      const sum = vals.reduce(
        (acc, v) => acc + (typeof v === "number" && isFinite(v) ? v : 0),
        0
      );
      return sum > 0;
    });
  }, [data, funcLabels]);

  // 2. usage_label → row object, for quick lookup
  const rowByLabel: Record<string, any> = useMemo(() => {
    const out: Record<string, any> = {};
    filteredData.forEach((r) => {
      out[r.usage_label] = r;
    });
    return out;
  }, [filteredData]);

  // keep canonical order, but only labels we actually still have
  const orderedUsageLabels = useMemo(
    () => canonicalUsageOrder.filter((lbl) => rowByLabel[lbl]),
    [canonicalUsageOrder, rowByLabel]
  );

  // draw smallest last so hover works (small polygons on top)
  const radarOrder = useMemo(
    () => [...orderedUsageLabels].reverse(),
    [orderedUsageLabels]
  );

  // Per-usage-level stats (from backend)
  const groupStats = useMemo(
    () =>
      orderedUsageLabels.map((lbl) => {
        const row = rowByLabel[lbl] || {};
        return {
          label: lbl,
          n: row.n ?? 0,
          pct: row.pct ?? 0,
          mean: row.group_mean ?? 0,
          min: row.group_min ?? 0,
          max: row.group_max ?? 0,
        };
      }),
    [orderedUsageLabels, rowByLabel]
  );

  const totalN = useMemo(
    () =>
      groupStats.reduce(
        (acc, g) => acc + (typeof g.n === "number" ? g.n : 0),
        0
      ),
    [groupStats]
  );

  // 3. Build matrix aligned with orderedUsageLabels
  const matrix = useMemo(() => {
    return orderedUsageLabels.map((lbl) => {
      const row = rowByLabel[lbl];
      return funcLabels.map((task) => row[task]);
    });
  }, [orderedUsageLabels, rowByLabel, funcLabels]);

  // >>> dynamic range for bar spider based on stacked column sums <<<
  const maxRadialValue = useMemo(() => {
    if (!matrix.length) return 4; // fallback

    const numTasks = matrix[0].length;
    let globalMax = 0;

    for (let j = 0; j < numTasks; j++) {
      let colSum = 0;
      for (let i = 0; i < matrix.length; i++) {
        const v = matrix[i][j];
        if (typeof v === "number" && isFinite(v)) {
          colSum += v;
        }
      }
      if (colSum > globalMax) {
        globalMax = colSum;
      }
    }

    if (!isFinite(globalMax) || globalMax <= 0) return 4;
    return Math.ceil(globalMax); // closest bigger integer
  }, [matrix]);
  // <<< END dynamic range >>>

  // purples for grouped bar
  const colorPalette = [
    "#4c1d95",
    "#5b21b6",
    "#6b21a8",
    "#7e22ce",
    "#9333ea",
    "#a855f7",
    "#c084fc",
    "#e9d5ff",
  ];

  // trimmed purple colorscale for heatmap (avoid ultra-white low end)
  const purplesScale: [number, string][] = [
    [0.0, "#e9d5ff"],
    [0.25, "#9333ea"],
    [0.5, "#6b21a8"],
    [0.75, "#5b21b6"],
    [1.0, "#4c1d95"],
  ];

  // scale 1–4 → 0–100 (same idea as knowledge chart)
  const USAGE_SCALE = 100 / 3;

  // after filtering AND ordering, do we still have anything?
  const hasPlottable = orderedUsageLabels.length > 0;

  // shared colors for radar + barpolar
  const radarColors: Record<string, string> = {
    "No use": "#4c1d95",
    "Low use": "#6b21a8",
    "Moderate use": "#9333ea",
    "Advanced use": "#c084fc",
  };

  return (
    <div>
      {/* Filters */}
      <div className="flex flex-wrap justify-center gap-2 mb-3">
        <select
          value={gender}
          onChange={(e) => setGender(e.target.value)}
          className="border border-slate-300 rounded-md px-3 py-1 text-slate-700 text-sm shadow-sm hover:border-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-200 transition"
        >
          <option value="All">All Genders</option>
          <option value="Female">Female</option>
          <option value="Male">Male</option>
          <option value="Non-binary">Non-binary</option>
          <option value="No answer">No answer</option>
        </select>
        <select
          value={experience || ""}
          onChange={(e) => setExperience(e.target.value || null)}
          className="border border-slate-300 rounded-md px-3 py-1 text-slate-700 text-sm shadow-sm hover:border-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-200 transition"
        >
          <option value="">All Experience</option>
          <option value="Less than 5">Less than 5</option>
          <option value="Between 5 and 10">Between 5 and 10</option>
          <option value="Between 11 and 20">Between 11 and 20</option>
          <option value="More than 20">More than 20</option>
        </select>
        <select
          value={profile || ""}
          onChange={(e) => setProfile(e.target.value || null)}
          className="border border-slate-300 rounded-md px-3 py-1 text-slate-700 text-sm shadow-sm hover:border-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-200 transition"
        >
          <option value="">All Profiles</option>
          <option value="Senior Lecturer">Senior Lecturer</option>
          <option value="Associate">Associate</option>
          <option value="PreDoc">PreDoc</option>
          <option value="PostDoc">PostDoc</option>
          <option value="Collab">Collab</option>
          <option value="Lecturer">Lecturer</option>
          <option value="Professor">Professor</option>
        </select>
        <select
          value={chartFamily}
          onChange={(e) =>
            setChartFamily(e.target.value as "bar" | "heatmap" | "spider")
          }
          className="border border-slate-300 rounded-md px-3 py-1 text-slate-700 text-sm shadow-sm hover:border-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-200 transition"
        >
          <option value="bar">Grouped Bar</option>
          <option value="heatmap">Heatmap</option>
          <option value="spider">Spider</option>
        </select>
      </div>

      {/* SPIDER MODE TOGGLE – centered, outside the graph */}
      {chartFamily === "spider" && !loading && hasPlottable && (
        <div className="flex justify-center mb-3">
          <div className="inline-flex rounded-lg border border-slate-300 bg-white shadow-sm overflow-hidden">
            <button
              onClick={() => setSpiderMode("area")}
              className={
                "px-3 py-1.5 text-xs md:text-sm " +
                (spiderMode === "area"
                  ? "bg-purple-50 text-purple-700"
                  : "text-slate-600 hover:bg-slate-50")
              }
            >
              Spider (area)
            </button>
            <button
              onClick={() => setSpiderMode("bars")}
              className={
                "px-3 py-1.5 text-xs md:text-sm border-l border-slate-300 " +
                (spiderMode === "bars"
                  ? "bg-purple-50 text-purple-700"
                  : "text-slate-600 hover:bg-slate-50")
              }
            >
              Spider (bars)
            </button>
          </div>
        </div>
      )}

      {/* Chart wrapper (flex-col + height per chartFamily) */}
      <div
        className="relative w-full rounded-xl border border-slate-200 bg-white overflow-hidden flex flex-col"
        style={{ height: chartFamily === "bar" ? "730px" : "600px" }}
      >
        {loading && (
          <div className="absolute inset-0 bg-slate-100 animate-pulse" />
        )}

        {!loading && (!hasPlottable || noData) && (
          <div
            className="absolute inset-0 flex items-center justify-center"
            style={{ background: tintBg, border: tintBorder }}
          >
            <p
              style={{
                color: tintText,
                fontWeight: 600,
                letterSpacing: ".2px",
              }}
            >
              No data for the selected filters.
            </p>
          </div>
        )}

        {!loading && hasPlottable && (
          <>
            {chartFamily === "bar" && (
              <>
                {/* TOP: grouped bar (tasks × usage levels) */}
                <div className="flex-1">
                  <Plot
                    data={funcLabels.map((taskLabel, i) => ({
                      x: orderedUsageLabels,
                      y: orderedUsageLabels.map(
                        (lbl) => rowByLabel[lbl][taskLabel]
                      ),
                      name: taskLabel,
                      type: "bar",
                      orientation: "v",
                      marker: {
                        color: colorPalette[i % colorPalette.length],
                      },
                      hovertemplate:
                        `<b>AI Usage Level:</b> %{x}<br><b>${taskLabel}:</b> %{y:.2f}<extra></extra>`,
                    }))}
                    layout={{
                      barmode: "group",
                      title: {
                        text: "How often is AI used across tasks?",
                        y: 0.96,
                        font: { size: barTitleSize },
                      },
                      xaxis: {
                        tickfont: { size: radarTickFontSize },
                      },
                      yaxis: {
                        title: { text: "Avg Usage Frequency (1–4)" },
                        range: [0, 4],
                        automargin: true,
                      },
                      legend: {
                        orientation: "h",
                        y: -0.2,
                        x: 0.071,
                        font: { size: barLegendSize },
                        bordercolor: "#e2e8f0",
                        borderwidth: 1,
                      },
                      margin: { t: 80, l: 60, r: 30, b: 80 },
                      paper_bgcolor: "rgba(0,0,0,0)",
                      plot_bgcolor: "rgba(0,0,0,0)",
                    }}
                    style={{ width: "100%", height: "390px" }}
                    config={{ displayModeBar: false }}
                  />
                </div>

                {/* BOTTOM: usage group distribution + mean/min/max line (dual axis) */}
                <div className="border-t border-slate-100 px-4 pb-4 pt-2">
                  <Plot
                    data={[
                      // Bars: % of respondents (left axis)
                      {
                        x: groupStats.map((g) => g.label),
                        y: groupStats.map((g) => g.pct ?? 0),
                        type: "bar" as const,
                        name: "% of respondents",
                        marker: {
                          color: "#ede9fe", // light purple
                          line: { color: "#6b21a8", width: 1 },
                        },
                        customdata: groupStats.map((g) => g.n ?? 0),
                        hovertemplate:
                          "<b>%{x}</b><br>Share: %{y:.1f}% (n=%{customdata})<extra></extra>",
                      },
                      // Line: avg usage (1–4) mapped to 0–100 (right axis)
                      {
                        x: groupStats.map((g) => g.label),
                        y: groupStats.map((g) =>
                          ((g.mean ?? 1) - 1) * USAGE_SCALE
                        ),
                        type: "scatter" as const,
                        mode: "lines+markers",
                        name: "Avg usage (1–4)",
                        yaxis: "y2",
                        line: { color: "#6b21a8", width: 3 },
                        marker: { color: "#6b21a8", size: 7 },
                        error_y: {
                          type: "data",
                          symmetric: false,
                          array: groupStats.map((g) =>
                            Math.max(
                              0,
                              ((g.max ?? 1) - (g.mean ?? 1)) * USAGE_SCALE
                            )
                          ),
                          arrayminus: groupStats.map((g) =>
                            Math.max(
                              0,
                              ((g.mean ?? 1) - (g.min ?? 1)) * USAGE_SCALE
                            )
                          ),
                          visible: true,
                          thickness: 1.4,
                          width: 5,
                          color: "#6b21a8",
                        },
                        customdata: groupStats.map((g) => [
                          g.mean ?? 0,
                          g.min ?? 0,
                          g.max ?? 0,
                        ]),
                        hovertemplate:
                          "<b>%{x}</b>" +
                          "<br>Mean: %{customdata[0]:.2f}" +
                          "<br>Min: %{customdata[1]:.2f}" +
                          "<br>Max: %{customdata[2]:.2f}<extra></extra>",
                      },
                    ]}
                    layout={{
                      title: {
                        text: "Usage group distribution",
                        font: { size: barTitleSize },
                        y: 1,
                      },
                      xaxis: {
                        categoryorder: "array",
                        categoryarray: canonicalUsageOrder,
                        tickfont: { size: radarTickFontSize },
                      },
                      // LEFT axis: % respondents, owns gridlines
                      yaxis: {
                        title: { text: "% of respondents" },
                        rangemode: "tozero",
                        range: [0, 100],
                        tickmode: "array",
                        tickvals: [0, 20, 40, 60, 80, 100],
                        ticktext: ["0", "20", "40", "60", "80", "100"],
                        gridcolor: "#e2e8f0",
                        zeroline: false,
                      },
                      // RIGHT axis: usage 1–4 mapped to 0–100
                      yaxis2: {
                        title: { text: "Avg usage (1–4)" },
                        overlaying: "y",
                        side: "right",
                        range: [0, 100],
                        showgrid: false,
                        tickmode: "array",
                        // 0,20,40,60,80,100 → 1,1.6,2.2,2.8,3.4,4
                        tickvals: [0, 20, 40, 60, 80, 100],
                        ticktext: ["1", "1.6", "2.2", "2.8", "3.4", "4"],
                      },
                      legend: {
                        orientation: "h",
                        x: 0.5,
                        xanchor: "center",
                        y: -0.2,
                        font: { size: 11 },
                        bordercolor: "#e2e8f0",
                        borderwidth: 1,
                      },
                      margin: { t: 50, l: 60, r: 60, b: 70 },
                      paper_bgcolor: "rgba(0,0,0,0)",
                      plot_bgcolor: "rgba(0,0,0,0)",
                    }}
                    style={{ width: "100%", height: "260px" }}
                    config={{ displayModeBar: false }}
                  />
                </div>
              </>
            )}

            {chartFamily === "heatmap" && (
              <Plot
                data={[
                  {
                    z: matrix,
                    x: funcLabels,
                    y: orderedUsageLabels,
                    type: "heatmap",
                    colorscale: purplesScale,
                    colorbar: {
                      title: { text: "Usage", font: { color: "#6b21a8" } },
                      tickfont: { color: "#6b21a8" },
                      outlinecolor: "#6b21a8",
                      outlinewidth: 1,
                    },
                    hovertemplate:
                      `<b>AI Usage Level:</b> %{y}<br><b>Task:</b> %{x}` +
                      `<br><b>Avg Frequency:</b> %{z:.2f}<extra></extra>`,
                  },
                ]}
                layout={{
                  title: {
                    text: "How often is AI used across tasks?",
                    y: 0.96,
                    font: { size: barTitleSize },
                  },
                  yaxis: {
                    autorange: "reversed",
                    tickfont: { size: radarTickFontSize },
                  },
                  xaxis: { tickfont: { size: 11 } },
                  margin: { t: 110, l: 110, r: 0, b: 110 },
                  paper_bgcolor: "rgba(0,0,0,0)",
                  plot_bgcolor: "rgba(0,0,0,0)",
                  font: { color: "#334155" },
                }}
                config={{ displayModeBar: false }}
                style={{ width: "95%", height: "100%" }}
              />
            )}

            {chartFamily === "spider" && spiderMode === "area" && (
              <Plot
                data={radarOrder.map((lbl) => {
                  const color = radarColors[lbl] || "#6b21a8";
                  const row = rowByLabel[lbl];
                  const rVals = funcLabels.map((task) => row[task]);

                  const n = row?.n ?? 0;
                  const pct = row?.pct ?? 0;
                  const mean = row?.group_mean ?? 0;
                  const min = row?.group_min ?? 0;
                  const max = row?.group_max ?? 0;

                  // multi-line legend label
                  const legendName = [
                    lbl,
                    `n=${n} · ${pct.toFixed(1)}%`,
                    `μ=${mean.toFixed(2)} · min=${min.toFixed(
                      2
                    )} · max=${max.toFixed(2)}`,
                  ].join("<br>");

                  return {
                    type: "scatterpolar" as const,
                    r: rVals.concat(rVals[0]),
                    theta: funcLabels.concat(funcLabels[0]),
                    fill: "toself",
                    name: legendName,
                    line: { color, width: 3 },
                    fillcolor: color + "40",
                    hovertemplate:
                      `<b>%{theta}</b><br>Usage Level: <b>${lbl}</b>` +
                      `<br>Avg Frequency: %{r:.2f}<extra></extra>`,
                  };
                })}
                layout={{
                  title: {
                    text: "How often is AI used across tasks?",
                    font: { size: barTitleSize, color: "#334155" },
                  },
                  polar: {
                    bgcolor: "rgba(0,0,0,0)",
                    radialaxis: {
                      visible: true,
                      showline: true,
                      range: [0, 4],
                      gridcolor: "#f1f5f9",
                      gridwidth: 1.3,
                      tickfont: { color: "#475569", size: 11 },
                      tickangle: 0,
                      ticksuffix: " ",
                      title: {
                        text: "Usage frequency",
                        font: { size: 11 },
                      },
                    },
                    angularaxis: {
                      gridcolor: "#e2e8f0",
                      linecolor: "#cbd5e1",
                      showline: true,
                      linewidth: 1.5,
                      tickfont: {
                        color: "#334155",
                        size: radarTickFontSize,
                      },
                      ticklen: 8,
                      ticks: "",
                      direction: "clockwise",
                      rotation: 90,
                    },
                  },
                  showlegend: true,
                  legend: {
                    title: {
                      text:
                        `AI usage level (total n=${totalN})` +
                        '<br><span style="font-size:11px">mean / min / max across tasks</span>',
                      font: { color: "#334155", size: radarLegendSize - 1 },
                    },
                    orientation: "v",
                    y: 1.05,
                    x: -0.12,
                    xanchor: "left",
                    yanchor: "top",
                    font: {
                      color: "#334155",
                      size: radarLegendSize - 2,
                    },
                    bgcolor: "rgba(255,255,255,0.9)",
                    bordercolor: "#e2e8f0",
                    borderwidth: 1,
                  },
                  margin: { t: 90, l: 20, r: 40, b: 40 },
                  paper_bgcolor: "rgba(0,0,0,0)",
                  plot_bgcolor: "rgba(0,0,0,0)",
                }}
                style={{ width: "100%", height: "100%" }}
                config={{ displayModeBar: false }}
              />
            )}

            {chartFamily === "spider" && spiderMode === "bars" && (
              <Plot
                data={radarOrder.map((lbl) => {
                  const color = radarColors[lbl] || "#6b21a8";
                  const row = rowByLabel[lbl];
                  const rVals = funcLabels.map((task) => row[task]);

                  const n = row?.n ?? 0;
                  const pct = row?.pct ?? 0;
                  const mean = row?.group_mean ?? 0;
                  const min = row?.group_min ?? 0;
                  const max = row?.group_max ?? 0;

                  const legendName = [
                    lbl,
                    `n=${n} · ${pct.toFixed(1)}%`,
                    `μ=${mean.toFixed(2)} · min=${min.toFixed(
                      2
                    )} · max=${max.toFixed(2)}`,
                  ].join("<br>");

                  return {
                    type: "barpolar" as const,
                    r: rVals,
                    theta: funcLabels,
                    name: legendName,
                    marker: {
                      color,
                      line: { color: "#ffffff", width: 1 },
                    },
                    opacity: 0.95,
                    hovertemplate:
                      `<b>%{theta}</b><br>Usage Level: <b>${lbl}</b>` +
                      `<br>Avg Frequency: %{r:.2f}<extra></extra>`,
                  };
                })}
                layout={{
                  title: {
                    text: "How often is AI used across tasks?",
                    font: { size: barTitleSize, color: "#334155" },
                    y: 0.96,
                  },
                  polar: {
                    bgcolor: "rgba(0,0,0,0)",
                    radialaxis: {
                      // dynamic range based on stacked column sums
                      range: [0, maxRadialValue],
                      visible: false,
                      showline: false,
                      gridcolor: "#f1f5f9",
                      gridwidth: 1.3,
                      showticklabels: false,
                      ticks: "",
                      title: {
                        text: "Usage frequency",
                        font: { size: 11 },
                      },
                    },
                    angularaxis: {
                      gridcolor: "#e2e8f0",
                      linecolor: "#cbd5e1",
                      showline: true,
                      linewidth: 1.5,
                      tickfont: {
                        color: "#334155",
                        size: radarTickFontSize,
                      },
                      ticklen: 8,
                      ticks: "",
                      direction: "clockwise",
                      rotation: 90,
                    },
                  },
                  // stacked so the visual "columns" match the range logic
                  barmode: "stack",
                  showlegend: true,
                  legend: {
                    title: {
                      text:
                        `AI usage level (total n=${totalN})` +
                        '<br><span style="font-size:11px">mean / min / max across tasks</span>',
                      font: { color: "#334155", size: radarLegendSize - 1 },
                    },
                    orientation: "v",
                    y: 1.05,
                    x: -0.12,
                    xanchor: "left",
                    yanchor: "top",
                    font: { color: "#334155", size: radarLegendSize - 2 },
                    bgcolor: "rgba(255,255,255,0.9)",
                    bordercolor: "#e2e8f0",
                    borderwidth: 1,
                  },
                  margin: { t: 90, l: 20, r: 40, b: 40 },
                  paper_bgcolor: "rgba(0,0,0,0)",
                  plot_bgcolor: "rgba(0,0,0,0)",
                }}
                style={{ width: "100%", height: "100%" }}
                config={{ displayModeBar: false }}
              />
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default UsesFunctionalityChart;
