import React, { useState, useEffect } from 'react';
import { ChevronDown, ChevronUp, BookOpen, Users, Eye, GraduationCap } from 'lucide-react';
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

// -------------------------
// Knowledge Bar Chart Component (REAL DATA)
// -------------------------
const KnowledgeBarChart = ({ facultyName }: { facultyName: string }) => {
  const [data, setData] = useState<{ categories: string[]; values: number[] } | null>(null);

  useEffect(() => {
    fetch(`http://localhost:8000/api/faculty/${facultyName}/knowledge-distribution`)
      .then((res) => res.json())
      .then((json) => {
        // Ensure data is ordered properly (Cap → Poc → Bon → Expert)
        const orderedCategories = ["No knowledge", "Little knowledge", "Good knowledge", "Expert knowledge"];
        const sortedValues = orderedCategories.map(cat => {
          const index = json.categories.indexOf(cat);
          return index >= 0 ? json.values[index] : 0;
        });
        setData({ categories: orderedCategories, values: sortedValues });
      })
      .catch((err) => console.error('Error fetching knowledge data:', err));
  }, [facultyName]);

  if (!data) return <p className="text-gray-500">Loading knowledge data...</p>;

  return (
  <Plot
    data={[
      {
        x: data.categories,
        y: data.values,
        type: 'bar',
        marker: { color: '#b91c1c' },
      },
    ]}
    layout={{
      title: {
        text: 'Self-assessment of AI Knowledge',
        font: { size: 20, color: '#334155' },
        xref: 'paper',
        x: 0.5, // center align
      },
      xaxis: {
        title: {
          text: 'Knowledge Assessment',
          font: { size: 14, color: '#334155' },
          standoff: 20,
        },
        categoryorder: 'array',
        categoryarray: data.categories,
        tickfont: { color: '#334155', size: 10 },
      },
      yaxis: {
        title: {
          text: 'Occurrences',
          font: { size: 14, color: '#334155' },
        },
        tickfont: { color: '#334155' },
      },
      margin: { t: 80, l: 70, r: 40, b: 70 },
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)',
    }}
    style={{ width: '100%', height: '380px' }}
    config={{ displayModeBar: false }}
  />
);

};

const NormativePieChart = ({ facultyName }: { facultyName: string }) => {
  const [data, setData] = useState<{ categories: string[]; values: number[] } | null>(null);

  useEffect(() => {
    fetch(`http://localhost:8000/api/faculty/${facultyName}/normative-distribution`)
      .then((res) => res.json())
      .then(setData)
      .catch((err) => console.error('Error fetching normative data:', err));
  }, [facultyName]);

  if (!data) return <p className="text-gray-500">Loading normative data...</p>;

    // Define short labels mapping
  const shortLabels: Record<string, string> = {
    "Yes, there is a guide or normative": "Yes",
    "I ignore if there's a guide or normative": "Don't know",
    "There is no guide or normative": "No",
  };

  // Map long labels to short ones (but keep full text for hover)
  const displayLabels = data.categories.map(cat => shortLabels[cat] || cat);
  return (
    <Plot
      data={[
        {
          labels: displayLabels, // shorter labels for chart
          values: data.values,
          type: 'pie',
          textinfo: 'label+percent',
          hoverinfo: 'text+percent',
          text: data.categories, // original long text shown in hover if needed
          marker: {
          colors: ['#05cc25', '#e01717', '#ffed45'],
          },
        },
      ]}
      layout={{
        title: {
          text: 'Is there any guide or normative at UB?',
          font: { size: 18, color: '#334155' },
          xref: 'paper',
          x: 0.2,
        },
        showlegend: true,
        legend: {
          orientation: 'v',
          x: 1,
          y: 0.5,
          font: { color: '#334155' },
        },
        margin: { t: 60, l: 20, r: 20, b: 20 },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
      }}
      style={{ width: '100%', height: '350px' }}
      config={{ displayModeBar: false }}
    />
  );
};

