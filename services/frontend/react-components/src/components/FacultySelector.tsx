import React, { useState } from 'react';
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

/** Short display names for cards only */
const shortDisplayName = (name: string) => {
  if (name === "Economics and Business") return "Economics";
  if (name === "Geography and History") return "Geography";
  if (name === "Audiovisual Media") return "Media";
  return name;
};

const FacultySelector: React.FC<FacultySelectorProps> = ({ onFacultySelect }) => {
  const [hoveredCard, setHoveredCard] = useState<string | null>(null);

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

            return (
              <div
                key={faculty.name || `faculty-${index}`}   // ← add this
                className={`
                  relative cursor-pointer transform transition-all duration-300 ease-out
                  ${hoveredCard === faculty.name ? 'scale-105 -translate-y-2' : ''}
                `}
                onMouseEnter={() => setHoveredCard(faculty.name)}
                onMouseLeave={() => setHoveredCard(null)}
                onClick={() => handleFacultyClick(faculty)}
                style={{ animationDelay: `${index * 50}ms` }}
              >
              {/* Card */}
              <div
                className="bg-white rounded-2xl shadow-sm overflow-hidden h-32 relative transition-shadow duration-300"
                style={{
                  boxShadow:
                    hoveredCard === faculty.name
                      ? '0 12px 28px rgba(2, 6, 23, 0.12)'
                      : '0 2px 6px rgba(2, 6, 23, 0.06)',
                  border: hoveredCard === faculty.name
                    ? `1px solid ${faculty.color}`
                    : '1px solid #e2e8f0', // neutral
                }}
              >
                {/* Accent bar */}
                <div
                  className="absolute top-0 left-0 right-0"
                  style={{ height: hoveredCard === faculty.name ? 4 : 1, backgroundColor: faculty.color, transition: 'height 200ms ease' }}
                />

                {/* Content */}
                <div className="p-6 h-full flex flex-col justify-between">
                  <h3 className="font-medium text-slate-800 text-lg leading-tight mb-2">
                    {displayName}
                  </h3>

                  <div className="flex items-center justify-between">
                    <div
                      className="p-2 rounded-lg"
                      style={{ backgroundColor: `${faculty.color}20` }}
                    >
                      <div style={{ color: faculty.color }}>{faculty.icon}</div>
                    </div>

                    <ChevronRight
                      className="w-5 h-5 transition-all duration-200"
                      style={{
                        color: hoveredCard === faculty.name ? '#334155' : '#94a3b8',
                        transform: hoveredCard === faculty.name ? 'translateX(4px)' : 'translateX(0)',
                      }}
                    />
                  </div>
                </div>

                {/* Overlay (no Tailwind group-hover) */}
                <div
                  className="absolute inset-0 pointer-events-none"
                  style={{
                    backgroundColor: faculty.color,
                    opacity: hoveredCard === faculty.name ? 0.06 : 0,
                    transition: 'opacity 300ms ease',
                  }}
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
