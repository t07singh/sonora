import React, { useState, useEffect } from 'react';
import { AppMode, SwarmState, SystemLog as LogType, DialogueSegment, CharacterProfile, ProjectTemplate, StylePriority } from './types';
import Sidebar from './components/Sidebar';
import StudioHub from './components/StudioHub';
import Analytics from './components/Analytics';
import MixerDeck from './components/MixerDeck';
import VoiceLink from './components/VoiceLink';
import ProductionHub from './components/ProductionHub';
import CoreManifest from './components/CoreManifest';
import StudioWalkthrough from './components/StudioWalkthrough';
import SurgicalEditor from './components/SurgicalEditor';
import CloudProvisioning from './components/CloudProvisioning';

const App: React.FC = () => {
  const [activeMode, setActiveMode] = useState<AppMode>(AppMode.HUB);
  const [logs, setLogs] = useState<LogType[]>([]);
  const [auditVisible, setAuditVisible] = useState(false);
  const [wsStatus, setWsStatus] = useState<'CONNECTING' | 'CONNECTED' | 'DISCONNECTED'>('DISCONNECTED');
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    return (localStorage.getItem('sonora-theme') as 'light' | 'dark') || 'light';
  });
  
  const [segments, setSegments] = useState<DialogueSegment[] | null>(null);
  const [activeEditingSeg, setActiveEditingSeg] = useState<DialogueSegment | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeFile, setActiveFile] = useState<File | null>(null);
  const [lastTake, setLastTake] = useState<string | null>(null);
  const [projectTemplate, setProjectTemplate] = useState<ProjectTemplate>('NONE');
  const [stylePriority, setStylePriority] = useState<StylePriority>('EMOTION_FIDELITY');
  const [directorNotes, setDirectorNotes] = useState("");
  
  const [profiles, setProfiles] = useState<CharacterProfile[]>([
    { id: 'v1', name: 'SAKURA', consistency: 0.98, version: 'v1.0-PROD', isLocked: true, traits: ['High-Pitch', 'Feminine', 'Heroic'] },
    { id: 'v2', name: 'HIRO', consistency: 0.95, version: 'v1.2-ALPHA', isLocked: false, traits: ['Heroic', 'Shonen', 'Mid-Range'] },
  ]);

  const [swarmStatus, setSwarmStatus] = useState<SwarmState>({
    separator: 'SYNC_ACTIVE',
    transcriber: 'SYNC_ACTIVE',
    synthesizer: 'SYNC_ACTIVE',
    translator: 'SYNC_ACTIVE',
    vision: 'SYNC_ACTIVE'
  });

  useEffect(() => {
    document.documentElement.className = theme;
    localStorage.setItem('sonora-theme', theme);
  }, [theme]);

  const toggleTheme = () => setTheme(prev => prev === 'light' ? 'dark' : 'light');

  const addLog = (msg: string, type: any = 'info') => {
    setLogs(prev => [{ 
      id: Math.random().toString(), 
      msg, 
      type, 
      timestamp: Date.now() 
    }, ...prev].slice(0, 50));
  };

  const resetProject = () => {
    setSegments(null);
    setLastTake(null);
    setActiveFile(null);
    setProjectTemplate('NONE');
    setDirectorNotes("");
    setActiveMode(AppMode.HUB);
    addLog("Studio Hub: Project state cleared.", "system");
  };

  useEffect(() => {
    setWsStatus('CONNECTED');
    addLog("Neural Link established.", "success");
  }, []);

  const executeFullPipeline = async (videoFile: File) => {
    if (!segments) return;
    setIsProcessing(true);
    await new Promise(r => setTimeout(r, 1200));
    setLastTake(`exports/${videoFile.name.split('.')[0]}_DUBBED.mp4`);
    addLog(`MASTER COMPLETE: Entering Mixer Deck.`, "success");
    setIsProcessing(false);
    setActiveMode(AppMode.MIXER);
  };

  return (
    <div className="flex h-screen overflow-hidden font-sans bg-slate-50 dark:bg-slate-950 transition-colors duration-300">
      <Sidebar activeMode={activeMode} onModeChange={setActiveMode} swarmStatus={swarmStatus} />
      
      <main className="flex-1 flex flex-col min-w-0 border-l border-slate-200 dark:border-slate-800">
        <header className="h-16 px-8 flex items-center justify-between glass z-20 border-b border-slate-200 dark:border-slate-800">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl gradient-btn flex items-center justify-center text-white font-black text-xl shadow-lg">S</div>
            <div>
               <h1 className="font-display font-black text-xl tracking-tight text-slate-800 dark:text-slate-100 uppercase leading-none">
                 {activeMode.replace('_', ' ')}
               </h1>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            <button 
              onClick={toggleTheme}
              className="p-2.5 rounded-xl hover:bg-slate-200 dark:hover:bg-slate-800 transition-colors text-slate-500 dark:text-slate-400"
              title="Toggle Theme"
            >
              {theme === 'light' ? '🌙' : '☀️'}
            </button>

            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
               <div className={`w-2 h-2 rounded-full ${wsStatus === 'CONNECTED' ? 'bg-emerald-400' : 'bg-rose-400'} animate-pulse`}></div>
               <span className="text-[10px] font-black tracking-widest text-slate-500 dark:text-slate-400 uppercase">{wsStatus}</span>
            </div>
            
            <button 
                onClick={() => setAuditVisible(true)}
                className="text-[10px] font-black px-4 py-2 bg-slate-900 dark:bg-slate-100 dark:text-slate-950 text-white rounded-lg hover:opacity-90 transition-all active:scale-95 shadow-sm uppercase tracking-widest"
            >
                Audit
            </button>
          </div>
        </header>

        <div className="flex-1 overflow-hidden relative flex flex-col">
          <div className="flex-1 overflow-hidden bg-white dark:bg-slate-950 transition-colors">
            {activeMode === AppMode.HUB && (
              <StudioHub 
                addLog={addLog} 
                isProcessing={isProcessing}
                setIsProcessing={setIsProcessing}
                segments={segments}
                setSegments={setSegments}
                onOpenSurgicalEditor={(seg) => {
                  setActiveEditingSeg(seg);
                  setActiveMode(AppMode.SOUND_EDITOR);
                }}
                setActiveFile={setActiveFile}
              />
            )}
            {activeMode === AppMode.PRODUCTION && (
              <ProductionHub profiles={profiles} setProfiles={setProfiles} addLog={addLog} />
            )}
            {activeMode === AppMode.ANALYTICS && <Analytics />}
            {activeMode === AppMode.MIXER && (
              <MixerDeck lastTake={lastTake} segments={segments} onProjectFinish={resetProject} directorNotes={directorNotes} setDirectorNotes={setDirectorNotes} />
            )}
            {activeMode === AppMode.DIRECTOR && <VoiceLink addLog={addLog} />}
            {activeMode === AppMode.CORE && <CoreManifest />}
            {activeMode === AppMode.WALKTHROUGH && <StudioWalkthrough />}
            {activeMode === AppMode.CLOUD_SYNC && <CloudProvisioning addLog={addLog} />}
            {activeMode === AppMode.SOUND_EDITOR && activeEditingSeg && (
              <SurgicalEditor 
                segment={activeEditingSeg} 
                onCommit={(updated) => {
                    if (segments) setSegments(segments.map(s => s.id === updated.id ? updated : s));
                    setActiveMode(AppMode.HUB);
                    setActiveEditingSeg(null);
                }} 
                onCancel={() => { setActiveMode(AppMode.HUB); setActiveEditingSeg(null); }}
              />
            )}
          </div>

          {/* SWARM_HANDSHAKE Box - Always Dark as requested in screenshot */}
          <div className="h-44 dark-swarm-box border-t border-blue-500/30 p-6 font-mono relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-blue-500/20 to-transparent"></div>
            <div className="flex justify-between items-center mb-3">
              <span className="text-[10px] font-black text-blue-400 tracking-[0.3em] uppercase">Swarm_Handshake</span>
              <div className="flex items-center gap-3">
                 <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_rgba(52,211,153,0.5)]"></div>
                 <span className="text-[9px] font-bold text-emerald-400 uppercase tracking-widest">Live_Relay</span>
              </div>
            </div>
            <div className="space-y-1.5 overflow-y-auto h-24 pr-2 scrollbar-hide">
              {logs.map(log => (
                <div key={log.id} className="text-[11px] flex gap-4 border-l border-white/5 pl-3 py-0.5 hover:bg-white/5 transition-colors">
                  <span className="text-slate-500 shrink-0">[{new Date(log.timestamp).toLocaleTimeString([], {hour12: false})}]</span>
                  <span className={
                    log.type === 'success' ? 'text-emerald-400' : 
                    log.type === 'warn' ? 'text-rose-400' : 
                    log.type === 'system' ? 'text-blue-400' : 'text-slate-300'
                  }>
                    {log.msg}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {auditVisible && (
          <div className="absolute inset-0 bg-slate-900/60 backdrop-blur-md z-50 flex items-center justify-center animate-in fade-in duration-300">
             <div className="bg-white dark:bg-slate-900 p-8 max-w-md w-full rounded-3xl shadow-2xl border border-slate-200 dark:border-slate-800">
                <h2 className="text-lg font-black uppercase tracking-widest mb-6 dark:text-white flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full bg-blue-500"></div>
                  Node Cluster Audit
                </h2>
                <div className="space-y-4 font-mono text-[11px]">
                  {(Object.entries(swarmStatus) as [string, string][]).map(([name, status]) => (
                    <div key={name} className="flex justify-between border-b border-slate-100 dark:border-slate-800 pb-2">
                      <span className="capitalize text-slate-500 dark:text-slate-400 font-bold">{name}</span>
                      <span className="text-emerald-500 font-black tracking-tighter">{status}</span>
                    </div>
                  ))}
                </div>
                <button onClick={() => setAuditVisible(false)} className="mt-8 w-full py-4 bg-slate-900 dark:bg-slate-100 dark:text-slate-950 text-white rounded-2xl font-black text-[10px] tracking-widest shadow-lg active:scale-95 transition-all">TERMINATE AUDIT</button>
             </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default App;