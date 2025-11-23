import React, { useEffect, useMemo, useState } from "react";
import Plot from "react-plotly.js";

type APIResp = {
  categories: string[];
  levels: string[]; // ["Strongly disagree", "Disagree", "Agree", "Strongly agree"]
  series: { name: string; values: number[] }[];
  totals_by_cat: number[];
  long_labels: Record<string, string>;
};

const LEVEL_ORDER = ["Strongly disagree", "Disagree", "Agree", "Strongly agree"] as const;

const COLOR_BY_LEVEL: Record<string, string> = {
  "Strongly disagree": "#f0fdf4", // green-50  (lightest)
  "Disagree":          "#bbf7d0", // green-200
  "Agree":             "#34d399", // green-400
  "Strongly agree":    "#065f46", // green-900 (darkest)
};

const useWindowWidth = () => {
  const [w, setW] = useState<number>(() =>
    typeof window !== "undefined" ? window.innerWidth : 1024
  );
  useEffect(() => {
    const on = () => setW(window.innerWidth);
    window.addEventListener("resize", on);
    return () => window.removeEventListener("resize", on);
  }, []);
  return w;
};

const PerceptionsStudentsAttitudesBar: React.FC<{
  facultyName: string;
  facultyColor?: string; // default perceptions green
}> = ({ facultyName, facultyColor = "#15803d" }) => {
  const [data, setData] = useState<APIResp | null>(null);
  const [loading, setLoading] = useState(false);
  const [noData, setNoData] = useState(false);

  // filters
  const [gender, setGender] = useState<string>("All");
  const [experience, setExperience] = useState<string | null>(null);
  const [profile, setProfile] = useState<string | null>(null);

  const winW = useWindowWidth();
  const lt820 = winW < 820;
  const titleSize  = lt820 ? 16 : 20;
  const legendSize = lt820 ? 11 : 13;
  const tickSize   = lt820 ? 10 : 12;

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
      )}/perceptions-students-attitudes-distribution?${params.toString()}`,
      { cache: "no-store" }
    )
      .then((r) => r.json())
      .then((json: APIResp) => {
        setData(json);
        const anyPos =
          json?.series?.some((s) => s.values.some((v) => v > 0)) ?? false;
        setNoData(!anyPos);
      })
      .catch(() => {
        setData(null);
        setNoData(true);
      })
      .finally(() => setLoading(false));
  }, [facultyName, gender, experience, profile]);

  const traces = useMemo(() => {
    if (!data) return [];
    const totals = data.totals_by_cat.map((t) => Math.max(1, t));

    const seriesSorted = [...data.series].sort(
      (a, b) => LEVEL_ORDER.indexOf(a.name as any) - LEVEL_ORDER.indexOf(b.name as any)
    );

    return seriesSorted
      .filter((s) => s.values.some((v) => v > 0))
      .map((s) => {
        const pct = s.values.map((v, i) =>
          totals[i] ? (v * 100) / totals[i] : 0
        );
        const custom = s.values.map((v, i) => [
          v,
          totals[i],
          data.long_labels[data.categories[i]] || data.categories[i],
          pct[i],
        ]);
        return {
          type: "bar" as const,
          orientation: "v" as const,
          x: data.categories,
          y: s.values, // raw counts; barnorm='percent' normalizes for drawing
          name: s.name,
          marker: {
            color: COLOR_BY_LEVEL[s.name] ?? "#86efac",
            line: { color: "rgba(255,255,255,0.95)", width: 1 }, // slice separators
          },
          customdata: custom,
          hovertemplate:
            `<b>%{customdata[2]}</b><br>` + // long label
            `Level: <b>${s.name}</b><br>` +
            `Count: <b>%{customdata[0]}</b> / %{customdata[1]}<br>` +
            `Share: <b>%{customdata[3]:.1f}%</b><extra></extra>`,
        };
      });
  }, [data]);

  return (
    <div className="mt-6">
      {/* Filters */}
      <div className="flex flex-wrap justify-center gap-2 mb-4">
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

      <div className="relative w-full h-[560px] rounded-xl border border-slate-200 bg-white overflow-hidden">
        {loading && <div className="absolute inset-0 bg-slate-100 animate-pulse" />}

        {!loading && (noData || !data) && (
          <div
            className="absolute inset-0 flex items-center justify-center"
            style={{
              background: "rgba(21,128,61,0.06)",
              border: "1px solid rgba(21,128,61,0.25)",
            }}
          >
            <p
              style={{ color: facultyColor, fontWeight: 600, letterSpacing: ".2px" }}
            >
              No data for the selected filters.
            </p>
          </div>
        )}

        {!loading && data && !noData && (
          <Plot
            data={traces}
            layout={{
              barmode: "stack",
              barnorm: "percent",

              title: {
                text: "Agreement with statements about AI and students",
                font: { size: titleSize, color: "#334155" },
                y: 0.96,
              },

              xaxis: {
                automargin: true,
                tickfont: { size: tickSize, color: "#334155" },
                showline: true,
                linecolor: "#060707",
                linewidth: 1,
                showgrid: true,
                gridcolor: "#f1f5f9",
                gridwidth: 1,
                ticks: "outside",
                tickcolor: "#cbd5e1",
                ticklen: 6,
              },
              yaxis: {
                title: { text: "Share of responses", font: { size: 12, color: "#334155" } },
                range: [0, 100],
                ticksuffix: "%",
                showgrid: true,
                gridcolor: "#e5e9f2",
                gridwidth: 1.2,
                zerolinecolor: "#94a3b8",
              },

              legend: {
                title: { text: "Agreement level", font: { size: legendSize, color: "#334155" } },
                orientation: "h",
                y: -0.22,
                x: 0.17,
                font: { size: legendSize, color: "#334155" },
                bordercolor: "#e2e8f0",
                borderwidth: 1,
              },

              bargap: 0.25,
              bargroupgap: 0.08,
              margin: { t: 80, l: 60, r: 20, b: 110 },
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
        )}
      </div>
    </div>
  );
};

export default PerceptionsStudentsAttitudesBar;
