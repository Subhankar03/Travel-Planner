import React, { useState, useEffect, useRef } from 'react';
import { Send, Navigation, ChevronDown, AlertCircle } from 'lucide-react';
import type { ChatMessage } from '../hooks/useGlideTripChat';

interface ChatPanelProps {
  messages: ChatMessage[];
  isStreaming: boolean;
  sendMessage: (content: string) => void;
  error?: string | null;
}

export default function ChatPanel({ messages, isStreaming, sendMessage, error }: ChatPanelProps) {
  const [query, setQuery] = useState('');
  const endOfMessagesRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Scroll to bottom whenever messages array changes or streaming
    endOfMessagesRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isStreaming]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isStreaming) {
      sendMessage(query);
      setQuery('');
    }
  };

  return (
    <div className="flex flex-col h-full bg-background relative">
      {/* Header */}
      <header className="flex-none p-5 lg:p-6 flex items-center gap-2">
        <Navigation className="w-5 h-5 text-primary" fill="currentColor" />
        <span className="font-bold text-xl tracking-tight text-primary">GlideTrip</span>
      </header>

      {/* Chat Feed */}
      <div className="flex-1 overflow-y-auto px-5 lg:px-8 pb-32">
        <div className="flex flex-col gap-8 max-w-2xl mx-auto w-full pt-4">
          {messages.map((msg, idx) => (
            <div key={msg.id || idx} className={`w-full flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
              
              {/* User Message */}
              {msg.role === 'user' && (
                <div className="bg-primary text-white px-6 py-3 rounded-full text-[15px] shadow-sm max-w-[85%]">
                  {msg.content}
                </div>
              )}

              {/* AI Message */}
              {msg.role === 'assistant' && (
                <div className="w-full flex flex-col items-start max-w-[95%]">
                  
                  {/* Process Expander (Mock) */}
                  {msg.process && (
                    <button className="flex items-center gap-2 bg-surfaceAlt text-text-primary px-3 py-1.5 rounded-t-lg text-sm border border-b-0 border-divider/50 hover:bg-primary-light transition-colors mb-2 mt-4 cursor-pointer">
                      <ChevronDown className="w-4 h-4 text-text-secondary" />
                      {msg.process}
                    </button>
                  )}

                  {/* AI Content - Editorial style, no bubble */}
                  <div className="text-text-primary text-base leading-relaxed tracking-normal font-normal max-w-none prose prose-p:my-2 prose-ul:my-2">
                    {/* Render plain text for now. We can add Markdown rendering later if needed. */}
                    {msg.content.split('\n').map((line, i) => (
                      <span key={i}>
                        {line}
                        <br />
                      </span>
                    ))}
                  </div>
                </div>
              )}

            </div>
          ))}

          {error && (
            <div className="w-full flex items-center gap-3 p-4 rounded-xl bg-red-50 text-red-600 outline outline-1 outline-red-200 mt-4">
               <AlertCircle className="w-5 h-5" />
               <span className="text-[15px] font-medium">{error}</span>
            </div>
          )}
          
          <div ref={endOfMessagesRef} className="h-4" />
        </div>
      </div>

      {/* Input Bar */}
      <div className="absolute bottom-0 w-full p-5 lg:p-8 bg-gradient-to-t from-background via-background to-transparent pb-8">
        <form onSubmit={handleSubmit} className="max-w-2xl mx-auto relative group">
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask about your trip..."
            rows={1}
            className="w-full min-h-[56px] px-5 py-4 pr-14 rounded-2xl border border-divider shadow-warm focus:outline-none focus:border-primary focus:ring-4 focus:ring-primary/10 transition-all text-text-primary placeholder:text-text-muted bg-surface resize-none overflow-hidden"
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e);
              }
            }}
          />
          <button
            type="submit"
            disabled={!query.trim()}
            className="absolute right-3 top-3 w-9 h-9 rounded-full bg-primary text-white flex items-center justify-center hover:bg-primary-hover disabled:bg-primary-light transition-colors"
          >
            <Send className="w-4 h-4 ml-0.5" />
          </button>
        </form>
      </div>
    </div>
  );
}
