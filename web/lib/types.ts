export type Mode = "compare" | "stress";
export type View = "editor" | "results" | "analytics";
export type Rating = "up" | "down" | null;

export interface Prompt {
  id: string;
  title: string;
  content: string;
}

export interface UploadedFile {
  id: string;
  name: string;
  size: number;
}

export interface Result {
  promptId: string;
  modelId: string;
  content: string;
  contextLoad: number;
  iteration: number;
}

export interface Session {
  id: string;
  name: string;
  date: string;
  promptCount: number;
  modelCount: number;
}

export interface Model {
  id: string;
  name: string;
  provider: string;
  color: string;
  chartColor: string;
  maxTokens: number;
}

