"use client";

import { Loader2 } from "lucide-react";
import { useEffect, useState } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";

const DEFAULT_STAGES = [
  "Analyzing image",
  "Extracting features",
  "Generating portrait",
  "Running quality check",
];

/** Stage boundaries (ms): 0–5s, 5–15s, 15–60s, 60s+ */
const STAGE_AT_MS = [0, 5_000, 15_000, 60_000] as const;
const PROGRESS_CAP = 95;
const TICK_MS = 400;

function stageForElapsed(elapsedMs: number, stageCount: number): number {
  if (elapsedMs < STAGE_AT_MS[1]) return 0;
  if (elapsedMs < STAGE_AT_MS[2]) return 1;
  if (elapsedMs < STAGE_AT_MS[3]) return 2;
  return Math.min(stageCount - 1, 3);
}

function progressForElapsed(elapsedMs: number): number {
  if (elapsedMs < STAGE_AT_MS[1]) {
    return 10 + (elapsedMs / STAGE_AT_MS[1]) * 10;
  }
  if (elapsedMs < STAGE_AT_MS[2]) {
    const t = (elapsedMs - STAGE_AT_MS[1]) / (STAGE_AT_MS[2] - STAGE_AT_MS[1]);
    return 20 + t * 15;
  }
  if (elapsedMs < STAGE_AT_MS[3]) {
    const t = (elapsedMs - STAGE_AT_MS[2]) / (STAGE_AT_MS[3] - STAGE_AT_MS[2]);
    return 35 + t * 45;
  }
  const extra = elapsedMs - STAGE_AT_MS[3];
  return Math.min(PROGRESS_CAP, 80 + (extra / 60_000) * 15);
}

interface LoadingPipelineProps {
  title?: string;
  stages?: string[];
  activeStage?: number;
  indeterminate?: boolean;
}

export function LoadingPipeline({
  title = "Processing",
  stages = DEFAULT_STAGES,
  activeStage: controlledStage,
  indeterminate = true,
}: LoadingPipelineProps) {
  const [simulatedStage, setSimulatedStage] = useState(0);
  const [progress, setProgress] = useState(10);

  const activeStage = indeterminate ? simulatedStage : (controlledStage ?? 0);

  useEffect(() => {
    if (!indeterminate) return;

    const startTime = Date.now();
    setSimulatedStage(0);
    setProgress(10);

    const timer = window.setInterval(() => {
      const elapsed = Date.now() - startTime;
      setSimulatedStage(stageForElapsed(elapsed, stages.length));
      setProgress(progressForElapsed(elapsed));
    }, TICK_MS);

    return () => window.clearInterval(timer);
  }, [indeterminate, stages.length]);

  const progressValue = indeterminate
    ? progress
    : ((activeStage + 1) / stages.length) * 100;

  return (
    <Card className="mx-auto w-full max-w-xl">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-primary">
          <Loader2 className="h-5 w-5 animate-spin" />
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <Progress value={progressValue} />

        <ul className="space-y-3">
          {stages.map((stage, index) => {
            const isActive = index === activeStage;
            const isDone = index < activeStage;

            return (
              <li
                key={stage}
                className={cn(
                  "flex items-center gap-3 rounded-lg border px-3 py-2 text-sm transition-colors duration-300",
                  isActive && "border-primary bg-accent/50 font-medium text-foreground",
                  isDone && "border-green-200 bg-green-50 text-green-800",
                  !isActive && !isDone && "border-border text-muted-foreground",
                )}
              >
                <span
                  className={cn(
                    "h-2 w-2 shrink-0 rounded-full transition-colors duration-300",
                    isActive && "animate-pulse bg-primary",
                    isDone && "bg-green-600",
                    !isActive && !isDone && "bg-border",
                  )}
                />
                {stage}
              </li>
            );
          })}
        </ul>
      </CardContent>
    </Card>
  );
}
