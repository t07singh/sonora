import React from 'react';
import { AppMode, SwarmState } from '../types';

interface SidebarProps {
  activeMode: AppMode;
  onModeChange: (mode: AppMode) => void;
  swarmStatus: SwarmState;
}

const Sidebar: React.FC<SidebarProps> = ({ activeMode, onModeChange }) => {
  const modes = [
    { id: AppMode.HUB, label: 'Studio Hub', icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6' },
    { id: AppMode.ANALYTICS, label: 'Analytics', icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z' },
    { id: AppMode.MIXER, label: 'Mixer Deck', icon: 'M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4' },
    { id: AppMode.PRODUCTION, label: 'Production', icon: 'M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4' },
    { id: AppMode.CORE, label: 'Nuclear Core', icon: 'M13 10V3L4 14h7v7l9-11h-7z' },
    { id: AppMode.CLOUD_SYNC, label: 'Cloud Hub', icon: 'M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z' },
    { id: AppMode.WALKTHROUGH, label: 'Guide', icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z' },
  ];

  return (
    <aside className="w-64 bg-slate-50 dark:bg-slate-950 h-screen flex flex-col p-6 transition-colors duration-300">
      <div className="mb-10 px-2 flex flex-col">
        <span className="text-2xl font-display font-black tracking-tighter text-slate-900 dark:text-white uppercase italic">
          Sonora
        </span>
        <span className="text-[9px] font-black uppercase tracking-[0.4em] text-primary/80 -mt-1 ml-0.5">
          Workstation Core
        </span>
      </div>

      <nav className="flex-1 space-y-1.5">
        {modes.map((mode) => (
          <button
            key={mode.id}
            onClick={() => onModeChange(mode.id)}
            className={`w-full flex items-center gap-4 px-4 py-3 rounded-2xl transition-all duration-200 group ${
              activeMode === mode.id
                ? 'bg-white dark:bg-slate-900 text-primary shadow-sm border border-slate-200 dark:border-slate-800'
                : 'text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-900/50'
            }`}
          >
            <div className={`p-2 rounded-lg transition-colors ${activeMode === mode.id ? 'bg-primary/10' : 'bg-transparent'}`}>
              <svg className={`w-4 h-4 ${activeMode === mode.id ? 'stroke-primary' : 'stroke-current opacity-70 group-hover:opacity-100'}`} fill="none" viewBox="0 0 24 24" strokeWidth={activeMode === mode.id ? 2.5 : 2}>
                <path strokeLinecap="round" strokeLinejoin="round" d={mode.icon} />
              </svg>
            </div>
            <span className="text-[11px] font-black tracking-widest uppercase">{mode.label}</span>
          </button>
        ))}
      </nav>

      <div className="mt-auto p-5 bg-white/50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-3xl transition-colors">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-8 h-8 rounded-xl bg-primary/20 flex items-center justify-center text-primary font-black text-xs shadow-inner">A</div>
            <div>
               <div className="text-[10px] font-black dark:text-white leading-none uppercase">Aiko L.</div>
               <div className="text-[8px] text-slate-400 font-bold uppercase mt-1">Lead Architect</div>
            </div>
          </div>
          <div className="space-y-1.5">
             <div className="flex justify-between text-[8px] font-black text-slate-400 uppercase tracking-widest">
                <span>Memory usage</span>
                <span className="text-primary">68%</span>
             </div>
             <div className="h-1.5 w-full bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden">
                <div className="h-full bg-primary" style={{ width: '68%' }}></div>
             </div>
          </div>
      </div>
    </aside>
  );
};

export default Sidebar;