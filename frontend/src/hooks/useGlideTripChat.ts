import { useState, useRef, useCallback, useEffect } from 'react';
import { fetchEventSource } from '@microsoft/fetch-event-source';
import { v4 as uuidv4 } from 'uuid';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  /** Process steps that ran during this message (persisted after streaming ends). */
  steps?: string[];
}

export interface Flight {
  airline?: string;
  price?: number | string;
  departure_time?: string;
  arrival_time?: string;
  origin?: string;
  destination?: string;
  [key: string]: unknown;
}

export interface Hotel {
  name?: string;
  hotel_name?: string;
  price?: number | string;
  location?: string;
  address?: string;
  rating?: number | string;
  [key: string]: unknown;
}

export interface Place {
  name?: string;
  title?: string;
  description?: string;
  address?: string;
  type?: string;
  rating?: number;
  thumbnail?: string;
  gps_coordinates?: { latitude: number; longitude: number };
  [key: string]: unknown;
}

export interface ResultsStore {
  flights: Flight[];
  hotels: Hotel[];
  places: Place[];
}

// ── Location helper ─────────────────────────────────────────────────────────
async function getBrowserLocation(): Promise<string> {
  try {
    const res = await fetch('https://ipinfo.io/json');
    if (!res.ok) {
      return 'Unknown Location';
    }
    const data = await res.json();
    const city = data.city || 'Unknown City';
    const region = data.region || 'Unknown Region';
    return `${city}, ${region}`;
  } catch (error) {
    console.error('Failed to get location via IP:', error);
    return 'Unknown Location';
  }
}

// ── Parse raw tool output for places ────────────────────────────────────────
function parsePlacesPayload(raw: unknown): Place[] {
  if (Array.isArray(raw)) {
    // Already a flat array of place objects
    if (raw.length > 0 && typeof raw[0] === 'object' && raw[0] !== null) {
      if ('places' in (raw[0] as object)) {
        // Array of category objects → flatten
        return (raw as { places: Place[] }[]).flatMap((cat) => cat.places ?? []);
      }
      // Direct array of places
      return raw as Place[];
    }
  }
  if (raw && typeof raw === 'object') {
    const obj = raw as Record<string, unknown>;
    // Single category object: { category_label, places: [...] }
    if (Array.isArray(obj.places)) {
      return obj.places as Place[];
    }
    // Wrapped: { result: [ { places: [...] }, ... ] }
    if (Array.isArray(obj.result)) {
      return (obj.result as { places?: Place[] }[]).flatMap((cat) => cat.places ?? []);
    }
    if (Array.isArray(obj.results)) {
      return (obj.results as { places?: Place[] }[]).flatMap((cat) => cat.places ?? []);
    }
  }
  return [];
}

export function useGlideTripChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [results, setResults] = useState<ResultsStore>({ flights: [], hotels: [], places: [] });
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [userLocation, setUserLocation] = useState<string>('Unknown Location');

  const threadIdRef = useRef(uuidv4());

  // Resolve location on mount
  useEffect(() => {
    getBrowserLocation().then(setUserLocation);
  }, []);

  const updateLastAIMessage = useCallback((updates: Partial<ChatMessage>) => {
    setMessages((prev) => {
      const last = prev[prev.length - 1];
      if (!last || last.role === 'user') {
        return [...prev, { id: uuidv4(), role: 'assistant', content: '', ...updates }];
      }
      const newArr = [...prev];
      newArr[newArr.length - 1] = { ...last, ...updates };
      return newArr;
    });
  }, []);

  const appendStep = useCallback((step: string) => {
    setMessages((prev) => {
      const last = prev[prev.length - 1];
      if (!last || last.role === 'user') {
        return [...prev, { id: uuidv4(), role: 'assistant', content: '', steps: [step] }];
      }
      const newArr = [...prev];
      const existing = last.steps ?? [];
      newArr[newArr.length - 1] = { ...last, steps: [...existing, step] };
      return newArr;
    });
  }, []);

  const appendResult = useCallback((toolName: string, data: unknown) => {
    setResults((prev) => {
      if (toolName === 'search_flights') {
        const newFlights = Array.isArray(data) ? (data as Flight[]) : [data as Flight];
        return { ...prev, flights: [...prev.flights, ...newFlights] };
      }
      if (toolName === 'search_hotels') {
        const newHotels = Array.isArray(data) ? (data as Hotel[]) : [data as Hotel];
        return { ...prev, hotels: [...prev.hotels, ...newHotels] };
      }
      if (toolName === 'search_local_places') {
        const places = parsePlacesPayload(data);
        return { ...prev, places: [...prev.places, ...places] };
      }
      return prev;
    });
  }, []);

  const sendMessage = useCallback(
    async (content: string, overrideMessages?: ChatMessage[]) => {
      const currentMessages = overrideMessages ?? messages;
      const userMsg: ChatMessage = { id: uuidv4(), role: 'user', content };
      const newMessages = [...currentMessages, userMsg];

      setMessages(newMessages);
      setIsStreaming(true);
      setError(null);

      let currentAIContent = '';

      try {
        await fetchEventSource('http://127.0.0.1:8000/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            messages: newMessages.map((m) => ({ role: m.role, content: m.content })),
            thread_id: threadIdRef.current,
            user_location: userLocation,
          }),
          onmessage(ev) {
            if (ev.data === '[DONE]') return;
            try {
              const data = JSON.parse(ev.data);

              switch (data.type) {
                case 'text-delta':
                  currentAIContent += data.delta;
                  updateLastAIMessage({ content: currentAIContent });
                  break;
                case 'tool-input-start': {
                  const toolLabel = (data.toolName as string)
                    .replace('search_', '')
                    .replace(/_/g, ' ')
                    .replace(/\b\w/g, (c: string) => c.toUpperCase());
                  appendStep(`Searching ${toolLabel}...`);
                  break;
                }
                case 'data-search_flights':
                case 'data-search_hotels':
                case 'data-search_local_places':
                case 'data-get_route_directions':
                  appendResult(data.type.replace('data-', ''), data.data);
                  break;
                case 'error':
                  setError(data.errorText || 'An error occurred during generation.');
                  break;
              }
            } catch (e) {
              console.error('Failed to parse SSE data chunk', e, ev.data);
            }
          },
          onclose() {
            setIsStreaming(false);
          },
          onerror(err) {
            console.error('SSE Error:', err);
            setError('Lost connection to backend.');
            setIsStreaming(false);
            throw err; // Stop retrying
          },
        });
      } catch (err) {
        console.error('fetchEventSource caught:', err);
        setIsStreaming(false);
      }
    },
    [messages, updateLastAIMessage, appendStep, appendResult, userLocation],
  );

  return { messages, results, isStreaming, error, sendMessage };
}
