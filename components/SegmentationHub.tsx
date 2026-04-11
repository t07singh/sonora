import React, { useRef, useState, useEffect } from 'react';
import { AppMode, DialogueSegment, SwarmNodeStatus } from '../types';

interface NeuralSegment {
  id: string;
  start: number;
  end: number;
  speaker: string;
  text: string;
  clip_path: string;
  relative_clip_path: string;
}

const SegmentationHub: React.FC<{
  addLog: (msg: string, type?: any) => void;
  onProceed: (segments: DialogueSegment[]) => void;
  isProcessing: boolean;
  setIsProcessing: (v: boolean) => void;
}> = ({ addLog, onProceed, isProcessing, setIsProcessing }) => {
  const [segments, setSegments] = useState<NeuralSegment[] | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Poll for job status
  useEffect(() => {
    let interval: any;
    if (jobId && !segments) {
      interval = setInterval(async () => {
        try {
          const res = await fetch(`http://localhost:8000/api/job/${jobId}`);
          if (res.ok) {
            const data = await res.json();
            if (data.status === 'Complete') {
              setSegments(data.result.segments);
              setIsProcessing(false);
              setJobId(null);
              clearInterval(interval);
              addLog(`Neural Segmentation complete: ${data.result.segments.length} segments mapped.`, "success");
            } else if (data.status === 'Error') {
              addLog(`Segmentation Error: ${data.error}`, "warn");
              setIsProcessing(false);
              setJobId(null);
              clearInterval(interval);
            }
          }
        } catch (e) {
          console.error("Polling error", e);
        }
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [jobId, segments]);

  const handleFileSelect = async (file: File) => {
    setIsProcessing(true);
    addLog(`Pipeline: Target acquired: "${file.name}". Starting Neural Diarization...`, "system");
    
    try {
      // In a real implementation with Docker, we'd upload the file first
      // But for this "proceed" logic, we'll assume the /api/pipeline/segment understands the path
      // or we send the path if it's already in the shared volume.
      // Here we simulate the trigger.
      const response = await fetch('http://localhost:8000/api/pipeline/segment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ video_path: `/tmp/sonora/${file.name}`, project_id: 'auto' })
      });

      if (response.ok) {
        const data = await response.json();
        setJobId(data.job_id);
      } else {
        addLog("Handshake failed: Segmentation engine unreachable.", "warn");
        setIsProcessing(false);
      }
    } catch (err) {
      addLog("Network error during segmentation trigger.", "warn");
      setIsProcessing(false);
    }
  };

  const handleSpeakerChange = (id: string, newSpeaker: string) => {
    if (!segments) return;
    setSegments(segments.map(s => s.id === id ? { ...s, speaker: newSpeaker } : s));
  };

  const handleGlobalRename = (oldName: string, newName: string) => {
     if (!segments) return;
     setSegments(segments.map(s => s.speaker === oldName ? { ...s, speaker: newName } : s));
  };

  const confirmAndProceed = () => {
    if (!segments) return;
    addLog("Segmentation layout confirmed. Proceeding to Script Translation...", "success");
    
    // Map internal NeuralSegment to DialogueSegment for the rest of the app
    const dialogueSegments: DialogueSegment[] = segments.map(s => ({
      id: s.id,
      speaker_id: s.speaker,
      start: s.start,
      end: s.end,
      original: s.text,
      translation: "", // To be filled in next step
      morae_count: 0,
      syllable_count: 0,
      emotion: "neutral",
      prosody_instruction: "",
      stretch_rate: 1.0,
      spectral_match: false,
      artifacts: []
    }));
    
    onProceed(dialogueSegments);
  };

  return (
    <div className="flex flex-col h-full bg-slate-50 dark:bg-slate-950 overflow-hidden transition-colors">
      <header className="p-8 border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/50 flex justify-between items-center">
        <div>
           <h2 className="text-2xl font-display font-black dark:text-white tracking-tighter uppercase italic flex items-center gap-3">
             <span className="text-primary">01.</span> Neural Segmentation
           </h2>
           <p className="text-[10px] text-slate-400 font-bold uppercase tracking-[0.3em] mt-1">Isolating characters and sentences</p>
        </div>
        {segments && (
          <button 
            onClick={confirmAndProceed}
            className="px-8 py-3 bg-primary text-white rounded-xl font-black text-[10px] uppercase tracking-widest shadow-lg shadow-primary/20 hover:scale-105 transition-all active:scale-95"
          >
            Confirm Layout & Proceed
          </button>
        )}
      </header>

      {!segments ? (
        <div className="flex-1 flex flex-col items-center justify-center p-12">
          <div 
            onClick={() => !isProcessing && fileInputRef.current?.click()}
            className={`w-64 h-64 bg-white dark:bg-slate-900 rounded-[64px] border-4 border-dashed border-slate-200 dark:border-slate-800 flex flex-col items-center justify-center cursor-pointer hover:border-primary group transition-all shadow-xl relative overflow-hidden ${isProcessing ? 'animate-pulse' : ''}`}
          >
            {isProcessing && (
               <div className="absolute inset-0 bg-primary/5 flex items-center justify-center">
                  <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
               </div>
            )}
            <input type="file" ref={fileInputRef} className="hidden" accept="video/*" onChange={e => e.target.files && handleFileSelect(e.target.files[0])} />
            <div className="text-6xl mb-4 group-hover:scale-110 transition-transform">🎞️</div>
            <span className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-400 group-hover:text-primary transition-colors">Dissect Video</span>
          </div>
          <div className="text-center mt-8">
            <h3 className="text-lg font-black dark:text-slate-100 uppercase tracking-widest">{isProcessing ? 'Analyzing Audio Waves...' : 'Drop Anime Episode Here'}</h3>
            <p className="text-xs text-slate-500 mt-2 max-w-sm font-medium">Character voices will be automatically detected and sliced into frame-accurate samples.</p>
          </div>
        </div>
      ) : (
        <div className="flex-1 overflow-hidden flex flex-col">
          <div className="p-4 bg-slate-100 dark:bg-slate-800/50 flex gap-4 overflow-x-auto scrollbar-hide border-b border-slate-200 dark:border-slate-800">
             {/* Character Quick-Rename Pills */}
             {Array.from(new Set(segments.map(s => s.speaker))).map(speaker => (
               <div key={speaker} className="flex items-center gap-2 bg-white dark:bg-slate-900 px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm shrink-0">
                  <div className="w-2 h-2 rounded-full bg-primary"></div>
                  <input 
                    className="text-[10px] font-black uppercase tracking-widest bg-transparent outline-none w-24"
                    defaultValue={speaker}
                    onBlur={(e) => handleGlobalRename(speaker, e.target.value)}
                  />
               </div>
             ))}
          </div>

          <div className="flex-1 overflow-y-auto p-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 scrollbar-hide">
            {segments.map((seg) => (
              <div key={seg.id} className="bg-white dark:bg-slate-900 rounded-3xl overflow-hidden border border-slate-200 dark:border-slate-800 hover:shadow-2xl hover:-translate-y-1 transition-all group">
                <div className="aspect-video bg-slate-950 relative overflow-hidden">
                   <video 
                     src={`http://localhost:8000/api/segments/${seg.relative_clip_path}`}
                     className="w-full h-full object-cover opacity-60 group-hover:opacity-100 transition-opacity"
                     onMouseEnter={(e) => e.currentTarget.play()}
                     onMouseLeave={(e) => { e.currentTarget.pause(); e.currentTarget.currentTime = 0; }}
                     muted
                     loop
                   />
                   <div className="absolute top-3 left-3 px-2 py-1 bg-black/60 backdrop-blur-md rounded-lg text-[9px] font-mono text-white">
                      {seg.start.toFixed(2)}s - {seg.end.toFixed(2)}s
                   </div>
                   <div className="absolute bottom-3 right-3 w-8 h-8 bg-primary rounded-full flex items-center justify-center text-white scale-0 group-hover:scale-100 transition-transform cursor-pointer">
                      ▶️
                   </div>
                </div>
                <div className="p-5">
                   <div className="flex justify-between items-center mb-3">
                      <input 
                        className="text-[10px] font-black text-primary uppercase tracking-[0.2em] bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded outline-none w-32"
                        value={seg.speaker}
                        onChange={(e) => handleSpeakerChange(seg.id, e.target.value)}
                      />
                      <span className="text-[10px] font-bold text-slate-400">#{seg.id}</span>
                   </div>
                   <p className="text-sm font-medium text-slate-700 dark:text-slate-300 line-clamp-2 leading-relaxed italic">
                      "{seg.text}"
                   </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default SegmentationHub;
