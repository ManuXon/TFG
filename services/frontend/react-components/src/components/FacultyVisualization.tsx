import React, { useState, useEffect, useCallback } from 'react';
import {
  ChevronDown, ChevronUp,
  BookOpen, Users, Eye, GraduationCap,
  Palette, Microscope, Globe, Scale, TrendingUp, Pill, MessageSquare,
  Brain, Atom, Map as MapIcon, Video, Heart, Calculator, Stethoscope, FlaskConical,
} from "lucide-react";
import KnowledgeApplicationsWordCloud from "./KnowledgeApplicationsWordCloud";
import Plot from 'react-plotly.js';

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

const facultyIconMapLC: Record<string, (typeof facultyIconMap)[FacultyIconKey]> =
  Object.fromEntries(
    (Object.entries(facultyIconMap) as [FacultyIconKey, (typeof facultyIconMap)[FacultyIconKey]][])
      .map(([k, v]) => [norm(k), v])
  );

const pickFacultyIcon = (facultyName: string) =>
  facultyIconMapLC[norm(facultyName)] || Globe;

// -------------------------
// Knowledge Bar Chart
// -------------------------
const KnowledgeBarChart = ({ facultyName }: { facultyName: string }) => {
  const [selected, setSelected] = useState<string[]>(["gender","experience"]);
  const [data, setData] = useState<any | null>(null);

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
      .catch((err) => console.error("Error fetching knowledge data:", err));
  }, [facultyName, selected]);

  if (!data) return <p className="text-gray-500">Loading knowledge data...</p>;

  // --- SINGLE DEMOGRAPHIC ---
  if (data.mode === "single") {
    return (
      <div>
        <div className="flex justify-center gap-6 mb-4">
          {["gender", "experience", "profile"].map((opt) => (
            <label key={opt} className="flex items-center space-x-2 text-slate-700">
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
                `<b>%{x}</b><br>` +
                `Avg Knowledge Score: <b>%{y:.2f}</b><extra></extra>`,
            },
          ]}
          layout={{
            title: {
              text: `Average Knowledge Score by ${data.demographics[0]}`,
              font: { size: 18, color: "#334155" },
              y: 0.95,
            },
            xaxis: { title: `${data.demographics[0]} categories`, tickfont: { size: 10 } },
            yaxis: { title:{text: "Avg Knowledge Score (1–4)", tickfont: { size: 10 } }, range: [0, 4]},
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
    // --- DUAL DEMOGRAPHIC STACKED ---
  if (data.mode === "dual") {
    const mainGroups = Array.from(new Set(data.data.map((d: any) => d.main))) as string[];
    const subGroups  = Array.from(new Set(data.data.map((d: any) => d.sub))) as string[];

    // Build main -> main_avg map for percentage math
    const mainAvgMap: Record<string, number> = {};
    data.data.forEach((r: any) => {
      if (mainAvgMap[r.main] == null) mainAvgMap[r.main] = r.main_avg;
    });

    const traces = subGroups.map((sub, idx) => {
      const yValues = mainGroups.map((m) => {
        const rec = data.data.find((d: any) => d.main === m && d.sub === sub);
        return rec ? rec.contribution : 0;
      });

      const subAvg   = mainGroups.map((m) => {
        const rec = data.data.find((d: any) => d.main === m && d.sub === sub);
        return rec ? rec.mean_sub : 0;
      });

      const counts   = mainGroups.map((m) => {
        const rec = data.data.find((d: any) => d.main === m && d.sub === sub);
        return rec ? rec.n_sub : 0;
      });

      const percentages = mainGroups.map((m, i) => {
        const mainAvg = mainAvgMap[m] || 0;
        const val     = yValues[i] || 0;
        return mainAvg > 0 ? ((val / mainAvg) * 100).toFixed(1) : "0.0";
      });

      return {
        x: mainGroups,
        y: yValues,
        name: sub,
        type: "bar",
        marker: { color: ["#dc2626", "#f87171", "#fb923c", "#fde68a", "#7f1d1d"][idx % 5] },
        // Pass extra fields for a rich hover
        customdata: yValues.map((_, i) => [subAvg[i], counts[i], percentages[i]]),
        hovertemplate:
          `<b>%{x}</b><br>` +
          `${data.demographics[1]}: <b>${sub}</b><br>` +
          `Sub avg: %{customdata[0]:.2f} (n=%{customdata[1]})<br>` +
          `Contribution to main avg: <b>%{y:.2f}</b><br>` +
          `Share: <b>%{customdata[2]}%</b><extra></extra>`,
      };
    });

    return (
      <div>
        <div className="flex justify-center gap-6 mb-4">
          {["gender", "experience", "profile"].map((opt) => (
            <label key={opt} className="flex items-center space-x-2 text-slate-700">
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
              text: `Average Knowledge Score by: ${data.demographics[0]} × ${data.demographics[1]}`,
              font: { size: 18, color: "#334155" },
              y: 0.95,
            },
            xaxis: { title: data.demographics[0], tickfont: { size: 10 } },
            yaxis: {
              title: { text: "Avg Knowledge Score (1–4)" },
              tickfont: { size: 10 },
              range: [0, 4], // main averages live in [1,4]; stacks now sum to main avg
            },
            legend: { orientation: "h", y: -0.25, x: 0.071, font: { size: 14 }, bordercolor: "#e2e8f0", borderwidth: 1 },
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
  }

  return <></>;
};

// -------------------------
// Normative Pie Chart
// -------------------------
const NormativePieChart = ({ facultyName }: { facultyName: string }) => {
  const [data, setData] = useState<{ categories: string[]; values: number[] } | null>(null);

  useEffect(() => {
    fetch(`http://localhost:8000/api/faculty/${facultyName}/normative-distribution`)
      .then((res) => res.json())
      .then(setData)
      .catch((err) => console.error('Error fetching normative data:', err));
  }, [facultyName]);

  if (!data) return <p className="text-gray-500">Loading normative data...</p>;

  const shortLabels: Record<string, string> = {
    "Yes, there is a guide or normative": "Yes",
    "I ignore if there's a guide or normative": "Don't know",
    "There is no guide or normative": "No",
  };

  const displayLabels = data.categories.map(cat => shortLabels[cat] || cat);

  return (
  <Plot
    data={[
      {
        labels: displayLabels,
        values: data.values,
        type: "pie",
        textinfo: "label+percent",
        hovertemplate:
          `<b>%{label}</b><br>` +
          `Responses: <b>%{value}</b><br>` +
          `Share: <b>%{percent}</b><extra></extra>`,
        marker: {
          colors: ["#dc2626", "#f87171", "#fb923c", "#fde68a"], // red-orange palette
          line: { color: "#ffffff", width: 2 }, // clean separation between slices
        },
      },
    ]}
    layout={{
      title: {
        text: "Is there any guide or normative at UB?",
        font: { size: 18, color: "#334155" },
        xref: "paper",
        x: 0.00,
        y: 1.05,
      },
      showlegend: true,
      legend: {
        orientation: "h",
        x: 0.15,
        font: { color: "#334155", size: 14 },
        bgcolor: "rgba(255,255,255,0.7)",
        bordercolor: "#e2e8f0", borderwidth: 1
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
const KnowledgeFunctionalityChart = ({ facultyName }: { facultyName: string }) => {
  const [chartType, setChartType] = useState<'bar' | 'heatmap' | 'radar'>('radar');
  const [data, setData] = useState<any[]>([]);

  const [gender, setGender] = useState<string>("All");
  const [experience, setExperience] = useState<string | null>(null);
  const [profile, setProfile] = useState<string | null>(null);

  const fetchData = useCallback(() => {
    const params = new URLSearchParams();
    if (gender && gender !== "All") params.append("gender", gender);
    if (experience) params.append("experience", experience);
    if (profile) params.append("profile", profile);

    fetch(`http://localhost:8000/api/faculty/${facultyName}/knowledge-functionality-correlation?${params.toString()}`)
      .then((res) => res.json())
      .then(setData)
      .catch((err) => console.error("Error fetching knowledge-functionality data:", err));
  }, [facultyName, gender, experience, profile]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (!data.length) return <p className="text-gray-500">Loading knowledge functionality data...</p>;

  // The y-axis labels are now the IA knowledge text tags
  const knowledgeLabels = data.map((d) => d.knowledge_label);

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

  const matrix = data.map((d) =>
    funcLabels.map((label, i) => Object.values(d)[i + 1]) // skip first column (knowledge_label)
  );

  const colorPalette = [
    "#7f1d1d", "#991b1b", "#b91c1c", "#dc2626", "#ef4444",
    "#f87171", "#fb923c", "#fdba74", "#fde68a", "#fef08a",
    "#a16207", "#78350f", "#451a03"
  ];

  return (
    <div>
      {/* --- Filters Section --- */}
      <div className="flex flex-wrap justify-center gap-2 mb-4">
        <select value={gender} onChange={(e) => setGender(e.target.value)}
                className="border border-slate-300 rounded-md px-3 py-1 text-slate-700 text-sm shadow-sm hover:border-slate-400 focus:outline-none focus:ring-2 focus:ring-red-200 transition" >
          <option value="All">All Genders</option>
          <option value="Female">Female</option>
          <option value="Male">Male</option> <option value="Non-binary">Non-binary</option>
          <option value="No answer">No answer</option>
        </select>
        <select value={experience || ""} onChange={(e) => setExperience(e.target.value || null)}
                className="border border-slate-300 rounded-md px-3 py-1 text-slate-700 text-sm shadow-sm hover:border-slate-400 focus:outline-none focus:ring-2 focus:ring-red-200 transition" >
          <option value="">All Experience</option>
          <option value="Less than 5 ">Less than 5</option>
          <option value="Between 5 and 10">Between 5 and 10</option>
          <option value="Between 11 and 20">Between 11 and 20</option>
          <option value="More than 20">More than 20</option> </select>
        <select value={profile || ""} onChange={(e) => setProfile(e.target.value || null)}
                className="border border-slate-300 rounded-md px-3 py-1 text-slate-700 text-sm shadow-sm hover:border-slate-400 focus:outline-none focus:ring-2 focus:ring-red-200 transition" >
          <option value="">All Profiles</option>
          <option value="Senior Lecturer">Senior Lecturer</option>
          <option value="Associate">Associate</option>
          <option value="PreDoc">PreDoc</option>
          <option value="PostDoc">PostDoc</option> <option value="Collab">Collab</option>
          <option value="Lecturer">Lecturer</option> <option value="Professor">Professor</option>
        </select> {/* Chart type selector */}
        <select value={chartType} onChange={(e) => setChartType(e.target.value as any)}
                className="border border-slate-300 rounded-md px-3 py-1 text-slate-700 text-sm shadow-sm hover:border-slate-400 focus:outline-none focus:ring-2 focus:ring-red-200 transition" >
          <option value="bar">Grouped Bar</option>
          <option value="heatmap">Heatmap</option>
          <option value="radar">Spider</option>
        </select>
      </div>

      {/* --- Grouped Bar Chart (Horizontal Layout) --- */}
      {chartType === "bar" && (
        <Plot
          data={funcLabels.map((label, i) => ({
            x: knowledgeLabels, // now the textual categories go on the X axis
            y: data.map((d) => Object.values(d)[i + 1]), // numeric values on Y
            name: label,
            type: "bar",
            orientation: "v", // bars go vertically, but the whole plot is rotated
            marker: { color: colorPalette[i % colorPalette.length] },
            hovertemplate:
              `<b>IA Knowledge:</b> %{x}<br>` +
              `<b>${label}:</b> %{y:.2f}<extra></extra>`,
          }))}

          layout={{
            barmode: "group",
            title: {
              text: "AI Knowledge vs Familiarity with AI Applications",
              y: 0.96,
              font: { size: 21 },
            },
            xaxis: {
              categoryorder: "array",
              categoryarray: [
                "No knowledge",
                "Little knowledge",
                "Good knowledge",
                "Expert knowledge",
              ],
              tickfont: {size: 13}
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
              font: { size: 14 },
              bordercolor: "#e2e8f0",
              borderwidth: 1,
            },
            margin: { t: 80, l: 60, r: 30, b: 80 },
            paper_bgcolor: "rgba(0,0,0,0)",
            plot_bgcolor: "rgba(0,0,0,0)",
          }}

          style={{ width: "100%", height: "600px" }}
          config={{ displayModeBar: false }}
        />
      )}


      {/* --- Heatmap --- */}
      {chartType === "heatmap" && (
        <Plot
          data={[
            {
              z: matrix,
              x: funcLabels,
              y: knowledgeLabels,
              type: "heatmap",
              colorscale: "Reds",
              colorbar: { title: { text: "Familiarity"} },
              hovertemplate:
                `<b>IA Knowledge:</b> %{y}<br>` +
                `<b>Functionality:</b> %{x}<br>` +
                `<b>Avg Familiarity:</b> %{z:.2f}<extra></extra>`,
            },
          ]}
          layout={{
            title: {
              text: "AI Knowledge vs Familiarity with AI Applications",
              y: 0.96,
              font: { size: 21 },
            },
            y: 1.0,
            yaxis: { autorange: "reversed", tickfont: { size: 9.5 } },
            xaxis: { tickfont: { size: 11 } },
            margin: { t: 110, l: 95, r: 0, b: 110 },
            paper_bgcolor: "rgba(0,0,0,0)",
            plot_bgcolor: "rgba(0,0,0,0)",
            font: { color: "#334155" },
          }}
          config={{ displayModeBar: false }}
          style={{ width: "100%", height: "600px" }}
        />
      )}
    {/* --- Radar --- */}
    {chartType === "radar" && (
      <Plot
        data={data.map((d, i) => {
          // Assign distinct but thematically consistent colors for each knowledge level
          const radarColors: Record<string, string> = {
            "No knowledge": "#b91c1c",        // Deep red
            "Little knowledge": "#fb923c",    // Orange
            "Good knowledge": "#facc15",      // Golden yellow
            "Expert knowledge": "#84cc16",    // Lime green for contrast
          };

          const color = radarColors[d.knowledge_label] || "#b91c1c";

          return {
            type: "scatterpolar",
            r: matrix[i].concat(matrix[i][0]), // close loop
            theta: funcLabels.concat(funcLabels[0]),
            fill: "toself",
            name: d.knowledge_label,
            line: {
              color,
              width: 3,
            },
            fillcolor: color + "40", // semi-transparent fill for nice overlap
            hovertemplate:
              `<b>%{theta}</b><br>` +
              `Knowledge Level: <b>${d.knowledge_label}</b><br>` +
              `Avg Familiarity: %{r:.2f}<extra></extra>`,
          };
        })}
        layout={{
          title: {
            text: "AI Knowledge vs Familiarity with AI Applications",
            font: { size: 21, color: "#334155" },
            y: 0.96,
          },
          polar: {
            bgcolor: "rgba(0,0,0,0)",
            radialaxis: {
              visible: false,
              showline: false,
              range: [0, 4],
              gridcolor: "#f1f5f9", // subtle grid tone
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
              tickfont: { color: "#334155", size: 13 },
              ticklen: 8,
              ticks: "",
              direction: "clockwise",
              rotation: 90, // makes first label at top for symmetry
            },
          },
          showlegend: true,
          legend: {
            orientation: "v",
            y: 1,
            x:-0.04,
            xanchor: "left",
            font: { color: "#334155", size: 14 },
            bordercolor: "#e2e8f0",
            borderwidth: 1,
          },
          margin: { t: 90, l: 80, r: 40, b: 40 },
          paper_bgcolor: "rgba(0,0,0,0)",
          plot_bgcolor: "rgba(0,0,0,0)",
        }}
        style={{ width: "100%", height: "600px" }}
        config={{ displayModeBar: false }}
      />
    )}
    </div>
  );
};


// -------------------------
// Faculty Visualization Layout
// -------------------------
const FacultyVisualization: React.FC<{ faculty: Faculty; onBack: () => void }> = ({ faculty, onBack }) => {
  const [expandedAreas, setExpandedAreas] = useState<Set<string>>(new Set(['']));

  const toggleArea = (areaName: string) => {
    setExpandedAreas((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(areaName)) newSet.delete(areaName);
      else newSet.add(areaName);
      return newSet;
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 py-8 px-4">
      <div className="max-w-7xl mx-auto">
        <button
          onClick={onBack}
          className="mb-6 px-4 py-2 bg-white rounded-lg shadow-sm border border-slate-200 text-slate-600 hover:text-slate-800 hover:shadow-md transition-all duration-200">
          ← Back to Faculty Selection
        </button>

        <div
          className="bg-white rounded-3xl shadow-lg scroll"
          style={{ borderWidth: '3px', borderStyle: 'solid', borderColor: faculty.color }}>
          <div className="p-8 border-b border-slate-200 flex items-center">
            <div
              className="p-3 rounded-lg mr-4 shadow-sm"
              style={{ backgroundColor: `${faculty.color}20` }}
              title={faculty.name}
            >
              {(() => {
                // reuse pickFacultyIcon helper
                const Icon = pickFacultyIcon(faculty.name);
                return <Icon className="w-8 h-8" style={{ color: faculty.color }} />;
              })()}
            </div>

            <div>
              <h1 className="text-3xl font-normal text-slate-800">{faculty.name}</h1>
              <p className="text-slate-500 text-sm mt-1">Data Visualizations & Analytics</p>
            </div>
          </div>

          <div className="p-6 space-y-4">
            {dataAreas.map((area) => {
              const isExpanded = expandedAreas.has(area.name);
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
                  {/* Header */}
                  <button
                    onClick={() => toggleArea(area.name)}
                    className="w-full p-6 flex items-center justify-between hover:bg-slate-50 transition-colors duration-200"
                  >
                    <div className="flex items-center space-x-4">
                      <div className="p-3 rounded-xl text-white shadow-md" style={{ backgroundColor: area.color }}>
                        {area.icon}
                      </div>
                      <div className="text-left">
                        <h2 className="text-2xl font-medium text-slate-800">{area.name}</h2>
                        <p className="text-slate-500 text-sm mt-1">{area.description}</p>
                      </div>
                    </div>

                    <div
                      className="p-2 rounded-lg transition-colors duration-200"
                      style={{ backgroundColor: isExpanded ? `${area.color}15` : 'transparent' }}
                    >
                      {isExpanded ? (
                        <ChevronUp className="w-6 h-6" style={{ color: area.color }} />
                      ) : (
                        <ChevronDown className="w-6 h-6 text-slate-400" />
                      )}
                    </div>
                  </button>

                  {/* Content */}
                  <div
                    className={`transition-all duration-300 ease-in-out overflow-hidden ${
                      isExpanded ? 'opacity-100' : 'max-h-0 opacity-0'
                    }`}
                  >
                    <div className="p-6 border-t" style={{ borderColor: `${area.color}30` }}>
                      <div className="min-h-[400px] bg-slate-50 rounded-xl p-8 border-2 border-dashed border-slate-200">
                        {area.name === 'Knowledge' ? (
                        <>
                          {/* --- FIRST ROW --- */}
                          <div className="flex flex-col gap-6">
                            {/* Row 1: Full-width KnowledgeFunctionalityChart */}
                            <div className="bg-white rounded-xl p-4 shadow-sm border border-slate-200">
                              <KnowledgeFunctionalityChart facultyName={faculty.name} />
                            </div>

                            {/* Row 2: Bar (60%) + Pie (40%) */}
                            <div className="flex flex-col lg:flex-row gap-6">
                              {/* Bar Chart (60%) */}
                              <div className="lg:w-3/5 bg-white rounded-xl p-4 shadow-sm border border-slate-200">
                                <KnowledgeBarChart facultyName={faculty.name} />
                              </div>

                              {/* Pie Chart (40%) */}
                              <div className="lg:w-2/5 bg-white rounded-xl p-4 shadow-sm border border-slate-200">
                                <NormativePieChart facultyName={faculty.name} />
                              </div>
                            </div>
                          </div>

                          {/* --- SECOND ROW: WORD CLOUD --- */}
                          <div className="mt-6 bg-white rounded-xl p-6 shadow-sm border border-slate-200 w-full">
                            <KnowledgeApplicationsWordCloud facultyName={faculty.name} />
                          </div>
                        </>
                      ) : (
                        <div className="text-center py-16">
                          <div
                            className="inline-flex p-4 rounded-full mb-4"
                            style={{ backgroundColor: `${area.color}15` }}
                          >
                            <div style={{ color: area.color }}>{area.icon}</div>
                          </div>
                          <h3 className="text-xl font-medium text-slate-700 mb-2">
                            {area.name} Visualizations
                          </h3>
                          <p className="text-slate-500">
                            Your {area.name.toLowerCase()} charts and graphs will be displayed here
                          </p>
                          <p className="text-slate-400 text-sm mt-2">
                            This container can hold multiple visualizations and will expand as needed
                          </p>
                        </div>
                      )}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="p-6 bg-slate-50 border-t border-slate-200 text-center text-slate-500 text-sm" style={{borderRadius: '23px'}}>
            Click on each section to expand and view detailed visualizations
          </div>
        </div>
      </div>
    </div>
  );
};

export default FacultyVisualization;
