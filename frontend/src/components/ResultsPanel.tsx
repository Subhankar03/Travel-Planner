import { useState } from 'react';
import { PlaneTakeoff, Hotel as HotelIcon, MapPin, Star } from 'lucide-react';
import type { ResultsStore, Flight, Hotel, Place } from '../hooks/useGlideTripChat';

interface ResultsPanelProps {
  results: ResultsStore;
}

export default function ResultsPanel({ results }: ResultsPanelProps) {
  const [activeTab, setActiveTab] = useState<'flights' | 'hotels' | 'places'>('flights');

  const tabs = [
    { id: 'flights', label: `Flights (${results.flights.length})`, icon: <PlaneTakeoff className="w-4 h-4" /> },
    { id: 'hotels', label: `Hotels (${results.hotels.length})`, icon: <HotelIcon className="w-4 h-4" /> },
    { id: 'places', label: `Places (${results.places.length})`, icon: <MapPin className="w-4 h-4" /> },
  ] as const;

  return (
    <div className="flex flex-col h-full w-full bg-surface">
      {/* Sticky Tabs */}
      <div className="sticky top-0 z-20 flex gap-6 px-8 pt-6 border-b border-divider bg-surface">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as 'flights' | 'hotels' | 'places')}
            className={`flex items-center gap-2 pb-4 text-[15px] font-medium transition-colors relative ${
              activeTab === tab.id ? 'text-primary' : 'text-text-secondary hover:text-text-primary'
            }`}
          >
            {tab.icon}
            {tab.label}
            {activeTab === tab.id && (
              <span className="absolute bottom-0 left-0 w-full h-[2px] bg-primary rounded-t-full" />
            )}
          </button>
        ))}
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto px-8 py-6 pb-4">
        {activeTab === 'flights' && (
          <div className="flex flex-col gap-4">
            {results.flights.length === 0 ? (
               <div className="flex items-center justify-center p-10 border border-dashed border-divider rounded-2xl text-text-muted">
                 No flights found yet. Ask me to search!
               </div>
            ) : (
               results.flights.map((flight, i) => <FlightCard key={i} data={flight} />)
            )}
          </div>
        )}
        
        {activeTab === 'hotels' && (
          <div className="flex flex-col gap-4">
            {results.hotels.length === 0 ? (
               <div className="flex items-center justify-center p-10 border border-dashed border-divider rounded-2xl text-text-muted">
                 No hotels found yet. Ask me to search!
               </div>
            ) : (
               results.hotels.map((hotel, i) => <HotelCard key={i} data={hotel} />)
            )}
          </div>
        )}

        {activeTab === 'places' && (
          <div className="flex flex-col gap-4">
            {results.places.length === 0 ? (
               <div className="flex items-center justify-center p-10 border border-dashed border-divider rounded-2xl text-text-muted">
                 No places explored yet.
               </div>
            ) : (
               results.places.map((place, i) => <PlaceCard key={i} data={place} />)
            )}
          </div>
        )}
      </div>

      {/* Map Area */}
      <div className="h-[40%] min-h-[300px] border-t border-divider relative bg-surfaceAlt flex items-center justify-center z-0">
         <div className="text-text-muted flex flex-col items-center gap-2">
            <MapPin className="w-8 h-8 opacity-50" />
            <span>Map integration coming soon...</span>
         </div>
      </div>
    </div>
  );
}

