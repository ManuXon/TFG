import React, { useEffect, useMemo, useState } from "react";
import Plot from "react-plotly.js";

type APIResp = {
  categories: string[]; // ["Not interested at all", "Low interest", ...]
  values: number[];     // counts
  total: number;
};

const ORDER = [
  "Not interested at all",
  "Low interest",
  "Moderate interest",
  "High interest",
] as const;

// Training palette: light → dark (anchored at #b45309)
const COLOR_BY_LABEL: Record<string, string> = {
  "Not interested at all": "#fff7ed", // orange-50
  "Low interest":          "#fed7aa", // orange-200
  "Moderate interest":     "#fb923c", // orange-400
  "High interest":         "#b45309", // orange-700 (Training brand color)
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

const TrainingInterestPie: React.FC<{
  facultyName: string;
  facultyColor?: string; // default Training color
}> = ({ facultyName, facultyColor = "#b45309" }) => {
  const [data, setData] = useState<APIResp | null>(null);
  const [loading, setLoading] = useState(false);

  // Filters (same semantics as the rest)
  const [gender, setGender] = useState<string>("All");
  const [experience, setExperience] = useState<string | null>(null);
  const [profile, setProfile] = useState<string | null>(null);

  const winW = useWindowWidth();
  const lt670 = winW < 670;
  const lt600 = winW < 600;
  const pieTitleSize = lt600 ? 9 : lt670 ? 10 : 13;

  useEffect(() => {
    setLoading(true);
    const params = new URLSearchParams();
    if (gender && gender !== "All") params.append("gender", gender);
    if (experience) params.append("experience", experience);
    if (profile) params.append("profile", profile);

    fetch(
      `http://localhost:8000/api/faculty/${encodeURIComponent(
        facultyName
      )}/training-interest-distribution?${params.toString()}`,
      { cache: "no-store" }
    )
      .then((r) => r.json())
      .then((json: APIResp) => setData(json))
      .catch(() => setData({ categories: [], values: [], total: 0 }))
      .finally(() => setLoading(false));
  }, [facultyName, gender, experience, profile]);

  const tuples = useMemo(() => {
    if (!data) return [];
    return (data.categories || []).map((label, i) => ({
      label,
      value: data.values?.[i] ?? 0,
    }));
  }, [data]);

  const filtered = useMemo(
    () =>
      tuples
        .filter((t) => (t.value ?? 0) > 0)
        .sort(
          (a, b) => ORDER.indexOf(a.label as any) - ORDER.indexOf(b.label as any)
        ),
    [tuples]
  );

  const labels = filtered.map((t) => t.label);
  const values = filtered.map((t) => t.value);
  const colors = labels.map((l) => COLOR_BY_LABEL[l] ?? "#fb923c");
  const total = values.reduce((s, v) => s + (v || 0), 0);

  return (
    <div className="mt-6">
      {/* Compact filters */}
      <div className="flex flex-wrap justify-center gap-2 mb-4">
        <select
          value={gender}
          onChange={(e) => setGender(e.target.value)}
          className="border border-slate-300 rounded-md px-2 py-1 text-slate-700 text-xs shadow-sm hover:border-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-200 transition"
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
          className="border border-slate-300 rounded-md px-2 py-1 text-slate-700 text-xs shadow-sm hover:border-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-200 transition"
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
          className="border border-slate-300 rounded-md px-2 py-1 text-slate-700 text-xs shadow-sm hover:border-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-200 transition"
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

      <div className="relative w-full h-[470px] rounded-xl border border-slate-200 bg-white overflow-hidden">
        {loading && <div className="absolute inset-0 bg-slate-100 animate-pulse" />}

        {!loading && (!data || !filtered.length || total === 0) ? (
          <div className="h-full flex items-center justify-center text-slate-400">
            No responses for this selection.
          </div>
        ) : (
          <Plot
            data={[
              {
                labels,
                values,
                type: "pie" as const,
                sort: false,
                text: labels,              // full labels; uniformtext handles overflow
                textinfo: "text+percent",
                textposition: "inside",
                insidetextorientation: "auto",
                hovertemplate:
                  `<b>%{label}</b><br>Responses: <b>%{value}</b><br>Share: <b>%{percent}</b><extra></extra>`,
                marker: {
                  colors,
                  line: { color: "#ffffff", width: 2 },
                },
                textfont: { size: 12 },
              },
            ]}
            layout={{
              title: {
                text: "Interest in learning more about AI (teaching & research)",
                font: { size: pieTitleSize, color: "#334155" },
                xref: "paper",
                x: 0.0,
                y: 1.05,
              },
              showlegend: true,
              legend: {
                orientation: "h",
                x: 0.07,
                font: { color: "#334155", size: 13 },
                bgcolor: "rgba(255,255,255,0.7)",
                bordercolor: "#e2e8f0",
                borderwidth: 1,
              },
              uniformtext: { mode: "hide", minsize: 10 },
              margin: { t: 70, l: 20, r: 20, b: 10 },
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

export default TrainingInterestPie;
