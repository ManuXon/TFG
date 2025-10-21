import React, { useEffect, useState } from 'react';
import {
  GraduationCap,
  ChevronRight,
  Palette,
  Microscope,
  Globe,
  Scale,
  TrendingUp,
  BookOpen,
  Pill,
  MessageSquare,
  Brain,
  Atom,
  Map,
  Video,
  Heart,
  Calculator,
  Stethoscope,
  Users,
  FlaskConical
} from 'lucide-react';

/** ---------- ScoreIndicator (same as your other components) ---------- */
const getScoreColor = (score: number): string => {
  if (score >= 80) return "#22c55e";
  if (score >= 60) return "#84cc16";
  if (score >= 40) return "#eab308";
  if (score >= 20) return "#f97316";
  return "#ef4444";
};

const ScoreIndicator: React.FC<{ score: number }> = ({ score }) => {
  const color = getScoreColor(score);
  const percentage = Math.max(0, Math.min(100, score || 0));
  return (
    <div className="flex items-center justify-center">
      <div className="relative w-12 h-12">
        <svg className="w-12 h-12 transform -rotate-90">
          <circle cx="24" cy="24" r="20" stroke="#e5e7eb" strokeWidth="4" fill="none" />
          <circle
            cx="24"
            cy="24"
            r="20"
            stroke={color}
            strokeWidth="4"
            fill="none"
            strokeDasharray={`${2 * Math.PI * 20}`}
            strokeDashoffset={`${2 * Math.PI * 20 * (1 - percentage / 100)}`}
            strokeLinecap="round"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-xs font-semibold text-slate-700">{Math.round(percentage)}</span>
        </div>
      </div>
    </div>
  );
};
/** ------------------------------------------------------------------- */

interface Faculty {
  name: string;
  color: string;
  icon: React.ReactNode;
}

const faculties: Faculty[] = [
  { name: "Fine Arts", color: "#E6194B", icon: <Palette className="w-6 h-6" /> },
  { name: "Biology", color: "#3CB44B", icon: <Microscope className="w-6 h-6" /> },
  { name: "Earth Sciences", color: "#0082C8", icon: <Globe className="w-6 h-6" /> },
  { name: "Law", color: "#F58231", icon: <Scale className="w-6 h-6" /> },
  { name: "Economics and Business", color: "#911EB4", icon: <TrendingUp className="w-6 h-6" /> },
  { name: "Education", color: "#46F0F0", icon: <BookOpen className="w-6 h-6" /> },
  { name: "Pharmacy", color: "#F032E6", icon: <Pill className="w-6 h-6" /> },
  { name: "Philology", color: "#FABEBE", icon: <MessageSquare className="w-6 h-6" /> },
  { name: "Philosophy", color: "#008080", icon: <Brain className="w-6 h-6" /> },
  { name: "Physics", color: "#AA6E28", icon: <Atom className="w-6 h-6" /> },
  { name: "Geography and History", color: "#FFD8B1", icon: <Map className="w-6 h-6" /> },
  { name: "Audiovisual Media", color: "#000075", icon: <Video className="w-6 h-6" /> },
  { name: "Nursing", color: "#808000", icon: <Heart className="w-6 h-6" /> },
  { name: "Maths and CS", color: "#9A6324", icon: <Calculator className="w-6 h-6" /> },
  { name: "Medicine", color: "#4363D8", icon: <Stethoscope className="w-6 h-6" /> },
  { name: "Psychology", color: "#FFE119", icon: <Users className="w-6 h-6" /> },
  { name: "Chemistry", color: "#DCBEFF", icon: <FlaskConical className="w-6 h-6" /> }
];

interface FacultySelectorProps {
  onFacultySelect?: (faculty: Faculty) => void;
}

type FacultyScores = {
  knowledge_score: number | null;
  uses_score: number | null;
  perceptions_score: number | null;
  training_needs_score: number | null;
  total_score: number | null; // mean of the four
};

/** Short display names for cards only */
const shortDisplayName = (name: string) => {
  if (name === "Economics and Business") return "Economics";
  if (name === "Geography and History") return "Geography";
  if (name === "Audiovisual Media") return "Media";
  return name;
};

const API_BASE = "http://localhost:8000";

const average = (arr: any[]) => {
  const nums = arr.map(Number).filter((n) => Number.isFinite(n));
  if (!nums.length) return null;
  return nums.reduce((a, b) => a + b, 0) / nums.length;
};

