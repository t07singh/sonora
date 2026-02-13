import React from 'react';

const CoreManifest: React.FC = () => {
  const signalChain = [
    { id: 'INGEST', name: 'Media Ingestion', worker: 'FFmpeg Node', desc: 'Demuxing & Normalization', latency: '4ms' },
    { id: 'ASR', name: 'Transient Whisper', worker: 'INT8 Engine', desc: 'Word-Level Timing Extraction', latency: '450ms' },
    { id: 'LING', name: 'Isometric GPT', worker: 'Gemini 3 Flash', desc: 'Syllabic Adaptation', latency: '120ms' },
    { id: 'PROS', name: 'Prosody Mapper', worker: 'Neural Tokenizer', desc: 'Acoustic Feature Alignment', latency: '15ms' },
    { id: 'SYNTH', name: 'Qwen3 Synthesis', worker: '12Hz Transformer', desc: 'Vocal Reconstruction', latency: '98ms' },
    { id: 'VISION', name: 'Sync-Master', worker: 'Wav2Lip-HQ', desc: '720p HQ Mouth Reconstruction', latency: '2400ms' },
  ];

  return (
    <div className="p-10 h-full overflow-y-auto space-y-12 font-['Inter']">
      <div className="max-w-5xl mx-auto space-y-10">
        <header>
          <h2 className="text-4xl font-['Outfit'] font-black text-slate-800 tracking-tighter uppercase">Nuclear Core Definition</h2>
          <p className="text-slate-400 font-bold uppercase tracking-[0.4em] text-[10px] mt-4">System Schematic // Shipping Ready v5.2</p>
        </header>

        <div className="grid grid-cols-12 gap-10">
          <div className="col-span-8 space-y-6">
            <h3 className="text-xs font-black text-[#FF7EB9] uppercase tracking-widest">Neural Signal Chain</h3>
            <div className="relative">
              {/* Connector Line */}
              <div className="absolute left-6 top-8 bottom-8 w-[2px] bg-gradient-to-b from-[#FF7EB9] via-[#B97EFF] to-[#7EB9FF] opacity-20"></div>
              
              <div className="space-y-4">
                {signalChain.map((step, i) => (
                  <div key={step.id} className="relative pl-16 group">
                    <div className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 bg-white border-2 border-slate-200 rounded-full z-10 group-hover:border-[#FF7EB9] transition-colors shadow-sm">
                      <div className="absolute inset-0.5 rounded-full bg-slate-50 group-hover:bg-[#FF7EB9] group-hover:animate-ping opacity-75"></div>
                    </div>
                    <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-100 group-hover:shadow-xl group-hover:-translate-y-1 transition-all flex justify-between items-center">
                       <div>
                         <p className="text-[8px] font-black text-slate-400 uppercase tracking-widest mb-1">{step.worker}</p>
                         <h4 className="text-lg font-black text-slate-800">{step.name}</h4>
                         <p className="text-[10px] text-slate-400 font-medium">{step.desc}</p>
                       </div>
                       <div className="text-right">
                          <p className="text-[8px] font-black text-slate-300 uppercase">Target Latency</p>
                          <p className="text-xl font-mono font-black text-slate-700">{step.latency}</p>
                       </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="col-span-4 space-y-8">
            <div className="bg-slate-900 rounded-[40px] p-8 text-white shadow-2xl relative overflow-hidden">
               <div className="absolute top-0 right-0 w-32 h-32 bg-[#FF7EB9] opacity-10 blur-[60px]"></div>
               <h3 className="text-sm font-black uppercase tracking-widest mb-8 text-[#FF7EB9]">Nuclear Constraints</h3>
               <div className="space-y-6 font-mono text-[9px] opacity-80">
                  <div className="flex justify-between border-b border-white/5 pb-2">
                    <span className="text-slate-500">BUS_STRUCTURE</span>
                    <span>QUAD_BUS_SURGICAL</span>
                  </div>
                  <div className="flex justify-between border-b border-white/5 pb-2">
                    <span className="text-slate-500">MAX_VRAM_POOL</span>
                    <span>8.2GB_NATIVE</span>
                  </div>
                  <div className="flex justify-between border-b border-white/5 pb-2">
                    <span className="text-slate-500">SAMPLING_RATE</span>
                    <span>44100Hz_HI-FI</span>
                  </div>
                  <div className="flex justify-between border-b border-white/5 pb-2">
                    <span className="text-slate-500">QUANTIZATION</span>
                    <span>FP16_HARDENED</span>
                  </div>
               </div>
               <div className="mt-10 p-5 bg-white/5 rounded-2xl border border-white/10">
                  <p className="text-[8px] font-black text-slate-500 uppercase mb-3">Core Identity Hash</p>
                  <p className="text-[10px] break-all font-mono">SONORA_B0F_99X_12HZ_SIGMA</p>
               </div>
            </div>

            <div className="bg-white rounded-[40px] p-8 border border-slate-100 shadow-sm">
              <h3 className="text-sm font-black uppercase tracking-widest mb-6 text-slate-800">Master Mix Logic</h3>
              <div className="space-y-4">
                 <div className="p-4 bg-slate-50 rounded-2xl">
                    <p className="text-[9px] font-black text-slate-400 uppercase mb-2">Layer 1: Background</p>
                    <p className="text-[10px] font-bold text-slate-600">Preserved original stems (BGM/SFX) via Demucs v4.</p>
                 </div>
                 <div className="p-4 bg-slate-50 rounded-2xl">
                    <p className="text-[9px] font-black text-slate-400 uppercase mb-2">Layer 2: Human Artifacts</p>
                    <p className="text-[10px] font-bold text-slate-600">Isolated breaths, gasps, and laughs re-injected with phase-aligned crossfades.</p>
                 </div>
                 <div className="p-4 bg-[#FF7EB9]/5 rounded-2xl border border-[#FF7EB9]/10">
                    <p className="text-[9px] font-black text-[#FF7EB9] uppercase mb-2">Layer 3: Neural Performance</p>
                    <p className="text-[10px] font-bold text-slate-700">Qwen3-TTS generated performance mapped to director-cue prosody.</p>
                 </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CoreManifest;