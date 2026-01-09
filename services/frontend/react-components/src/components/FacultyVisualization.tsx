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

  const getScoreColor = (score: number): string => {
    if (score >= 80) return '#22c55e';
    if (score >= 60) return '#84cc16';
    if (score >= 40) return '#eab308';
    if (score >= 20) return '#f97316';
    return '#ef4444';
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
  {
    name: 'Comments',
    color: '#0ea5e9',
    icon: <MessageSquare className="w-6 h-6" />,
    description: 'General comments about AI and the survey',
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
                text: "Avg Knowledge Score",
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
            title: { text: "Avg Knowledge Score" },
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
  facultyColor: string;
}> = ({ facultyName, facultyColor }) => {
  const [chartFamily, setChartFamily] =
    useState<"bar" | "heatmap" | "spider">("spider");

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

  const knowledgeLabels = data.map((d) => d.knowledge_label);
  const matrix = data.map((d) =>
    funcLabels.map((_, i) => Object.values(d)[i + 1])
  );

  const maxRadialValue = React.useMemo(() => {
    if (!matrix.length) return 4;

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
    return Math.ceil(globalMax);
  }, [matrix]);

  const groupStats = data.map((d) => ({
    label: d.knowledge_label,
    n: d.n,
    pct: d.pct,
    mean: d.group_mean,
    min: d.group_min,
    max: d.group_max,
  }));

  const canonicalKnowledgeOrder = [
    "No knowledge",
    "Little knowledge",
    "Good knowledge",
    "Expert knowledge",
  ];

  const orderedGroupStats = canonicalKnowledgeOrder
    .map((label) => groupStats.find((g) => g.label === label))
    .filter((g): g is (typeof groupStats)[number] => Boolean(g));

  const totalN = orderedGroupStats.reduce(
    (acc, g) => acc + (typeof g.n === "number" ? g.n : 0),
    0
  );

  const FAMILIARITY_SCALE = 100 / 3;

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

  const radarColors: Record<string, string> = {
    "No knowledge": "#b91c1c",
    "Little knowledge": "#fa7112",
    "Good knowledge": "#fd9c49",
    "Expert knowledge": "#fac681",
  };

  const knowledgeTitleText = "What's the knowledge within applications?";

  const KnowledgeTitleWithTooltip: React.FC<{ label: string }> = ({
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
        <span className="inline-flex items-center justify-center w-4 h-4 text-[11px] rounded-full border border-rose-400 text-rose-600 bg-rose-50 font-semibold cursor-help leading-none">
          ?
        </span>
        <div className="pointer-events-none absolute left-1/2 top-full z-10 hidden w-[320px] -translate-x-1/2 translate-y-2 rounded-md bg-rose-50 px-3 py-2 text-xs text-slate-700 shadow-lg ring-1 ring-rose-200 group-hover:block">
          <p className="font-semibold mb-1 text-rose-900">
            How to read this chart
          </p>
          <p className="mb-1">Original survey questions:</p>
          <ul className="list-disc pl-4 space-y-0.5 mb-2">
            <li>
              <span className="font-medium">
                “Rate your knowledge about AI.”
              </span>{" "}
              Answers range from no knowledge to advanced knowledge.
            </li>
            <li>
              <span className="font-medium">
                “I know AI applications for...”
              </span>{" "}
              for each application shown on the axes.
            </li>
          </ul>
          <p className="mb-1 font-medium">Numeric scale used for averages:</p>
          <ul className="list-disc pl-4 space-y-0.5">
            <li>1 = I don't know any</li>
            <li>2 = I know a few</li>
            <li>3 = I know several</li>
            <li>4 = I know many</li>
          </ul>
        </div>
      </div>
    </div>
  );

  return (
    <div>
      <div className="flex flex-wrap justify-center gap-2 mb-3">
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
          value={chartFamily}
          onChange={(e) =>
            setChartFamily(e.target.value as "bar" | "heatmap" | "spider")
          }
          className="border border-slate-300 rounded-md px-3 py-1 text-slate-700 text-sm shadow-sm hover:border-slate-400 focus:outline-none focus:ring-2 focus:ring-red-200 transition"
        >
          <option value="bar">Grouped Bar</option>
          <option value="heatmap">Heatmap</option>
          <option value="spider">Spider</option>
        </select>
      </div>

      {chartFamily === "spider" && !loading && !noData && (
        <div className="flex justify-center mb-3">
          <div className="inline-flex rounded-lg border border-slate-300 bg-white shadow-sm overflow-hidden">
            <button
              onClick={() => setSpiderMode("area")}
              className={
                "px-3 py-1.5 text-xs md:text-sm " +
                (spiderMode === "area"
                  ? "bg-rose-50 text-rose-700"
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
                  ? "bg-rose-50 text-rose-700"
                  : "text-slate-600 hover:bg-slate-50")
              }
            >
              Spider (bars)
            </button>
          </div>
        </div>
      )}

      <div
        className="relative w-full rounded-xl border border-slate-200 bg-white overflow-hidden flex flex-col"
        style={{ height: chartFamily === "bar" ? "730px" : "600px" }}
      >
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
            {chartFamily === "bar" && (
              <>
                <div className="flex-1 flex flex-col">
                  <KnowledgeTitleWithTooltip label={knowledgeTitleText} />
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
                        `<b>AI Knowledge:</b> %{x}<br><b>${label}:</b> %{y:.2f}<extra></extra>`,
                    }))}
                    layout={{
                      barmode: "group",
                      title: { text: "" },
                      xaxis: {
                        categoryorder: "array",
                        categoryarray: canonicalKnowledgeOrder,
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
                      margin: { t: 40, l: 60, r: 30, b: 80 },
                      paper_bgcolor: "rgba(0,0,0,0)",
                      plot_bgcolor: "rgba(0,0,0,0)",
                    }}
                    style={{ width: "100%", height: "390px" }}
                    config={{ displayModeBar: false }}
                  />
                </div>

                <div className="border-t border-slate-100 px-4 pb-4 pt-2">
                  <Plot
                    data={[
                      {
                        x: orderedGroupStats.map((g) => g.label),
                        y: orderedGroupStats.map((g) => g.pct ?? 0),
                        type: "bar" as const,
                        name: "% of respondents",
                        marker: {
                          color: "#fee2e2",
                          line: { color: "#b91c1c", width: 1 },
                        },
                        customdata: orderedGroupStats.map((g) => g.n ?? 0),
                        hovertemplate:
                          "<b>%{x}</b><br>Share: %{y:.1f}% (n=%{customdata})<extra></extra>",
                      },
                      {
                        x: orderedGroupStats.map((g) => g.label),
                        y: orderedGroupStats.map((g) =>
                          ((g.mean ?? 1) - 1) * FAMILIARITY_SCALE
                        ),
                        type: "scatter" as const,
                        mode: "lines+markers",
                        name: "Avg familiarity (1–4)",
                        yaxis: "y2",
                        line: { color: "#b91c1c", width: 3 },
                        marker: { color: "#b91c1c", size: 7 },
                        error_y: {
                          type: "data",
                          symmetric: false,
                          array: orderedGroupStats.map((g) =>
                            Math.max(
                              0,
                              ((g.max ?? 1) - (g.mean ?? 1)) * FAMILIARITY_SCALE
                            )
                          ),
                          arrayminus: orderedGroupStats.map((g) =>
                            Math.max(
                              0,
                              ((g.mean ?? 1) - (g.min ?? 1)) * FAMILIARITY_SCALE
                            )
                          ),
                          visible: true,
                          thickness: 1.4,
                          width: 5,
                          color: "#b91c1c",
                        },
                        customdata: orderedGroupStats.map((g) => [
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
                        text: "Knowledge group distribution",
                        font: { size: barTitleSize },
                        y: 1,
                      },
                      xaxis: {
                        categoryorder: "array",
                        categoryarray: canonicalKnowledgeOrder,
                        tickfont: { size: radarTickFontSize },
                      },
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
                      yaxis2: {
                        title: { text: "Avg familiarity (1–4)" },
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
                <KnowledgeTitleWithTooltip label={knowledgeTitleText} />
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
                    title: { text: "" },
                    yaxis: {
                      autorange: "reversed",
                      tickfont: { size: radarTickFontSize },
                    },
                    xaxis: { tickfont: { size: 11 } },
                    margin: { t: 40, l: 135, r: 0, b: 110 },
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
                <KnowledgeTitleWithTooltip label={knowledgeTitleText} />
                <Plot
                  data={data.map((d: any, i: number) => {
                    const color = radarColors[d.knowledge_label] || "#b91c1c";

                    const n = d.n ?? 0;
                    const pct = d.pct ?? 0;
                    const mean = d.group_mean ?? 0;
                    const min = d.group_min ?? 0;
                    const max = d.group_max ?? 0;

                    const legendName = [
                      `<span style="font-weight:600">${d.knowledge_label}</span>`,
                      `<span style="font-size:11px; color:#4b5563">n=${n} · ${pct.toFixed(
                        1
                      )}% · μ=${mean.toFixed(2)} [${min.toFixed(
                        2
                      )}–${max.toFixed(2)}]</span>`,
                    ].join("<br>");

                    return {
                      type: "scatterpolar" as const,
                      r: matrix[i].concat(matrix[i][0]),
                      theta: funcLabels.concat(funcLabels[0]),
                      fill: "toself",
                      hoveron: "points",
                      name: legendName,
                      line: { color, width: 3 },
                      fillcolor: color + "40",
                      hovertemplate:
                        `<b>%{theta}</b><br>Knowledge Level: <b>${d.knowledge_label}</b>` +
                        `<br>Avg Familiarity: %{r:.2f}<extra></extra>`,
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
                          text: "Application familiarity",
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
                          `<span style="font-weight:600">AI Knowledge level</span> (total n=${totalN})` +
                          '<br><span style="font-size:11px; font-style:italic">mean / min / max across applications</span>',
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
                <KnowledgeTitleWithTooltip label={knowledgeTitleText} />
                <Plot
                  data={data.map((d: any, i: number) => {
                    const color = radarColors[d.knowledge_label] || "#b91c1c";
                    const rVals = matrix[i];

                    const n = d.n ?? 0;
                    const pct = d.pct ?? 0;
                    const mean = d.group_mean ?? 0;
                    const min = d.group_min ?? 0;
                    const max = d.group_max ?? 0;

                    const legendName = [
                      `<span style="font-weight:600">${d.knowledge_label}</span>`,
                      `<span style="font-size:11px; color:#4b5563">n=${n} · ${pct.toFixed(
                        1
                      )}% · μ=${mean.toFixed(2)} [${min.toFixed(
                        2
                      )}–${max.toFixed(2)}]</span>`,
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
                        `<b>%{theta}</b><br>Knowledge Level: <b>${d.knowledge_label}</b>` +
                        `<br>Avg Familiarity: %{r:.2f}<extra></extra>`,
                    };
                  })}
                  layout={{
                    title: { text: "" },
                    polar: {
                      bgcolor: "rgba(0,0,0,0)",
                      radialaxis: {
                        range: [0, maxRadialValue],
                        visible: false,
                        showline: false,
                        gridcolor: "#f1f5f9",
                        gridwidth: 1.3,
                        showticklabels: false,
                        ticks: "",
                        title: {
                          text: "Application familiarity",
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
                    barmode: "stack",
                    showlegend: true,
                    legend: {
                      title: {
                        text:
                          `<span style="font-weight:600">AI Knowledge level</span> (total n=${totalN})` +
                          '<br><span style="font-size:11px; font-style:italic">mean / min / max across applications</span>',
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

// -------------------------
// Open-text helper pieces
// -------------------------

type SentimentFine =
  | "very_negative"
  | "negative"
  | "mixed"
  | "positive"
  | "very_positive"
  | "neutral";

type OpenTextItem = {
  row_id: number;
  sentiment: "negative" | "neutral" | "positive";
  sentiment_fine: SentimentFine;
  cluster_id: number;
  cluster_label: string;
  main_topics: string[];
  english_text: string;
};

type OpenTextItemsResponse = {
  items: OpenTextItem[];
};

const SENTIMENT_LEVELS: {
  id: SentimentFine;
  label: string;
  color: string;
}[] = [
  { id: "very_negative", label: "Very negative", color: "#b91c1c" },
  { id: "negative", label: "Negative", color: "#f97316" },
  { id: "mixed", label: "Mixed", color: "#0f172a" },
  { id: "positive", label: "Positive", color: "#22c55e" },
  { id: "very_positive", label: "Very positive", color: "#16a34a" },
  { id: "neutral", label: "Neutral", color: "#6b7280" },
];

const DEFAULT_SENTIMENT_INDEX = (() => {
  const idx = SENTIMENT_LEVELS.findIndex((s) => s.id === "mixed");
  return idx >= 0 ? idx : 0;
})();

interface OpenTextBrowserProps {
  facultyName: string;
  endpoint: string;
  title: string;
  accentColor: string;
  subtitle?: string;
}

const OpenTextBrowser: React.FC<OpenTextBrowserProps> = ({
  facultyName,
  endpoint,
  title,
  accentColor,
  subtitle,
}) => {
  const [items, setItems] = useState<OpenTextItem[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const [sentimentIndex, setSentimentIndex] = useState<number>(
    DEFAULT_SENTIMENT_INDEX
  );
  const [selectedCluster, setSelectedCluster] = useState<string>("All");
  const [selectedTopics, setSelectedTopics] = useState<string[]>([]);

  const selectedSentiment: SentimentFine =
    SENTIMENT_LEVELS[sentimentIndex]?.id ??
    SENTIMENT_LEVELS[DEFAULT_SENTIMENT_INDEX].id;

  const sentimentGradient = React.useMemo(() => {
    const n = SENTIMENT_LEVELS.length;
    if (n === 0) return "#e5e7eb";

    const valuePct = (i: number) => (i / (n - 1)) * 100;
    const stops: string[] = [];

    for (let i = 0; i < n; i++) {
      const color = SENTIMENT_LEVELS[i].color;
      const left = i === 0 ? 0 : (valuePct(i - 1) + valuePct(i)) / 2;
      const right = i === n - 1 ? 100 : (valuePct(i) + valuePct(i + 1)) / 2;
      stops.push(`${color} ${left}%`, `${color} ${right}%`);
    }

    return `linear-gradient(to right, ${stops.join(", ")})`;
  }, []);

  useEffect(() => {
    setLoading(true);
    setError(null);

    const params = new URLSearchParams({ faculty: facultyName });

    fetch(`${API_BASE}${endpoint}?${params.toString()}`, { cache: "no-store" })
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((d: OpenTextItemsResponse) => {
        setItems(Array.isArray(d?.items) ? d.items : []);
      })
      .catch((err) => {
        console.error("Error fetching open-text items:", err);
        setError("Error fetching open-text data.");
        setItems([]);
      })
      .finally(() => setLoading(false));
  }, [facultyName, endpoint]);

  const allClusters = React.useMemo(
    () =>
      Array.from(
        new Set(
          items
            .map((it) => it.cluster_label)
            .filter((s) => typeof s === "string" && s.trim().length > 0)
        )
      ).sort((a, b) => a.localeCompare(b)),
    [items]
  );

  const availableTopics = React.useMemo(() => {
    let base = items.filter((it) => it.sentiment_fine === selectedSentiment);

    if (selectedCluster !== "All") {
      base = base.filter((it) => it.cluster_label === selectedCluster);
    }

    const topicSet = new Set<string>();
    base.forEach((it) => {
      (it.main_topics || []).forEach((t) => {
        const trimmed = t?.trim();
        if (trimmed) topicSet.add(trimmed);
      });
    });

    return Array.from(topicSet).sort((a, b) => a.localeCompare(b));
  }, [items, selectedSentiment, selectedCluster]);

  useEffect(() => {
    setSelectedTopics((prev) => prev.filter((t) => availableTopics.includes(t)));
  }, [availableTopics]);

  const totalItems = items.length;

  const filteredItems = React.useMemo(() => {
    let base = items.filter((it) => it.sentiment_fine === selectedSentiment);

    if (selectedCluster !== "All") {
      base = base.filter((it) => it.cluster_label === selectedCluster);
    }

    if (selectedTopics.length > 0) {
      base = base.filter((it) =>
        (it.main_topics || []).some((t) => selectedTopics.includes(t))
      );
    }

    return base;
  }, [items, selectedSentiment, selectedCluster, selectedTopics]);

  const currentSentimentMeta = SENTIMENT_LEVELS[sentimentIndex];

  const toggleTopic = (topic: string) => {
    setSelectedTopics((prev) =>
      prev.includes(topic)
        ? prev.filter((t) => t !== topic)
        : [...prev, topic]
    );
  };

  const handleClusterChange = (value: string) => {
    setSelectedCluster(value);
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h4
            className="text-sm font-semibold mb-1"
            style={{ color: accentColor }}
          >
            {title}
          </h4>
          {subtitle && (
            <p className="text-xs text-slate-500 max-w-xl">{subtitle}</p>
          )}
        </div>
        {totalItems > 0 && (
          <div className="text-xs text-slate-500">
            {totalItems} analysed comments
          </div>
        )}
      </div>

      <div className="space-y-3">
        <div>
          <p className="text-xs font-medium text-slate-600 mb-1">Feelings</p>

          <div className="flex items-start gap-3">
            <div className="flex-1 min-w-0 max-w-[970px]">
              <input
                type="range"
                min={0}
                max={SENTIMENT_LEVELS.length - 1}
                step={1}
                value={sentimentIndex}
                onChange={(e) => setSentimentIndex(Number(e.target.value))}
                className="w-full h-2 rounded-full appearance-none cursor-pointer"
                style={{
                  background: sentimentGradient,
                }}
              />

              <div className="relative mt-2 h-5 w-full">
                {SENTIMENT_LEVELS.map((level, idx) => {
                  const active = idx === sentimentIndex;

                  const basePct =
                    (idx / (SENTIMENT_LEVELS.length - 1)) * 100;

                  let leftPct = basePct;
                  if (idx === 0) {
                    leftPct = basePct + 4.5;
                  }

                  return (
                    <button
                      key={level.id}
                      type="button"
                      onClick={() => setSentimentIndex(idx)}
                      className={`absolute top-0 -translate-x-1/2 text-[11px] md:text-xs font-medium whitespace-nowrap transition-colors ${
                        active
                          ? "text-slate-900"
                          : "text-slate-400 hover:text-slate-700"
                      }`}
                      style={{ left: `${leftPct}%` }}
                    >
                      {level.label}
                    </button>
                  );
                })}
              </div>
            </div>

            <span
              className="inline-flex items-center justify-center px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wide"
              style={{
                backgroundColor: currentSentimentMeta.color + "20",
                color: currentSentimentMeta.color,
                whiteSpace: "nowrap",
              }}
            >
              {currentSentimentMeta.label}
            </span>
          </div>
        </div>

        <div className="flex flex-col md:flex-row gap-4 md:items-start">
          <div className="w-full md:w-1/3">
            <p className="text-xs font-medium text-slate-600 mb-1">
              Cluster label
            </p>
            <select
              value={selectedCluster}
              onChange={(e) => handleClusterChange(e.target.value)}
              className="w-full border border-slate-300 rounded-md px-3 py-1.5 text-xs text-slate-700 shadow-sm hover:border-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-200"
            >
              <option value="All">All clusters</option>
              {allClusters.map((cl) => (
                <option key={cl} value={cl}>
                  {cl}
                </option>
              ))}
            </select>
          </div>

          <div className="flex-1">
            <p className="text-xs font-medium text-slate-600 mb-1">
              Topics (refine within feelings &amp; cluster)
            </p>
            {availableTopics.length === 0 ? (
              <p className="text-xs text-slate-400">
                No topics available for the current filters.
              </p>
            ) : (
              <div className="flex flex-wrap gap-1.5">
                {availableTopics.map((topic) => {
                  const active = selectedTopics.includes(topic);
                  return (
                    <button
                      key={topic}
                      onClick={() => toggleTopic(topic)}
                      className={`text-[11px] px-2.5 py-1 rounded-full border transition-all ${
                        active
                          ? "shadow-sm bg-slate-800 text-white"
                          : "bg-white hover:bg-slate-50 text-slate-700"
                      }`}
                      style={{
                        borderColor: active ? "#0f172a" : "#e5e7eb",
                      }}
                    >
                      {topic}
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="mt-2">
        {loading && (
          <div className="w-full h-[220px] rounded-xl bg-slate-100 animate-pulse" />
        )}

        {!loading && error && (
          <div className="text-xs text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
            {error}
          </div>
        )}

        {!loading && !error && totalItems === 0 && (
          <div className="text-xs text-slate-500 text-center py-6">
            No open-text data for this faculty and question.
          </div>
        )}

        {!loading && !error && totalItems > 0 && filteredItems.length === 0 && (
          <div className="text-xs text-slate-500 text-center py-6">
            No comments match the current filters.
          </div>
        )}

        {!loading && !error && filteredItems.length > 0 && (
          <div className="space-y-3 max-h-[320px] overflow-y-auto pr-1">
            {filteredItems.map((it) => {
              const meta =
                SENTIMENT_LEVELS.find((s) => s.id === it.sentiment_fine) ||
                currentSentimentMeta;

              return (
                <div
                  key={it.row_id}
                  className="rounded-xl border bg-white px-3 py-2.5 text-xs text-slate-700 shadow-sm"
                  style={{
                    borderColor: meta.color + "55",
                  }}
                >
                  <div className="flex justify-between items-start gap-2 mb-1">
                    <div className="flex items-center gap-2">
                      <span
                        className="inline-flex items-center justify-center px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wide"
                        style={{
                          backgroundColor: meta.color + "20",
                          color: meta.color,
                        }}
                      >
                        {meta.label}
                      </span>
                      {it.cluster_label && (
                        <span className="text-[11px] text-slate-500 italic">
                          {it.cluster_label}
                        </span>
                      )}
                    </div>
                    <span className="text-[10px] text-slate-400">
                      ID: {it.row_id}
                    </span>
                  </div>

                  {it.main_topics && it.main_topics.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-1">
                      {it.main_topics.map((t) => (
                        <span
                          key={t}
                          className="inline-flex items-center px-1.5 py-0.5 rounded-full bg-slate-100 text-[10px] text-slate-600 border border-slate-200"
                        >
                          {t}
                        </span>
                      ))}
                    </div>
                  )}

                  <p className="text-[11px] leading-snug">
                    {it.english_text || (
                      <span className="italic text-slate-400">
                        [no English text]
                      </span>
                    )}
                  </p>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

const OpenTextPerceptionsOpportunities: React.FC<{ facultyName: string }> = ({
  facultyName,
}) => {
  return (
    <OpenTextBrowser
      facultyName={facultyName}
      endpoint="/api/open_text/perceptions/opportunities/items"
      title="Opportunities and risks – open text answers"
      accentColor="#15803d"
      subtitle="Filtered answers to the open question about opportunities and risks of AI at university."
    />
  );
};

const OpenTextPerceptionsPositioning: React.FC<{ facultyName: string }> = ({
  facultyName,
}) => {
  return (
    <OpenTextBrowser
      facultyName={facultyName}
      endpoint="/api/open_text/perceptions/positioning/items"
      title="Reasons behind their positioning"
      accentColor="#15803d"
      subtitle="How teachers justify their positioning towards AI in teaching and evaluation."
    />
  );
};

const OpenTextTrainingOtherNeeds: React.FC<{ facultyName: string }> = ({
  facultyName,
}) => {
  return (
    <OpenTextBrowser
      facultyName={facultyName}
      endpoint="/api/open_text/training/other_needs/items"
      title="Other training needs (open text)"
      accentColor="#b45309"
      subtitle="Additional training needs described by teachers, beyond the predefined options."
    />
  );
};

const CommentsSection: React.FC<{ facultyName: string }> = ({ facultyName }) => {
  return (
    <OpenTextBrowser
      facultyName={facultyName}
      endpoint="/api/open_text/comments/items"
      title="General comments on AI and the survey"
      accentColor="#0ea5e9"
      subtitle="Free comments and meta-comments from the end of the survey."
    />
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

  // NEW: survey data availability
  const [hasSurveyData, setHasSurveyData] = useState<boolean | null>(null);
  const [loadingSurveyInfo, setLoadingSurveyInfo] = useState<boolean>(true);

  // Fetch section scores (existing)
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

  // NEW: check whether this faculty has any survey responses
  useEffect(() => {
    let cancelled = false;
    setLoadingSurveyInfo(true);

    fetch(`${API_BASE}/api/survey/faculties?min_count=1`, { cache: "no-store" })
      .then((res) => res.json())
      .then((data) => {
        if (cancelled) return;
        const rows = Array.isArray(data?.faculties) ? data.faculties : [];
        const found = rows.some(
          (r: any) => r?.faculty_name === faculty.name
        );
        setHasSurveyData(found);
      })
      .catch(() => {
        // fail-open: if the endpoint fails, we don't block the layout
        if (!cancelled) setHasSurveyData(true);
      })
      .finally(() => {
        if (!cancelled) setLoadingSurveyInfo(false);
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

  // NEW: empty-state when there are no survey answers for this faculty
  if (!loadingSurveyInfo && hasSurveyData === false) {
    const Icon = pickFacultyIcon(faculty.name);
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 py-8 px-4">
        <div className="max-w-3xl mx-auto">
          <button
            onClick={onBack}
            className="mb-6 px-4 py-2 bg-white rounded-lg shadow-sm border border-slate-200 text-slate-600 hover:text-slate-800 hover:shadow-md transition-all duration-200"
          >
            ← Back to Faculty Selection
          </button>

          <div className="bg-white rounded-3xl shadow-lg border border-dashed border-slate-300 p-10 flex flex-col items-center text-center">
            <div
              className="mb-4 p-4 rounded-2xl"
              style={{ backgroundColor: `${faculty.color}15` }}
            >
              <Icon className="w-12 h-12" style={{ color: faculty.color }} />
            </div>
            <h1 className="text-2xl font-semibold text-slate-800 mb-2">
              No available data for this faculty
            </h1>
            <p className="text-sm text-slate-500 mb-4 max-w-md">
              We haven&apos;t received any survey responses from the{" "}
              <span className="font-medium">{faculty.name}</span> faculty yet.
              Once responses are collected, this page will display detailed
              visualizations.
            </p>
            <button
              onClick={onBack}
              className="mt-1 px-4 py-2 bg-slate-900 text-white rounded-lg shadow-sm hover:bg-slate-800 transition-colors text-sm"
            >
              ← Back to Faculty Selection
            </button>
          </div>
        </div>
      </div>
    );
  }

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
                                facultyColor={"#15803d"}
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
                              <div className="lg:w-3/5 bg-white rounded-xl p-4 shadow-sm border border-slate-200">
                                <PerceptionsProfAttitudeSpider facultyName={faculty.name} facultyColor="#15803d" />
                              </div>
                              <div className="lg:w-2/5 bg-white rounded-xl p-4 shadow-sm border border-slate-200">
                                <PerceptionsTasksSupportPie facultyName={faculty.name} facultyColor="#15803d" />
                              </div>
                            </div>
                            <div className="mt-6 bg-white rounded-xl p-4 shadow-sm border border-slate-200">
                              <OpenTextPerceptionsPositioning facultyName={faculty.name} />
                            </div>
                            <div className="mt-6 bg-white rounded-xl p-4 shadow-sm border border-slate-200">
                              <PerceptionsOpportunitiesRisksBar
                                facultyName={faculty.name}
                                facultyColor="#15803d"
                              />
                            </div>
                            <div className="mt-6 bg-white rounded-xl p-4 shadow-sm border border-slate-200">
                              <OpenTextPerceptionsOpportunities facultyName={faculty.name} />
                            </div>
                          </div>
                        ) : area.name === 'Training' ? (
                          <div className="flex flex-col gap-6">
                            <div className="bg-white rounded-xl p-4 shadow-sm border border-slate-200">
                              <TrainingReceivedSpider facultyName={faculty.name} facultyColor="#b45309" />
                            </div>

                            <div className="mt-6 flex flex-col lg:flex-row gap-6">
                              <div className="lg:w-2/5 bg-white rounded-xl p-4 shadow-sm border border-slate-200 min-h-[520px]">
                                <TrainingInterestPie facultyName={faculty.name} facultyColor="#b45309" />
                              </div>
                              <div className="lg:w-3/5 bg-white rounded-xl p-4 shadow-sm border border-slate-200 min-h-[520px]">
                                <TrainingNeedsBar facultyName={faculty.name} facultyColor="#b45309" />
                              </div>
                            </div>
                            <div className="mt-6 bg-white rounded-xl p-4 shadow-sm border border-slate-200">
                              <OpenTextTrainingOtherNeeds facultyName={faculty.name} />
                            </div>
                          </div>
                        ) : area.name === 'Comments' ? (
                          <div className="flex flex-col gap-6">
                            <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
                              <CommentsSection facultyName={faculty.name} />
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