async function fetchAllFacultyScores(): Promise<Record<string, FacultyScores>> {
  const entries = await Promise.all(
    faculties.map(async (f) => {
      try {
        const res = await fetch(
          `${API_BASE}/api/faculty/${encodeURIComponent(f.name)}/scores`,
          { cache: "no-store" }
        );
        if (!res.ok) throw new Error(`${res.status}`);
        const data = await res.json();
        const item: FacultyScores = {
          knowledge_score: data.knowledge_score ?? null,
          uses_score: data.uses_score ?? null,
          perceptions_score: data.perceptions_score ?? null,
          training_needs_score: data.training_needs_score ?? null,
          total_score:
            typeof data.total_score === "number"
              ? data.total_score
              : average([
                  data.knowledge_score,
                  data.uses_score,
                  data.perceptions_score,
                  data.training_needs_score,
                ]),
        };
        return [f.name, item] as const;
      } catch {
        return [f.name, { knowledge_score: null, uses_score: null, perceptions_score: null, training_needs_score: null, total_score: null }] as const;
      }
    })
  );
  return Object.fromEntries(entries);
}

const FacultySelector: React.FC<FacultySelectorProps> = ({ onFacultySelect }) => {
  const [hoveredCard, setHoveredCard] = useState<string | null>(null);
  const [scores, setScores] = useState<Record<string, FacultyScores>>({});

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const map = await fetchAllFacultyScores();
      if (!cancelled) setScores(map);
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const handleFacultyClick = (faculty: Faculty) => {
    onFacultySelect?.(faculty);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 py-12 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center mb-4">
            <GraduationCap className="w-8 h-8 text-slate-600 mr-3" />
            <h1 className="text-4xl font-light text-slate-800">University of Barcelona</h1>
          </div>
          <p className="text-slate-600 text-lg font-light">
            Select a faculty to explore its data visualizations
          </p>
        </div>

        {/* Faculty Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {faculties.map((faculty, index) => {
            const displayName = shortDisplayName(faculty.name);
            const total = scores[faculty.name]?.total_score;

            return (
              <div
                key={faculty.name}
                className={`
                  relative group cursor-pointer transform transition-all duration-300 ease-out
                  ${hoveredCard === faculty.name ? 'scale-105 -translate-y-2' : 'hover:scale-102 hover:-translate-y-1'}
                `}
                onMouseEnter={() => setHoveredCard(faculty.name)}
                onMouseLeave={() => setHoveredCard(null)}
                onClick={() => handleFacultyClick(faculty)}
                style={{ animationDelay: `${index * 50}ms` }}
              >
                {/* Card */}
                <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden h-32 relative group-hover:shadow-xl transition-shadow duration-300">
                  {/* Color accent bar */}
                  <div
                    className="absolute top-0 left-0 right-0 h-1"
                    style={{ backgroundColor: faculty.color }}
                  />

                  {/* Content (made relative for absolute indicator) */}
                  <div className="p-6 h-full flex flex-col justify-between relative">
                    {/* Score indicator: top-right, inside content */}
                    {typeof total === "number" ? (
                      <div className="absolute top-3 right-3 pointer-events-none">
                        <ScoreIndicator score={total} />
                      </div>
                    ) : (
                      <div
                        className="absolute top-11 right-20 w-14 h-14 rounded-full border-2 border-dashed border-slate-200"
                        title="Loading score..."
                      />
                    )}

                    {/* Title (padded-right, so it doesn't collide with indicator) */}
                    <h3 className="font-medium text-slate-800 text-lg leading-tight mb-2 pr-20">
                      {displayName}
                    </h3>

                    {/* Bottom row: icon (left) + chevron (right) */}
                    <div className="flex items-center justify-between">
                      <div
                        className="p-2 rounded-lg"
                        style={{ backgroundColor: `${faculty.color}20` }}
                      >
                        <div style={{ color: faculty.color }}>
                          {faculty.icon}
                        </div>
                      </div>

                      <ChevronRight
                        className={`
                          w-5 h-5 text-slate-400 transition-all duration-200
                          ${hoveredCard === faculty.name ? 'text-slate-600 translate-x-1' : ''}
                        `}
                      />
                    </div>
                  </div>

                  {/* Hover overlay */}
                  <div
                    className={`
                      absolute inset-0 opacity-0 group-hover:opacity-5 transition-opacity duration-300
                    `}
                    style={{ backgroundColor: faculty.color }}
                  />
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer note */}
        <div className="text-center mt-12">
          <p className="text-slate-500 text-sm">
            Click on any faculty card to explore detailed visualizations and analytics
          </p>
        </div>
      </div>
    </div>
  );
};

export default FacultySelector;
