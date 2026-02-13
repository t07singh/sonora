export enum AppMode {
  HUB = 'STUDIO_HUB',
  ANALYTICS = 'ANALYTICS',
  MIXER = 'MIXER_DECK',
  DIRECTOR = 'DIRECTOR_LINK',
  PRODUCTION = 'PRODUCTION_SCALE',
  CORE = 'SYSTEM_CORE',
  WALKTHROUGH = 'STUDIO_WALKTHROUGH',
  SOUND_EDITOR = 'SOUND_EDITOR',
  CLOUD_SYNC = 'CLOUD_SYNC'
}

export type ProjectTemplate = 'ACTION_SHONEN' | 'EMOTIONAL_SLICE' | 'DARK_SEINEN' | 'NONE';

export type SwarmNodeStatus = 'ONLINE' | 'OFFLINE' | 'DEGRADED' | 'SYNC_ACTIVE' | 'PURGING' | 'LOADING' | 'PROVISIONING';

export interface SwarmState {
  separator: SwarmNodeStatus;
  transcriber: SwarmNodeStatus;
  synthesizer: SwarmNodeStatus;
  translator: SwarmNodeStatus;
  vision: SwarmNodeStatus;
}

export interface SystemLog {
  id: string;
  msg: string;
  type: 'info' | 'warn' | 'success' | 'neural' | 'system';
  timestamp: number;
}

export interface Artifact {
  id: string;
  type: 'laugh' | 'gasp' | 'breath' | 'sigh';
  timestamp: number;
  duration: number;
  confidence: number;
  isSelected: boolean;
}

export type StylePriority = 'EMOTION_FIDELITY' | 'LITERAL_ACCURACY' | 'LIP_SYNC_MAX';

export interface DialogueSegment {
  id: string;
  speaker_id: string;
  start: number;
  end: number;
  original: string;
  translation: string;
  morae_count: number;
  syllable_count: number;
  emotion: string;
  prosody_instruction: string;
  stretch_rate: number;
  spectral_match: boolean;
  artifacts: Artifact[];
  nisqa_score?: number;
  surgery_complete?: boolean;
  emotional_priority?: boolean;
  intensity_data?: number[];
}

export interface Project {
  id: string;
  name: string;
  episodes: number;
  completed: number;
  characters: string[];
  lastUpdate: number;
  style_priority?: StylePriority;
  template?: ProjectTemplate;
  director_notes?: string;
}

export interface QueueItem {
  id: string;
  filename: string;
  project: string;
  episode: string;
  priority: 'NORMAL' | 'URGENT';
  status: 'COMPLETED' | 'PROCESSING' | 'QUEUED';
  progress: number;
}

export interface CharacterProfile {
  id: string;
  name: string;
  consistency: number;
  version: string;
  isLocked: boolean;
  traits: string[];
}