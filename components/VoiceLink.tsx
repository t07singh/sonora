
import React, { useState, useEffect, useRef } from 'react';

interface VoiceLinkProps {
  addLog: (msg: string, type?: 'info' | 'warn' | 'success') => void;
}

const VoiceLink: React.FC<VoiceLinkProps> = ({ addLog }) => {
  const [isActive, setIsActive] = useState(false);
  const [volume, setVolume] = useState<number[]>(new Array(40).fill(10));
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const animationRef = useRef<number | null>(null);

  const startMonitor = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      const analyser = audioContext.createAnalyser();
      const source = audioContext.createMediaStreamSource(stream);
      
      source.connect(analyser);
      analyser.fftSize = 256;
      
      audioContextRef.current = audioContext;
      analyserRef.current = analyser;
      setIsActive(true);
      addLog("Director AI: Voice Link Active. Monitoring Prosody...", "info");
      
      const bufferLength = analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);
      
      const update = () => {
        analyser.getByteFrequencyData(dataArray);
        // Map top frequencies to the 40 bars
        const step = Math.floor(bufferLength / 40);
        const newVolume = Array.from({length: 40}).map((_, i) => (dataArray[i * step] / 255) * 100);
        setVolume(newVolume);
        animationRef.current = requestAnimationFrame(update);
      };
      update();
    } catch (err) {
      addLog("Director AI: Microphone Access Denied.", "warn");
    }
  };

  const stopMonitor = () => {
    setIsActive(false);
    if (animationRef.current) cancelAnimationFrame(animationRef.current);
    if (streamRef.current) streamRef.current.getTracks().forEach(track => track.stop());
    if (audioContextRef.current) audioContextRef.current.close();
    setVolume(new Array(40).fill(10));
    addLog("Director AI: Monitoring Standby.", "info");
  };

  useEffect(() => {
    return () => stopMonitor();
  }, []);

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-8 space-y-12 animate-in fade-in duration-700">
      <div className="anime-card p-12 max-w-2xl w-full text-center space-y-10 relative overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-2 gradient-btn"></div>
        
        <div className="flex justify-center items-end gap-1.5 h-24">
          {volume.map((v, i) => (
            <div 
              key={i} 
              className={`w-1.5 rounded-full transition-all duration-75 ${isActive ? 'bg-[#FF7EB9]' : 'bg-slate-100'}`}
              style={{ height: isActive ? `${Math.max(6, v)}%` : '6px' }}
            />
          ))}
        </div>

        <div>
          <h2 className="text-3xl font-['Outfit'] font-black text-slate-800">
            {isActive ? 'DIRECTOR HUD: ACTIVE' : 'DIRECTOR HUB: STANDBY'}
          </h2>
          <p className="text-slate-400 text-xs font-bold uppercase tracking-[0.4em] mt-3">
            Real-Time Acoustic Feedback Engine
          </p>
        </div>

        <button 
          onClick={isActive ? stopMonitor : startMonitor}
          className={`px-16 py-4 rounded-2xl font-black tracking-tighter text-sm transition-all shadow-lg hover:scale-105 active:scale-95 ${
            isActive 
              ? 'bg-slate-100 text-slate-400 border border-slate-200' 
              : 'gradient-btn text-white'
          }`}
        >
          {isActive ? 'STOP MONITOR' : 'ENGAGE VOICE LINK'}
        </button>

        <div className="grid grid-cols-2 gap-4">
           <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100">
             <div className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Feedback Path</div>
             <div className="text-sm font-bold text-[#FF7EB9]">{isActive ? 'LIVE_STREAM' : 'BUFFER_WAIT'}</div>
           </div>
           <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100">
             <div className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Input Latency</div>
             <div className="text-sm font-bold text-[#B97EFF]">{isActive ? '< 8ms' : 'N/A'}</div>
           </div>
        </div>
      </div>
    </div>
  );
};

export default VoiceLink;
