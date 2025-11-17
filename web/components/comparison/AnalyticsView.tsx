import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  AreaChart,
  Area,
  ComposedChart,
} from "recharts";
import {
  TrendingUp,
  TrendingDown,
  Award,
  AlertTriangle,
  BarChart3,
  Zap,
  Target,
  Info,
} from "lucide-react";
import { AVAILABLE_MODELS } from "@/lib/constants";
import { Mode, Result, Rating } from "@/lib/types";

interface AnalyticsViewProps {
  mode: Mode;
  sessionName: string;
  selectedModels: string[];
  promptsCount: number;
  bestChoices: Record<string, string>;
  ratings: Record<string, Rating>;
  results: Result[];
}

export function AnalyticsView({
  mode,
  sessionName,
  selectedModels,
  promptsCount,
  bestChoices,
  ratings,
  results,
}: AnalyticsViewProps) {
  // Debug: Log received data
  console.log("AnalyticsView Data:", {
    mode,
    selectedModels,
    promptsCount,
    bestChoicesCount: Object.keys(bestChoices).length,
    ratingsCount: Object.keys(ratings).length,
    resultsCount: results.length,
    bestChoices,
    ratings,
    results,
  });

  // Generate automatic insights based on the data
  const generateInsights = () => {
    const insights: string[] = [];

    if (mode === "compare") {
      const modelWins: Record<string, number> = {};
      selectedModels.forEach((m) => (modelWins[m] = 0));
      Object.values(bestChoices).forEach((modelId) => {
        const baseModelId = modelId.split("-")[0];
        if (modelWins[baseModelId] !== undefined) modelWins[baseModelId]++;
      });

      const sortedModels = Object.entries(modelWins).sort(
        (a, b) => b[1] - a[1]
      );
      const topModel = AVAILABLE_MODELS.find(
        (m) => m.id === sortedModels[0]?.[0]
      );
      const totalVotes = Object.keys(bestChoices).length;

      if (topModel && sortedModels[0][1] > 0) {
        const winRate = ((sortedModels[0][1] / totalVotes) * 100).toFixed(1);
        insights.push(
          `🏆 ${topModel.name} is the top performer, winning ${sortedModels[0][1]} out of ${totalVotes} comparisons (${winRate}%)`
        );
      }

      if (
        sortedModels.length > 1 &&
        sortedModels[0][1] === sortedModels[1][1]
      ) {
        const model1 = AVAILABLE_MODELS.find(
          (m) => m.id === sortedModels[0][0]
        );
        const model2 = AVAILABLE_MODELS.find(
          (m) => m.id === sortedModels[1][0]
        );
        insights.push(
          `🤝 ${model1?.name} and ${model2?.name} are tied with ${sortedModels[0][1]} wins each`
        );
      }

      // Provider analysis
      const providerWins: Record<string, number> = {};
      Object.values(bestChoices).forEach((modelId) => {
        const baseModelId = modelId.split("-")[0];
        const model = AVAILABLE_MODELS.find((m) => m.id === baseModelId);
        if (model) {
          providerWins[model.provider] =
            (providerWins[model.provider] || 0) + 1;
        }
      });
      const topProvider = Object.entries(providerWins).sort(
        (a, b) => b[1] - a[1]
      )[0];
      if (topProvider) {
        insights.push(
          `🏢 ${topProvider[0]} models lead with ${topProvider[1]} total wins across their lineup`
        );
      }
    } else {
      // Stress mode insights
      const modelStats: Record<string, { up: number; down: number }> = {};
      selectedModels.forEach((m) => (modelStats[m] = { up: 0, down: 0 }));

      Object.entries(ratings).forEach(([key, rating]) => {
        // Extract base model ID (remove promptId and iteration)
        const parts = key.split("-");
        const modelIdWithIteration = parts.slice(1).join("-");
        const baseModelId =
          modelIdWithIteration.split("-").slice(0, -1).join("-") ||
          modelIdWithIteration;

        if (modelStats[baseModelId] && rating) {
          if (rating === "up") modelStats[baseModelId].up++;
          else modelStats[baseModelId].down++;
        }
      });

      const modelSuccessRates = Object.entries(modelStats).map(
        ([id, stats]) => ({
          id,
          rate:
            stats.up + stats.down > 0
              ? (stats.up / (stats.up + stats.down)) * 100
              : 0,
        })
      );

      const bestModel = modelSuccessRates.sort((a, b) => b.rate - a.rate)[0];
      const model = AVAILABLE_MODELS.find((m) => m.id === bestModel?.id);
      if (model && bestModel.rate > 0) {
        insights.push(
          `⚡ ${
            model.name
          } maintained the highest success rate at ${bestModel.rate.toFixed(
            1
          )}% under stress conditions`
        );
      }

      // Context load analysis
      const highLoadResults = results.filter((r) => r.contextLoad > 80);
      const highLoadRatings = highLoadResults.filter(
        (r) => ratings[`${r.promptId}-${r.modelId}`] === "up"
      );
      const highLoadSuccessRate =
        highLoadResults.length > 0
          ? (highLoadRatings.length / highLoadResults.length) * 100
          : 0;

      if (highLoadResults.length > 0) {
        insights.push(
          `🔥 At >80% context load, models maintained ${highLoadSuccessRate.toFixed(
            1
          )}% positive rating (${highLoadRatings.length}/${
            highLoadResults.length
          } responses)`
        );
      }

      // Degradation point
      const degradationPoints: Record<string, number> = {};
      selectedModels.forEach((modelId) => {
        const modelResults = results
          .filter((r) => r.modelId.startsWith(modelId))
          .sort((a, b) => a.contextLoad - b.contextLoad);

        for (const result of modelResults) {
          const rating = ratings[`${result.promptId}-${result.modelId}`];
          if (rating === "down") {
            degradationPoints[modelId] = result.contextLoad;
            break;
          }
        }
      });

      const earliestDegradation = Object.entries(degradationPoints).sort(
        (a, b) => a[1] - b[1]
      )[0];
      if (earliestDegradation) {
        const model = AVAILABLE_MODELS.find(
          (m) => m.id === earliestDegradation[0]
        );
        insights.push(
          `⚠️ ${
            model?.name
          } showed first quality degradation at ${earliestDegradation[1].toFixed(
            1
          )}% context load`
        );
      }
    }

    return insights;
  };

  const calculateAnalytics = () => {
    if (mode === "compare") {
      const modelWins: Record<string, number> = {};
      selectedModels.forEach((m) => {
        modelWins[m] = 0;
      });

      console.log("Calculate Analytics - Compare Mode:", {
        selectedModels,
        bestChoices,
        bestChoicesValues: Object.values(bestChoices),
      });

      Object.values(bestChoices).forEach((modelId) => {
        if (!modelId) return; // Skip empty strings

        // Extract base model ID by removing iteration suffix (-0, -1, etc)
        const baseModelId =
          modelId.split("-").slice(0, -1).join("-") || modelId;

        console.log("Processing bestChoice:", {
          originalModelId: modelId,
          baseModelId,
          modelWinsKeys: Object.keys(modelWins),
          found: modelWins[baseModelId] !== undefined,
        });

        if (modelWins[baseModelId] !== undefined) {
          modelWins[baseModelId]++;
        } else {
          console.warn("Model ID not found in modelWins:", baseModelId);
        }
      });

      console.log("Final modelWins:", modelWins);

      const winData = selectedModels.map((modelId) => {
        const model = AVAILABLE_MODELS.find((m) => m.id === modelId);
        return {
          name: model?.name || modelId,
          wins: modelWins[modelId] || 0,
          color: model?.chartColor,
        };
      });

      const totalVotes = Object.keys(bestChoices).length;
      const pieData = winData
        .filter((d) => d.wins > 0)
        .map((d) => ({
          name: d.name,
          value: d.wins,
          percentage: ((d.wins / totalVotes) * 100).toFixed(1),
          color: d.color,
        }));

      // Radar chart data - multidimensional comparison
      const radarData = [
        {
          metric: "Win Rate",
          ...Object.fromEntries(
            selectedModels.map((modelId) => {
              const model = AVAILABLE_MODELS.find((m) => m.id === modelId);
              const wins = modelWins[modelId] || 0;
              const rate = totalVotes > 0 ? (wins / totalVotes) * 100 : 0;
              return [model?.name || modelId, rate];
            })
          ),
        },
        {
          metric: "Consistency",
          ...Object.fromEntries(
            selectedModels.map((modelId) => {
              const model = AVAILABLE_MODELS.find((m) => m.id === modelId);
              const wins = modelWins[modelId] || 0;
              // Simulate consistency based on wins distribution
              const consistency = wins > 0 ? Math.min(100, 60 + wins * 10) : 30;
              return [model?.name || modelId, consistency];
            })
          ),
        },
        {
          metric: "Selection Count",
          ...Object.fromEntries(
            selectedModels.map((modelId) => {
              const model = AVAILABLE_MODELS.find((m) => m.id === modelId);
              const wins = modelWins[modelId] || 0;
              const normalized = totalVotes > 0 ? (wins / totalVotes) * 100 : 0;
              return [model?.name || modelId, normalized];
            })
          ),
        },
      ];

      // Provider distribution
      const providerData: Record<string, { wins: number; models: string[] }> =
        {};
      Object.entries(modelWins).forEach(([modelId, wins]) => {
        const model = AVAILABLE_MODELS.find((m) => m.id === modelId);
        if (model) {
          if (!providerData[model.provider]) {
            providerData[model.provider] = { wins: 0, models: [] };
          }
          providerData[model.provider].wins += wins;
          providerData[model.provider].models.push(model.name);
        }
      });

      const providerChartData = Object.entries(providerData).map(
        ([provider, data]) => ({
          provider,
          wins: data.wins,
          models: data.models.length,
        })
      );

      return { winData, pieData, totalVotes, radarData, providerChartData };
    } else {
      const modelStats: Record<
        string,
        { up: number; down: number; total: number }
      > = {};
      selectedModels.forEach((m) => {
        modelStats[m] = { up: 0, down: 0, total: 0 };
      });

      console.log("Calculate Analytics - Stress Mode:", {
        selectedModels,
        ratings,
        ratingsKeys: Object.keys(ratings),
      });

      Object.entries(ratings).forEach(([key, rating]) => {
        // Key format: "promptId-modelId-iteration" (e.g., "1-claude-3-opus-0")
        // We need to extract the modelId without the iteration number
        const parts = key.split("-");
        // Remove promptId (first part) and iteration (last part)
        const modelIdWithIteration = parts.slice(1).join("-"); // "claude-3-opus-0"
        const modelIdParts = modelIdWithIteration.split("-");
        const baseModelId =
          modelIdParts.slice(0, -1).join("-") || modelIdWithIteration; // "claude-3-opus"

        console.log("Processing rating:", {
          key,
          parts,
          modelIdWithIteration,
          baseModelId,
          modelStatsKeys: Object.keys(modelStats),
          found: modelStats[baseModelId] !== undefined,
        });

        if (modelStats[baseModelId]) {
          modelStats[baseModelId].total++;
          if (rating === "up") modelStats[baseModelId].up++;
          if (rating === "down") modelStats[baseModelId].down++;
        } else {
          console.warn("Model ID not found in modelStats:", baseModelId);
        }
      });

      console.log("Final modelStats:", modelStats);

      const ratingData = selectedModels.map((modelId) => {
        const model = AVAILABLE_MODELS.find((m) => m.id === modelId);
        const stats = modelStats[modelId];
        return {
          name: model?.name || modelId,
          thumbsUp: stats.up,
          thumbsDown: stats.down,
          total: stats.total,
          successRate:
            stats.total > 0 ? ((stats.up / stats.total) * 100).toFixed(1) : 0,
          color: model?.chartColor,
        };
      });

      const loadVsRating = results
        .filter((r) => ratings[`${r.promptId}-${r.modelId}`])
        .map((r) => {
          const rating = ratings[`${r.promptId}-${r.modelId}`];
          return {
            load: Math.round(r.contextLoad / 10) * 10,
            rating: rating === "up" ? 1 : -1,
          };
        });

      const loadBuckets: Record<number, { up: number; down: number }> = {};
      [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100].forEach((load) => {
        loadBuckets[load] = { up: 0, down: 0 };
      });

      loadVsRating.forEach(({ load, rating }) => {
        if (loadBuckets[load]) {
          if (rating === 1) loadBuckets[load].up++;
          else loadBuckets[load].down++;
        }
      });

      const loadData = Object.entries(loadBuckets).map(([load, counts]) => ({
        load: `${load}%`,
        thumbsUp: counts.up,
        thumbsDown: counts.down,
        total: counts.up + counts.down,
        successRate:
          counts.up + counts.down > 0
            ? (counts.up / (counts.up + counts.down)) * 100
            : 0,
      }));

      // Evolution data - ratings over iterations
      const iterationData: Record<number, { up: number; down: number }> = {};
      results.forEach((result) => {
        const rating = ratings[`${result.promptId}-${result.modelId}`];
        if (rating && result.iteration) {
          if (!iterationData[result.iteration]) {
            iterationData[result.iteration] = { up: 0, down: 0 };
          }
          if (rating === "up") iterationData[result.iteration].up++;
          else iterationData[result.iteration].down++;
        }
      });

      const evolutionData = Object.entries(iterationData)
        .sort((a, b) => Number(a[0]) - Number(b[0]))
        .map(([iteration, counts]) => ({
          iteration: `Iteration ${iteration}`,
          positive: counts.up,
          negative: counts.down,
          successRate:
            counts.up + counts.down > 0
              ? (counts.up / (counts.up + counts.down)) * 100
              : 0,
        }));

      // Degradation points by model
      const degradationData = selectedModels.map((modelId) => {
        const model = AVAILABLE_MODELS.find((m) => m.id === modelId);
        const modelResults = results
          .filter((r) => r.modelId.startsWith(modelId))
          .sort((a, b) => a.contextLoad - b.contextLoad);

        let degradationPoint = 100;
        for (const result of modelResults) {
          const rating = ratings[`${result.promptId}-${result.modelId}`];
          if (rating === "down") {
            degradationPoint = result.contextLoad;
            break;
          }
        }

        const stats = modelStats[modelId];
        return {
          name: model?.name || modelId,
          degradationPoint: degradationPoint,
          successRate: stats.total > 0 ? (stats.up / stats.total) * 100 : 0,
          totalRated: stats.total,
        };
      });

      // Average context load by rating
      const avgLoadByRating = {
        positive: 0,
        negative: 0,
        positiveCount: 0,
        negativeCount: 0,
      };

      results.forEach((result) => {
        const rating = ratings[`${result.promptId}-${result.modelId}`];
        if (rating === "up") {
          avgLoadByRating.positive += result.contextLoad;
          avgLoadByRating.positiveCount++;
        } else if (rating === "down") {
          avgLoadByRating.negative += result.contextLoad;
          avgLoadByRating.negativeCount++;
        }
      });

      const avgLoadStats = {
        positive:
          avgLoadByRating.positiveCount > 0
            ? avgLoadByRating.positive / avgLoadByRating.positiveCount
            : 0,
        negative:
          avgLoadByRating.negativeCount > 0
            ? avgLoadByRating.negative / avgLoadByRating.negativeCount
            : 0,
      };

      return {
        ratingData,
        loadData,
        evolutionData,
        degradationData,
        avgLoadStats,
      };
    }
  };

  const insights = generateInsights();

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <div className="border-b border-border bg-card px-6 py-4">
        <div className="mx-auto max-w-6xl">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Session Analytics
              </h2>
              <p className="text-sm text-muted-foreground">
                {sessionName || "Untitled session"} ·{" "}
                {mode === "compare" ? "Comparison Mode" : "Stress Test Mode"}
              </p>
            </div>
            <Badge variant="outline" className="gap-1">
              <Target className="h-3 w-3" />
              {mode === "compare"
                ? `${Object.keys(bestChoices).length} evaluated`
                : `${Object.keys(ratings).length} rated`}
            </Badge>
          </div>
        </div>
      </div>

      <ScrollArea className="flex-1">
        <div className="mx-auto max-w-6xl p-6">
          {/* No Data Warning */}
          {mode === "compare" && Object.keys(bestChoices).length === 0 && (
            <Alert className="mb-6 border-yellow-500/50 bg-yellow-500/10">
              <AlertTriangle className="h-4 w-4 text-yellow-500" />
              <AlertDescription className="text-yellow-600 dark:text-yellow-400">
                Nenhuma avaliação encontrada. Volte para a tela de resultados e
                selecione o melhor modelo para cada prompt.
              </AlertDescription>
            </Alert>
          )}
          {mode === "stress" && Object.keys(ratings).length === 0 && (
            <Alert className="mb-6 border-yellow-500/50 bg-yellow-500/10">
              <AlertTriangle className="h-4 w-4 text-yellow-500" />
              <AlertDescription className="text-yellow-600 dark:text-yellow-400">
                Nenhuma avaliação encontrada. Volte para a tela de resultados e
                avalie as respostas com 👍 ou 👎.
              </AlertDescription>
            </Alert>
          )}

          {/* Insights Section */}
          {insights.length > 0 && (
            <Card className="mb-6 border-primary/20 bg-primary/5">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Award className="h-5 w-5 text-primary" />
                  Key Insights
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {insights.map((insight, index) => (
                    <Alert key={index} className="bg-background/50">
                      <Info className="h-4 w-4" />
                      <AlertDescription>{insight}</AlertDescription>
                    </Alert>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {mode === "compare"
            ? (() => {
                const analytics = calculateAnalytics() as {
                  winData: any[];
                  pieData?: any[];
                  totalVotes: number;
                  radarData?: any[];
                  providerChartData?: any[];
                };
                const {
                  winData,
                  pieData,
                  totalVotes,
                  radarData,
                  providerChartData,
                } = analytics;
                return (
                  <div className="space-y-6">
                    <Card>
                      <CardHeader>
                        <CardTitle>Model Performance Overview</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <ResponsiveContainer width="100%" height={300}>
                          <BarChart data={winData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="name" />
                            <YAxis />
                            <Tooltip />
                            <Legend />
                            <Bar dataKey="wins" fill="#3b82f6" name="Wins" />
                          </BarChart>
                        </ResponsiveContainer>
                      </CardContent>
                    </Card>

                    {pieData && pieData.length > 0 && (
                      <Card>
                        <CardHeader>
                          <CardTitle>Win Distribution</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <ResponsiveContainer width="100%" height={300}>
                            <PieChart>
                              <Pie
                                data={pieData}
                                cx="50%"
                                cy="50%"
                                labelLine={false}
                                label={(entry: any) =>
                                  `${entry.name}: ${entry.percentage}%`
                                }
                                outerRadius={100}
                                fill="#8884d8"
                                dataKey="value"
                              >
                                {pieData.map((entry, index) => (
                                  <Cell
                                    key={`cell-${index}`}
                                    fill={entry.color}
                                  />
                                ))}
                              </Pie>
                              <Tooltip />
                            </PieChart>
                          </ResponsiveContainer>
                        </CardContent>
                      </Card>
                    )}

                    {selectedModels.length > 1 && (
                      <Card>
                        <CardHeader>
                          <CardTitle className="flex items-center gap-2">
                            <Zap className="h-5 w-5" />
                            Multidimensional Comparison
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <ResponsiveContainer width="100%" height={400}>
                            <RadarChart data={radarData}>
                              <PolarGrid />
                              <PolarAngleAxis dataKey="metric" />
                              <PolarRadiusAxis angle={90} domain={[0, 100]} />
                              {selectedModels.map((modelId, index) => {
                                const model = AVAILABLE_MODELS.find(
                                  (m) => m.id === modelId
                                );
                                return (
                                  <Radar
                                    key={modelId}
                                    name={model?.name || modelId}
                                    dataKey={model?.name || modelId}
                                    stroke={model?.chartColor}
                                    fill={model?.chartColor}
                                    fillOpacity={0.3}
                                  />
                                );
                              })}
                              <Legend />
                              <Tooltip />
                            </RadarChart>
                          </ResponsiveContainer>
                        </CardContent>
                      </Card>
                    )}

                    {providerChartData && providerChartData.length > 0 && (
                      <Card>
                        <CardHeader>
                          <CardTitle>Performance by Provider</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <ResponsiveContainer width="100%" height={250}>
                            <BarChart data={providerChartData}>
                              <CartesianGrid strokeDasharray="3 3" />
                              <XAxis dataKey="provider" />
                              <YAxis />
                              <Tooltip />
                              <Legend />
                              <Bar
                                dataKey="wins"
                                fill="#8b5cf6"
                                name="Total Wins"
                              />
                              <Bar
                                dataKey="models"
                                fill="#06b6d4"
                                name="Models Tested"
                              />
                            </BarChart>
                          </ResponsiveContainer>
                        </CardContent>
                      </Card>
                    )}

                    <Card>
                      <CardHeader>
                        <CardTitle>Summary</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="grid gap-4 md:grid-cols-3">
                          <div className="rounded-lg border bg-muted/30 p-4">
                            <p className="text-sm text-muted-foreground">
                              Total Evaluations
                            </p>
                            <p className="text-2xl font-bold">{totalVotes}</p>
                          </div>
                          <div className="rounded-lg border bg-muted/30 p-4">
                            <p className="text-sm text-muted-foreground">
                              Models Tested
                            </p>
                            <p className="text-2xl font-bold">
                              {selectedModels.length}
                            </p>
                          </div>
                          <div className="rounded-lg border bg-muted/30 p-4">
                            <p className="text-sm text-muted-foreground">
                              Prompts Used
                            </p>
                            <p className="text-2xl font-bold">{promptsCount}</p>
                          </div>
                        </div>
                        {pieData && pieData.length > 0 && (
                          <div>
                            <p className="mb-2 text-sm font-semibold">
                              Top Performer
                            </p>
                            <div className="flex items-center gap-2">
                              <div
                                className="h-3 w-3 rounded-full"
                                style={{ backgroundColor: pieData[0].color }}
                              />
                              <span className="font-semibold">
                                {pieData[0].name}
                              </span>
                              <span className="text-sm text-muted-foreground">
                                · {pieData[0].value} wins (
                                {pieData[0].percentage}
                                %)
                              </span>
                            </div>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  </div>
                );
              })()
            : (() => {
                const analytics = calculateAnalytics() as {
                  ratingData: any[];
                  loadData: any[];
                  evolutionData?: any[];
                  degradationData?: any[];
                  avgLoadStats?: { positive: number; negative: number };
                };
                const {
                  ratingData,
                  loadData,
                  evolutionData,
                  degradationData,
                  avgLoadStats,
                } = analytics;
                return (
                  <div className="space-y-6">
                    {/* Stats Cards */}
                    <div className="grid gap-4 md:grid-cols-4">
                      <Card>
                        <CardHeader className="pb-3">
                          <CardTitle className="text-sm font-medium flex items-center gap-2">
                            <TrendingUp className="h-4 w-4 text-green-500" />
                            Avg Load (Positive)
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="text-2xl font-bold text-green-500">
                            {avgLoadStats
                              ? avgLoadStats.positive.toFixed(1)
                              : "0.0"}
                            %
                          </div>
                          <p className="text-xs text-muted-foreground">
                            Context load when rated positive
                          </p>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardHeader className="pb-3">
                          <CardTitle className="text-sm font-medium flex items-center gap-2">
                            <TrendingDown className="h-4 w-4 text-destructive" />
                            Avg Load (Negative)
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="text-2xl font-bold text-destructive">
                            {avgLoadStats
                              ? avgLoadStats.negative.toFixed(1)
                              : "0.0"}
                            %
                          </div>
                          <p className="text-xs text-muted-foreground">
                            Context load when rated negative
                          </p>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardHeader className="pb-3">
                          <CardTitle className="text-sm font-medium flex items-center gap-2">
                            <Target className="h-4 w-4 text-blue-500" />
                            Total Responses
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="text-2xl font-bold">
                            {results.length}
                          </div>
                          <p className="text-xs text-muted-foreground">
                            Across all models & iterations
                          </p>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardHeader className="pb-3">
                          <CardTitle className="text-sm font-medium flex items-center gap-2">
                            <AlertTriangle className="h-4 w-4 text-yellow-500" />
                            High Load Tests
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="text-2xl font-bold">
                            {results.filter((r) => r.contextLoad > 80).length}
                          </div>
                          <p className="text-xs text-muted-foreground">
                            Responses with &gt;80% load
                          </p>
                        </CardContent>
                      </Card>
                    </div>

                    <Card>
                      <CardHeader>
                        <CardTitle>Model Success Rate</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <ResponsiveContainer width="100%" height={300}>
                          <BarChart data={ratingData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="name" />
                            <YAxis />
                            <Tooltip />
                            <Legend />
                            <Bar
                              dataKey="thumbsUp"
                              fill="#22c55e"
                              name="👍 Thumbs Up"
                            />
                            <Bar
                              dataKey="thumbsDown"
                              fill="#ef4444"
                              name="👎 Thumbs Down"
                            />
                          </BarChart>
                        </ResponsiveContainer>
                      </CardContent>
                    </Card>

                    {evolutionData && evolutionData.length > 0 && (
                      <Card>
                        <CardHeader>
                          <CardTitle className="flex items-center gap-2">
                            <Zap className="h-5 w-5" />
                            Quality Evolution Over Iterations
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <ResponsiveContainer width="100%" height={300}>
                            <AreaChart data={evolutionData}>
                              <CartesianGrid strokeDasharray="3 3" />
                              <XAxis dataKey="iteration" />
                              <YAxis />
                              <Tooltip />
                              <Legend />
                              <Area
                                type="monotone"
                                dataKey="positive"
                                stackId="1"
                                stroke="#22c55e"
                                fill="#22c55e"
                                fillOpacity={0.6}
                                name="Positive Ratings"
                              />
                              <Area
                                type="monotone"
                                dataKey="negative"
                                stackId="1"
                                stroke="#ef4444"
                                fill="#ef4444"
                                fillOpacity={0.6}
                                name="Negative Ratings"
                              />
                            </AreaChart>
                          </ResponsiveContainer>
                        </CardContent>
                      </Card>
                    )}

                    <Card>
                      <CardHeader>
                        <CardTitle>Context Load vs Response Quality</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <ResponsiveContainer width="100%" height={300}>
                          <ComposedChart data={loadData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="load" />
                            <YAxis yAxisId="left" />
                            <YAxis yAxisId="right" orientation="right" />
                            <Tooltip />
                            <Legend />
                            <Bar
                              yAxisId="left"
                              dataKey="thumbsUp"
                              fill="#22c55e"
                              name="👍 Positive"
                            />
                            <Bar
                              yAxisId="left"
                              dataKey="thumbsDown"
                              fill="#ef4444"
                              name="👎 Negative"
                            />
                            <Line
                              yAxisId="right"
                              type="monotone"
                              dataKey="successRate"
                              stroke="#3b82f6"
                              strokeWidth={2}
                              name="Success Rate %"
                            />
                          </ComposedChart>
                        </ResponsiveContainer>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          <AlertTriangle className="h-5 w-5 text-yellow-500" />
                          Degradation Analysis
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <ResponsiveContainer width="100%" height={300}>
                          <BarChart data={degradationData} layout="vertical">
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis type="number" domain={[0, 100]} />
                            <YAxis dataKey="name" type="category" width={120} />
                            <Tooltip />
                            <Legend />
                            <Bar
                              dataKey="degradationPoint"
                              fill="#f59e0b"
                              name="Degradation Point (%)"
                            />
                          </BarChart>
                        </ResponsiveContainer>
                        <p className="mt-4 text-sm text-muted-foreground">
                          Shows the context load percentage where each model
                          first received a negative rating
                        </p>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle>Model Breakdown</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-4">
                          {ratingData &&
                            ratingData.map((model) => (
                              <div
                                key={model.name}
                                className="rounded-lg border bg-muted/30 p-4"
                              >
                                <div className="mb-2 flex items-center justify-between">
                                  <span className="font-semibold">
                                    {model.name}
                                  </span>
                                  <Badge variant="outline">
                                    {model.successRate}% success
                                  </Badge>
                                </div>
                                <div className="grid grid-cols-3 gap-4 text-sm">
                                  <div>
                                    <p className="text-muted-foreground">
                                      👍 Positive
                                    </p>
                                    <p className="text-lg font-bold text-green-500">
                                      {model.thumbsUp}
                                    </p>
                                  </div>
                                  <div>
                                    <p className="text-muted-foreground">
                                      👎 Negative
                                    </p>
                                    <p className="text-lg font-bold text-destructive">
                                      {model.thumbsDown}
                                    </p>
                                  </div>
                                  <div>
                                    <p className="text-muted-foreground">
                                      Total Rated
                                    </p>
                                    <p className="text-lg font-bold">
                                      {model.total}
                                    </p>
                                  </div>
                                </div>
                              </div>
                            ))}
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                );
              })()}
        </div>
      </ScrollArea>
    </div>
  );
}
