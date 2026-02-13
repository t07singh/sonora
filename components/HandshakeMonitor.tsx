
import React, { useRef, useEffect } from 'react';

interface HandshakeMonitorProps {
  logs: { id: string, msg: string, type: 'info' | 'warn' | 'success' }[];
}

const HandshakeMonitor: React.FC<HandshakeMonitorProps> = ({ logs }) => {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  return (
    <div className="h-full flex flex-col p-4">
      <h3 className="text-[10px] font-bold text-amber-800 uppercase tracking-widest mb-4 border-b border-amber-900/20 pb-2">
        Handshake_Protocol_Feed
      </h3>
      <div className="flex-1 overflow-y-auto space-y-3 font-mono text-[10px]">
        {logs.map((log) => (
          <div key={log.id} className="flex gap-2 animate-in fade-in slide-in-from-right-1 duration-300">
            <span className="text-amber-900 shrink-0">[{new Date().toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}]</span>
            <span className={`
              ${log.type === 'success' ? 'text-green-600' : ''}
              ${log.type === 'warn' ? 'text-red-500' : ''}
              ${log.type === 'info' ? 'text-amber-600' : ''}
            `}>
              {log.msg}
            </span>
          </div>
        ))}
        <div ref={endRef} />
      </div>
    </div>
  );
};

export default HandshakeMonitor;
