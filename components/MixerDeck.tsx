import React, { useState } from 'react';
import { DialogueSegment } from '../types';

interface MixerDeckProps {
  lastTake: string | null;
  segments: DialogueSegment[] | null;
  onProjectFinish: () => void;
  directorNotes: string;
  setDirectorNotes: (val: string) => void;
}

const MixerDeck: React.FC<MixerDeckProps> = ({ lastTake, onProjectFinish, directorNotes, setDirectorNotes }) => {
  const [isExporting, setIsExporting] = useState(false);
  
  const tracks = [
    { id: 'dub', name: "Neural Dub (L3)", level: 90, gain: "+1.1x", color: "bg-primary" },
    { id: 'cues', name: "Human Cues (L2)", level: 80, gain: "1.0x", color: "bg-accent" },
    { id: 'world', name: "World Stem (L1)", level: 65, gain: "0.8x", color: "bg-secondary" },
  ];

  return (
    <div className="p-8 h-full flex flex-col space-y-6 bg-white dark:bg-slate-950 transition-colors overflow-y-auto">
      <div className="bg-slate-900 dark:bg-slate-900 rounded-[32px] p-8 text-white relative overflow-hidden">
        <div className="relative z-10">
          <p className="text-primary text-[10px] font-black uppercase tracking-widest mb-2">Master Continuity</p>
          <h3 className="font-display font-black text-3xl tracking-tight">Surgical Mixer</h3>
          
          <div className="grid grid-cols-3 gap-4 mt-8">
             {tracks.map(t => (
               <div key={t.id} className="p-4 bg-white/5 rounded-2xl border border-white/10">
                  <div className="flex justify-between items-center mb-1">
                    <p className="text-[9px] font-bold text-slate-500 uppercase">{t.id}_Bus</p>
                  </div>
                  <p className="text-xs font-bold">{t.name}</p>
                  <p className="text-[11px] font-mono text-secondary mt-2">{t.gain}</p>
               </div>
             ))}
          </div>
        </div>
      </div>

      <div className="flex gap-4 overflow-x-auto pb-4">
        {tracks.map((track) => (
          <div key={track.id} className="bg-slate-50 dark:bg-slate-900/50 p-6 rounded-2xl border border-slate-100 dark:border-slate-800 flex flex-col items-center min-w-[180px]">
            <div className="h-64 w-12 bg-slate-200 dark:bg-slate-800 rounded-full relative mb-6 flex justify-center py-4">
              <div className="absolute w-8 h-12 bg-white dark:bg-slate-100 rounded-xl shadow-md border border-slate-200 dark:border-slate-800 cursor-pointer transition-all"
                style={{ bottom: `calc(${track.level}% - 24px)` }}>
              </div>
            </div>
            <div className="text-center">
              <div className="text-[11px] font-bold dark:text-white uppercase mb-3">{track.name}</div>
              <div className="flex gap-2">
                <button className="px-3 py-1.5 rounded-lg bg-slate-900 dark:bg-slate-800 text-[9px] font-bold text-white uppercase">Mute</button>
                <button className="px-3 py-1.5 rounded-lg bg-white dark:bg-slate-700 text-[9px] font-bold text-slate-500 dark:text-slate-300 border border-slate-200 dark:border-slate-600 uppercase">Solo</button>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      <div className="mt-auto bg-slate-50 dark:bg-slate-900 p-6 rounded-[24px] border border-slate-200 dark:border-slate-800 flex items-center justify-between">
        <div className="flex gap-8 px-4">
          <div>
            <p className="text-[10px] font-bold text-slate-400 uppercase mb-1">Peak</p>
            <p className="text-lg font-mono font-bold dark:text-white">-0.12dB</p>
          </div>
          <div>
            <p className="text-[10px] font-bold text-slate-400 uppercase mb-1">Phase</p>
            <p className="text-lg font-mono font-bold text-emerald-500">OK</p>
          </div>
        </div>
        
        <button 
          onClick={() => setIsExporting(true)}
          className="gradient-btn text-white px-10 py-4 rounded-xl font-bold text-xs uppercase tracking-widest shadow-lg"
        >
          {isExporting ? 'ENCODING...' : 'EXPORT MASTER'}
        </button>
      </div>
    </div>
  );
};

export default MixerDeck;