function FlightCard({ data }: { data: Flight }) {
  // Try to parse out the flight details if structure exists, else fallback
  const airline = data.airline || 'Flight';
  const price = data.price ? `₹${data.price}` : 'Price unknown';
  const dep = data.departure_time || 'TBD';
  const arr = data.arrival_time || 'TBD';
  const ori = data.origin || '';
  const dest = data.destination || '';

  return (
    <div className="w-full bg-surface border border-divider rounded-[14px] p-5 flex items-center justify-between hover:shadow-warm transition-shadow group">
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 bg-surfaceAlt rounded-xl flex items-center justify-center text-text-secondary font-bold border border-divider/50 text-xs text-center p-1 wrap-break-words">
          {airline.substring(0, 4).toUpperCase()}
        </div>
        <div className="flex flex-col">
          <span className="font-semibold text-text-primary text-[15px]">{dep} {ori} &rarr; {arr} {dest}</span>
          <span className="text-text-secondary text-sm">{airline}</span>
        </div>
      </div>
      <div className="flex flex-col items-end gap-2">
        <span className="font-bold text-semantic-price">{price}</span>
        <button className="px-4 py-1.5 rounded-lg bg-surfaceAlt text-primary text-sm font-medium hover:bg-primary-light transition-colors">
          Select
        </button>
      </div>
    </div>
  );
}

function HotelCard({ data }: { data: Hotel }) {
  const name = data.name || data.hotel_name || 'Hotel';
  const price = data.price ? `₹${data.price} / night` : 'Price unknown';
  const loc = data.location || data.address || '';
  const rating = typeof data.rating === 'string' ? parseInt(data.rating) : (data.rating || 4);

  return (
    <div className="w-full bg-surface border border-divider rounded-[14px] p-4 flex items-center gap-5 hover:shadow-warm transition-shadow group">
      <div className="w-24 h-24 bg-surfaceAlt rounded-xl shrink-0 relative overflow-hidden border border-divider/50 flex items-center justify-center">
         <HotelIcon className="w-8 h-8 text-divider" />
      </div>
      <div className="flex flex-col flex-1 h-full py-1">
        <span className="font-semibold text-text-primary text-[15px]">{name}</span>
        <div className="flex items-center gap-1 text-semantic-star mt-1">
          {Array.from({ length: rating }).map((_, i) => (
              <Star key={i} className="w-3.5 h-3.5 fill-current" />
          ))}
        </div>
        <span className="text-text-secondary text-sm mt-auto">{loc}</span>
      </div>
      <div className="flex flex-col items-end justify-between h-full py-1 gap-4">
        <span className="font-bold text-semantic-price whitespace-nowrap">{price}</span>
        <button className="px-4 py-1.5 rounded-lg bg-primary text-white text-sm font-medium hover:bg-primary-hover transition-colors shadow-sm shadow-primary/20">
          Details
        </button>
      </div>
    </div>
  );
}

function PlaceCard({ data }: { data: Place }) {
  const name = (data.title as string) || (data.name as string) || 'Place';
  const address = (data.address as string) || '';
  const type = (data.type as string) || '';
  const rating = (data.rating as number) ?? 0;
  const description = (data.description as string) || '';
  const thumbnail = data.thumbnail as string | undefined;

  return (
    <div className="w-full bg-surface border border-divider rounded-[14px] overflow-hidden hover:shadow-warm transition-shadow flex">
      {/* Thumbnail */}
      <div className="w-24 shrink-0 bg-surfaceAlt relative overflow-hidden flex items-center justify-center">
        {thumbnail ? (
          <img src={thumbnail} alt={name} className="w-full h-full object-cover" />
        ) : (
          <MapPin className="w-7 h-7 text-divider" />
        )}
      </div>

      {/* Info */}
      <div className="flex flex-col flex-1 px-4 py-3 gap-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <span className="font-semibold text-text-primary text-[14px] leading-snug line-clamp-2">{name}</span>
          {type && (
            <span className="shrink-0 text-[11px] font-medium text-semantic-places bg-semantic-places/10 px-2 py-0.5 rounded-full">
              {type}
            </span>
          )}
        </div>

        {rating > 0 && (
          <div className="flex items-center gap-1">
            <Star className="w-3 h-3 text-semantic-star fill-current" />
            <span className="text-[13px] font-medium text-text-body">{rating}</span>
          </div>
        )}

        {(description || address) && (
          <p className="text-[12px] text-text-secondary line-clamp-2 mt-auto">
            {description || address}
          </p>
        )}
      </div>
    </div>
  );
}
