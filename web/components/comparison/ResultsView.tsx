import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Progress } from "@/components/ui/progress";
import {
  Copy,
  ChevronLeft,
  ChevronRight,
  ThumbsUp,
  ThumbsDown,
  AlertCircle,
  CheckCircle2,
  EyeOff,
  Target,
} from "lucide-react";
import { AVAILABLE_MODELS } from "@/lib/constants";
import { Mode, Prompt, Result, Rating } from "@/lib/types";

interface ResultsViewProps {
  mode: Mode;
  sessionName: string;
  stressIterations: number;
  blindModeEnabled: boolean;
  prompts: Prompt[];
  results: Result[];
  currentPromptIndex: number;
  setCurrentPromptIndex: (index: number) => void;
  ratings: Record<string, Rating>;
  toggleRating: (resultKey: string, rating: Rating) => void;
  bestChoices: Record<string, string>;
  selectBest: (promptId: string, modelId: string) => void;
  completionProgress: { current: number; total: number };
}

export function ResultsView({
  mode,
  sessionName,
  stressIterations,
  blindModeEnabled,
  prompts,
  results,
  currentPromptIndex,
  setCurrentPromptIndex,
  ratings,
  toggleRating,
  bestChoices,
  selectBest,
  completionProgress,
}: ResultsViewProps) {
  const currentPrompt = prompts[currentPromptIndex];
  const promptResults = results.filter((r) => r.promptId === currentPrompt?.id);

  const goToPreviousPrompt = () => {
    if (currentPromptIndex > 0) {
      setCurrentPromptIndex(currentPromptIndex - 1);
    }
  };

  const goToNextPrompt = () => {
    if (currentPromptIndex < prompts.length - 1) {
      setCurrentPromptIndex(currentPromptIndex + 1);
    }
  };

  const getBlindLabel = (index: number) => {
    const labels = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"];
    return labels[index] || `${index + 1}`;
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text).catch(() => {});
  };

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <div className="border-b border-border bg-card px-6 py-4">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <div className="flex items-center gap-4">
            <div>
              <h2 className="text-xl font-semibold">
                {currentPrompt?.title || `Prompt ${currentPromptIndex + 1}`}
              </h2>
              <p className="text-sm text-muted-foreground">
                {promptResults.length} response
                {promptResults.length !== 1 ? "s" : ""} ·{" "}
                {sessionName || "Untitled session"}
                {mode === "stress" &&
                  ` · ${stressIterations} iterations per model`}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {blindModeEnabled && (
              <Badge variant="outline" className="gap-1">
                <EyeOff className="h-3 w-3" />
                Blind Mode Active
              </Badge>
            )}

            {completionProgress.total > 0 && (
              <div className="flex items-center gap-2">
                <Badge
                  variant={
                    completionProgress.current === completionProgress.total
                      ? "default"
                      : "outline"
                  }
                  className="gap-1"
                >
                  <Target className="h-3 w-3" />
                  {completionProgress.current} / {completionProgress.total}{" "}
                  {mode === "compare" ? "prompts" : "responses"} evaluated
                </Badge>
              </div>
            )}

            <Separator orientation="vertical" className="mx-2 h-6" />

            <Button
              variant="outline"
              size="sm"
              onClick={goToPreviousPrompt}
              disabled={currentPromptIndex === 0}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>

            <span className="text-sm text-muted-foreground">
              {currentPromptIndex + 1} / {prompts.length}
            </span>

            <Button
              variant="outline"
              size="sm"
              onClick={goToNextPrompt}
              disabled={currentPromptIndex === prompts.length - 1}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      <ScrollArea className="flex-1">
        <div className="mx-auto max-w-6xl p-6">
          <Card className="mb-6 bg-muted/30">
            <CardContent className="p-4">
              <p className="text-sm font-mono">{currentPrompt?.content}</p>
            </CardContent>
          </Card>

          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {promptResults.map((result, index) => {
              const baseModelId = result.modelId.split("-")[0];
              const model = AVAILABLE_MODELS.find((m) => m.id === baseModelId);
              const resultKey = `${result.promptId}-${result.modelId}`;

              const isChosen =
                mode === "compare" &&
                bestChoices[currentPrompt.id] === result.modelId;
              const currentRating = mode === "stress" && ratings[resultKey];

              return (
                <Card
                  key={result.modelId}
                  className={`flex flex-col ${
                    isChosen ? "ring-2 ring-primary" : ""
                  }`}
                >
                  <CardHeader className="pb-3">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        {blindModeEnabled ? (
                          <Badge variant="outline" className="text-xs">
                            Response {getBlindLabel(index)}
                          </Badge>
                        ) : (
                          <div className="flex items-center gap-2">
                            <div
                              className={`h-2 w-2 rounded-full ${model?.color}`}
                            />
                            <span className="text-sm font-semibold">
                              {model?.name}
                            </span>
                          </div>
                        )}
                        {isChosen && (
                          <CheckCircle2 className="h-4 w-4 text-primary" />
                        )}
                      </div>

                      {mode === "stress" && (
                        <div className="space-y-1">
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-muted-foreground">
                              Context Load
                            </span>
                            <span
                              className={`font-semibold ${
                                result.contextLoad > 80
                                  ? "text-destructive"
                                  : result.contextLoad > 50
                                  ? "text-yellow-500"
                                  : "text-green-500"
                              }`}
                            >
                              {result.contextLoad.toFixed(1)}%
                            </span>
                          </div>
                          <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
                            <div
                              className={`h-full transition-all ${
                                result.contextLoad > 80
                                  ? "bg-destructive"
                                  : result.contextLoad > 50
                                  ? "bg-yellow-500"
                                  : "bg-green-500"
                              }`}
                              style={{ width: `${result.contextLoad}%` }}
                            />
                          </div>
                          {result.contextLoad > 80 && (
                            <div className="flex items-center gap-1 text-[10px] text-muted-foreground">
                              <AlertCircle className="h-3 w-3 text-destructive" />
                              <span>High load - quality may degrade</span>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent className="flex flex-1 flex-col space-y-3">
                    <ScrollArea className="flex-1">
                      <div className="h-64">
                        <pre className="whitespace-pre-wrap font-mono text-xs text-muted-foreground">
                          {result.content}
                        </pre>
                      </div>
                    </ScrollArea>

                    {mode === "compare" ? (
                      <div className="flex gap-2">
                        <Button
                          variant={isChosen ? "default" : "outline"}
                          size="sm"
                          className="flex-1"
                          onClick={() =>
                            selectBest(currentPrompt.id, result.modelId)
                          }
                        >
                          {isChosen ? (
                            <>
                              <CheckCircle2 className="mr-2 h-3 w-3" />
                              Best
                            </>
                          ) : (
                            "Mark as Best"
                          )}
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => copyToClipboard(result.content)}
                        >
                          <Copy className="h-4 w-4" />
                        </Button>
                      </div>
                    ) : (
                      <div className="flex gap-2">
                        <Button
                          variant={
                            currentRating === "up" ? "default" : "outline"
                          }
                          size="sm"
                          className="flex-1"
                          onClick={() => toggleRating(resultKey, "up")}
                        >
                          <ThumbsUp
                            className={`h-4 w-4 ${
                              currentRating === "up" ? "fill-current" : ""
                            }`}
                          />
                        </Button>
                        <Button
                          variant={
                            currentRating === "down" ? "default" : "outline"
                          }
                          size="sm"
                          className={`flex-1 ${
                            currentRating === "down"
                              ? "bg-destructive hover:bg-destructive/90"
                              : ""
                          }`}
                          onClick={() => toggleRating(resultKey, "down")}
                        >
                          <ThumbsDown
                            className={`h-4 w-4 ${
                              currentRating === "down" ? "fill-current" : ""
                            }`}
                          />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => copyToClipboard(result.content)}
                        >
                          <Copy className="h-4 w-4" />
                        </Button>
                      </div>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>

          <Card className="mt-6 bg-muted/30">
            <CardHeader>
              <CardTitle className="text-base">
                {mode === "compare" ? "Selection Info" : "Rating Summary"}
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground">
              <p>
                {mode === "compare"
                  ? "Select the best response for each prompt. Only one can be marked as best per prompt."
                  : "Rate each response with 👍 (accurate/good) or 👎 (inaccurate/poor). Track when models start losing quality as context load increases."}
              </p>
            </CardContent>
          </Card>
        </div>
      </ScrollArea>
    </div>
  );
}
