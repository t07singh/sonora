
import React, { useState, useEffect } from 'react';

interface SwarmDashboardProps {
  addLog: (msg: string, type?: 'info' | 'warn' | 'success') => void;
}

const SwarmDashboard: React.FC<SwarmDashboardProps> = ({ addLog }) => {
  const [metrics, setMetrics] = useState({ cpu: 42, ram: 65, latency: 97 });
  
  useEffect(() => {
    const interval = setInterval(() => {
      setMetrics(prev => ({
        cpu: Math.min(100, Math.max(0, prev.cpu + (Math.random() * 10 - 5))),
        ram: Math.min(100, Math.max(0, prev.ram + (Math.random() * 2 - 1))),
        latency: 97 + (Math.random() * 4 - 2)
      }));
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  const agents = [
    { name: 'Qwen3-TTS-0.6B', role: 'Vocal Synthesis', status: 'Online', load: 88, tokenizer: '12Hz' },
    { name: 'Vibe-Reasoning', role: 'Context Mapping', status: 'Online', load: 34, tokenizer: '25Hz' },
    { name: 'Orchestrator', role: 'Handshake Control', status: 'Standby', load: 5, tokenizer: 'N/A' },
  ];

  return (
    <div className="flex-1 p-8 space-y-8 bg-[#080808]">
      <div className="grid grid-cols-3 gap-6">
        <div className="border border-amber-900/20 bg-black/40 p-5 rounded-lg">
          <div className="text-[10px] text-amber-700 mb-2 font-bold tracking-widest uppercase">Global CPU Pulse</div>
          <div className="text-3xl font-light text-amber-500">{metrics.cpu.toFixed(1)}%</div>
          <div className="w-full bg-amber-950 h-1 mt-4 rounded-full overflow-hidden">
            <div className="h-full bg-amber-500 transition-all duration-500" style={{ width: `${metrics.cpu}%` }} />
          </div>
        </div>
        <div className="border border-amber-900/20 bg-black/40 p-5 rounded-lg">
          <div className="text-[10px] text-amber-700 mb-2 font-bold tracking-widest uppercase">Handshake Latency</div>
          <div className="text-3xl font-light text-green-500">{metrics.latency.toFixed(0)}ms</div>
          <div className="text-[10px] text-green-900 mt-2">Target: &lt;100ms</div>
        </div>
        <div className="border border-amber-900/20 bg-black/40 p-5 rounded-lg">
          <div className="text-[10px] text-amber-700 mb-2 font-bold tracking-widest uppercase">9P VHDX Health</div>
          <div className="text-3xl font-light text-blue-500">OPTIMAL</div>
          <div className="text-[10px] text-blue-900 mt-2">Mode: Write-Through</div>
        </div>
      </div>

      <div className="space-y-4">
        <h2 className="text-xs font-bold text-amber-600 tracking-[0.2em] border-b border-amber-900/20 pb-2">ACTIVE_SWARM_NODES</h2>
        <div className="space-y-2">
          {agents.map((agent) => (
            <div key={agent.name} className="flex items-center justify-between p-4 border border-amber-900/10 bg-black hover:bg-amber-950/5 transition-colors group">
              <div className="flex items-center gap-4">
                <div className={`w-2 h-2 rounded-full ${agent.status === 'Online' ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.5)]' : 'bg-amber-900 animate-pulse'}`}></div>
                <div>
                  <div className="text-xs font-bold text-amber-100">{agent.name}</div>
                  <div className="text-[10px] text-amber-800 uppercase">{agent.role}</div>
                </div>
              </div>
              <div className="flex items-center gap-8">
                <div className="text-right">
                  <div className="text-[10px] text-amber-900 uppercase">Load</div>
                  <div className="text-xs text-amber-500">{agent.load}%</div>
                </div>
                <div className="text-right">
                  <div className="text-[10px] text-amber-900 uppercase">Clock</div>
                  <div className="text-xs text-amber-500">{agent.tokenizer}</div>
                </div>
                <button 
                  onClick={() => addLog(`Command sent to ${agent.name}: RE-SYNC`, 'info')}
                  className="px-3 py-1 border border-amber-900/40 text-[10px] text-amber-600 hover:bg-amber-500 hover:text-black transition-all"
                >
                  REBOOT
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="p-6 border-2 border-dashed border-amber-900/20 rounded-xl">
        <div className="flex items-center gap-3 mb-4">
          <svg className="w-5 h-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <h3 className="text-sm font-bold text-red-500 uppercase tracking-widest">Architectural Advisory: WSL2 9P Lag</h3>
        </div>
        <p className="text-[11px] text-amber-700 leading-relaxed max-w-2xl italic">
          CRITICAL: Polling `/tmp/sonora` on a Windows host mount may cause "Zombie Audio" artifacts due to Plan-9 caching. 
          Recommendation: Migrate all shared_data nodes to native WSL VHDX partition `/home/architect/sonora/shared` to enforce Atomic Write visibility.
        </p>
      </div>
    </div>
  );
};

export default SwarmDashboard;
