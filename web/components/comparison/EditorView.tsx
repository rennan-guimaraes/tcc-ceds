import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Label } from "@/components/ui/label";
import {
  Plus,
  Trash2,
  Play,
  Zap,
  Eye,
  EyeOff,
  Paperclip,
  X,
  Sparkles,
  FileText,
} from "lucide-react";
import { AVAILABLE_MODELS } from "@/lib/constants";
import { Mode, Prompt, UploadedFile } from "@/lib/types";

interface EditorViewProps {
  mode: Mode;
  setMode: (mode: Mode) => void;
  sessionName: string;
  setSessionName: (name: string) => void;
  blindModeEnabled: boolean;
  setBlindModeEnabled: (enabled: boolean) => void;
  stressIterations: number;
  setStressIterations: (iterations: number) => void;
  selectedModels: string[];
  toggleModel: (modelId: string) => void;
  files: UploadedFile[];
  removeFile: (fileId: string) => void;
  fileInputRef: React.RefObject<HTMLInputElement | null>;
  handleFileUpload: (event: React.ChangeEvent<HTMLInputElement>) => void;
  prompts: Prompt[];
  addPrompt: () => void;
  removePrompt: (id: string) => void;
  updatePrompt: (id: string, field: "title" | "content", value: string) => void;
  runComparison: () => void;
  canRun: boolean;
  isRunning: boolean;
}

