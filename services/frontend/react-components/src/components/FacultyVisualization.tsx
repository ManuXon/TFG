import React, { useState, useEffect, useCallback } from 'react';
import {
  ChevronDown, ChevronUp,
  BookOpen, Users, Eye, GraduationCap,
  Palette, Microscope, Globe, Scale, TrendingUp, Pill, MessageSquare,
  Brain, Atom, Map as MapIcon, Video, Heart, Calculator, Stethoscope, FlaskConical,
} from "lucide-react";
import UsesFunctionalityChart from "./UsesFunctionalityChart";
import UsesBarChart from "./UsesBarChart";
import ProposesPieChart from "./ProposesPieChart";
import UsesApplicationsWordCloud from "./UsesApplicationsWordCloud";
import KnowledgeApplicationsWordCloud from "./KnowledgeApplicationsWordCloud";
import UsesStudentsFunctionalityChart from "./UsesStudentsFunctionalityChart";
import UsesStudentsAdequacyPieChart from "./UsesStudentsAdequacyPieChart";
import StudentsDocChangeByAdequacyBar from "./StudentsDocChangeByAdequacyBar";
import PerceptionsPrioritiesSpider from "./PerceptionsPrioritiesSpider";
import ToolsWordCloud from "./ToolsWordCloud";
import PerceptionsStudentsUsesBar from "./PerceptionsStudentsUsesBar";
import PerceptionsStudentsAttitudesBar from "./PerceptionsStudentsAttitudesBar";
import PerceptionsTasksSupportPie from "./PerceptionsTasksSupportPie";
import PerceptionsProfAttitudeSpider from "./PerceptionsProfAttitudeSpider";
import PerceptionsOpportunitiesRisksBar from "./PerceptionsOpportunitiesRisksBar";
import TrainingReceivedSpider from "./TrainingReceivedSpider";
import TrainingInterestPie from "./TrainingInterestPie";
import TrainingNeedsBar from "./TrainingNeedsBar";





import Plot from 'react-plotly.js';

