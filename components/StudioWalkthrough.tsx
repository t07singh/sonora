
import React from 'react';

const WalkthroughStep: React.FC<{
  time: string;
  title: string;
  description: string;
  files: string[];
  icon: string;
  isEven: boolean;
  type?: 'AUTO' | 'SURGICAL';
}> = ({ time, title, description, files, icon, isEven, type = 'AUTO' }) => (
  <div className={`flex items-center w-full mb-16 ${isEven ? 'flex-row-reverse' : ''}`}>
    <div className="w-5/12">
      <div className={`anime-card p-8 bg-white hover:shadow-2xl transition-all border-none relative overflow-hidden group`}>
        <div className="absolute top-0 right-0 p-6">
          <span className={`text-[8px] font-black px-3 py-1.5 rounded-lg border uppercase tracking-widest ${type === 'SURGICAL' ? 'bg-[#FF7EB9]/10 text-[#FF7EB9] border-[#FF7EB9]/20' : 'bg-slate-100 text-slate-400 border-slate-200'}`}>
            {type}
          </span>
        </div>
        <p className="text-[#FF7EB9] text-[10px] font-black uppercase tracking-widest mb-3">{time}</p>
        <h3 className="text-xl font-black text-slate-800 mb-4">{title}</h3>
        <p className="text-sm text-slate-500 font-medium leading-relaxed mb-6">{description}</p>
        <div className="flex flex-wrap gap-2">
          {files.map(file => (
            <span key={file} className="px-3 py-1.5 bg-slate-50 text-slate-400 font-mono text-[9px] rounded-lg border border-slate-100">
              {file}
            </span>
          ))}
        </div>
      </div>
    </div>
    <div className="w-2/12 flex justify-center relative">
      <div className="w-4 h-4 bg-[#FF7EB9] rounded-full z-10 shadow-[0_0_15px_#FF7EB9] border-4 border-white"></div>
    </div>
    <div className="w-5/12"></div>
  </div>
);

const StudioWalkthrough: React.FC = () => {
  const steps = [
    {
      time: "09:00 AM",
      title: "Automated Ingestion",
      description: "Original audio is dissected into clean stems using the background core. This happens automatically for all incoming media.",
      files: ["audio_separator.py", "path_manager.py"],
      icon: "📥",
      type: "AUTO" as const
    },
    {
      time: "11:30 AM",
      title: "Neural Script Synthesis",
      description: "Gemini Pro creates the translated script. Stock dubbing performance is generated using default character profiles.",
      files: ["orchestrator.py", "vibevoice.py"],
      icon: "📜",
      type: "AUTO" as const
    },
    {
      time: "02:00 PM",
      title: "ELECTIVE: Surgical Correction",
      description: "The user identifies a specific segment needing repair. They invoke the Sound Editing Core to manually adjust lip-sync (Librosa) or re-inject Japanese artifacts.",
      files: ["bus_mixer.py", "emotional_splicer.py"],
      icon: "🔬",
      type: "SURGICAL" as const
    },
    {
      time: "04:30 PM",
      title: "Master Continuity Assembly",
      description: "The side-feature edits are merged back into the master timeline. The final master assembly produces the shipping-ready episode.",
      files: ["PostProcessor", "BusType.MASTER"],
      icon: "🚢",
      type: "AUTO" as const
    }
  ];

  return (
    <div className="p-10 h-full overflow-y-auto font-['Inter'] relative">
      <div className="max-w-4xl mx-auto py-20">
        <header className="text-center mb-32 space-y-4">
          <h2 className="text-5xl font-['Outfit'] font-black text-slate-800 tracking-tighter uppercase italic">The Studio Day</h2>
          <p className="text-slate-400 font-bold uppercase tracking-[0.6em] text-[10px]">Automated Pipeline + Surgical Interventions</p>
        </header>

        <div className="relative">
          <div className="absolute left-1/2 top-0 bottom-0 w-1 bg-slate-100 -translate-x-1/2"></div>
          {steps.map((step, i) => (
            <WalkthroughStep key={i} {...step} isEven={i % 2 !== 0} />
          ))}
        </div>
      </div>
    </div>
  );
};

export default StudioWalkthrough;