export function EditorView({
  mode,
  setMode,
  sessionName,
  setSessionName,
  blindModeEnabled,
  setBlindModeEnabled,
  stressIterations,
  setStressIterations,
  selectedModels,
  toggleModel,
  files,
  removeFile,
  fileInputRef,
  handleFileUpload,
  prompts,
  addPrompt,
  removePrompt,
  updatePrompt,
  runComparison,
  canRun,
  isRunning,
}: EditorViewProps) {
  return (
    <div className="flex flex-1 overflow-hidden">
      {/* Sidebar */}
      <aside className="flex w-80 flex-col border-r border-border bg-card">
        <ScrollArea className="flex-1 p-4">
          <div className="space-y-6">
            <div>
              <Label className="mb-2">Session Name</Label>
              <Input
                placeholder="e.g., Product copy comparison"
                value={sessionName}
                onChange={(e) => setSessionName(e.target.value)}
              />
            </div>

            <Separator />

            <div>
              <Label className="mb-3">Mode</Label>
              <div className="grid grid-cols-2 gap-2">
                <Button
                  variant={mode === "compare" ? "default" : "outline"}
                  size="sm"
                  onClick={() => setMode("compare")}
                >
                  <Sparkles className="mr-2 h-3 w-3" />
                  Compare
                </Button>
                <Button
                  variant={mode === "stress" ? "default" : "outline"}
                  size="sm"
                  onClick={() => setMode("stress")}
                >
                  <Zap className="mr-2 h-3 w-3" />
                  Stress
                </Button>
              </div>
            </div>

            <div className="rounded-md border border-border bg-muted/30 p-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {blindModeEnabled ? (
                    <EyeOff className="h-4 w-4 text-primary" />
                  ) : (
                    <Eye className="h-4 w-4 text-muted-foreground" />
                  )}
                  <Label className="text-sm">Blind Mode</Label>
                </div>
                <Button
                  variant={blindModeEnabled ? "default" : "outline"}
                  size="sm"
                  onClick={() => setBlindModeEnabled(!blindModeEnabled)}
                >
                  {blindModeEnabled ? "ON" : "OFF"}
                </Button>
              </div>
              <p className="mt-2 text-xs text-muted-foreground">
                Hide model names in results for unbiased evaluation
              </p>
            </div>

            {mode === "stress" && (
              <div className="space-y-3 rounded-md border border-border bg-muted/30 p-3">
                <div className="flex items-center gap-2">
                  <Zap className="h-4 w-4 text-primary" />
                  <Label className="text-sm font-semibold">
                    Stress Test Config
                  </Label>
                </div>
                <div>
                  <Label className="mb-2 text-xs text-muted-foreground">
                    Number of Outputs per Model
                  </Label>
                  <Input
                    type="number"
                    min="1"
                    max="20"
                    value={stressIterations}
                    onChange={(e) =>
                      setStressIterations(
                        Math.max(1, Math.min(20, parseInt(e.target.value) || 1))
                      )
                    }
                    className="text-sm"
                  />
                  <p className="mt-1 text-xs text-muted-foreground">
                    Context will be divided across {stressIterations} iterations,
                    reaching 100% at the last output
                  </p>
                </div>
              </div>
            )}

            <Separator />

            <div>
              <div className="mb-3 flex items-center justify-between">
                <Label>Select Models</Label>
                <Badge variant="outline" className="text-xs">
                  {selectedModels.length} selected
                </Badge>
              </div>
              <div className="space-y-2">
                {AVAILABLE_MODELS.map((model) => {
                  const isSelected = selectedModels.includes(model.id);
                  return (
                    <button
                      key={model.id}
                      onClick={() => toggleModel(model.id)}
                      className={`flex w-full items-center gap-3 rounded-md border p-3 text-left transition-colors ${
                        isSelected
                          ? "border-primary bg-primary/10"
                          : "border-border bg-card hover:bg-accent"
                      }`}
                    >
                      <div className={`h-3 w-3 rounded-full ${model.color}`} />
                      <div className="flex-1">
                        <div className="text-sm font-medium">{model.name}</div>
                        <div className="text-xs text-muted-foreground">
                          {model.provider} ·{" "}
                          {(model.maxTokens / 1000).toFixed(0)}k tokens
                        </div>
                      </div>
                      {isSelected && (
                        <div className="h-4 w-4 rounded-full bg-primary" />
                      )}
                    </button>
                  );
                })}
              </div>
            </div>

            <Separator />

            <div>
              <div className="mb-3 flex items-center justify-between">
                <Label>Context Files</Label>
                <Badge variant="outline" className="text-xs">
                  {files.length} file{files.length !== 1 ? "s" : ""}
                </Badge>
              </div>
              <Button
                variant="outline"
                size="sm"
                className="w-full"
                onClick={() => fileInputRef.current?.click()}
              >
                <Paperclip className="mr-2 h-4 w-4" />
                Attach Files
              </Button>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                className="hidden"
                onChange={handleFileUpload}
              />

              {files.length > 0 && (
                <div className="mt-3 space-y-2">
                  {files.map((file) => (
                    <div
                      key={file.id}
                      className="flex items-center gap-2 rounded-md border border-border bg-card p-2 text-xs"
                    >
                      <FileText className="h-4 w-4 text-muted-foreground" />
                      <div className="flex-1">
                        <div className="font-medium">{file.name}</div>
                        <div className="text-muted-foreground">
                          {(file.size / 1024).toFixed(1)} KB
                        </div>
                      </div>
                      <button
                        onClick={() => removeFile(file.id)}
                        className="text-muted-foreground hover:text-foreground"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
              <p className="mt-2 text-xs text-muted-foreground">
                Files will be used as context for all prompts in this session.
              </p>
            </div>
          </div>
        </ScrollArea>

        <div className="border-t border-border p-4">
          <Button
            className="w-full"
            onClick={runComparison}
            disabled={!canRun || isRunning}
            size="lg"
          >
            {isRunning ? (
              <>
                <span className="mr-2 animate-spin">⏳</span>
                Running...
              </>
            ) : (
              <>
                <Play className="mr-2 h-4 w-4" />
                {mode === "stress" ? "Run Stress Test" : "Run Comparison"}
              </>
            )}
          </Button>
          {!canRun && (
            <p className="mt-2 text-center text-xs text-muted-foreground">
              Add at least 1 prompt and select 1 model
            </p>
          )}
        </div>
      </aside>

      {/* Main Editor Area */}
      <main className="flex-1 overflow-hidden">
        <ScrollArea className="h-full">
          <div className="mx-auto max-w-4xl p-6">
            <div className="mb-6 flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold">Prompts</h2>
                <p className="text-sm text-muted-foreground">
                  Create multiple prompts to compare across selected models
                </p>
              </div>
              <Button onClick={addPrompt} variant="outline">
                <Plus className="mr-2 h-4 w-4" />
                Add Prompt
              </Button>
            </div>

            <div className="space-y-4">
              {prompts.map((prompt, index) => (
                <Card key={prompt.id}>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <Badge variant="outline">Prompt {index + 1}</Badge>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removePrompt(prompt.id)}
                        disabled={prompts.length === 1}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <Label className="mb-2 text-muted-foreground">
                        Title (optional)
                      </Label>
                      <Input
                        placeholder="e.g., Technical explanation"
                        value={prompt.title}
                        onChange={(e) =>
                          updatePrompt(prompt.id, "title", e.target.value)
                        }
                      />
                    </div>
                    <div>
                      <Label className="mb-2 text-muted-foreground">
                        Prompt Content
                      </Label>
                      <Textarea
                        placeholder="Enter your prompt here..."
                        value={prompt.content}
                        onChange={(e) =>
                          updatePrompt(prompt.id, "content", e.target.value)
                        }
                        rows={6}
                        className="resize-none font-mono text-sm"
                      />
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </ScrollArea>
      </main>
    </div>
  );
}

