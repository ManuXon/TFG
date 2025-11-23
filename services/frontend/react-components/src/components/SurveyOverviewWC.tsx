// assets/react/components/SurveyOverviewWC.tsx
import React, { useEffect, useMemo, useState } from "react";
import { X, Users, Building2, Calendar, User, Briefcase, Monitor, BarChart3, School } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import Plot from "react-plotly.js";

const CHART_HEIGHT = 320;      // was 360
const CARD_MIN_HEIGHT = 340;   // was 380


type DemographicCategory = "age" | "gender" | "profile" | "experience" | "mode";

const API_BASE = "http://localhost:8000";

const BUTTONS: Array<{
  id: DemographicCategory;
  label: string;
  color: string;
  icon: React.ReactNode;
}> = [
  { id: "age",        label: "Age Groups",          color: "#3b82f6", icon: <Calendar className="w-5 h-5" /> },
  { id: "gender",     label: "Gender",              color: "#8b5cf6", icon: <User className="w-5 h-5" /> },
  { id: "profile",    label: "UB Profile",          color: "#10b981", icon: <Briefcase className="w-5 h-5" /> },
  { id: "experience", label: "Teaching Experience", color: "#f59e0b", icon: <Building2 className="w-5 h-5" /> },
  { id: "mode",       label: "Teaching Mode",       color: "#ec4899", icon: <Monitor className="w-5 h-5" /> },
];

type SummaryResp = { total_responses: number; total_faculties: number };
type DistResp = { categories: string[]; counts: number[] };
type FacultiesResp = { faculties: { faculty_name: string; responses: number }[]; total: number };

const useFaculties = () => {
  const [data, setData] = useState<{ name: string; responses: number }[]>([]);
  useEffect(() => {
    fetch(`${API_BASE}/api/survey/faculties?min_count=1`, { cache: "no-store" })
      .then(r => r.json())
      .then((d: FacultiesResp) => {
        const rows = (d?.faculties ?? []).map(f => ({ name: f.faculty_name, responses: Number(f.responses || 0) }));
        setData(rows);
      })
      .catch(() => setData([]));
  }, []);
  return data;
};

const useSummary = (faculty: string | "All") => {
  const [summary, setSummary] = useState<SummaryResp>({ total_responses: 0, total_faculties: 0 });
  useEffect(() => {
    const params = new URLSearchParams();
    if (faculty && faculty !== "All") params.set("faculty", faculty);
    fetch(`${API_BASE}/api/survey/summary${params.toString() ? `?${params.toString()}` : ""}`, { cache: "no-store" })
      .then(r => r.json())
      .then((d: SummaryResp) =>
        setSummary({
          total_responses: Number(d?.total_responses ?? 0),
          total_faculties: Number(d?.total_faculties ?? 0),
        })
      )
      .catch(() => setSummary({ total_responses: 0, total_faculties: 0 }));
  }, [faculty]);
  return summary;
};

const useDistribution = (category: DemographicCategory | null, faculty: string | "All") => {
  const [dist, setDist] = useState<DistResp>({ categories: [], counts: [] });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!category) { setDist({ categories: [], counts: [] }); return; }
    setLoading(true);
    const params = new URLSearchParams({ category });
    if (faculty && faculty !== "All") params.set("faculty", faculty);

    fetch(`${API_BASE}/api/survey/distribution?${params.toString()}`, { cache: "no-store" })
      .then(r => r.json())
      .then((d: DistResp) => setDist({ categories: d?.categories ?? [], counts: d?.counts ?? [] }))
      .catch(() => setDist({ categories: [], counts: [] }))
      .finally(() => setLoading(false));
  }, [category, faculty]);

  return { dist, loading };
};

