import React, { useEffect, useMemo, useState } from "react";
import Plot from "react-plotly.js";

type APIResp = {
  categories: string[];
  values: number[];
  domain: string;
  total: number;
};

const LEVEL_ORDER = ["Strongly disagree", "Disagree", "Agree", "Strongly agree"] as const;

const COLOR_BY_LABEL: Record<string, string> = {
  "Strongly disagree": "#f0fdf4",
  "Disagree":          "#bbf7d0",
  "Agree":             "#34d399",
  "Strongly agree":    "#065f46",
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

const PerceptionsTasksSupportPie: React.FC<{
  facultyName: string;
  facultyColor?: string;
}> = ({ facultyName, facultyColor = "#15803d" }) => {
  const [domain, setDomain] = useState<"teaching" | "research">("teaching");
  const [data, setData] = useState<APIResp | null>(null);
  const [loading, setLoading] = useState(false);

  const [gender, setGender] = useState<string>("All");
  const [experience, setExperience] = useState<string | null>(null);
  const [profile, setProfile] = useState<string | null>(null);

  const winW = useWindowWidth();
  const lt670 = winW < 670;
  const lt600 = winW < 600;
  const pieTitleSize = lt600 ? 12 : lt670 ? 13 : 16;

  useEffect(() => {
    setLoading(true);
    const params = new URLSearchParams({ domain });
    if (gender && gender !== "All") params.append("gender", gender);
    if (experience) params.append("experience", experience);
    if (profile) params.append("profile", profile);

    fetch(
      `http://localhost:8000/api/faculty/${encodeURIComponent(
        facultyName
      )}/perceptions-tasks-support-distribution?${params.toString()}`,
      { cache: "no-store" }
    )
      .then((r) => r.json())
      .then((json: APIResp) => setData(json))
      .catch(() =>
        setData({ categories: [], values: [], domain: "", total: 0 })
      )
      .finally(() => setLoading(false));
  }, [facultyName, domain, gender, experience, profile]);

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
          (a, b) =>
            LEVEL_ORDER.indexOf(a.label as any) -
            LEVEL_ORDER.indexOf(b.label as any)
        ),
    [tuples]
  );

  const labels = filtered.map((t) => t.label);
  const values = filtered.map((t) => t.value);
  const colors = labels.map((l) => COLOR_BY_LABEL[l] ?? "#86efac");
  const sliceText = labels; // full labels (uniformtext hides if too small)
  const total = values.reduce((s, v) => s + (v || 0), 0);

  return (
    <div className="w-full">
      {/* Toggle */}
      <div className="flex justify-center mb-2">
        <div className="inline-flex rounded-md border border-slate-300 bg-white shadow-sm overflow-hidden">
          <button
            onClick={() => setDomain("teaching")}
            className={`px-3 py-1.5 text-sm ${
              domain === "teaching"
                ? "bg-emerald-50 text-emerald-700"
                : "text-slate-600 hover:bg-slate-50"
            }`}
          >
            Teaching tasks
          </button>
          <button
            onClick={() => setDomain("research")}
            className={`px-3 py-1.5 text-sm border-l border-slate-300 ${
              domain === "research"
                ? "bg-emerald-50 text-emerald-700"
                : "text-slate-600 hover:bg-slate-50"
            }`}
          >
            Research tasks
          </button>
        </div>
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
                text: sliceText,
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
                text:
                  domain === "teaching"
                    ? "Does AI enrich/support your teaching tasks?"
                    : "Does AI enrich/support your research tasks?",
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
            style={{ width: "100%", height: "100%" }}
            config={{ displayModeBar: false }}
          />
        )}
      </div>
    </div>
  );
};

export default PerceptionsTasksSupportPie;
