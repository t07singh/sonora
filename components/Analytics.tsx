import React from 'react';

const Analytics: React.FC = () => {
  const stats = [
    { label: 'Sync Fidelity', value: '0.94', trend: '+0.02', color: 'text-primary' },
    { label: 'Emotion Index', value: '88.4%', trend: '+1.5%', color: 'text-accent' },
    { label: 'Node Latency', value: '14ms', trend: '-2ms', color: 'text-secondary' },
  ];

  return (
    <div className="p-10 h-full overflow-y-auto bg-white dark:bg-slate-950 transition-colors">
      <header className="mb-10">
        <h2 className="text-2xl font-display font-bold dark:text-white tracking-tight">System Telemetry</h2>
        <p className="text-xs text-slate-400 uppercase mt-1">Real-time inference distribution</p>
      </header>
      
      <div className="grid grid-cols-3 gap-6 mb-10">
        {stats.map((stat, i) => (
          <div key={i} className="p-6 bg-slate-50 dark:bg-slate-900 rounded-2xl border border-slate-100 dark:border-slate-800">
            <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">{stat.label}</div>
            <div className="flex items-baseline gap-3">
              <div className={`text-4xl font-display font-black tracking-tighter ${stat.color}`}>{stat.value}</div>
              <div className="text-[10px] font-bold text-emerald-500">{stat.trend}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="p-8 bg-slate-50 dark:bg-slate-900 rounded-[32px] border border-slate-100 dark:border-slate-800">
        <div className="flex justify-between items-center mb-10">
          <h3 className="text-sm font-black dark:text-white uppercase tracking-widest">Swarm Distribution</h3>
          <div className="flex gap-2">
            <span className="px-3 py-1 bg-white dark:bg-slate-800 text-[10px] font-bold rounded-lg border border-slate-100 dark:border-slate-700 dark:text-slate-300">12Hz Processing</span>
          </div>
        </div>
        
        <div className="flex items-end justify-between h-48 gap-2">
          {[75, 45, 95, 30, 85, 90, 65, 100, 55, 80].map((h, i) => (
            <div key={i} className="flex-1 bg-slate-200 dark:bg-slate-800 rounded-lg relative overflow-hidden group">
              <div 
                className="absolute bottom-0 w-full bg-gradient-to-t from-primary to-accent transition-all duration-700"
                style={{ height: `${h}%` }}
              ></div>
            </div>
          ))}
        </div>
        <div className="flex justify-between mt-4">
           {Array.from({length: 10}).map((_, i) => (
             <span key={i} className="text-[8px] font-bold text-slate-400">NODE_{i+1}</span>
           ))}
        </div>
      </div>
    </div>
  );
};

export default Analytics;