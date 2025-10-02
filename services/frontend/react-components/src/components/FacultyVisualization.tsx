import React, { useState } from 'react';
import { ChevronDown, ChevronUp, BookOpen, Users, Eye, GraduationCap } from 'lucide-react';

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

const dataAreas: DataArea[] = [
  {
    name: 'Knowledge',
    color: '#b91c1c',
    icon: <BookOpen className="w-6 h-6" />,
    description: 'Academic knowledge and research data'
  },
  {
    name: 'Uses',
    color: '#6b21a8',
    icon: <Users className="w-6 h-6" />,
    description: 'Usage patterns and behavioral analytics'
  },
  {
    name: 'Perceptions',
    color: '#15803d',
    icon: <Eye className="w-6 h-6" />,
    description: 'Student and faculty perceptions'
  },
  {
    name: 'Training',
    color: '#b45309',
    icon: <GraduationCap className="w-6 h-6" />,
    description: 'Training programs and development'
  }
];

interface FacultyVisualizationProps {
  faculty: Faculty;
  onBack: () => void;
}

const FacultyVisualization: React.FC<FacultyVisualizationProps> = ({ faculty, onBack }) => {
  const [expandedAreas, setExpandedAreas] = useState<Set<string>>(new Set(['Knowledge']));

  const toggleArea = (areaName: string) => {
    setExpandedAreas(prev => {
      const newSet = new Set(prev);
      if (newSet.has(areaName)) {
        newSet.delete(areaName);
      } else {
        newSet.add(areaName);
      }
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

        {/* Main Container with Faculty Color Border */}
        <div
          className="bg-white rounded-3xl shadow-lg overflow-hidden"
          style={{
            borderWidth: '3px',
            borderStyle: 'solid',
            borderColor: faculty.color
          }}
        >
          {/* Header */}
          <div className="p-8 border-b border-slate-200">
            <div className="flex items-center">
              <div
                className="w-8 h-8 rounded-full mr-4 shadow-md"
                style={{ backgroundColor: faculty.color }}
              />
              <div>
                <h1 className="text-3xl font-light text-slate-800">
                  {faculty.name}
                </h1>
                <p className="text-slate-500 text-sm mt-1">
                  Data Visualizations & Analytics
                </p>
              </div>
            </div>
          </div>

          {/* Data Areas */}
          <div className="p-6 space-y-4">
            {dataAreas.map((area, index) => {
              const isExpanded = expandedAreas.has(area.name);

              return (
                <div
                  key={area.name}
                  className="rounded-2xl overflow-hidden transition-all duration-300"
                  style={{
                    borderWidth: '2px',
                    borderStyle: 'solid',
                    borderColor: area.color,
                    backgroundColor: isExpanded ? '#ffffff' : '#fafafa'
                  }}
                >
                  {/* Area Header */}
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
                        <h2 className="text-2xl font-medium text-slate-800">
                          {area.name}
                        </h2>
                        <p className="text-slate-500 text-sm mt-1">
                          {area.description}
                        </p>
                      </div>
                    </div>

                                                                        <div
                      className="p-2 rounded-lg transition-colors duration-200"
                      style={{
                        backgroundColor: isExpanded ? `${area.color}15` : 'transparent'
                      }}
                    >
                      {isExpanded ? (
                        <ChevronUp className="w-6 h-6" style={{ color: area.color }} />
                      ) : (
                        <ChevronDown className="w-6 h-6 text-slate-400" />
                      )}
                    </div>
                  </button>

                  {/* Expandable Content Area */}
                  <div
                    className={`
                      transition-all duration-300 ease-in-out overflow-hidden
                      ${isExpanded ? 'max-h-[2000px] opacity-100' : 'max-h-0 opacity-0'}
                    `}
                  >
                    <div
                      className="p-6 border-t"
                      style={{ borderColor: `${area.color}30` }}
                    >
                      {/* Visualization Container */}
                      <div className="min-h-[400px] bg-slate-50 rounded-xl p-8 border-2 border-dashed border-slate-200">
                        <div className="text-center py-16">
                          <div
                            className="inline-flex p-4 rounded-full mb-4"
                            style={{ backgroundColor: `${area.color}15` }}
                          >
                                                                            <div style={{ color: area.color }}>
                              {area.icon}
                            </div>
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
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Footer Info */}
          <div className="p-6 bg-slate-50 border-t border-slate-200">
            <p className="text-center text-slate-500 text-sm">
              Click on each section to expand and view detailed visualizations
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FacultyVisualization;
