import React, { useState, useEffect, useRef } from 'react';
import { Send, Navigation, ChevronDown, ChevronUp, Loader2, AlertCircle, Search } from 'lucide-react';
import type { ChatMessage } from '../hooks/useGlideTripChat';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface ChatPanelProps {
  messages: ChatMessage[];
  isStreaming: boolean;
  sendMessage: (content: string) => void;
  error?: string | null;
}

// ── Collapsible Steps Panel ──────────────────────────────────────────────────
function StepsExpander({ steps, isStreaming }: { steps: string[]; isStreaming: boolean }) {
  const [open, setOpen] = useState(true);
  const isActive = isStreaming && steps.length > 0;
  const lastStep = steps[steps.length - 1];

  return (
    <div className="w-full mb-3 rounded-xl border border-divider bg-surfaceAlt overflow-hidden">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center gap-2.5 px-3.5 py-2.5 text-sm text-text-secondary hover:bg-primary-light/40 transition-colors"
      >
        {isActive ? (
          <Loader2 className="w-3.5 h-3.5 text-primary animate-spin shrink-0" />
        ) : (
          <Search className="w-3.5 h-3.5 text-primary shrink-0" />
        )}
        <span className="flex-1 text-left text-text-primary font-medium truncate">
          {isActive ? lastStep : `Research (${steps.length} step${steps.length > 1 ? 's' : ''})`}
        </span>
        {open ? (
          <ChevronUp className="w-3.5 h-3.5 shrink-0" />
        ) : (
          <ChevronDown className="w-3.5 h-3.5 shrink-0" />
        )}
      </button>

      {open && (
        <div className="px-3.5 pb-2.5 flex flex-col gap-1.5 border-t border-divider/60 pt-2">
          {steps.map((step, i) => (
            <div key={i} className="flex items-center gap-2 text-[13px] text-text-secondary">
              <span
                className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                  isActive && i === steps.length - 1
                    ? 'bg-primary animate-pulse'
                    : 'bg-semantic-places'
                }`}
              />
              {step}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Typing cursor ────────────────────────────────────────────────────────────
function TypingCursor() {
  return (
    <span className="inline-block w-[2px] h-[1em] bg-primary ml-0.5 align-middle animate-[blink_0.9s_step-end_infinite]" />
  );
}

export default function ChatPanel({ messages, isStreaming, sendMessage, error }: ChatPanelProps) {
  const [query, setQuery] = useState('');
  const endOfMessagesRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isStreaming]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isStreaming) {
      sendMessage(query);
      setQuery('');
    }
  };

  // Is the last message still being streamed?
  const lastMsgIsStreaming = (idx: number) => isStreaming && idx === messages.length - 1;

  return (
    <div className="flex flex-col h-full bg-background relative">
      {/* Header */}
      <header className="flex-none p-5 lg:p-6 flex items-center gap-2">
        <Navigation className="w-5 h-5 text-primary" fill="currentColor" />
        <span className="font-bold text-xl tracking-tight text-primary">GlideTrip</span>
      </header>

      {/* Chat Feed */}
      <div className="flex-1 overflow-y-auto px-5 lg:px-8 pb-36">
        <div className="flex flex-col gap-6 max-w-2xl mx-auto w-full pt-4">
          {messages.map((msg, idx) => (
            <div
              key={msg.id || idx}
              className={`w-full flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
            >
              {/* User Message */}
              {msg.role === 'user' && (
                <div className="bg-primary text-white px-5 py-3 rounded-2xl rounded-br-sm text-[15px] shadow-sm max-w-[85%] whitespace-pre-wrap leading-relaxed">
                  {msg.content}
                </div>
              )}

              {/* AI Message */}
              {msg.role === 'assistant' && (
                <div className="w-full flex flex-col items-start">
                  {/* Collapsible steps */}
                  {(msg.steps?.length ?? 0) > 0 && (
                    <StepsExpander
                      steps={msg.steps!}
                      isStreaming={lastMsgIsStreaming(idx)}
                    />
                  )}

                  {/* AI Content */}
                  <div className="text-text-primary text-[15px] leading-relaxed font-normal max-w-none w-full prose prose-p:my-2 prose-ul:my-2 prose-ol:my-2 prose-li:my-0.5 prose-headings:font-semibold prose-headings:text-text-primary prose-a:text-primary">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {msg.content}
                    </ReactMarkdown>
                    {/* Blinking cursor while this message is being streamed */}
                    {lastMsgIsStreaming(idx) && msg.content && <TypingCursor />}
                  </div>
                </div>
              )}
            </div>
          ))}

          {/* Loading dots if streaming started but no content yet */}
          {isStreaming && messages.length > 0 && messages[messages.length - 1].role === 'user' && (
            <div className="flex items-center gap-1.5 py-1">
              <span className="w-2 h-2 rounded-full bg-primary/60 animate-bounce [animation-delay:0ms]" />
              <span className="w-2 h-2 rounded-full bg-primary/60 animate-bounce [animation-delay:150ms]" />
              <span className="w-2 h-2 rounded-full bg-primary/60 animate-bounce [animation-delay:300ms]" />
            </div>
          )}

          {error && (
            <div className="w-full flex items-center gap-3 p-4 rounded-xl bg-red-50 text-red-600 border border-red-200 mt-2">
              <AlertCircle className="w-5 h-5 shrink-0" />
              <span className="text-[14px] font-medium">{error}</span>
            </div>
          )}

          <div ref={endOfMessagesRef} className="h-4" />
        </div>
      </div>

      {/* Input Bar */}
      <div className="absolute bottom-0 w-full px-5 lg:px-8 pb-6 pt-4 bg-linear-to-t from-background via-background to-transparent">
        <form onSubmit={handleSubmit} className="max-w-2xl mx-auto relative">
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask about your trip..."
            rows={1}
            disabled={isStreaming}
            className="w-full min-h-[52px] px-5 py-3.5 pr-14 rounded-2xl border border-divider shadow-warm focus:outline-none focus:border-primary focus:ring-4 focus:ring-primary/10 transition-all text-text-primary placeholder:text-text-muted bg-surface resize-none overflow-hidden disabled:opacity-60"
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e);
              }
            }}
          />
          <button
            type="submit"
            disabled={!query.trim() || isStreaming}
            className="absolute right-3 top-2.5 w-9 h-9 rounded-full bg-primary text-white flex items-center justify-center hover:bg-primary-hover disabled:bg-primary-light transition-colors shadow-sm"
          >
            {isStreaming ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4 ml-0.5" />
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
