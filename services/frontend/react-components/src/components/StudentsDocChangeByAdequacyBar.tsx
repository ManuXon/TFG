import React, { useEffect, useState } from "react";
import Plot from "react-plotly.js";

type APIShape = {
  adequacy_bins: string[];
  series: { name: string; values: number[] }[];
  totals_by_bin: number[];
};

const StudentsDocChangeByAdequacyBar: React.FC<{ facultyName: string }> = ({ facultyName }) => {
  const [data, setData] = useState<APIShape | null>(null);
  const [winW, setWinW] = useState<number>(typeof window !== "undefined" ? window.innerWidth : 1024);

  // NEW: filters (same as other components)
  const [gender, setGender] = useState<string>("All");
  const [experience, setExperience] = useState<string | null>(null);
  const [profile, setProfile] = useState<string | null>(null);

  useEffect(() => {
    const onResize = () => setWinW(window.innerWidth);
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  useEffect(() => {
    const params = new URLSearchParams();
    if (gender && gender !== "All") params.append("gender", gender);
    if (experience) params.append("experience", experience);
    if (profile) params.append("profile", profile);

    const url = `http://localhost:8000/api/faculty/${encodeURIComponent(
      facultyName
    )}/students-docchange-by-adequacy${params.toString() ? `?${params.toString()}` : ""}`;

    fetch(url, { cache: "no-store" })
      .then((r) => r.json())
      .then((json) => setData(json))
      .catch(() => setData({ adequacy_bins: [], series: [], totals_by_bin: [] }));
  }, [facultyName, gender, experience, profile]);

  if (!data) return <p className="text-gray-500">Loading correlation…</p>;
  if (!data.adequacy_bins.length || !data.series.length) {
    return (
      <div>
        {/* Filters stay visible even if there’s no data */}
        <div className="flex flex-wrap justify-center gap-2 mb-4">
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
        </div>

        <p className="text-slate-500 text-center">No data for this faculty.</p>
      </div>
    );
  }

  const lt740 = winW < 740;
  const titleSize = lt740 ? 14 : 18;
  const legendSize = lt740 ? 11 : 13;

  // Purple-ish palette (8 options max)
  const colors = ["#4c1d95","#5b21b6","#6d28d9","#7e22ce","#8b5cf6","#a78bfa","#c4b5fd","#ddd6fe"];

  const traces = data.series.map((s, i) => ({
    x: data.adequacy_bins,
    y: s.values,
    name: s.name,
    type: "bar" as const,
    marker: { color: colors[i % colors.length] },
    customdata: s.values.map((v, idx) => {
      const total = data.totals_by_bin[idx] || 0;
      const pct = total > 0 ? (v / total) * 100 : 0;
      return [pct];
    }),
    hovertemplate:
      `<b>%{x}</b><br>` +
      `Change: <b>${s.name}</b><br>` +
      `Count: <b>%{y}</b><br>` +
      `Share of bin: <b>%{customdata[0]:.1f}%</b><extra></extra>`,
  }));

  return (
    <div>
      {/* Filters */}
      <div className="flex flex-wrap justify-center gap-2 mb-4">
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
      </div>

      <Plot
        data={traces}
        layout={{
          barmode: "stack",
          title: {
            text: "Are there any course changes? (grouped by perceived adequacy)",
            font: { size: titleSize, color: "#334155" }
          },
          xaxis: { tickfont: { size: 11 } },
          yaxis: { title: { text: "Number of responses" }, rangemode: "tozero" },
          legend: {
            orientation: "h",
            y: -0.25,
            x: 0.11,
            font: { size: legendSize },
            bordercolor: "#e2e8f0",
            borderwidth: 1
          },
          margin: { t: 70, l: 55, r: 20, b: 90 },
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
    </div>
  );
};

export default StudentsDocChangeByAdequacyBar;