/* -------------------------------------------------
   small util hook: current window width (for breakpoints)
------------------------------------------------- */
function useWindowWidth() {
  const [w, setW] = useState<number>(() =>
    typeof window !== "undefined" ? window.innerWidth : 1024
  );

  useEffect(() => {
    const onResize = () => setW(window.innerWidth);
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  return w;
}

/** ---------- Minimal gradient progress bar (masked; lg & sm) ---------- */
const ScoreBar: React.FC<{ score: number; size?: 'lg' | 'sm' }> = ({ score, size = 'lg' }) => {
  const pct = Math.max(0, Math.min(100, Number.isFinite(score) ? score : 0));
  const gradient =
    "linear-gradient(90deg," +
    "#7f1d1d 0%," +
    "#b91c1c 8%," +
    "#ef4444 18%," +
    "#f97316 34%," +
    "#f59e0b 50%," +
    "#facc15 66%," +
    "#a3e635 83%," +
    "#22c55e 100%)";

  const dims =
    size === 'sm'
      ? { h: 'h-3.5', w: 'w-[16rem] md:w-[20rem] xl:w-[40rem]' }
      : { h: 'h-4',   w: 'w-[26rem] md:w-[34rem] xl:w-[50rem]' };

  return (
    <div
      className="flex items-center select-none"
      role="progressbar"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={Math.round(pct)}
      aria-label="Score"
    >
      <div
        className={`relative ${dims.h} ${dims.w} rounded-full ring-1 ring-slate-300 shadow-inner overflow-hidden bg-slate-200/70`}
        style={{ background: gradient }}
      >
        <div
          className="absolute inset-y-0 right-0 bg-slate-200/85 transition-all duration-500 ease-out"
          style={{ width: `${100 - pct}%` }}
        />
        <div
          className="pointer-events-none absolute inset-0"
          style={{
            background:
              "linear-gradient(180deg, rgba(255,255,255,0.50) 0%, rgba(255,255,255,0.14) 45%, rgba(255,255,255,0) 100%)",
          }}
        />
        <div className="pointer-events-none absolute inset-0 ring-1 ring-black/5 rounded-full" />
      </div>
    </div>
  );
};
/** ------------------------------------------------------------------- */

/** ---------- Compact "scoreboard" total display (square) ---------- */
const TotalScoreBoard: React.FC<{ score: number | null; label?: string }> = ({
  score,
  label = "Overall",
}) => {
  const pct = Math.max(
    0,
    Math.min(100, Number.isFinite(score as number) ? (score as number) : 0)
  );

  // Color based on score ranges
  const getScoreColor = (score: number): string => {
    if (score >= 80) return '#22c55e'; // green
    if (score >= 60) return '#84cc16'; // lime
    if (score >= 40) return '#eab308'; // yellow
    if (score >= 20) return '#f97316'; // orange
    return '#ef4444'; // red
  };

  const scoreColor = getScoreColor(pct);

  return (
    <div className="flex items-center gap-3" style={{ marginRight: '5px' }}>
      <div className="text-right">
        <p className="text-xs text-slate-500 font-medium uppercase tracking-wide">{label}</p>
      </div>
      <div
        className="px-6 py-3 rounded-full shadow-lg flex items-center gap-3 transition-all duration-300 hover:scale-105"
        role="img"
        aria-label={`${label} score ${pct} out of 100`}
        style={{
          backgroundColor: `${scoreColor}20`,
          borderWidth: '2px',
          borderStyle: 'solid',
          borderColor: scoreColor,
        }}
      >
        <div className="flex items-baseline gap-1">
          <span className="text-3xl font-bold" style={{ color: scoreColor }}>
            {Math.round(pct)}
          </span>
          <span
            className="text-sm font-medium opacity-70"
            style={{ color: scoreColor }}
          >
            /100
          </span>
        </div>
        <div
          className="w-2 h-2 rounded-full animate-pulse"
          style={{ backgroundColor: scoreColor }}
        />
      </div>
    </div>
  );
};
/** ------------------------------------------------------------------- */

// -------------------------
// Types
// -------------------------
interface Faculty {
  name: string;
  color: string;
}

interface DataArea {
  name: string;
  color: string;
  icon: React.ReactNode;
  description: string;
}

type FacultyScores = {
  knowledge_score: number | null;
  uses_score: number | null;
  perceptions_score: number | null;
  training_needs_score: number | null;
  total_score: number | null;
};

// -------------------------
// Data Areas Definition
// -------------------------
const dataAreas: DataArea[] = [
  {
    name: 'Knowledge',
    color: '#b91c1c',
    icon: <BookOpen className="w-6 h-6" />,
    description: 'Academic knowledge and research data',
  },
  {
    name: 'Uses',
    color: '#6b21a8',
    icon: <Users className="w-6 h-6" />,
    description: 'Usage patterns and behavioral analytics',
  },
  {
    name: 'Perceptions',
    color: '#15803d',
    icon: <Eye className="w-6 h-6" />,
    description: 'Student and faculty perceptions',
  },
  {
    name: 'Training',
    color: '#b45309',
    icon: <GraduationCap className="w-6 h-6" />,
    description: 'Training programs and development',
  },
];

// Canonical faculty name → icon
const facultyIconMap = {
  "Fine Arts": Palette,
  "Biology": Microscope,
  "Earth Sciences": Globe,
  "Law": Scale,
  "Economics and Business": TrendingUp,
  "Education": BookOpen,
  "Pharmacy": Pill,
  "Philology": MessageSquare,
  "Philosophy": Brain,
  "Physics": Atom,
  "Geography and History": MapIcon,
  "Audiovisual Media": Video,
  "Nursing": Heart,
  "Maths and CS": Calculator,
  "Medicine": Stethoscope,
  "Psychology": Users,
  "Chemistry": FlaskConical,
} as const;

type FacultyIconKey = keyof typeof facultyIconMap;
const norm = (s: string) =>
  s.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
const facultyIconMapLC: Record<
  string,
  (typeof facultyIconMap)[FacultyIconKey]
> = Object.fromEntries(
  (Object.entries(facultyIconMap) as [
    FacultyIconKey,
    (typeof facultyIconMap)[FacultyIconKey]
  ][]).map(([k, v]) => [norm(k), v])
);
const pickFacultyIcon = (facultyName: string) =>
  facultyIconMapLC[norm(facultyName)] || Globe;

const API_BASE = "http://localhost:8000";

// -------------------------
// Knowledge Bar Chart
// -------------------------
const KnowledgeBarChart = ({ facultyName }: { facultyName: string }) => {
  const [selected, setSelected] = useState<string[]>(["gender", "experience"]);
  const [data, setData] = useState<any | null>(null);

  const winW = useWindowWidth();
  const lt684 = winW < 684;

  // responsive sizes for title + legend (bar chart rule <684px)
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
      ? `http://localhost:8000/api/faculty/${facultyName}/knowledge-distribution?demographic1=${d1}&demographic2=${d2}`
      : `http://localhost:8000/api/faculty/${facultyName}/knowledge-distribution?demographic1=${d1}`;

    fetch(url)
      .then((res) => res.json())
      .then(setData)
      .catch((err) =>
        console.error("Error fetching knowledge data:", err)
      );
  }, [facultyName, selected]);

  if (!data) return <p className="text-gray-500">Loading knowledge data...</p>;

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
                className="accent-red-600 w-4 h-4 cursor-pointer"
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
              marker: { color: "#b91c1c", opacity: 0.9 },
              text: data.values.map((v: number) => v.toFixed(1)),
              textposition: "auto",
              hovertemplate:
                `<b>%{x}</b><br>Avg Knowledge Score: <b>%{y:.2f}</b><extra></extra>`,
            },
          ]}
          layout={{
            title: {
              text: `Knowledge Score by ${data.demographics[0]}`,
              font: { size: barTitleSize, color: "#334155" },
              y: 0.95,
            },
            xaxis: {
              title: `${data.demographics[0]} categories`,
              tickfont: { size: 10 },
            },
            yaxis: {
              title: {
                text: "Avg Knowledge Score (1–4)",
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

  const mainGroups = Array.from(
    new Set(data.data.map((d: any) => d.main))
  ) as string[];
  const subGroups = Array.from(
    new Set(data.data.map((d: any) => d.sub))
  ) as string[];
  const mainAvgMap: Record<string, number> = {};
  data.data.forEach((r: any) => {
    if (mainAvgMap[r.main] == null) mainAvgMap[r.main] = r.main_avg;
  });

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
        color: ["#dc2626", "#f87171", "#fb923c", "#fde68a", "#7f1d1d"][
          idx % 5
        ],
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
              className="accent-red-600 w-4 h-4 cursor-pointer"
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
            text: `Knowledge Score by: ${data.demographics[0]} × ${data.demographics[1]}`,
            font: { size: barTitleSize, color: "#334155" },
            y: 0.95,
          },
          xaxis: { title: data.demographics[0], tickfont: { size: 10 } },
          yaxis: {
            title: { text: "Avg Knowledge Score (1–4)" },
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

// -------------------------
// Normative Pie Chart
// -------------------------
const NormativePieChart = ({ facultyName }: { facultyName: string }) => {
  const [data, setData] = useState<{
    categories: string[];
    values: number[];
  } | null>(null);

  const winW = useWindowWidth();
  const lt670 = winW < 670;
  const lt600 = winW < 600;

  const pieTitleSize = lt600 ? 14
                    : lt670 ? 15
                            : 18;

  useEffect(() => {
    fetch(
      `http://localhost:8000/api/faculty/${facultyName}/normative-distribution`
    )
      .then((res) => res.json())
      .then(setData)
      .catch((err) =>
        console.error("Error fetching normative data:", err)
      );
  }, [facultyName]);

  if (!data) return <p className="text-gray-500">Loading normative data...</p>;

  const shortLabels: Record<string, string> = {
    "Yes, there is a guide or normative": "Yes",
    "I ignore if there's a guide or normative": "Don't know",
    "There is no guide or normative": "No",
  };
  const displayLabels = data.categories.map(
    (cat) => shortLabels[cat] || cat
  );

  return (
    <Plot
      data={[
        {
          labels: displayLabels,
          values: data.values,
          type: "pie",
          textinfo: "label+percent",
          hovertemplate:
            `<b>%{label}</b><br>Responses: <b>%{value}</b><br>Share: <b>%{percent}</b><extra></extra>`,
          marker: {
            colors: ["#dc2626", "#f87171", "#fb923c", "#fde68a"],
            line: { color: "#ffffff", width: 2 },
          },
        },
      ]}
      layout={{
        title: {
          text: "Is there any guide or normative at UB?",
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

// -------------------------
// Interest-Knowledge Chart (With Toggle)
// -------------------------
const KnowledgeFunctionalityChart: React.FC<{
  facultyName: string;
  facultyColor: string; // passed in from parent
}> = ({ facultyName, facultyColor }) => {
  const [chartType, setChartType] = useState<'bar' | 'heatmap' | 'radar'>(
    'radar'
  );
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
  const radarLegendSize   = lt740 ? 12 : 14;
  const radarTickFontSize = lt740 ? 10 : 13;

  // RGBA helper for tinted "no data"
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
      let r = 0, g = 0, b = 0;
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
      )}/knowledge-functionality-correlation?${params.toString()}`,
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

  // Static labels (match backend order)
  const funcLabels = [
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
  ];

  // Derived only when there is data
  const knowledgeLabels = data.map((d) => d.knowledge_label);
  const matrix = data.map((d) =>
    funcLabels.map((_, i) => Object.values(d)[i + 1])
  );

  const colorPalette = [
    "#7f1d1d",
    "#991b1b",
    "#b91c1c",
    "#dc2626",
    "#ef4444",
    "#f87171",
    "#fb923c",
    "#fdba74",
    "#fde68a",
    "#fef08a",
    "#a16207",
    "#78350f",
    "#451a03",
  ];

  return (
    <div>
      {/* Filters ALWAYS visible */}
      <div className="flex flex-wrap justify-center gap-2 mb-4">
        <select
          value={gender}
          onChange={(e) => setGender(e.target.value)}
          className="border border-slate-300 rounded-md px-3 py-1 text-slate-700 text-sm shadow-sm hover:border-slate-400 focus:outline-none focus:ring-2 focus:ring-red-200 transition"
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
          className="border border-slate-300 rounded-md px-3 py-1 text-slate-700 text-sm shadow-sm hover:border-slate-400 focus:outline-none focus:ring-2 focus:ring-red-200 transition"
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
          className="border border-slate-300 rounded-md px-3 py-1 text-slate-700 text-sm shadow-sm hover:border-slate-400 focus:outline-none focus:ring-2 focus:ring-red-200 transition"
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
          value={chartType}
          onChange={(e) => setChartType(e.target.value as any)}
          className="border border-slate-300 rounded-md px-3 py-1 text-slate-700 text-sm shadow-sm hover:border-slate-400 focus:outline-none focus:ring-2 focus:ring-red-200 transition"
        >
          <option value="bar">Grouped Bar</option>
          <option value="heatmap">Heatmap</option>
          <option value="radar">Spider</option>
        </select>
      </div>

      {/* Chart Area */}
      <div className="relative w-full h-[600px] rounded-xl border border-slate-200 bg-white overflow-hidden">
        {loading && (
          <div className="absolute inset-0 bg-slate-100 animate-pulse" />
        )}

        {!loading && noData && (
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

        {!loading && !noData && (
          <>
            {chartType === "bar" && (
              <Plot
                data={funcLabels.map((label, i) => ({
                  x: knowledgeLabels,
                  y: data.map((d) => Object.values(d)[i + 1]),
                  name: label,
                  type: "bar",
                  orientation: "v",
                  marker: {
                    color: colorPalette[i % colorPalette.length],
                  },
                  hovertemplate:
                    `<b>IA Knowledge:</b> %{x}<br><b>${label}:</b> %{y:.2f}<extra></extra>`,
                }))}
                layout={{
                  barmode: "group",
                  title: {
                    text: "Whats the knowledge within applications?",
                    y: 0.96,
                    font: { size: barTitleSize },
                  },
                  xaxis: {
                    categoryorder: "array",
                    categoryarray: [
                      "No knowledge",
                      "Little knowledge",
                      "Good knowledge",
                      "Expert knowledge",
                    ],
                    tickfont: { size: radarTickFontSize },
                  },
                  yaxis: {
                    title: { text: "Avg Application Familiarity (1–4)" },
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
                style={{ width: "100%", height: "100%" }}
                config={{ displayModeBar: false }}
              />
            )}

            {chartType === "heatmap" && (
              <Plot
                data={[
                  {
                    z: matrix,
                    x: funcLabels,
                    y: knowledgeLabels,
                    type: "heatmap",
                    colorscale: "Reds",
                    colorbar: { title: { text: "Familiarity" } },
                    hovertemplate:
                      `<b>IA Knowledge:</b> %{y}` +
                      `<br><b>Functionality:</b> %{x}` +
                      `<br><b>Avg Familiarity:</b> %{z:.2f}<extra></extra>`,
                  },
                ]}
                layout={{
                  title: {
                    text: "Whats the knowledge within applications?",
                    y: 0.96,
                    font: { size: barTitleSize },
                  },
                  y: 1.0,
                  yaxis: {
                    autorange: "reversed",
                    tickfont: { size: radarTickFontSize },
                  },
                  xaxis: { tickfont: { size: 11 } },
                  // ADDED right margin + using 95% width in style below
                  margin: { t: 110, l: 135, r: 0, b: 110 },
                  paper_bgcolor: "rgba(0,0,0,0)",
                  plot_bgcolor: "rgba(0,0,0,0)",
                  font: { color: "#334155" },
                }}
                config={{ displayModeBar: false }}
                style={{ width: "95%", height: "100%" }}
              />
            )}

            {chartType === "radar" && (
              <Plot
                data={data.map((d, i) => {
                  const radarColors: Record<string, string> = {
                    "No knowledge": "#b91c1c",
                    "Little knowledge": "#fa7112",
                    "Good knowledge": "#fd9c49",
                    "Expert knowledge": "#fac681",
                  };
                  const color =
                    radarColors[d.knowledge_label] || "#b91c1c";
                  return {
                    type: "scatterpolar" as const,
                    r: matrix[i].concat(matrix[i][0]),
                    theta: funcLabels.concat(funcLabels[0]),
                    fill: "toself",
                    name: d.knowledge_label,
                    line: { color, width: 3 },
                    fillcolor: color + "40",
                    hovertemplate:
                      `<b>%{theta}</b><br>Knowledge Level: <b>${d.knowledge_label}</b>` +
                      `<br>Avg Familiarity: %{r:.2f}<extra></extra>`,
                  };
                })}
                layout={{
                  title: {
                    text: "Whats the knowledge within applications?",
                    font: { size: barTitleSize, color: "#334155" },
                    y: 0.96,
                  },
                  polar: {
                    bgcolor: "rgba(0,0,0,0)",
                    radialaxis: {
                      visible: false,
                      showline: false,
                      range: [0, 4],
                      gridcolor: "#f1f5f9",
                      gridwidth: 1.3,
                      tickfont: { color: "#475569", size: 11 },
                      tickangle: 0,
                      ticksuffix: " ",
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
                      text: "AI Knowledge level",
                      font: { color: "#334155", size: radarLegendSize },
                    },
                    orientation: "v",
                    y: 1,
                    x: -0.04,
                    xanchor: "left",
                    font: { color: "#334155", size: radarLegendSize },
                    bordercolor: "#e2e8f0",
                    borderwidth: 1,
                  },
                  margin: { t: 90, l: 80, r: 40, b: 40 },
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

// -------------------------
// Faculty Visualization Layout
// -------------------------
const FacultyVisualization: React.FC<{
  faculty: Faculty;
  onBack: () => void;
}> = ({ faculty, onBack }) => {
  const [expandedAreas, setExpandedAreas] = useState<Set<string>>(
    new Set([''])
  );
  const [scores, setScores] = useState<FacultyScores | null>(null);
  const [loadingScores, setLoadingScores] = useState<boolean>(true);

  useEffect(() => {
    let cancelled = false;
    setLoadingScores(true);
    fetch(
      `${API_BASE}/api/faculty/${encodeURIComponent(
        faculty.name
      )}/scores`,
      { cache: "no-store" }
    )
      .then((res) => res.json())
      .then((data) => {
        if (!cancelled) setScores(data as FacultyScores);
      })
      .catch(() => {
        if (!cancelled) setScores(null);
      })
      .finally(() => {
        if (!cancelled) setLoadingScores(false);
      });
    return () => {
      cancelled = true;
    };
  }, [faculty.name]);

  const toggleArea = (areaName: string) => {
    setExpandedAreas((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(areaName)) newSet.delete(areaName);
      else newSet.add(areaName);
      return newSet;
    });
  };

  const areaScore = (areaName: string) => {
    if (!scores) return null;
    if (areaName === 'Knowledge') return scores.knowledge_score;
    if (areaName === 'Uses') return scores.uses_score;
    if (areaName === 'Perceptions') return scores.perceptions_score;
    if (areaName === 'Training') return scores.training_needs_score;
    return null;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 py-8 px-4">
      <div className="max-w-7xl mx-auto">
        <button
          onClick={onBack}
          className="mb-6 px-4 py-2 bg-white rounded-lg shadow-sm border border-slate-200 text-slate-600 hover:text-slate-800 hover:shadow-md transition-all duration-200"
        >
          ← Back to Faculty Selection
        </button>

        <div
          className="bg-white rounded-3xl shadow-lg scroll"
          style={{
            borderWidth: '3px',
            borderStyle: 'solid',
            borderColor: faculty.color,
          }}
        >
          {/* Header */}
          <div className="p-8 border-b border-slate-200">
            <div className="flex items-center justify-between gap-4 flex-wrap">
              {/* Left: icon + title */}
              <div className="flex items-center gap-4 min-w-0">
                <div
                  className="p-4 rounded-xl shadow-sm shrink-0"
                  style={{ backgroundColor: `${faculty.color}20` }}
                  title={faculty.name}
                >
                  {(() => {
                    const Icon = pickFacultyIcon(faculty.name);
                    return (
                      <Icon
                        className="w-12 h-12"
                        style={{ color: faculty.color }}
                      />
                    );
                  })()}
                </div>

                <div className="min-w-0">
                  <h1 className="text-3xl font-normal text-slate-800 truncate">
                    {faculty.name}
                  </h1>
                  <p className="text-slate-500 text-sm mt-1">
                    Data Visualizations & Analytics
                  </p>
                </div>
              </div>

              {/* Right: badge scoreboard */}
              <div className="ml-auto">
                {loadingScores ? (
                  <div className="w-[7.5rem] h-[7.5rem] md:w-[8.5rem] md:h-[8.5rem] rounded-2xl bg-slate-100 ring-1 ring-slate-200 animate-pulse" />
                ) : scores?.total_score != null ? (
                  <TotalScoreBoard score={scores.total_score} />
                ) : null}
              </div>
            </div>
          </div>

          {/* Body */}
          <div className="p-6 space-y-4">
            {dataAreas.map((area) => {
              const isExpanded = expandedAreas.has(area.name);
              const thisScore = areaScore(area.name);

              return (
                <div
                  key={area.name}
                  className="rounded-2xl overflow-hidden transition-all duration-300"
                  style={{
                    borderWidth: '2px',
                    borderStyle: 'solid',
                    borderColor: area.color,
                    backgroundColor: isExpanded ? '#ffffff' : '#fafafa',
                  }}
                >
                  {/* Section header */}
                  <button
                    onClick={() => toggleArea(area.name)}
                    className="w-full p-6 hover:bg-slate-50 transition-colors duration-200 text-left"
                  >
                    <div className="grid items-center gap-4 md:gap-6 grid-cols-[auto_minmax(11rem,36rem)_minmax(18rem,24rem)_1fr_auto] lg:grid-cols-[auto_minmax(8rem,40rem)_minmax(30rem,44rem)_1fr_auto]">
                      <div
                        className="p-3 rounded-xl text-white shadow-md shrink-0"
                        style={{ backgroundColor: area.color }}
                      >
                        {area.icon}
                      </div>
                      <div className="text-left max-w-[16rem] lg:max-w-[16rem]">
                        <h2 className="text-2xl font-medium text-slate-800">
                          {area.name}
                        </h2>
                        <p className="text-slate-500 text-sm mt-1">
                          {area.description}
                        </p>
                      </div>

                      {/* Section score bars */}
                      <div className="hidden md:flex justify-start">
                        {loadingScores ? (
                          <div className="h-3.5 w-[20rem] lg:w-[24rem] rounded-full bg-slate-100 ring-1 ring-slate-300 animate-pulse" />
                        ) : thisScore != null ? (
                          <ScoreBar score={thisScore} size="sm" />
                        ) : null}
                      </div>

                      <div className="hidden md:block" />
                      <div
                        className="justify-self-end p-2 rounded-lg transition-colors duration-200"
                        style={{
                          backgroundColor: isExpanded
                            ? `${area.color}15`
                            : 'transparent',
                        }}
                      >
                        {isExpanded ? (
                          <ChevronUp
                            className="w-6 h-6"
                            style={{ color: area.color }}
                          />
                        ) : (
                          <ChevronDown className="w-6 h-6 text-slate-400" />
                        )}
                      </div>
                    </div>
                  </button>

                  {/* Section content */}
                  <div
                    className={`transition-all duration-300 ease-in-out overflow-hidden ${
                      isExpanded
                        ? 'opacity-100'
                        : 'max-h-0 opacity-0'
                    }`}
                  >
                    <div
                      className="p-6 border-t"
                      style={{ borderColor: `${area.color}30` }}
                    >
                      <div className="min-h-[400px] bg-slate-50 rounded-xl p-8 border-2 border-dashed border-slate-200">
                        {area.name === 'Knowledge' ? (
                        <>
                          <div className="flex flex-col gap-6">
                            <div className="bg-white rounded-xl p-4 shadow-sm border border-slate-200">
                              <KnowledgeFunctionalityChart
                                facultyName={faculty.name}
                                facultyColor={faculty.color}
                              />
                            </div>

                            <div className="flex flex-col lg:flex-row gap-6">
                              <div className="lg:w-3/5 bg-white rounded-xl p-4 shadow-sm border border-slate-200">
                                <KnowledgeBarChart facultyName={faculty.name} />
                              </div>

                              <div className="lg:w-2/5 bg-white rounded-xl p-4 shadow-sm border border-slate-200">
                                <NormativePieChart facultyName={faculty.name} />
                              </div>
                            </div>
                          </div>

                          {/* Wordcloud hidden on <768px */}
                          <div className="mt-6 hidden md:block bg-white rounded-xl p-6 shadow-sm border border-slate-200 w-full">
                            <KnowledgeApplicationsWordCloud
                              facultyName={faculty.name}
                              facultyColor={faculty.color}
                            />
                          </div>
                        </>
                      ) : area.name === 'Uses' ? (
                        <>
                          <div className="flex flex-col gap-6">
                            <div className="bg-white rounded-xl p-4 shadow-sm border border-slate-200">
                              <UsesFunctionalityChart
                                facultyName={faculty.name}
                                facultyColor={faculty.color}
                              />
                            </div>
                            {/* Wordcloud hidden on <768px */}
                            <div className="mt-6 hidden md:block bg-white rounded-xl p-6 shadow-sm border border-slate-200 w-full">
                              <UsesApplicationsWordCloud
                                facultyName={faculty.name}
                                facultyColor={faculty.color}
                              />
                            </div>

                            <div className="flex flex-col lg:flex-row gap-6">
                              <div className="lg:w-3/5 bg-white rounded-xl p-4 shadow-sm border border-slate-200">
                                <UsesBarChart facultyName={faculty.name} />
                              </div>

                              <div className="lg:w-2/5 bg-white rounded-xl p-4 shadow-sm border border-slate-200">
                                <ProposesPieChart facultyName={faculty.name} />
                              </div>
                            </div>
                            {/* Students uses by proposal (same logic as UsesFunctionalityChart) */}
                          <div className="mt-6 bg-white rounded-xl p-4 shadow-sm border border-slate-200">
                            <UsesStudentsFunctionalityChart
                              facultyName={faculty.name}
                              facultyColor={faculty.color}
                            />
                          </div>
                            <div className="mt-6 flex flex-col lg:flex-row gap-6">
                              <div className="lg:w-2/5 bg-white rounded-xl p-4 shadow-sm border border-slate-200">
                                <UsesStudentsAdequacyPieChart facultyName={faculty.name} />
                              </div>

                              <div className="lg:w-3/5 bg-white rounded-xl p-4 shadow-sm border border-slate-200">
                                <StudentsDocChangeByAdequacyBar facultyName={faculty.name} />
                              </div>
                            </div>
                          </div>
                          <div className="mt-6 hidden md:block bg-white rounded-xl p-6 shadow-sm border border-slate-200 w-full">
                            <ToolsWordCloud
                              facultyName={faculty.name}
                              facultyColor={faculty.color}
                            />
                          </div>
                        </>
                      ) : area.name === 'Perceptions' ? (
                        <div className="flex flex-col gap-6">
                          <div className="bg-white rounded-xl p-4 shadow-sm border border-slate-200">
                            <PerceptionsPrioritiesSpider
                              facultyName={faculty.name}
                              facultyColor={"#15803d"}   // Perceptions green
                            />
                          </div>
                          <div className="bg-white rounded-xl p-4 shadow-sm border border-slate-200">
                            <PerceptionsStudentsUsesBar
                              facultyName={faculty.name}
                              facultyColor={"#15803d"}
                            />
                          </div>
                          <div className="mt-6 bg-white rounded-xl p-4 shadow-sm border border-slate-200">
                            <PerceptionsStudentsAttitudesBar
                              facultyName={faculty.name}
                              facultyColor="#15803d"
                            />
                          </div>
                          <div className="mt-6 flex flex-col lg:flex-row gap-6">
                            <div className="lg:w-2/5 bg-white rounded-xl p-4 shadow-sm border border-slate-200">
                              <PerceptionsTasksSupportPie facultyName={faculty.name} facultyColor="#15803d" />
                            </div>

                            <div className="lg:w-3/5 bg-white rounded-xl p-4 shadow-sm border border-slate-200">
                              <PerceptionsProfAttitudeSpider facultyName={faculty.name} facultyColor="#15803d" />
                            </div>
                          </div>
                          {/* NEW: Opportunities & Risks stacked bar */}
                          <div className="mt-6 bg-white rounded-xl p-4 shadow-sm border border-slate-200">
                            <PerceptionsOpportunitiesRisksBar
                              facultyName={faculty.name}
                              facultyColor="#15803d"
                            />
                          </div>
                        </div>
                      ) : area.name === 'Training' ? (
                        <div className="flex flex-col gap-6">
                          {/* A: Training received (spider) */}
                          <div className="bg-white rounded-xl p-4 shadow-sm border border-slate-200">
                            <TrainingReceivedSpider facultyName={faculty.name} facultyColor="#b45309" />
                          </div>

                          {/* B: Interest pie (40%) + Needs stacked bar (60%) */}
                          <div className="mt-6 flex flex-col lg:flex-row gap-6">
                            <div className="lg:w-2/5 bg-white rounded-xl p-4 shadow-sm border border-slate-200 min-h-[520px]">
                              <TrainingInterestPie facultyName={faculty.name} facultyColor="#b45309" />
                            </div>
                            <div className="lg:w-3/5 bg-white rounded-xl p-4 shadow-sm border border-slate-200 min-h-[520px]">
                              <TrainingNeedsBar facultyName={faculty.name} facultyColor="#b45309" />
                            </div>
                          </div>
                        </div>
                      ) : null}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          <div
            className="p-6 bg-slate-50 border-t border-slate-200 text-center text-slate-500 text-sm"
            style={{ borderRadius: '23px' }}
          >
            Click on each section to expand and view detailed visualizations
          </div>
        </div>
      </div>
    </div>
  );
};

export default FacultyVisualization;
