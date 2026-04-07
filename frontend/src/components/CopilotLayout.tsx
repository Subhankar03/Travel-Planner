
import { useEffect, useRef } from 'react';
import ChatPanel from './ChatPanel';
import ResultsPanel from './ResultsPanel';
import { useGlideTripChat } from '../hooks/useGlideTripChat';

interface CopilotLayoutProps {
  initialQuery: string;
}

export default function CopilotLayout({ initialQuery }: CopilotLayoutProps) {
  const { messages, results, isStreaming, error, sendMessage } = useGlideTripChat();
  const initRef = useRef(false);

  useEffect(() => {
    if (!initRef.current && initialQuery) {
      initRef.current = true;
      sendMessage(initialQuery, []);
    }
  }, [initialQuery, sendMessage]);

  return (
    <div className="flex h-screen w-full bg-background overflow-hidden relative">
      {/* Divider Line in the middle */}
      <div className="absolute left-[45%] top-0 bottom-0 w-px bg-divider z-10 hidden md:block" />

      {/* Left Panel: Chat */}
      <div className="w-full md:w-[45%] h-full flex flex-col relative z-20 bg-background">
        <ChatPanel 
          messages={messages} 
          isStreaming={isStreaming} 
          sendMessage={sendMessage} 
          error={error} 
        />
      </div>

      {/* Right Panel: Results & Map */}
      <div className="hidden md:flex w-[55%] h-full flex-col bg-surface z-0 relative">
        <ResultsPanel results={results} />
      </div>
    </div>
  );
}
