import { Model, Session } from "./types";

export const AVAILABLE_MODELS: Model[] = [
  {
    id: "gpt-4",
    name: "GPT-4",
    provider: "OpenAI",
    color: "bg-emerald-500",
    chartColor: "#10b981",
    maxTokens: 8192,
  },
  {
    id: "gpt-4-turbo",
    name: "GPT-4 Turbo",
    provider: "OpenAI",
    color: "bg-emerald-600",
    chartColor: "#059669",
    maxTokens: 128000,
  },
  {
    id: "claude-3-opus",
    name: "Claude 3 Opus",
    provider: "Anthropic",
    color: "bg-orange-500",
    chartColor: "#f97316",
    maxTokens: 200000,
  },
  {
    id: "claude-3-sonnet",
    name: "Claude 3 Sonnet",
    provider: "Anthropic",
    color: "bg-orange-600",
    chartColor: "#ea580c",
    maxTokens: 200000,
  },
  {
    id: "llama-3-70b",
    name: "Llama 3 70B",
    provider: "Meta",
    color: "bg-blue-500",
    chartColor: "#3b82f6",
    maxTokens: 8192,
  },
  {
    id: "gemini-pro",
    name: "Gemini Pro",
    provider: "Google",
    color: "bg-purple-500",
    chartColor: "#a855f7",
    maxTokens: 32768,
  },
];

export const MOCK_SESSIONS: Session[] = [
  {
    id: "1",
    name: "Product descriptions test",
    date: "2024-01-15",
    promptCount: 3,
    modelCount: 2,
  },
  {
    id: "2",
    name: "Code generation comparison",
    date: "2024-01-14",
    promptCount: 5,
    modelCount: 4,
  },
  {
    id: "3",
    name: "Stress test - long context",
    date: "2024-01-13",
    promptCount: 10,
    modelCount: 3,
  },
];

