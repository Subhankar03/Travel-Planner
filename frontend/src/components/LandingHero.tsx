import React, { useState } from 'react';
import { Send, Plane, Compass, Briefcase, Map, Camera, PlaneTakeoff, Hotel, MapPin, Navigation } from 'lucide-react';

interface LandingHeroProps {
  onStart: (query: string) => void;
}

export default function LandingHero({ onStart }: LandingHeroProps) {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onStart(query);
    }
  };

  const handleChipClick = (text: string) => {
    onStart(text);
  };

  return (
    <div className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden">
      {/* Navigation */}
      <nav className="absolute top-0 w-full p-6 flex justify-between items-center z-10">
        <div className="flex items-center gap-2 text-text-primary">
          <Navigation className="w-5 h-5 text-primary" fill="currentColor" />
          <span className="font-bold text-xl tracking-tight">GlideTrip</span>
        </div>
      </nav>

      {/* Floating Decorative Elements (Doodles) */}
      <div className="absolute inset-0 pointer-events-none opacity-40">
        <Plane className="absolute top-[20%] right-[15%] w-12 h-12 text-divider animate-[bounce_3s_ease-in-out_infinite]" />
        <Compass className="absolute bottom-[25%] left-[20%] w-14 h-14 text-divider animate-[bounce_4s_ease-in-out_infinite_reverse]" />
        <Briefcase className="absolute top-[40%] left-[10%] w-10 h-10 text-divider animate-[bounce_3.5s_ease-in-out_infinite]" />
        <Map className="absolute top-[50%] right-[10%] w-16 h-16 text-divider animate-[bounce_4.5s_ease-in-out_infinite_reverse]" />
        <Camera className="absolute bottom-[15%] right-[25%] w-12 h-12 text-divider animate-[bounce_3s_ease-in-out_infinite]" />
      </div>

      {/* Main Content */}
      <main className="w-full max-w-3xl px-6 z-10 flex flex-col items-center text-center -mt-16">
        <h1 className="text-5xl font-bold text-text-primary mb-4 tracking-tight">
          GlideTrip
        </h1>
        <p className="text-lg text-text-secondary mb-10 font-normal">
          One conversation. Complete travel plan.
        </p>

        {/* Input Field */}
        <form onSubmit={handleSubmit} className="w-full max-w-2xl relative mb-8 group">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Where do you want to go?"
            className="w-full h-14 pl-6 pr-14 rounded-2xl border border-divider shadow-sm focus:outline-none focus:border-primary focus:ring-4 focus:ring-primary/10 transition-all text-text-primary placeholder:text-text-muted bg-surface"
          />
          <button
            type="submit"
            disabled={!query.trim()}
            className="absolute right-2 top-2 w-10 h-10 rounded-full bg-primary text-white flex items-center justify-center hover:bg-primary-hover disabled:bg-primary-light transition-colors"
          >
            <Send className="w-4 h-4 ml-0.5" />
          </button>
        </form>

        {/* Prompt Chips */}
        <div className="flex flex-wrap items-center justify-center gap-3 mb-10">
          {[
            { icon: '✈️', text: 'Weekend getaway to Goa' },
            { icon: '🏔️', text: 'Budget trip to Manali' },
            { icon: '🌴', text: 'Luxury Kochi escape' },
          ].map((chip, idx) => (
            <button
              key={idx}
              onClick={() => handleChipClick(chip.text)}
              className="flex items-center gap-2 px-4 py-2 rounded-full bg-primary-light text-text-primary text-sm hover:bg-primary-subtle hover:scale-[1.02] transition-all"
            >
              <span>{chip.icon}</span>
              <span>{chip.text}</span>
            </button>
          ))}
        </div>

        {/* Capability Badges */}
        <div className="flex items-center justify-center gap-6">
          <Badge icon={<PlaneTakeoff className="w-3.5 h-3.5" />} text="Flights" />
          <Badge icon={<Hotel className="w-3.5 h-3.5" />} text="Hotels" />
          <Badge icon={<MapPin className="w-3.5 h-3.5" />} text="Local Places" />
        </div>
      </main>

      {/* Footer */}
      <footer className="absolute bottom-6 w-full text-center text-xs text-text-muted">
        Powered by Gemini &middot; LangGraph &middot; SerpAPI
      </footer>
    </div>
  );
}

function Badge({ icon, text }: { icon: React.ReactNode; text: string }) {
  return (
    <div className="flex items-center gap-1.5 px-3 py-1 rounded-full border border-divider text-xs text-text-secondary">
      {icon}
      <span>{text}</span>
    </div>
  );
}
