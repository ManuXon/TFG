import React, { useEffect, useMemo, useState } from "react";
import Plot from "react-plotly.js";

type Resp = {
  axis: string[];                 // short labels for ticks
  counts: number[];               // counts per axis slot
  total: number;                  // total selections
  long_map: Record<string, string>; // short -> long label
};

const rgba = (hex: string, a = 1) => {
  const s = hex.replace("#", "");
  const r = parseInt(s.slice(0, 2), 16);
  const g = parseInt(s.slice(2, 4), 16);
  const b = parseInt(s.slice(4, 6), 16);
  return `rgba(${r},${g},${b},${a})`;
};

const useWindowWidth = () => {
  const [w, setW] = useState<number>(() =>
    typeof window !== "undefined" ? window.innerWidth : 1024
  );
  useEffect(() => {
    const f = () => setW(window.innerWidth);
    window.addEventListener("resize", f);
    return () => window.removeEventListener("resize", f);
  }, []);
  return w;
};

const PerceptionsPrioritiesSpider: React.FC<{
  facultyName: string;
  facultyColor?: string; // default perceptions green
}> = ({ facultyName, facultyColor = "#15803d" }) => {
  const [data, setData] = useState<Resp | null>(null);
  const [loading, setLoading] = useState(false);
  const [noData, setNoData] = useState(false);

  // spider variant toggle
  const [spiderMode, setSpiderMode] = useState<"area" | "bars">("area");

  // filters
  const [gender, setGender] = useState<string>("All");
  const [experience, setExperience] = useState<string | null>(null);
  const [profile, setProfile] = useState<string | null>(null);

  const winW = useWindowWidth();
  const lt740 = winW < 740;
  const titleSize = lt740 ? 16 : 20;
  const tickSize = lt740 ? 10 : 12;

  const tintBg = rgba(facultyColor, 0.06);
  const tintBorder = `1px solid ${rgba(facultyColor, 0.25)}`;

  useEffect(() => {
    setLoading(true);
    setNoData(false);
    const params = new URLSearchParams();
    if (gender && gender !== "All") params.append("gender", gender);
    if (experience) params.append("experience", experience);
    if (profile) params.append("profile", profile);

    fetch(
      `http://localhost:8000/api/faculty/${encodeURIComponent(
        facultyName
      )}/perceptions-priorities?${params.toString()}`,
      { cache: "no-store" }
    )
      .then((r) => r.json())
      .then((json: Resp) => {
        setData(json);
        setNoData(
          !(
            json &&
            json.axis &&
            json.axis.length > 0 &&
            json.counts.some((v) => v > 0)
          )
        );
      })
      .catch(() => {
        setData(null);
        setNoData(true);
      })
      .finally(() => setLoading(false));
  }, [facultyName, gender, experience, profile]);

  // Close-loop arrays for polar (area mode)
  const rVals = useMemo(() => {
    if (!data) return [];
    const core = data.counts;
    return core.length ? core.concat(core[0]) : core;
  }, [data]);

  const theta = useMemo(() => {
    if (!data) return [];
    const core = data.axis; // keep SHORT labels on axis
    return core.length ? core.concat(core[0]) : core;
  }, [data]);

  // Long labels for hover + shares for tooltip
  const longAxis = useMemo(() => {
    if (!data) return [];
    return data.axis.map((short) => data.long_map?.[short] ?? short);
  }, [data]);

  const shares = useMemo(() => {
    if (!data) return [];
    return data.counts.map((v) =>
      data.total > 0 ? (v * 100) / data.total : 0
    );
  }, [data]);

  // Base customdata (no loop) for bar mode
  const baseCustomData = useMemo(() => {
    if (!data) return [];
    return longAxis.map((L, i) => [L, shares[i]]);
  }, [longAxis, shares, data]);

  // Closed-loop customdata for area mode
  const customdataClosed = useMemo(() => {
    const base = baseCustomData;
    return base.length ? base.concat([base[0]]) : base;
  }, [baseCustomData]);

  // Radial max: same logic for area & bars
  const radialMax = useMemo(() => {
    if (!data || !data.counts || data.counts.length === 0) return 1;
    const maxVal = Math.max(...data.counts);
    if (!isFinite(maxVal) || maxVal <= 0) return 1;
    return maxVal * 1.1;
  }, [data]);

  return (
    <div>
      {/* Filters */}
      <div className="flex flex-wrap justify-center gap-2 mb-3">
        <select
          value={gender}
          onChange={(e) => setGender(e.target.value)}
          className="border border-slate-300 rounded-md px-3 py-1 text-slate-700 text-sm shadow-sm hover:border-slate-400 focus:outline-none focus:ring-2 focus:ring-green-200 transition"
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
          className="border border-slate-300 rounded-md px-3 py-1 text-slate-700 text-sm shadow-sm hover:border-slate-400 focus:outline-none focus:ring-2 focus:ring-green-200 transition"
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
          className="border border-slate-300 rounded-md px-3 py-1 text-slate-700 text-sm shadow-sm hover:border-slate-400 focus:outline-none focus:ring-2 focus:ring-green-200 transition"
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
      </div>

      {/* SPIDER MODE TOGGLE – same style/placement as others */}
      {!loading && data && !noData && (
        <div className="flex justify-center mb-3">
          <div className="inline-flex rounded-lg border border-slate-300 bg-white shadow-sm overflow-hidden">
            <button
              onClick={() => setSpiderMode("area")}
              className={
                "px-3 py-1.5 text-xs md:text-sm " +
                (spiderMode === "area"
                  ? "bg-emerald-50 text-emerald-700"
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
                  ? "bg-emerald-50 text-emerald-700"
                  : "text-slate-600 hover:bg-slate-50")
              }
            >
              Spider (bars)
            </button>
          </div>
        </div>
      )}

      <div className="relative w-full h-[560px] rounded-xl border border-slate-200 bg-white overflow-hidden">
        {loading && (
          <div className="absolute inset-0 bg-slate-100 animate-pulse" />
        )}

        {!loading && (noData || !data) && (
          <div
            className="absolute inset-0 flex items-center justify-center"
            style={{ background: tintBg, border: tintBorder }}
          >
            <p
              style={{
                color: facultyColor,
                fontWeight: 600,
                letterSpacing: ".2px",
              }}
            >
              No data for the selected filters.
            </p>
          </div>
        )}

        {!loading && data && !noData && spiderMode === "area" && (
          <Plot
            data={[
              {
                type: "scatterpolar" as const,
                r: rVals,
                theta: theta,
                fill: "toself",
                name: "Top priorities (counts)",
                line: { color: facultyColor, width: 3 },
                fillcolor: rgba(facultyColor, 0.25),
                customdata: customdataClosed, // [longLabel, sharePct] closed loop
                hovertemplate:
                  `<b>%{customdata[0]}</b>` +
                  `<br>Count: <b>%{r}</b>` +
                  `<br>Share: <b>%{customdata[1]:.1f}%</b><extra></extra>`,
              },
            ]}
            layout={{
              title: {
                text: "Which teaching functions are prioritized?",
                font: { size: titleSize, color: "#334155" },
                y: 0.96,
              },
              polar: {
                bgcolor: "rgba(0,0,0,0)",
                radialaxis: {
                  visible: true,
                  range: [0, radialMax],
                  gridcolor: "#e2e8f0",
                  showline: true,
                  title: { text: "Total count", font: { size: 11 } },
                },
                angularaxis: {
                  gridcolor: "#e2e8f0",
                  linecolor: "#cbd5e1",
                  showline: true,
                  linewidth: 1.3,
                  tickfont: { color: "#334155", size: tickSize },
                },
              },
              showlegend: false,
              margin: { t: 90, l: 60, r: 40, b: 40 },
              paper_bgcolor: "rgba(0,0,0,0)",
              plot_bgcolor: "rgba(0,0,0,0)",
            }}
            style={{ width: "100%", height: "100%" }}
            config={{ displayModeBar: false }}
          />
        )}

        {!loading && data && !noData && spiderMode === "bars" && (
          <Plot
            data={[
              {
                type: "barpolar" as const,
                r: data.counts,
                theta: data.axis,
                name: "Top priorities (counts)",
                marker: {
                  color: facultyColor,
                  line: { color: "#ffffff", width: 1 },
                },
                opacity: 0.95,
                customdata: baseCustomData, // [longLabel, sharePct] per axis
                hovertemplate:
                  `<b>%{customdata[0]}</b>` +
                  `<br>Count: <b>%{r}</b>` +
                  `<br>Share: <b>%{customdata[1]:.1f}%</b><extra></extra>`,
              },
            ]}
            layout={{
              title: {
                text: "Which teaching functions are prioritized?",
                font: { size: titleSize, color: "#334155" },
                y: 0.96,
              },
              polar: {
                bgcolor: "rgba(0,0,0,0)",
                radialaxis: {
                  visible: true,
                  showline: true,
                  range: [0, radialMax],
                  gridcolor: "#e2e8f0",
                  gridwidth: 1.3,
                  showticklabels: true,
                  ticks: "",
                  tickfont: { color: "#475569", size: 11 },
                  title: {
                    text: "Total count",
                    font: { size: 11 },
                  },
                },
                angularaxis: {
                  gridcolor: "#e2e8f0",
                  linecolor: "#cbd5e1",
                  showline: true,
                  linewidth: 1.3,
                  tickfont: {
                    color: "#334155",
                    size: tickSize,
                  },
                  ticklen: 8,
                  ticks: "",
                },
              },
              barmode: "group",
              showlegend: false,
              margin: { t: 90, l: 60, r: 40, b: 40 },
              paper_bgcolor: "rgba(0,0,0,0)",
              plot_bgcolor: "rgba(0,0,0,0)",
            }}
            style={{ width: "100%", height: "100%" }}
            config={{ displayModeBar: false }}
          />
        )}
      </div>
    </div>
  );
};

export default PerceptionsPrioritiesSpider;