const SurveyOverviewWC: React.FC = () => {
  const [open, setOpen] = useState(false);
  const [selected, setSelected] = useState<DemographicCategory | null>(null);

  // Faculty filter state
  const faculties = useFaculties();
  const [faculty, setFaculty] = useState<string | "All">("All");

  // open/close via global events from Dash
  useEffect(() => {
    const onOpen = () => setOpen(true);
    const onClose = () => setOpen(false);
    window.addEventListener("mapai:openSurvey", onOpen as EventListener);
    window.addEventListener("mapai:closeSurvey", onClose as EventListener);
    return () => {
      window.removeEventListener("mapai:openSurvey", onOpen as EventListener);
      window.removeEventListener("mapai:closeSurvey", onClose as EventListener);
    };
  }, []);

  const { total_responses, total_faculties } = useSummary(faculty);
  const nf = React.useMemo(() => new Intl.NumberFormat(), []);
  const { dist, loading } = useDistribution(selected, faculty);

  const selectedButton = useMemo(() => BUTTONS.find(b => b.id === selected), [selected]);
  const sectionColor = selectedButton?.color ?? "#64748b"; // fallback slate

  const facultyOptions = useMemo(() => {
    const items = faculties.slice().sort((a, b) => a.name.localeCompare(b.name));
    return items;
  }, [faculties]);

  const facultyLabel = faculty === "All" ? "All Faculties" : faculty;

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            onClick={() => setOpen(false)}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[9998]"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-[9999] flex items-center justify-center p-4"
            onClick={() => setOpen(false)}
          >
            <div
              onClick={(e) => e.stopPropagation()}
              className="bg-white rounded-3xl shadow-2xl w-full max-w-5xl max-h-[90vh] overflow-hidden"
            >
              {/* Header */}
              <div className="relative bg-gradient-to-br from-slate-800 to-slate-900 p-8 border-b border-slate-700">
                <button
                  onClick={() => setOpen(false)}
                  className="absolute top-6 right-6 p-2 rounded-full bg-white/10 hover:bg-white/20 text-white transition-all duration-200 hover:scale-110"
                  aria-label="Close"
                >
                  <X className="w-5 h-5" />
                </button>

                {/* TOP ROW: Left = title; Right = faculty dropdown */}
                <div className="flex items-start justify-between gap-4 mb-2" style={{alignItems: 'center', marginRight: '37px'}}>
                  {/* Left: Icon + Title + Subtitle */}
                  <div className="flex items-center gap-3">
                    <div className="p-3 rounded-xl bg-blue-500/20 text-blue-300">
                      <BarChart3 className="w-8 h-8" /> {/* bigger icon */}
                    </div>
                    <div>
                      <h2 className="text-[34px] leading-tight font-light text-white">
                        Survey Overview
                      </h2>
                      <p className="text-slate-300 text-sm mt-1">General demographic metrics</p>
                    </div>
                  </div>

                  {/* Right: Faculty selector */}
                  <div className="flex items-center gap-2">
                    <div className="flex items-center gap-2 text-white">
                      <School className="w-6 h-6 opacity-90" /> {/* bigger icon */}
                      <span className="text-base font-medium">Faculty</span> {/* bigger label */}
                    </div>
                    <label htmlFor="faculty-select" className="sr-only">Faculty</label>
                    <select
                      id="faculty-select"
                      value={faculty}
                      onChange={(e) => setFaculty(e.target.value as any)}
                      className={
                        "faculty-select px-3 py-2 rounded-lg text-sm shadow-sm " +
                        "bg-gradient-to-br from-slate-800 to-slate-900 text-white " + // same as header
                        "border border-white/30 " +
                        "focus:outline-none focus:ring-2 focus:ring-blue-300/60"
                      }
                    >
                      <option value="All">All Faculties</option>
                      {facultyOptions.map((f) => (
                        <option key={f.name} value={f.name}>
                          {f.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-2 gap-4 mt-4">
                  {/* LEFT KPI: Selected faculty + responses */}
                  <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-6 border border-white/10">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="p-2 rounded-lg bg-blue-500/20">
                        <Users className="w-5 h-5 text-blue-400" />
                      </div>
                      <p className="text-slate-300 text-sm font-medium uppercase tracking-wide">
                        {facultyLabel}
                      </p>
                    </div>
                    <div className="flex items-baseline gap-2">
                      <span className="text-5xl font-bold text-white">
                        {nf.format(Number(total_responses) || 0)}
                      </span>
                      <span className="text-slate-400 text-lg">responses</span>
                    </div>
                  </div>

                  {/* RIGHT KPI: Total faculties (global) */}
                  <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-6 border border-white/10">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="p-2 rounded-lg bg-purple-500/20">
                        <Building2 className="w-5 h-5 text-purple-400" />
                      </div>
                      <p className="text-slate-300 text-sm font-medium uppercase tracking-wide">
                        Total Faculties
                      </p>
                    </div>
                    <div className="flex items-baseline gap-2">
                      <span className="text-5xl font-bold text-white">{total_faculties}</span>
                      <span className="text-slate-400 text-lg">faculties</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Content */}
              <div className="p-8 overflow-y-auto max-h-[calc(90vh-320px)]">
                {/* Buttons */}
                <div className="mb-8">
                  <h3 className="text-lg font-medium text-slate-700 mb-4">Demographic Breakdown</h3>
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
                    {BUTTONS.map((b) => {
                      const isSel = selected === b.id;
                      return (
                        <button
                          key={b.id}
                          onClick={() => setSelected(b.id)}
                          className="relative p-4 rounded-xl border-2 transition-all duration-200 hover:scale-105 hover:shadow-lg"
                          style={{ borderColor: isSel ? b.color : "#e2e8f0", background: isSel ? `${b.color}10` as any : "#fff" }}
                        >
                          <div className="p-2 rounded-lg mb-2 inline-flex" style={{ background: `${b.color}20`, color: b.color }}>
                            {b.icon}
                          </div>
                          <p className="text-sm font-medium" style={{ color: isSel ? b.color : "#475569" }}>
                            {b.label}
                          </p>
                          {isSel && (
                            <motion.div
                              layoutId="sel-ind"
                              className="absolute bottom-0 left-0 right-0 h-1 rounded-b-xl"
                              style={{ background: b.color }}
                              initial={false}
                              transition={{ duration: 0.2 }}
                            />
                          )}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Chart area */}
                <AnimatePresence mode="wait">
                  {selected ? (
                    <motion.div
                      key={`${selected}-${faculty}`}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -20 }}
                      transition={{ duration: 0.2 }}
                      className="rounded-2xl border-2 border-dashed p-6"
                      style={{
                        minHeight: CARD_MIN_HEIGHT,
                        borderColor: (selectedButton?.color ?? "#94a3b8") + "40",
                        background: (selectedButton?.color ?? "#94a3b8") + "0A",
                      }}
                    >
                      {loading ? (
                        <div
                          className="w-full bg-slate-100 animate-pulse rounded-xl"
                          style={{ height: CHART_HEIGHT }}
                        />
                      ) : dist.categories.length === 0 ? (
                        <div className="text-center py-16 text-slate-500">No data.</div>
                      ) : (
                        <Plot
                          data={[
                            {
                              x: dist.categories,
                              y: dist.counts,
                              type: "bar" as const,
                              hovertemplate: "<b>%{x}</b><br>Responses: %{y}<extra></extra>",
                              marker: {
                                color: sectionColor,
                                opacity: 0.95,
                                line: { width: 1, color: "rgba(0,0,0,0.25)" },
                              },
                            },
                          ]}
                          layout={{
                            title: { text: "", y: 0.98 },
                            margin: { t: 10, l: 60, r: 20, b: 80 },
                            yaxis: { title: "Responses", rangemode: "tozero" },
                            xaxis: { tickangle: 0, automargin: true },
                            paper_bgcolor: "rgba(0,0,0,0)",
                            plot_bgcolor: "rgba(0,0,0,0)",
                          }}
                          style={{ width: "100%", height: CHART_HEIGHT }}
                          config={{ displayModeBar: false }}
                        />
                      )}
                    </motion.div>
                  ) : (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="rounded-2xl bg-slate-50 border-2 border-slate-200 p-8 flex items-center justify-center"
                      style={{ minHeight: CARD_MIN_HEIGHT }}
                    >
                      <div className="text-center">
                        <div className="inline-flex p-4 rounded-full bg-slate-200 mb-4">
                          <BarChart3 className="w-8 h-8 text-slate-400" />
                        </div>
                        <h3 className="text-xl font-medium text-slate-600 mb-2">Select a Demographic Category</h3>
                        <p className="text-slate-500">Choose a category above to view its distribution</p>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default SurveyOverviewWC;
