"use client";

import { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  Sparkles,
  History,
  BarChart3,
  Layers,
  ChevronLeft,
} from "lucide-react";
import { AVAILABLE_MODELS, MOCK_SESSIONS } from "@/lib/constants";
import { Mode, View, Prompt, UploadedFile, Result, Rating } from "@/lib/types";
import { EditorView } from "@/components/comparison/EditorView";
import { ResultsView } from "@/components/comparison/ResultsView";
import { AnalyticsView } from "@/components/comparison/AnalyticsView";

export default function Home() {
  const [view, setView] = useState<View>("editor");
  const [mode, setMode] = useState<Mode>("compare");
  const [sessionName, setSessionName] = useState("");
  const [blindModeEnabled, setBlindModeEnabled] = useState(false);
  const [stressIterations, setStressIterations] = useState(5);
  const [selectedModels, setSelectedModels] = useState<string[]>([]);
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [prompts, setPrompts] = useState<Prompt[]>([
    { id: "1", title: "", content: "" },
  ]);
  const [results, setResults] = useState<Result[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [ratings, setRatings] = useState<Record<string, Rating>>({});
  const [bestChoices, setBestChoices] = useState<Record<string, string>>({});
  const [currentPromptIndex, setCurrentPromptIndex] = useState(0);
  const [showSessionsDialog, setShowSessionsDialog] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const getCompletionProgress = () => {
    if (mode === "compare") {
      const validPrompts = prompts.filter((p) => p.content.trim()).length;
      const selectedCount = Object.keys(bestChoices).filter(
        (key) => bestChoices[key]
      ).length;
      return { current: selectedCount, total: validPrompts };
    } else {
      const totalResults = results.length;
      const ratedResults = Object.keys(ratings).filter(
        (key) => ratings[key] !== null
      ).length;
      return { current: ratedResults, total: totalResults };
    }
  };

  const addPrompt = () => {
    setPrompts([
      ...prompts,
      {
        id: Date.now().toString(),
        title: "",
        content: "",
      },
    ]);
  };

  const removePrompt = (id: string) => {
    if (prompts.length > 1) {
      setPrompts(prompts.filter((p) => p.id !== id));
    }
  };

  const updatePrompt = (
    id: string,
    field: "title" | "content",
    value: string
  ) => {
    setPrompts(
      prompts.map((p) => (p.id === id ? { ...p, [field]: value } : p))
    );
  };

  const toggleModel = (modelId: string) => {
    setSelectedModels((prev) =>
      prev.includes(modelId)
        ? prev.filter((m) => m !== modelId)
        : [...prev, modelId]
    );
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const uploadedFiles = Array.from(event.target.files || []);
    const newFiles: UploadedFile[] = uploadedFiles.map((file) => ({
      id: `${Date.now()}-${file.name}`,
      name: file.name,
      size: file.size,
    }));
    setFiles([...files, ...newFiles]);
  };

  const removeFile = (fileId: string) => {
    setFiles(files.filter((f) => f.id !== fileId));
  };

  const calculateContextLoad = (
    modelId: string,
    iteration: number,
    totalIterations: number
  ): number => {
    const baseLoad = (iteration / totalIterations) * 100;
    const variance = Math.random() * 10 - 5;
    return Math.min(100, Math.max(0, baseLoad + variance));
  };

  const runComparison = async () => {
    setIsRunning(true);
    setResults([]);
    setRatings({});
    setBestChoices({});

    await new Promise((resolve) => setTimeout(resolve, 1200));

    const newResults: Result[] = [];
    const iterations = mode === "stress" ? stressIterations : 1;

    prompts.forEach((prompt) => {
      if (!prompt.content.trim()) return;

      selectedModels.forEach((modelId) => {
        const model = AVAILABLE_MODELS.find((m) => m.id === modelId);

        for (let i = 0; i < iterations; i++) {
          const contextLoad =
            mode === "stress"
              ? calculateContextLoad(modelId, i + 1, iterations)
              : 0;

          const iterationSuffix =
            mode === "stress" && iterations > 1
              ? ` (Output ${i + 1}/${iterations})`
              : "";

          newResults.push({
            promptId: prompt.id,
            modelId: `${modelId}-${i}`,
            content: `[Mock response from ${
              model?.name
            }${iterationSuffix}]\n\nPrompt: "${
              prompt.title || "Untitled"
            }"\n\n${
              mode === "stress"
                ? `⚡ STRESS TEST MODE\nContext Load: ${contextLoad.toFixed(
                    1
                  )}%\nIteration: ${
                    i + 1
                  }/${iterations}\nSimulated tokens: ${Math.floor(
                    (contextLoad / 100) * (model?.maxTokens || 8192)
                  )}\n\n`
                : ""
            }This is a simulated response for:\n"${prompt.content.substring(
              0,
              150
            )}${prompt.content.length > 150 ? "..." : ""}"\n\nContext files: ${
              files.length > 0 ? files.map((f) => f.name).join(", ") : "none"
            }\n\n${
              mode === "stress" && contextLoad > 80
                ? "⚠️ WARNING: High context load detected. Response quality may degrade.\n\n"
                : ""
            }In a real implementation, this would be the actual model output. In stress mode, you would see actual degradation as context fills up.`,
            contextLoad,
            iteration: i + 1,
          });
        }
      });
    });

    setResults(newResults);
    setIsRunning(false);
    setView("results");
    setCurrentPromptIndex(0);
  };

  const canRun =
    prompts.some((p) => p.content.trim()) && selectedModels.length > 0;

  const selectBest = (promptId: string, modelId: string) => {
    setBestChoices((prev) => {
      const newValue = prev[promptId] === modelId ? "" : modelId;
      const newChoices = {
        ...prev,
        [promptId]: newValue,
      };
      console.log("selectBest called:", {
        promptId,
        modelId,
        newValue,
        newChoices,
      });
      return newChoices;
    });
  };

  const toggleRating = (resultKey: string, newRating: Rating) => {
    setRatings((prev) => {
      const newValue = prev[resultKey] === newRating ? null : newRating;
      const newRatings = {
        ...prev,
        [resultKey]: newValue,
      };
      console.log("toggleRating called:", {
        resultKey,
        newRating,
        newValue,
        newRatings,
      });
      return newRatings;
    });
  };

  return (
    <div className="flex h-screen flex-col bg-background">
      {/* Top Navigation Bar */}
      <header className="border-b border-border bg-card">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 md:px-6">
          <div className="flex items-center gap-3">
            <Sparkles className="h-6 w-6 text-primary" />
            <div>
              <h1 className="text-lg font-bold">LLM Compare Lab</h1>
              <p className="text-xs text-muted-foreground">
                Compare modelos, prompts e contexto em um só lugar.
              </p>
            </div>
            <Badge variant="outline" className="ml-2 text-xs">
              MVP · Front-end only
            </Badge>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowSessionsDialog(true)}
            >
              <History className="mr-2 h-4 w-4" />
              Sessions
            </Button>
            {view === "results" && (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setView("analytics")}
                >
                  <BarChart3 className="mr-2 h-4 w-4" />
                  Analytics
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setView("editor")}
                >
                  <Layers className="mr-2 h-4 w-4" />
                  Editor
                </Button>
              </>
            )}
            {view === "analytics" && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setView("results")}
              >
                <ChevronLeft className="mr-2 h-4 w-4" />
                Back to Results
              </Button>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      {view === "editor" ? (
        <EditorView
          mode={mode}
          setMode={setMode}
          sessionName={sessionName}
          setSessionName={setSessionName}
          blindModeEnabled={blindModeEnabled}
          setBlindModeEnabled={setBlindModeEnabled}
          stressIterations={stressIterations}
          setStressIterations={setStressIterations}
          selectedModels={selectedModels}
          toggleModel={toggleModel}
          files={files}
          removeFile={removeFile}
          fileInputRef={fileInputRef}
          handleFileUpload={handleFileUpload}
          prompts={prompts}
          addPrompt={addPrompt}
          removePrompt={removePrompt}
          updatePrompt={updatePrompt}
          runComparison={runComparison}
          canRun={canRun}
          isRunning={isRunning}
        />
      ) : view === "results" ? (
        <ResultsView
          mode={mode}
          sessionName={sessionName}
          stressIterations={stressIterations}
          blindModeEnabled={blindModeEnabled}
          prompts={prompts}
          results={results}
          currentPromptIndex={currentPromptIndex}
          setCurrentPromptIndex={setCurrentPromptIndex}
          ratings={ratings}
          toggleRating={toggleRating}
          bestChoices={bestChoices}
          selectBest={selectBest}
          completionProgress={getCompletionProgress()}
        />
      ) : (
        <AnalyticsView
          mode={mode}
          sessionName={sessionName}
          selectedModels={selectedModels}
          promptsCount={prompts.length}
          bestChoices={bestChoices}
          ratings={ratings}
          results={results}
        />
      )}

      {/* Sessions Dialog */}
      <Dialog open={showSessionsDialog} onOpenChange={setShowSessionsDialog}>
        <DialogContent onClose={() => setShowSessionsDialog(false)}>
          <DialogHeader>
            <DialogTitle>Previous Sessions</DialogTitle>
            <DialogDescription>
              Load a previous comparison session to review results
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            {MOCK_SESSIONS.map((session) => (
              <button
                key={session.id}
                className="flex w-full items-start gap-3 rounded-md border border-border p-3 text-left hover:bg-accent"
                onClick={() => {
                  setShowSessionsDialog(false);
                }}
              >
                <History className="mt-0.5 h-4 w-4 text-muted-foreground" />
                <div className="flex-1">
                  <div className="font-medium">{session.name}</div>
                  <div className="text-xs text-muted-foreground">
                    {session.date} · {session.promptCount} prompts ·{" "}
                    {session.modelCount} models
                  </div>
                </div>
              </button>
            ))}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
