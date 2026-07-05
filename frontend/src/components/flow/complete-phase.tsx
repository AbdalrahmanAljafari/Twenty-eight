"use client";

import Link from "next/link";
import { CheckCircle2, RotateCcw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { copy } from "@/lib/copy";

interface CompletePhaseProps {
  onRestart: () => void;
}

export function CompletePhase({ onRestart }: CompletePhaseProps) {
  return (
    <Card className="border-green-200 bg-green-50/50">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-green-800">
          <CheckCircle2 className="h-5 w-5" />
          {copy.complete.title}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <p className="text-sm text-green-900">{copy.complete.message}</p>

        <div className="flex flex-wrap gap-2">
          <Button variant="outline" onClick={onRestart}>
            <RotateCcw className="h-4 w-4" />
            {copy.complete.restart}
          </Button>
          <Button asChild variant="secondary">
            <Link href="/">{copy.complete.home}</Link>
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