const InterestKnowledgeLinkChart = ({ facultyName }: { facultyName: string }) => {
  const [data, setData] = useState<any[]>([]);

  useEffect(() => {
    fetch(`http://localhost:8000/api/faculty/${facultyName}/interest-knowledge-link`)
      .then((res) => res.json())
      .then(setData)
      .catch((err) => console.error("Error fetching interest-knowledge link data:", err));
  }, [facultyName]);

  if (!data.length) return <p className="text-gray-500">Loading correlation data...</p>;

  const interests = data.map((d) => d.interest);

  const traces = [
    {
      y: interests,
      x: data.map((d) => d.knowledge_in_teaching),
      name: "Teaching",
      type: "bar",
      orientation: "h",
      marker: { color: "#1d4ed8" },
    },
    {
      y: interests,
      x: data.map((d) => d.knowledge_in_research),
      name: "Research",
      type: "bar",
      orientation: "h",
      marker: { color: "#9333ea" },
    },
    {
      y: interests,
      x: data.map((d) => d.knowledge_in_material_creation),
      name: "Material Creation",
      type: "bar",
      orientation: "h",
      marker: { color: "#f59e0b" },
    },
    {
      y: interests,
      x: data.map((d) => d.knowledge_in_evaluation),
      name: "Evaluation",
      type: "bar",
      orientation: "h",
      marker: { color: "#16a34a" },
    },
  ];

  return (
    <Plot
      data={traces}
      layout={{
        barmode: "group",
        title: {
          text: "Relation between AI Knowledge Interest and Areas",
          font: { size: 18, color: "#334155" },
        },
        xaxis: {
          title: "Average Agreement Level (1–4)",
          range: [0, 4],
          tickvals: [1, 2, 3, 4],

        },
        yaxis: {
          title: "Interest in AI",
          automargin: true,
          tickfont: { size: 9 },
        },
        margin: { t: 60, l: 160, r: 20, b: 60 },
        legend: {
          orientation: "h",
          y: -0.3,
          x: 0.5,
          xanchor: "center",
          font: { color: "#334155" },
        },
        paper_bgcolor: "rgba(0,0,0,0)",
        plot_bgcolor: "rgba(0,0,0,0)",
      }}
      config={{ displayModeBar: false }}
      style={{ width: "100%", height: "700px" }}
    />
  );
};



// -------------------------
// Faculty Visualization Component
// -------------------------
const FacultyVisualization: React.FC<{ faculty: Faculty; onBack: () => void }> = ({ faculty, onBack }) => {
  const [expandedAreas, setExpandedAreas] = useState<Set<string>>(new Set(['Knowledge']));

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
        {/* Back Button */}
        <button
          onClick={onBack}
          className="mb-6 px-4 py-2 bg-white rounded-lg shadow-sm border border-slate-200 text-slate-600 hover:text-slate-800 hover:shadow-md transition-all duration-200"
        >
          ← Back to Faculty Selection
        </button>

        {/* Faculty Card */}
        <div
          className="bg-white rounded-3xl shadow-lg overflow-hidden"
          style={{
            borderWidth: '3px',
            borderStyle: 'solid',
            borderColor: faculty.color,
          }}
        >
          {/* Header */}
          <div className="p-8 border-b border-slate-200 flex items-center">
            <div
              className="w-8 h-8 rounded-full mr-4 shadow-md"
              style={{ backgroundColor: faculty.color }}
            />
            <div>
              <h1 className="text-3xl font-light text-slate-800">{faculty.name}</h1>
              <p className="text-slate-500 text-sm mt-1">Data Visualizations & Analytics</p>
            </div>
          </div>

          {/* Data Areas */}
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
                      <div
                        className="p-3 rounded-xl text-white shadow-md"
                        style={{ backgroundColor: area.color }}
                      >
                        {area.icon}
                      </div>
                      <div className="text-left">
                        <h2 className="text-2xl font-medium text-slate-800">{area.name}</h2>
                        <p className="text-slate-500 text-sm mt-1">{area.description}</p>
                      </div>
                    </div>

                    <div
                      className="p-2 rounded-lg transition-colors duration-200"
                      style={{
                        backgroundColor: isExpanded ? `${area.color}15` : 'transparent',
                      }}
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
                      isExpanded ? 'max-h-[2000px] opacity-100' : 'max-h-0 opacity-0'
                    }`}
                  >
                    <div className="p-6 border-t" style={{ borderColor: `${area.color}30` }}>
                      <div className="min-h-[400px] bg-slate-50 rounded-xl p-8 border-2 border-dashed border-slate-200">
                        {area.name === 'Knowledge' ? (
                        <div className="flex flex-col lg:flex-row gap-6">
                          {/* LEFT SIDE */}
                          <div className="flex-1 bg-white rounded-xl p-4 shadow-sm border border-slate-200">
                            <InterestKnowledgeLinkChart facultyName={faculty.name} />
                          </div>

                          {/* RIGHT SIDE */}
                          <div className="flex flex-col w-full lg:w-1/2 gap-6">
                            <div className="bg-white rounded-xl p-4 shadow-sm border border-slate-200">
                              <KnowledgeBarChart facultyName={faculty.name} />
                            </div>
                            <div className="bg-white rounded-xl p-4 shadow-sm border border-slate-200">
                              <NormativePieChart facultyName={faculty.name} />
                            </div>
                          </div>
                        </div>
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

          {/* Footer */}
          <div className="p-6 bg-slate-50 border-t border-slate-200 text-center text-slate-500 text-sm">
            Click on each section to expand and view detailed visualizations
          </div>
        </div>
      </div>
    </div>
  );
};

export default FacultyVisualization;
