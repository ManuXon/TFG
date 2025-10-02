import React, { useState } from 'react';
import FacultySelector from './components/FacultySelector';
import FacultyVisualization from './components/FacultyVisualization';

interface Faculty {
  name: string;
  color: string;
}

function App() {
  const [selectedFaculty, setSelectedFaculty] = useState<Faculty | null>(null);

  const handleFacultySelect = (faculty: Faculty) => {
    setSelectedFaculty(faculty);
  };

  const handleBackToSelector = () => {
    setSelectedFaculty(null);
  };

  return (
    <div className="App">
      {!selectedFaculty ? (
        <FacultySelector onFacultySelect={handleFacultySelect} />
      ) : (
        <FacultyVisualization
          faculty={selectedFaculty}
          onBack={handleBackToSelector}
        />
      )}
    </div>
  );
}

export default App;
