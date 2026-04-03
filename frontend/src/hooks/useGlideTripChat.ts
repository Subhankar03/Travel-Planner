import { useState, useRef, useCallback } from 'react';
import { fetchEventSource } from '@microsoft/fetch-event-source';
import { v4 as uuidv4 } from 'uuid';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  process?: string;
}

export interface ResultsStore {
  flights: any[];
  hotels: any[];
  places: any[];
}

export function useGlideTripChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [results, setResults] = useState<ResultsStore>({ flights: [], hotels: [], places: [] });
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const threadIdRef = useRef(uuidv4());

  const updateLastAIMessage = useCallback((updates: Partial<ChatMessage>) => {
    setMessages(prev => {
      const last = prev[prev.length - 1];
      if (!last || last.role === 'user') {
        return [...prev, { id: uuidv4(), role: 'assistant', content: '', ...updates }];
      }
      const newArr = [...prev];
      newArr[newArr.length - 1] = { ...last, ...updates };
      return newArr;
    });
  }, []);

  const appendResult = useCallback((toolName: string, data: any) => {
    setResults(prev => {
      if (toolName === 'search_flights') {
        const newFlights = Array.isArray(data) ? data : [data];
        return { ...prev, flights: [...prev.flights, ...newFlights] };
      }
      if (toolName === 'search_hotels') {
        const newHotels = Array.isArray(data) ? data : [data];
        return { ...prev, hotels: [...prev.hotels, ...newHotels] };
      }
      if (toolName === 'search_local_places') {
        const newPlaces = Array.isArray(data) ? data : [data];
        return { ...prev, places: [...prev.places, ...newPlaces] };
      }
      return prev;
    });
  }, []);

  const sendMessage = useCallback(async (content: string, overrideMessages?: ChatMessage[]) => {
    const currentMessages = overrideMessages ?? messages;
    const userMsg: ChatMessage = { id: uuidv4(), role: 'user', content };
    const newMessages = [...currentMessages, userMsg];
    
    setMessages(newMessages);
    setIsStreaming(true);
    setError(null);

    let currentAIContent = '';
    let currentProcessStr = '';

    try {
      await fetchEventSource('http://127.0.0.1:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: newMessages.map(m => ({ role: m.role, content: m.content })),
          thread_id: threadIdRef.current,
          user_location: 'Delhi, India' // Default mock location
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
              case 'tool-input-start':
                currentProcessStr = `Searching ${data.toolName.replace('search_', '').replace('_', ' ')}...`;
                updateLastAIMessage({ process: currentProcessStr });
                break;
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
          updateLastAIMessage({ process: undefined }); // clear process
        },
        onerror(err) {
          console.error('SSE Error:', err);
          setError('Lost connection to backend.');
          setIsStreaming(false);
          updateLastAIMessage({ process: undefined });
          throw err; // Stop retrying
        }
      });
    } catch (err) {
      console.error('fetchEventSource caught:', err);
      setIsStreaming(false);
    }
  }, [messages, updateLastAIMessage, appendResult]);

  return { messages, results, isStreaming, error, sendMessage };
}
