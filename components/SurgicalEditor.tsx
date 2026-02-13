import React, { useState } from 'react';
import { DialogueSegment } from '../types';

interface SurgicalEditorProps {
  segment: DialogueSegment;
  onCommit: (updatedSegment: DialogueSegment) => void;
  onCancel: () => void;
}

const SurgicalEditor: React.FC<SurgicalEditorProps> = ({ segment, onCommit, onCancel }) => {
  const [editedSeg, setEditedSeg] = useState<DialogueSegment>({ ...segment });
  const [isSynthesizing, setIsSynthesizing] = useState(false);

  const countSyllables = (text: string) => {
    let word = text.toLowerCase().replace(/[^a-z]/g, '');
    if (word.length <= 3) return 1;
    word = word.replace(/(?:[^laeiouy]es|ed|[^laeiouy]e)$/, '');
    word = word.replace(/^y/, '');
    const syllables = word.match(/[aeiouy]{1,2}/g);
    return syllables ? syllables.length : 1;
  };

  const calculateMoraeProgress = () => {
    const target = editedSeg.morae_count || 10;
    const words = editedSeg.translation.split(/\s+/);
    const current = words.reduce((acc, w) => acc + countSyllables(w), 0);
    const stretchRate = current / target;
    const isViolation = stretchRate > 1.3 || stretchRate < 0.8;
    return { ratio: stretchRate, current, target, isViolation };
  };

  const morae = calculateMoraeProgress();

  return (
    <div className="h-full flex flex-col bg-white dark:bg-slate-950 transition-colors">
      <header className="h-16 bg-slate-900 flex items-center px-8 justify-between text-white shadow-lg">
        <div className="flex items-center gap-4">
          <div className="px-3 py-1 bg-primary text-white text-[9px] font-black rounded uppercase tracking-widest">Surgical_Editor</div>
          <h2 className="text-sm font-bold uppercase tracking-tight">Workbench: {editedSeg.speaker_id}</h2>
        </div>
        <div className="flex gap-3">
           <button onClick={onCancel} className="px-4 py-2 text-[10px] font-bold text-slate-400 hover:text-white uppercase transition-colors">Cancel</button>
           <button 
            disabled={morae.isViolation}
            onClick={() => onCommit({ ...editedSeg, surgery_complete: true })}
            className={`px-6 py-2 rounded-lg text-[10px] font-black text-white uppercase tracking-widest transition-all ${morae.isViolation ? 'bg-slate-700 cursor-not-allowed' : 'gradient-btn'}`}
           >
            Commit Changes
           </button>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        <div className="flex-1 p-10 space-y-8 overflow-y-auto">
          <div className="space-y-4">
            <div className="flex justify-between items-end">
               <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Temporal Alignment</h3>
               <span className={`text-xl font-mono font-bold ${morae.isViolation ? 'text-rose-500' : 'text-emerald-500'}`}>{morae.current} / {morae.target}</span>
            </div>
            
            <div className="relative">
              <textarea 
                value={editedSeg.translation}
                onChange={(e) => setEditedSeg({...editedSeg, translation: e.target.value})}
                className={`w-full h-32 p-6 bg-slate-50 dark:bg-slate-900 rounded-2xl border-2 transition-all outline-none text-lg font-bold text-slate-800 dark:text-white resize-none ${morae.isViolation ? 'border-rose-500' : 'border-slate-100 dark:border-slate-800 focus:border-primary'}`}
              />
              <div className="absolute bottom-4 left-6 right-6 h-1 bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden">
                 <div className={`h-full transition-all duration-300 ${morae.isViolation ? 'bg-rose-500' : 'bg-emerald-400'}`} style={{ width: `${Math.min(1.0, morae.current / morae.target) * 100}%` }}></div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
               <div className="p-4 bg-slate-50 dark:bg-slate-900 rounded-xl border border-slate-100 dark:border-slate-800">
                  <p className="text-[9px] font-bold text-slate-400 uppercase mb-2">Original</p>
                  <p className="text-sm dark:text-slate-300 font-medium">"{editedSeg.original}"</p>
               </div>
               <div className="p-4 bg-slate-900 rounded-xl text-white">
                  <p className="text-[9px] font-bold text-slate-500 uppercase mb-2">Stretch Ratio</p>
                  <p className={`text-lg font-mono font-bold ${morae.isViolation ? 'text-rose-400' : 'text-secondary'}`}>{morae.ratio.toFixed(2)}x</p>
               </div>
            </div>
          </div>
        </div>

        <div className="w-80 bg-slate-50 dark:bg-slate-900/30 p-8 border-l border-slate-100 dark:border-slate-900 flex flex-col">
           <h3 className="text-[10px] font-black text-slate-400 uppercase mb-6">Voice Parameters</h3>
           <div className="space-y-4">
             <div>
                <p className="text-[9px] font-bold text-slate-500 uppercase mb-2">Target Emotion</p>
                <select className="w-full p-2.5 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 text-xs font-bold dark:text-white">
                   <option>Neutral</option>
                   <option>Excited</option>
                   <option>Angry</option>
                </select>
             </div>
             <button 
                onClick={() => setIsSynthesizing(true)}
                disabled={isSynthesizing || morae.isViolation}
                className="w-full py-3 bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-950 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all"
              >
                PREVIEW PERFORMANCE
              </button>
           </div>
        </div>
      </div>
    </div>
  );
};

export default SurgicalEditor;