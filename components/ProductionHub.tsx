
import React, { useState, useRef } from 'react';
import { Project, QueueItem, CharacterProfile } from '../types';

interface ProductionHubProps {
  profiles: CharacterProfile[];
  setProfiles: React.Dispatch<React.SetStateAction<CharacterProfile[]>>;
  addLog: (msg: string, type?: 'info' | 'warn' | 'success') => void;
}

const ProductionHub: React.FC<ProductionHubProps> = ({ profiles, setProfiles, addLog }) => {
  const [activeTab, setActiveTab] = useState<'QUEUE' | 'PROJECTS' | 'QA' | 'VOICES'>('PROJECTS');
  const seriesInputRef = useRef<HTMLInputElement>(null);
  const batchInputRef = useRef<HTMLInputElement>(null);
  const digitizeInputRef = useRef<HTMLInputElement>(null);
  const [isDigitizing, setIsDigitizing] = useState(false);

  // Mock Data
  const [queue, setQueue] = useState<QueueItem[]>([
    { id: '1', filename: 'S01E01_Master.mp4', project: 'Hero Academia', episode: 'S01E01', priority: 'NORMAL', status: 'COMPLETED', progress: 1.0 },
    { id: '2', filename: 'S01E02_Master.mp4', project: 'Hero Academia', episode: 'S01E02', priority: 'NORMAL', status: 'PROCESSING', progress: 0.65 },
    { id: '3', filename: 'S01E03_Rush.mp4', project: 'Hero Academia', episode: 'S01E03', priority: 'URGENT', status: 'QUEUED', progress: 0 },
  ]);

  const [projects, setProjects] = useState<Project[]>([
    { id: 'p1', name: 'My Hero Academia S05', episodes: 12, completed: 8, characters: ['Deku', 'Bakugo'], lastUpdate: Date.now() },
    { id: 'p2', name: 'Demon Slayer S03', episodes: 12, completed: 12, characters: ['Tanjiro', 'Nezuko'], lastUpdate: Date.now() },
  ]);

  const handleDigitize = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setIsDigitizing(true);
      addLog(`Vocal Digitization: Analyzing ${file.name}...`, "info");
      
      // Simulate Gemini analysis of vocal traits
      await new Promise(r => setTimeout(r, 2000));
      
      const name = file.name.split('.')[0].toUpperCase();
      const newProfile: CharacterProfile = {
        id: `v${profiles.length + 1}`,
        name,
        consistency: 0.99,
        version: 'v1.0-STABLE',
        isLocked: true,
        traits: ['Deep', 'Commanding', 'Protagonist']
      };
      
      setProfiles([...profiles, newProfile]);
      addLog(`Asset Locked: ${name} vocal identity secured to production vault.`, "success");
      setIsDigitizing(false);
      if (digitizeInputRef.current) digitizeInputRef.current.value = '';
    }
  };

  const handleCreateNewSeries = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const newProject: Project = {
        id: `p${projects.length + 1}`,
        name: file.name.split('.')[0].replace(/_/g, ' '),
        episodes: 24,
        completed: 0,
        characters: ['NEW'],
        lastUpdate: Date.now()
      };
      setProjects([newProject, ...projects]);
      addLog(`Project Created: Series ${newProject.name} added to scale.`, "success");
      if (seriesInputRef.current) seriesInputRef.current.value = '';
    }
  };

  return (
    <div className="p-8 h-full overflow-y-auto space-y-8 animate-in fade-in duration-500">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-3xl font-['Outfit'] font-black text-slate-800 tracking-tight">Production Scale</h2>
        <div className="flex gap-1 p-1.5 bg-slate-100 rounded-2xl shadow-inner">
          {(['QUEUE', 'PROJECTS', 'QA', 'VOICES'] as const).map((t) => (
            <button
              key={t}
              onClick={() => setActiveTab(t)}
              className={`px-8 py-2.5 rounded-xl text-[10px] font-black tracking-widest transition-all ${
                activeTab === t ? 'bg-white text-[#FF7EB9] shadow-md' : 'text-slate-400 hover:text-slate-600'
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {activeTab === 'QUEUE' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center bg-white p-8 rounded-[32px] shadow-sm border border-slate-100 relative overflow-hidden">
            <div className="absolute -left-10 top-0 w-20 h-full bg-[#7EB9FF]/5 blur-2xl"></div>
            <div>
              <h3 className="text-sm font-black text-slate-800 uppercase tracking-tight">Batch Queue Manager</h3>
              <p className="text-[10px] text-slate-400 font-bold uppercase mt-2 tracking-widest flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-[#7EB9FF] animate-pulse"></div>
                Parallel Swarm Tasks: 04 ACTIVE
              </p>
            </div>
            <div className="relative">
              <input type="file" multiple className="hidden" ref={batchInputRef} accept="video/*" />
              <button 
                onClick={() => batchInputRef.current?.click()}
                className="gradient-btn text-white px-8 py-4 rounded-2xl text-[10px] font-black tracking-widest shadow-xl active:scale-95 transition-all"
              >
                UPLOAD EPISODE BATCH
              </button>
            </div>
          </div>
          
          <div className="grid gap-4">
            {queue.map((item) => (
              <div key={item.id} className="bg-white p-6 rounded-[24px] shadow-sm border border-slate-50 flex items-center justify-between group hover:border-[#FF7EB9]/30 hover:shadow-md transition-all">
                <div className="flex items-center gap-6">
                  <div className={`w-3 h-3 rounded-full ${item.status === 'COMPLETED' ? 'bg-emerald-400 shadow-[0_0_10px_#10b981]' : item.status === 'PROCESSING' ? 'bg-blue-400 animate-pulse' : 'bg-slate-200'}`}></div>
                  <div>
                    <div className="text-sm font-black text-slate-800">{item.filename}</div>
                    <div className="text-[10px] text-slate-400 font-bold uppercase mt-1 tracking-wider">{item.project} • {item.episode}</div>
                  </div>
                </div>
                <div className="flex items-center gap-10">
                  <div className={`text-[9px] font-black px-4 py-1.5 rounded-full uppercase tracking-tighter ${item.priority === 'URGENT' ? 'bg-rose-50 text-rose-500 border border-rose-100' : 'bg-slate-50 text-slate-400 border border-slate-100'}`}>
                    {item.priority}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'VOICES' && (
        <div className="space-y-10">
          <div className="anime-card p-10 bg-slate-900 border-none relative overflow-hidden group">
             <div className="absolute top-0 right-0 p-10 opacity-20">
                <div className="w-24 h-24 rounded-full border-4 border-[#B97EFF] animate-ping"></div>
             </div>
             <div className="relative z-10 max-w-xl">
                <h3 className="text-white text-3xl font-['Outfit'] font-black uppercase tracking-tight mb-4">Cross-Lingual Assignment</h3>
                <p className="text-slate-400 text-sm font-medium leading-relaxed mb-10">Assign original character identities to the English dub stream. Sonora maintains the actor's unique timbre, grit, and emotional range across the language gap.</p>
                
                <div className="group relative inline-block">
                  <button className="gradient-btn text-white px-12 py-5 rounded-2xl text-xs font-black tracking-[0.2em] shadow-2xl hover:scale-105 active:scale-95 transition-all">
                    LOCK ORIGINAL IDENTITY
                  </button>
                  <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-4 w-64 p-4 bg-white rounded-2xl shadow-2xl border border-slate-100 opacity-0 group-hover:opacity-100 pointer-events-none transition-all">
                    <p className="text-[10px] text-slate-600 font-bold text-center leading-relaxed">
                      <span className="text-[#FF7EB9]">✨ SONORA MAGIC:</span> Sonora will extract the Japanese timbre and transfer it to English phonemes. Language-agnostic soul preserved.
                    </p>
                    <div className="absolute top-full left-1/2 -translate-x-1/2 w-3 h-3 bg-white border-b border-r border-slate-100 rotate-45 -mt-1.5"></div>
                  </div>
                </div>
             </div>
          </div>

          <div className="grid grid-cols-3 gap-8">
            {profiles.map((v) => (
              <div key={v.id} className="anime-card p-8 bg-white relative overflow-hidden group hover:shadow-xl transition-all border-none">
                <div className={`absolute top-0 left-0 w-1.5 h-full ${v.isLocked ? 'bg-emerald-400' : 'bg-[#7EB9FF]'}`}></div>
                <h4 className="text-xl font-black text-slate-800 mb-6 uppercase">{v.name}</h4>
                <div className="flex flex-wrap gap-1.5 mb-8">
                  {v.traits.map(trait => (
                     <span key={trait} className="px-3 py-1 bg-slate-50 text-slate-500 rounded-lg text-[8px] font-black uppercase border border-slate-100">{trait}</span>
                  ))}
                </div>
                <div className="space-y-5">
                  <div className="flex justify-between items-center">
                    <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Consistency</span>
                    <span className="text-[11px] font-black text-[#FF7EB9]">{v.consistency * 100}%</span>
                  </div>
                  <div className="h-1.5 w-full bg-slate-50 rounded-full overflow-hidden">
                    <div className="h-full bg-gradient-to-r from-[#FF7EB9] to-[#B97EFF]" style={{ width: `${v.consistency * 100}%` }}></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'PROJECTS' && (
        <div className="grid grid-cols-2 gap-8">
          {projects.map((proj) => (
            <div key={proj.id} className="anime-card p-10 bg-white group hover:shadow-2xl transition-all border-none relative overflow-hidden">
              <div className="flex justify-between items-start mb-8">
                <div>
                  <h3 className="text-2xl font-black text-slate-800 tracking-tight leading-tight uppercase">{proj.name}</h3>
                </div>
              </div>
              <div className="space-y-5">
                <div className="flex justify-between text-[11px] font-black text-slate-500 uppercase tracking-widest">
                  <span>Episodes Processed</span>
                  <span className="text-slate-800">{proj.completed} / {proj.episodes}</span>
                </div>
                <div className="h-2.5 w-full bg-slate-50 rounded-full overflow-hidden shadow-inner">
                  <div className="h-full bg-gradient-to-r from-[#FF7EB9] to-[#B97EFF]" style={{ width: `${(proj.completed / proj.episodes) * 100}%` }}></div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ProductionHub;
