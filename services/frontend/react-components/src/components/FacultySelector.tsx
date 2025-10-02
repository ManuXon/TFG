import React, { useState } from 'react';
import { GraduationCap, ChevronRight } from 'lucide-react';

interface Faculty {
  name: string;
  color: string;
}

const faculties: Faculty[] = [
  { "name": "Fine Arts", "color": "#FF5733" },
  { "name": "Biology", "color": "#33FF57" },
  { "name": "Earth Sciences", "color": "#3357FF" },
  { "name": "Law", "color": "#FF33A1" },
  { "name": "Economics and Business", "color": "#33FFA1" },
  { "name": "Education", "color": "#A133FF" },
  { "name": "Pharmacy and Food Sciences", "color": "#FFA133" },
  { "name": "Philology and Communication", "color": "#33A1FF" },
  { "name": "Philosophy", "color": "#FF5733" },
  { "name": "Physics", "color": "#A1FF33" },
  { "name": "Geography and History", "color": "#FF3333" },
  { "name": "Information and Audiovisual Media", "color": "#33FF33" },
  { "name": "Nursing", "color": "#337FFF" },
  { "name": "Mathematics and Computer Science", "color": "#FF33FF" },
  { "name": "Medicine and Health Sciences", "color": "#333FFF" },
  { "name": "Psychology", "color": "#FFFF33" },
  { "name": "Chemistry", "color": "#FF6F33" }
];

interface FacultySelectorProps {
  onFacultySelect?: (faculty: Faculty) => void;
}

const FacultySelector: React.FC<FacultySelectorProps> = ({ onFacultySelect }) => {
  const [hoveredCard, setHoveredCard] = useState<string | null>(null);

  const handleFacultyClick = (faculty: Faculty) => {
    if (onFacultySelect) {
      onFacultySelect(faculty);
    }
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
          {faculties.map((faculty, index) => (
            <div
              key={faculty.name}
              className={`
                relative group cursor-pointer transform transition-all duration-300 ease-out
                ${hoveredCard === faculty.name ? 'scale-105 -translate-y-2' : 'hover:scale-102 hover:-translate-y-1'}
              `}
              onMouseEnter={() => setHoveredCard(faculty.name)}
              onMouseLeave={() => setHoveredCard(null)}
              onClick={() => handleFacultyClick(faculty)}
              style={{
                animationDelay: `${index * 50}ms`
              }}
            >
              {/* Card */}
              <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden h-32 relative group-hover:shadow-xl transition-shadow duration-300">
                {/* Color accent bar */}
                <div
                  className="absolute top-0 left-0 right-0 h-1"
                  style={{ backgroundColor: faculty.color }}
                />

                {/* Content */}
                <div className="p-6 h-full flex flex-col justify-between">
                  <div>
                    <h3 className="font-medium text-slate-800 text-lg leading-tight mb-2">
                      {faculty.name}
                    </h3>
                  </div>

                  {/* Bottom section with color indicator and arrow */}
                  <div className="flex items-center justify-between">
                    <div
                      className="w-4 h-4 rounded-full shadow-sm"
                      style={{ backgroundColor: faculty.color }}
                    />
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
          ))}
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
