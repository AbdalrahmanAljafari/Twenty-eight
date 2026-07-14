"use client";

import { useMemo } from "react";

import { BodyPhase } from "@/components/flow/body-phase";
import { CompletePhase } from "@/components/flow/complete-phase";
import { FacePhase } from "@/components/flow/face-phase";
import { WizardLayout } from "@/components/layout/wizard-layout";
import { TipsPanel } from "@/components/shared/tips-panel";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { copy } from "@/lib/copy";
import { useFlowStore } from "@/lib/flow-store";

export default function FlowPage() {
  const phase = useFlowStore((s) => s.phase);
  const faceResult = useFlowStore((s) => s.faceResult);
  const faceSourcePreview = useFlowStore((s) => s.faceSourcePreview);
  const bodyFrontPreview = useFlowStore((s) => s.bodyFrontPreview);
  const bodySidePreview = useFlowStore((s) => s.bodySidePreview);
  const setPhase = useFlowStore((s) => s.setPhase);
  const setFaceResult = useFlowStore((s) => s.setFaceResult);
  const setBodyPreviews = useFlowStore((s) => s.setBodyPreviews);
  const setBodyResult = useFlowStore((s) => s.setBodyResult);
  const reset = useFlowStore((s) => s.reset);

  const currentStep = phase === "face" ? 0 : phase === "body" ? 1 : 2;

  const portraitPreview = useMemo(() => {
    if (!faceResult?.portrait_base64) return null;
    if (faceResult.portrait_base64.startsWith("data:")) return faceResult.portrait_base64;
    return `data:image/png;base64,${faceResult.portrait_base64}`;
  }, [faceResult]);

  const tips: string[] =
    phase === "face"
      ? [...copy.faceTips]
      : phase === "body"
        ? [...copy.bodyFrontTips, ...copy.bodySideTips]
        : [];

  return (
    <WizardLayout
      title={copy.flow.title}
      description={copy.flow.description}
      steps={[...copy.flow.steps]}
      currentStep={currentStep}
      tips={tips.length > 0 ? <TipsPanel tips={tips} /> : null}
      preview={
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{copy.preview.title}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {phase === "body" && (bodyFrontPreview || bodySidePreview) ? (
              <>
                {bodyFrontPreview && (
                  <div>
                    <p className="mb-2 text-xs text-muted-foreground">{copy.preview.front}</p>
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={bodyFrontPreview}
                      alt="Front"
                      className="w-full rounded-lg border object-contain"
                    />
                  </div>
                )}
                {bodySidePreview && (
                  <div>
                    <p className="mb-2 text-xs text-muted-foreground">{copy.preview.side}</p>
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={bodySidePreview}
                      alt="Side"
                      className="w-full rounded-lg border object-contain"
                    />
                  </div>
                )}
              </>
            ) : portraitPreview ? (
              <div>
                <p className="mb-2 text-xs text-muted-foreground">{copy.preview.facePortrait}</p>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={portraitPreview}
                  alt="Face portrait"
                  className="w-full rounded-lg border object-contain"
                />
              </div>
            ) : faceSourcePreview ? (
              <div>
                <p className="mb-2 text-xs text-muted-foreground">{copy.preview.faceSource}</p>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={faceSourcePreview}
                  alt="Face source"
                  className="w-full rounded-lg border object-contain"
                />
              </div>
            ) : (
              <div className="flex min-h-48 items-center justify-center rounded-lg border border-dashed text-sm text-muted-foreground">
                {copy.preview.empty}
              </div>
            )}
          </CardContent>
        </Card>
      }
    >
      {phase === "face" && (
        <FacePhase
          existingResult={faceResult}
          existingSourcePreview={faceSourcePreview}
          onComplete={(result, sourcePreview) => {
            setFaceResult(result, sourcePreview);
            setPhase("body");
          }}
        />
      )}

      {phase === "body" && (
        <BodyPhase
          clientId={faceResult?.client_id}
          onPreviewsChange={setBodyPreviews}
          onComplete={(result) => {
            setBodyResult(result);
            setPhase("complete");
          }}
          onBack={() => setPhase("face")}
        />
      )}

      {phase === "complete" && <CompletePhase onRestart={reset} />}
    </WizardLayout>
  );
}
