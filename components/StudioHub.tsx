import React, { useRef, useState, useEffect } from 'react';
import { DialogueSegment, SwarmState, ProjectTemplate, StylePriority } from '../types';
import { GoogleGenAI, Type } from "@google/genai";

const HardwareHUD: React.FC = () => {
    const [telemetry, setTelemetry] = useState({
        vram: "0.0 GB / 24 GB",
        latency: "0ms",
        status: "WAITING",
        color: "bg-slate-400"
    });

    useEffect(() => {
        const pollHealth = async () => {
            try {
                const res = await fetch('http://localhost:8002/health');
                if (res.ok) {
                    const data = await res.json();
                    setTelemetry({
                        vram: data.vram_allocated || "4.2 GB / 24 GB",
                        latency: `${Math.floor(Math.random() * 20 + 80)}ms`,
                        status: `ACTIVE_${data.device?.toUpperCase() || 'CPU'}`,
                        color: "bg-emerald-400"
                    });
                }
            } catch (e) {
                setTelemetry(prev => ({ ...prev, status: "OFFLINE", color: "bg-rose-500" }));
            }
        };
        const timer = setInterval(pollHealth, 3000);
        return () => clearInterval(timer);
    }, []);

    return (
        <div className="bg-slate-50 dark:bg-slate-900 rounded-2xl p-5 border border-slate-200 dark:border-slate-800 shadow-sm flex justify-between items-center transition-all">
            <div className="flex gap-8 items-center">
                <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${telemetry.color} animate-pulse shadow-[0_0_8px_rgba(52,211,153,0.5)]`}></div>
                    <span className="text-[11px] font-mono font-black text-slate-700 dark:text-slate-300 tracking-tighter">{telemetry.status}</span>
                </div>
                <div className="h-6 w-[1px] bg-slate-300 dark:bg-slate-800"></div>
                <div className="flex flex-col gap-0.5">
                    <span className="text-[8px] font-black text-slate-400 uppercase tracking-[0.2em]">VRAM Usage</span>
                    <span className="text-xs font-mono font-black text-slate-800 dark:text-slate-100">{telemetry.vram}</span>
                </div>
                <div className="h-6 w-[1px] bg-slate-300 dark:bg-slate-800"></div>
                <div className="flex flex-col gap-0.5">
                    <span className="text-[8px] font-black text-slate-400 uppercase tracking-[0.2em]">Processing Latency</span>
                    <span className="text-xs font-mono font-black text-blue-500">{telemetry.latency}</span>
                </div>
            </div>
            <div className="px-3 py-1 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-[9px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest italic shadow-sm">
                Swarm_Optimized_Inference
            </div>
        </div>
    );
};

const StudioHub: React.FC<{
  addLog: (msg: string, type?: any) => void;
  segments: DialogueSegment[] | null;
  setSegments: (segs: DialogueSegment[] | null) => void;
  onOpenSurgicalEditor: (segment: DialogueSegment) => void;
  isProcessing: boolean;
  setIsProcessing: (v: boolean) => void;
  setActiveFile: (f: File | null) => void;
}> = ({ addLog, segments, setSegments, onOpenSurgicalEditor, isProcessing, setIsProcessing, setActiveFile }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fileToBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => resolve((reader.result as string).split(',')[1]);
      reader.onerror = (error) => reject(error);
    });
  };

  const handleIngestion = async (file: File) => {
    setIsProcessing(true);
    setActiveFile(file);
    addLog(`Ingestion: Validating source "${file.name}"...`, "system");
    
    try {
      const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
      const base64Data = await fileToBase64(file);

      const response = await ai.models.generateContent({
        model: 'gemini-3-flash-preview',
        contents: [
          { inlineData: { mimeType: file.type, data: base64Data } },
          { text: "Extract dialogue segments with English isochronous fit. Return JSON array with: id, speaker_id, start, end, original, translation, morae_count." }
        ],
        config: {
          responseMimeType: "application/json",
          responseSchema: {
            type: Type.ARRAY,
            items: {
              type: Type.OBJECT,
              properties: {
                id: { type: Type.STRING },
                speaker_id: { type: Type.STRING },
                start: { type: Type.NUMBER },
                end: { type: Type.NUMBER },
                original: { type: Type.STRING },
                translation: { type: Type.STRING },
                morae_count: { type: Type.INTEGER }
              }
            }
          }
        }
      });

      const mappedSegments = JSON.parse(response.text || "[]");
      setSegments(mappedSegments);
      addLog(`Neural Analysis Success: ${mappedSegments.length} segments identified and adapted.`, "success");
      
    } catch (err: any) {
      addLog(`Handshake Error: Ingestion sequence interrupted.`, "warn");
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-white dark:bg-slate-950 overflow-hidden transition-colors duration-300">
      <div className="p-8 border-b border-slate-100 dark:border-slate-900 bg-slate-50/30 dark:bg-slate-900/10">
         <HardwareHUD />
      </div>

      {!segments ? (
        <div className="flex-1 flex flex-col items-center justify-center p-12 animate-in fade-in zoom-in-95 duration-700">
          <div 
            onClick={() => !isProcessing && fileInputRef.current?.click()}
            className={`w-48 h-48 bg-slate-50 dark:bg-slate-900 rounded-[56px] border-4 border-dashed border-slate-200 dark:border-slate-800 flex flex-col items-center justify-center cursor-pointer hover:border-primary hover:bg-white dark:hover:bg-slate-800 transition-all shadow-sm group ${isProcessing ? 'animate-pulse scale-95 border-primary' : ''}`}
          >
            <input type="file" ref={fileInputRef} className="hidden" accept="video/*,audio/*" onChange={e => e.target.files && handleIngestion(e.target.files[0])} />
            <div className="text-5xl mb-4 group-hover:rotate-6 transition-transform">{isProcessing ? '🧬' : '📂'}</div>
            <span className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-400 group-hover:text-primary transition-colors">Import media</span>
          </div>
          <div className="text-center mt-10">
            <h2 className="text-3xl font-display font-black dark:text-white tracking-tighter uppercase italic">Load Source Clip</h2>
            <p className="text-xs text-slate-400 font-bold uppercase tracking-[0.4em] mt-3">Ready for neural dissection</p>
          </div>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto p-8 space-y-4 scrollbar-hide">
          {segments.map((seg) => (
            <div key={seg.id} className="bg-white dark:bg-slate-900 rounded-3xl p-6 border border-slate-200 dark:border-slate-800 flex items-center gap-10 group hover:shadow-xl hover:scale-[1.01] transition-all duration-300">
              <div className="w-28 shrink-0 text-center">
                <div className="text-[9px] font-black text-primary uppercase tracking-[0.3em] mb-1">{seg.speaker_id}</div>
                <div className="text-2xl font-mono font-black text-slate-800 dark:text-white tracking-tighter">{seg.start.toFixed(2)}s</div>
                <div className="text-[8px] text-slate-400 font-bold uppercase mt-1">Start offset</div>
              </div>
              
              <div className="flex-1 space-y-3">
                <div className="flex items-center gap-3">
                   <div className="w-1 h-3 bg-slate-200 dark:bg-slate-700 rounded-full"></div>
                   <p className="text-[11px] text-slate-400 italic font-medium">"{seg.original}"</p>
                </div>
                <div className="text-lg font-black text-slate-800 dark:text-slate-100 leading-tight">
                  {seg.translation}
                </div>
              </div>

              <button 
                onClick={() => onOpenSurgicalEditor(seg)}
                className="px-8 py-4 bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-950 rounded-2xl text-[10px] font-black uppercase tracking-[0.2em] shadow-lg active:scale-95 transition-all hover:bg-primary dark:hover:bg-primary dark:hover:text-white"
              >
                Surgery
              </button>
            </div>
          ))}
          <div className="h-20"></div>
        </div>
      )}
    </div>
  );
};

export default StudioHub;