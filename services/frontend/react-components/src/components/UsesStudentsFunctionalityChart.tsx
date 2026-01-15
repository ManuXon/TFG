import React, { useState, useEffect, useCallback, useMemo } from "react";
import Plot from "react-plotly.js";
import { useWindowWidth } from "./useWindowWidthHook";

const UsesStudentsFunctionalityChart: React.FC<{
  facultyName: string;
  facultyColor: string;
}> = ({ facultyName, facultyColor }) => {
  // Chart "family" dropdown (bar / heatmap / spider)
  const [chartFamily, setChartFamily] =
    useState<"bar" | "heatmap" | "spider">("spider");

  // Spider variant toggle (area radar vs bar spider)
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

  // Legend title for the grouped bar (series are tasks)
  const legendTitleText = "Student task";

  // tint for "no data"
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
      )}/students-uses-by-proposal?${params.toString()}`,
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

  // 11 student task labels (axis)
  const funcLabels = useMemo(
    () => [
      "Text Creation",
      "Multimedia Creation",
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

  // canonical proposal order
  const canonicalProposalOrder = useMemo(
    () => ["Never", "Sometimes", "Often", "Very often"],
    []
  );

  // 1) drop ghost rows (all zeros)
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

  // 2) index by proposal_label
  const rowByLabel: Record<string, any> = useMemo(() => {
    const out: Record<string, any> = {};
    filteredData.forEach((r) => {
      out[r.proposal_label] = r;
    });
    return out;
  }, [filteredData]);

  // 3) keep canonical order but only those present
  const orderedProposalLabels = useMemo(
    () => canonicalProposalOrder.filter((lbl) => rowByLabel[lbl]),
    [canonicalProposalOrder, rowByLabel]
  );

  // Smallest last so tiny polygons are on top
  const radarOrder = useMemo(
    () => [...orderedProposalLabels].reverse(),
    [orderedProposalLabels]
  );

  // Per-proposal stats from backend (for legend + distribution chart)
  const groupStats = useMemo(
    () =>
      orderedProposalLabels.map((lbl) => {
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
    [orderedProposalLabels, rowByLabel]
  );

  const totalN = useMemo(
    () =>
      groupStats.reduce(
        (acc, g) => acc + (typeof g.n === "number" ? g.n : 0),
        0
      ),
    [groupStats]
  );

  // 4) matrix aligned to ordered labels
  const matrix = useMemo(() => {
    return orderedProposalLabels.map((lbl) => {
      const row = rowByLabel[lbl];
      return funcLabels.map((task) => row[task]);
    });
  }, [orderedProposalLabels, rowByLabel, funcLabels]);

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

  // purples (same family as Uses)
  const barColors = [
    "#4c1d95",
    "#5b21b6",
    "#6b21a8",
    "#7e22ce",
    "#9333ea",
    "#a855f7",
    "#c084fc",
    "#e9d5ff",
  ];
  const purplesScale: [number, string][] = [
    [0.0, "#e9d5ff"],
    [0.25, "#9333ea"],
    [0.5, "#6b21a8"],
    [0.75, "#5b21b6"],
    [1.0, "#4c1d95"],
  ];

  // 1–4 → 0–100 for proposal average
  const PROPOSAL_SCALE = 100 / 3;

  const hasPlottable = orderedProposalLabels.length > 0;

  // Shared colors for spider area and spider bars
  const radarColors: Record<string, string> = {
    Never: "#4c1d95",
    Sometimes: "#6b21a8",
    Often: "#9333ea",
    "Very often": "#c084fc",
  };

  // ---------- Legend helpers (mirror Knowledge / Uses spider) ----------
  const formatProposalLegendName = useCallback(
    (
      label: string,
      n: number,
      pct: number,
      mean: number,
      min: number,
      max: number
    ) => {
      const safeN = Number.isFinite(n) ? n : 0;
      const safePct = Number.isFinite(pct) ? pct : 0;
      const safeMean = Number.isFinite(mean) ? mean : 0;
      const safeMin = Number.isFinite(min) ? min : 0;
      const safeMax = Number.isFinite(max) ? max : 0;

      return [
        `<span style="font-weight:600">${label}</span>`,
        `<span style="font-size:11px; color:#4b5563">n=${safeN} · ${safePct.toFixed(
          1
        )}% · μ=${safeMean.toFixed(2)} [${safeMin.toFixed(
          2
        )}–${safeMax.toFixed(2)}]</span>`,
      ].join("<br>");
    },
    []
  );

  const proposalLegendTitleText = useMemo(
    () =>
      `<span style="font-weight:600">AI proposal level</span> (total n=${totalN})` +
      '<br><span style="font-size:11px; font-style:italic">mean / min / max across tasks</span>',
    [totalN]
  );
  // --------------------------------------------------------------

  // ---- Title + custom tooltip (same style as Knowledge / Uses) ----
  const studentsTitleText = "Where do you propose AI use to students?";

  const StudentsTitleWithTooltip: React.FC<{ label: string }> = ({
    label,
  }) => (
    <div className="flex items-center justify-center mb-1">
      <div className="relative inline-flex items-center gap-1 group">
        <span
          className="text-slate-800 font-semibold"
          style={{ fontSize: barTitleSize }}
        >
          {label}
        </span>
        <span className="inline-flex items-center justify-center w-4 h-4 text-[11px] rounded-full border border-purple-400 text-purple-700 bg-purple-50 font-semibold cursor-help leading-none">
          ?
        </span>
        {/* Custom tooltip */}
        <div className="pointer-events-none absolute left-1/2 top-full z-10 hidden w-[320px] -translate-x-1/2 translate-y-2 rounded-md bg-purple-50 px-3 py-2 text-xs text-slate-700 shadow-lg ring-1 ring-purple-200 group-hover:block">
          <p className="font-semibold mb-1 text-purple-900">
            How to read this chart
          </p>
          <p className="mb-1">Original survey questions:</p>
          <ul className="list-disc pl-4 space-y-0.5 mb-2">
            <li>
              <span className="font-medium">
                “Do you ask or suggest your students to use AI tools?”
              </span>{" "}
              Answers range from never to very often.
            </li>
            <li>
              <span className="font-medium">
                “For which types of tasks do you propose AI tools to your
                students?”
              </span>{" "}
              for each task shown on the axes.
            </li>
          </ul>
          <p className="mb-1 font-medium">Numeric scale used for averages:</p>
          <ul className="list-disc pl-4 space-y-0.5">
            <li>1 = Never</li>
            <li>2 = Sometimes</li>
            <li>3 = Often</li>
            <li>4 = Very often</li>
          </ul>
        </div>
      </div>
    </div>
  );
  // --------------------------------------------------------------

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

      {/* Wrapper now flex-col with dynamic height (like Uses / Knowledge) */}
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
                {/* TOP: grouped bar (tasks × proposal levels) */}
                <div className="flex-1 flex flex-col">
                  <StudentsTitleWithTooltip label={studentsTitleText} />
                  <Plot
                    data={funcLabels.map((taskLabel, i) => ({
                      x: orderedProposalLabels,
                      y: orderedProposalLabels.map(
                        (lbl) => rowByLabel[lbl][taskLabel]
                      ),
                      name: taskLabel,
                      type: "bar",
                      marker: { color: barColors[i % barColors.length] },
                      hovertemplate:
                        `<b>Proposal Frequency:</b> %{x}<br><b>${taskLabel}:</b> %{y:.2f}<extra></extra>`,
                    }))}
                    layout={{
                      barmode: "group",
                      title: { text: "" }, // external React title + tooltip
                      xaxis: { tickfont: { size: radarTickFontSize } },
                      yaxis: {
                        title: { text: "Avg Frequency (1–4)" },
                        range: [0, 4],
                        automargin: true,
                      },
                      legend: {
                        title: {
                          text: legendTitleText,
                          font: { size: barLegendSize, color: "#334155" },
                        },
                        orientation: "h",
                        y: -0.2,
                        x: 0.071,
                        font: { size: barLegendSize },
                        bordercolor: "#e2e8f0",
                        borderwidth: 1,
                      },
                      margin: { t: 40, l: 60, r: 30, b: 80 },
                      paper_bgcolor: "rgba(0,0,0,0)",
                      plot_bgcolor: "rgba(0,0,0,0)",
                    }}
                    style={{ width: "100%", height: "390px" }}
                    config={{ displayModeBar: false }}
                  />
                </div>

                {/* BOTTOM: proposal group distribution + mean/min/max line */}
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
                      // Line: avg proposal 1–4 mapped to 0–100 (right axis)
                      {
                        x: groupStats.map((g) => g.label),
                        y: groupStats.map((g) =>
                          ((g.mean ?? 1) - 1) * PROPOSAL_SCALE
                        ),
                        type: "scatter" as const,
                        mode: "lines+markers",
                        name: "Avg proposal (1–4)",
                        yaxis: "y2",
                        line: { color: "#6b21a8", width: 3 },
                        marker: { color: "#6b21a8", size: 7 },
                        error_y: {
                          type: "data",
                          symmetric: false,
                          array: groupStats.map((g) =>
                            Math.max(
                              0,
                              ((g.max ?? 1) - (g.mean ?? 1)) * PROPOSAL_SCALE
                            )
                          ),
                          arrayminus: groupStats.map((g) =>
                            Math.max(
                              0,
                              ((g.mean ?? 1) - (g.min ?? 1)) * PROPOSAL_SCALE
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
                        text: "Proposal group distribution",
                        font: { size: barTitleSize },
                        y: 1,
                      },
                      xaxis: {
                        categoryorder: "array",
                        categoryarray: canonicalProposalOrder,
                        tickfont: { size: radarTickFontSize },
                      },
                      // LEFT axis: % respondents
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
                      // RIGHT axis: proposal avg (1–4) mapped to 0–100
                      yaxis2: {
                        title: { text: "Avg proposal (1–4)" },
                        overlaying: "y",
                        side: "right",
                        range: [0, 100],
                        showgrid: false,
                        tickmode: "array",
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
              <div className="flex-1 flex flex-col items-center">
                <StudentsTitleWithTooltip label={studentsTitleText} />
                <Plot
                  data={[
                    {
                      z: matrix,
                      x: funcLabels,
                      y: orderedProposalLabels,
                      type: "heatmap",
                      colorscale: purplesScale,
                      colorbar: { title: { text: "Avg Frequency" } },
                      hovertemplate:
                        `<b>Proposal Frequency:</b> %{y}<br><b>Task:</b> %{x}` +
                        `<br><b>Avg Frequency:</b> %{z:.2f}<extra></extra>`,
                    },
                  ]}
                  layout={{
                    title: { text: "" },
                    yaxis: {
                      autorange: "reversed",
                      tickfont: { size: radarTickFontSize },
                    },
                    xaxis: { tickfont: { size: 11 } },
                    margin: { t: 40, l: 110, r: 0, b: 110 },
                    paper_bgcolor: "rgba(0,0,0,0)",
                    plot_bgcolor: "rgba(0,0,0,0)",
                    font: { color: "#334155" },
                  }}
                  config={{ displayModeBar: false }}
                  style={{ width: "95%", height: "100%" }}
                />
              </div>
            )}

            {chartFamily === "spider" && spiderMode === "area" && (
              <div className="flex-1 flex flex-col">
                <StudentsTitleWithTooltip label={studentsTitleText} />
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

                    const legendName = formatProposalLegendName(
                      lbl,
                      n,
                      pct,
                      mean,
                      min,
                      max
                    );

                    return {
                      type: "scatterpolar" as const,
                      r: rVals.concat(rVals[0]),
                      theta: funcLabels.concat(funcLabels[0]),
                      fill: "toself",
                      hoveron: "points",
                      name: legendName,
                      line: { color, width: 3 },
                      fillcolor: color + "40",
                      hovertemplate:
                        `<b>%{theta}</b><br>Proposal Level: <b>${lbl}</b>` +
                        `<br>Avg Frequency: %{r:.2f}<extra></extra>`,
                    };
                  })}
                  layout={{
                    title: { text: "" },
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
                          text: "Proposal frequency",
                          font: { size: 11 },
                        },
                      },
                      angularaxis: {
                        gridcolor: "#e2e8f0",
                        linecolor: "#cbd5e1",
                        showline: true,
                        linewidth: 1.5,
                        tickfont: { color: "#334155", size: radarTickFontSize },
                        ticklen: 8,
                        ticks: "",
                        direction: "clockwise",
                        rotation: 90,
                      },
                    },
                    showlegend: true,
                    legend: {
                      title: {
                        text: proposalLegendTitleText,
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
                    margin: { t: 40, l: 20, r: 40, b: 40 },
                    paper_bgcolor: "rgba(0,0,0,0)",
                    plot_bgcolor: "rgba(0,0,0,0)",
                  }}
                  style={{ width: "100%", height: "100%" }}
                  config={{ displayModeBar: false }}
                />
              </div>
            )}

            {chartFamily === "spider" && spiderMode === "bars" && (
              <div className="flex-1 flex flex-col">
                <StudentsTitleWithTooltip label={studentsTitleText} />
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

                    const legendName = formatProposalLegendName(
                      lbl,
                      n,
                      pct,
                      mean,
                      min,
                      max
                    );

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
                        `<b>%{theta}</b><br>Proposal Level: <b>${lbl}</b>` +
                        `<br>Avg Frequency: %{r:.2f}<extra></extra>`,
                    };
                  })}
                  layout={{
                    title: { text: "" },
                    polar: {
                      bgcolor: "rgba(0,0,0,0)",
                      radialaxis: {
                        range: [0, maxRadialValue], // dynamic
                        visible: false,
                        showline: false,
                        gridcolor: "#f1f5f9",
                        gridwidth: 1.3,
                        showticklabels: false,
                        ticks: "",
                        title: {
                          text: "Proposal frequency",
                          font: { size: 11 },
                        },
                      },
                      angularaxis: {
                        gridcolor: "#e2e8f0",
                        linecolor: "#cbd5e1",
                        showline: true,
                        linewidth: 1.5,
                        tickfont: { color: "#334155", size: radarTickFontSize },
                        ticklen: 8,
                        ticks: "",
                        direction: "clockwise",
                        rotation: 90,
                      },
                    },
                    barmode: "stack",
                    showlegend: true,
                    legend: {
                      title: {
                        text: proposalLegendTitleText,
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
                    margin: { t: 40, l: 20, r: 40, b: 40 },
                    paper_bgcolor: "rgba(0,0,0,0)",
                    plot_bgcolor: "rgba(0,0,0,0)",
                  }}
                  style={{ width: "100%", height: "100%" }}
                  config={{ displayModeBar: false }}
                />
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default UsesStudentsFunctionalityChart;
