"use client";

import { ArrowLeft, ArrowRight } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { LoadingPipeline } from "@/components/shared/loading-pipeline";
import {
  defaultPipelineProviders,
  ProviderSettings,
  type PipelineProviders,
} from "@/components/flow/provider-settings";
import { FaceCropper } from "@/components/upload/face-cropper";
import { ImageDropzone } from "@/components/upload/image-dropzone";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useFaceGenerate } from "@/hooks/use-face-generate";
import type { GenerateFaceResponse } from "@/lib/types";
import { copy } from "@/lib/copy";
import { FACE_INPUT_SIZE } from "@/lib/crop-image";
import { fileToDataUrl } from "@/lib/utils";

type UploadMode = "select" | "crop" | "ready";

interface FacePhaseProps {
  existingResult?: GenerateFaceResponse | null;
  existingSourcePreview?: string | null;
  onComplete: (result: GenerateFaceResponse, sourcePreview: string) => void;
}

export function FacePhase({
  existingResult,
  existingSourcePreview,
  onComplete,
}: FacePhaseProps) {
  const hasExisting = Boolean(existingResult && existingSourcePreview);
  const [step, setStep] = useState(hasExisting ? 2 : 0);
  const [uploadMode, setUploadMode] = useState<UploadMode>("select");
  const [rawPreviewUrl, setRawPreviewUrl] = useState<string | null>(null);
  const [image, setImage] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(
    existingSourcePreview ?? null,
  );
  const [result, setResult] = useState<GenerateFaceResponse | null>(
    existingResult ?? null,
  );
  const [providers, setProviders] = useState<PipelineProviders>(
    defaultPipelineProviders,
  );

  const mutation = useFaceGenerate({
    onSuccess: (data) => {
      setResult(data);
      setStep(2);
    },
    onError: () => {
      setStep(0);
    },
  });

  useEffect(() => {
    return () => {
      if (rawPreviewUrl?.startsWith("blob:")) URL.revokeObjectURL(rawPreviewUrl);
      if (previewUrl?.startsWith("blob:") && previewUrl !== existingSourcePreview) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [rawPreviewUrl, previewUrl, existingSourcePreview]);

  const handleFileSelect = async (file: File | null) => {
    if (!file) {
      setRawPreviewUrl(null);
      setUploadMode("select");
      return;
    }

    const url = await fileToDataUrl(file);
    setRawPreviewUrl(url);
    setImage(null);
    setPreviewUrl(null);
    setUploadMode("crop");
  };

  const handleCropComplete = (file: File, croppedPreviewUrl: string) => {
    setImage(file);
    setPreviewUrl(croppedPreviewUrl);
    setUploadMode("ready");
  };

  const resetUpload = () => {
    setImage(null);
    setPreviewUrl(null);
    setRawPreviewUrl(null);
    setUploadMode("select");
    mutation.reset();
  };

  const portraitPreview = useMemo(() => {
    if (!result?.portrait_base64) return null;
    if (result.portrait_base64.startsWith("data:")) return result.portrait_base64;
    return `data:image/png;base64,${result.portrait_base64}`;
  }, [result]);

  const startGeneration = () => {
    if (!image) return;
    setStep(1);
    mutation.mutate({
      image,
      extractionProvider: providers.extractionProvider,
      generationProvider: providers.generationProvider,
      validationProvider: providers.validationProvider,
    });
  };

  const regenerate = () => {
    if (!image) return;
    setStep(1);
    mutation.mutate({
      image,
      extractionProvider: providers.extractionProvider,
      generationProvider: providers.generationProvider,
      validationProvider: providers.validationProvider,
    });
  };

  const handleContinueToBody = () => {
    if (!result || !previewUrl) return;
    onComplete(result, previewUrl);
  };

  if (step === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-primary">
            {uploadMode === "crop" ? copy.face.cropTitle : copy.face.uploadTitle}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {uploadMode === "select" && (
            <ImageDropzone
              label={copy.face.uploadTitle}
              value={null}
              previewUrl={null}
              onChange={handleFileSelect}
              disabled={mutation.isPending}
            />
          )}

          {uploadMode === "crop" && rawPreviewUrl && (
            <FaceCropper
              imageSrc={rawPreviewUrl}
              onCropComplete={handleCropComplete}
              onCancel={() => {
                setRawPreviewUrl(null);
                setUploadMode("select");
              }}
            />
          )}

          {uploadMode === "ready" && previewUrl && (
            <div className="space-y-4">
              <div className="mx-auto w-fit rounded-xl border border-primary/40 p-2">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={previewUrl}
                  alt="Cropped face"
                  width={FACE_INPUT_SIZE}
                  height={FACE_INPUT_SIZE}
                  className="rounded-lg"
                />
              </div>
              <p className="text-center text-sm text-muted-foreground">
                {FACE_INPUT_SIZE} × {FACE_INPUT_SIZE} px
              </p>
              <Button type="button" variant="outline" onClick={() => setUploadMode("crop")}>
                {copy.face.cropTitle}
              </Button>
            </div>
          )}

          {mutation.isError && (
            <Alert variant="destructive">{mutation.error.message}</Alert>
          )}

          {uploadMode === "ready" && (
            <ProviderSettings
              value={providers}
              onChange={setProviders}
              disabled={mutation.isPending}
            />
          )}

          {uploadMode !== "crop" && (
            <div className="flex flex-wrap gap-2">
              {uploadMode === "ready" && (
                <Button variant="outline" onClick={resetUpload}>
                  <ArrowLeft className="h-4 w-4" />
                  {copy.face.back}
                </Button>
              )}
              <Button
                onClick={startGeneration}
                disabled={!image || mutation.isPending || uploadMode !== "ready"}
              >
                {copy.face.upload}
                <ArrowRight className="h-4 w-4" />
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    );
  }

  if (step === 1) {
    return (
      <div className="space-y-4">
        <LoadingPipeline title={copy.face.processing} />
        {mutation.isError && (
          <Alert variant="destructive">{mutation.error.message}</Alert>
        )}
      </div>
    );
  }

  if (step === 2 && result) {
    return (
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>{copy.face.resultTitle}</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2">
            {previewUrl && (
              <div>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={previewUrl}
                  alt="Original"
                  className="w-full rounded-lg border object-contain"
                />
              </div>
            )}
            {portraitPreview && (
              <div>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={portraitPreview}
                  alt="Generated"
                  className="w-full rounded-lg border object-contain"
                />
              </div>
            )}
          </CardContent>
        </Card>

        <ProviderSettings
          value={providers}
          onChange={setProviders}
          disabled={mutation.isPending}
        />

        <div className="flex flex-wrap gap-2">
          <Button variant="outline" onClick={() => { resetUpload(); setStep(0); }}>
            <ArrowLeft className="h-4 w-4" />
            {copy.face.back}
          </Button>
          <Button
            variant="outline"
            onClick={regenerate}
            disabled={!image || mutation.isPending}
          >
            {copy.face.regenerate}
          </Button>
          <Button onClick={handleContinueToBody}>
            {copy.face.next}
            <ArrowRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    );
  }

  return null;
}
