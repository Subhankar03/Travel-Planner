import { useState } from 'react';
import LandingHero from './components/LandingHero';
import CopilotLayout from './components/CopilotLayout';

function App() {
  const [hasStarted, setHasStarted] = useState(false);
  const [initialQuery, setInitialQuery] = useState('');

  const handleStart = (query: string) => {
    setInitialQuery(query);
    setHasStarted(true);
  };

  return (
    <div className="min-h-screen bg-background text-text-body font-sans selection:bg-primary-light selection:text-text-primary">
      {!hasStarted ? (
        <LandingHero onStart={handleStart} />
      ) : (
        <CopilotLayout initialQuery={initialQuery} />
      )}
    </div>
  );
}

export default App;
