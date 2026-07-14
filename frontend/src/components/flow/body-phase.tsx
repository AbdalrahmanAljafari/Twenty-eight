"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowLeft, ArrowRight, CheckCircle2 } from "lucide-react";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { ImageDropzone } from "@/components/upload/image-dropzone";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useBodyGenerate } from "@/hooks/use-body-generate";
import type { GenerateBodyResponse } from "@/lib/types";
import { copy } from "@/lib/copy";
import { fileToDataUrl } from "@/lib/utils";

const bodySchema = z.object({
  heightCm: z.coerce.number().min(50).max(300),
  age: z.coerce.number().int().min(1).max(120),
});

type BodyFormValues = z.infer<typeof bodySchema>;

interface BodyPhaseProps {
  clientId?: string | null;
  onPreviewsChange: (front: string | null, side: string | null) => void;
  onComplete: (result: GenerateBodyResponse) => void;
  onBack: () => void;
}

export function BodyPhase({
  clientId,
  onPreviewsChange,
  onComplete,
  onBack,
}: BodyPhaseProps) {
  const [step, setStep] = useState(0);
  const [frontImage, setFrontImage] = useState<File | null>(null);
  const [sideImage, setSideImage] = useState<File | null>(null);
  const [frontPreview, setFrontPreview] = useState<string | null>(null);
  const [sidePreview, setSidePreview] = useState<string | null>(null);

  const form = useForm<BodyFormValues>({
    resolver: zodResolver(bodySchema),
    defaultValues: { heightCm: 170, age: 25 },
  });

  const mutation = useBodyGenerate({
    onSuccess: (data) => onComplete(data),
  });

  useEffect(() => {
    if (!frontImage) {
      setFrontPreview(null);
      return;
    }
    let active = true;
    void fileToDataUrl(frontImage).then((url) => {
      if (active) setFrontPreview(url);
    });
    return () => {
      active = false;
    };
  }, [frontImage]);

  useEffect(() => {
    if (!sideImage) {
      setSidePreview(null);
      return;
    }
    let active = true;
    void fileToDataUrl(sideImage).then((url) => {
      if (active) setSidePreview(url);
    });
    return () => {
      active = false;
    };
  }, [sideImage]);

  useEffect(() => {
    onPreviewsChange(frontPreview, sidePreview);
  }, [frontPreview, sidePreview, onPreviewsChange]);

  const onSubmit = form.handleSubmit((values) => {
    if (!frontImage || !sideImage) return;

    mutation.mutate({
      frontImage,
      sideImage,
      heightCm: values.heightCm,
      age: values.age,
      clientId: clientId ?? undefined,
    });
  });

  if (step === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-primary">{copy.body.frontTitle}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <ImageDropzone
            label="Choose source"
            value={frontImage}
            previewUrl={frontPreview}
            onChange={setFrontImage}
          />

          <div className="flex flex-wrap gap-2">
            <Button variant="outline" onClick={onBack}>
              <ArrowLeft className="h-4 w-4" />
              {copy.body.back}
            </Button>
            <Button onClick={() => setStep(1)} disabled={!frontImage}>
              {copy.body.next}
              <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (step === 1) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-primary">{copy.body.sideTitle}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <ImageDropzone
            label="Choose source"
            value={sideImage}
            previewUrl={sidePreview}
            onChange={setSideImage}
          />
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => setStep(0)}>
              <ArrowLeft className="h-4 w-4" />
              {copy.body.back}
            </Button>
            <Button onClick={() => setStep(2)} disabled={!sideImage}>
              {copy.body.next}
              <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{copy.body.uploadedTitle}</CardTitle>
      </CardHeader>
      <CardContent>
        <form className="space-y-6" onSubmit={onSubmit}>
          <div className="grid grid-cols-2 gap-3">
            {frontPreview && (
              /* eslint-disable-next-line @next/next/no-img-element */
              <img
                src={frontPreview}
                alt="Front"
                className="aspect-[3/4] w-full rounded-lg border object-cover"
              />
            )}
            {sidePreview && (
              /* eslint-disable-next-line @next/next/no-img-element */
              <img
                src={sidePreview}
                alt="Side"
                className="aspect-[3/4] w-full rounded-lg border object-cover"
              />
            )}
          </div>

          <Alert variant="success" className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 shrink-0" />
            {copy.body.validateMessage}
          </Alert>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="heightCm">{copy.body.heightLabel}</Label>
              <div className="relative">
                <Input
                  id="heightCm"
                  type="number"
                  step="0.1"
                  className="pr-12"
                  {...form.register("heightCm")}
                />
                <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">
                  {copy.body.heightUnit}
                </span>
              </div>
              {form.formState.errors.heightCm && (
                <p className="text-sm text-destructive">
                  {form.formState.errors.heightCm.message}
                </p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="age">{copy.body.ageLabel}</Label>
              <div className="relative">
                <Input id="age" type="number" className="pr-14" {...form.register("age")} />
                <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">
                  {copy.body.ageUnit}
                </span>
              </div>
              {form.formState.errors.age && (
                <p className="text-sm text-destructive">{form.formState.errors.age.message}</p>
              )}
            </div>
          </div>

          {mutation.isError && (
            <Alert variant="destructive">{mutation.error.message}</Alert>
          )}

          <div className="flex flex-wrap gap-2">
            <Button type="button" variant="outline" onClick={() => setStep(1)}>
              <ArrowLeft className="h-4 w-4" />
              {copy.body.back}
            </Button>
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? copy.body.submitting : copy.body.submit}
              {!mutation.isPending && <ArrowRight className="h-4 w-4" />}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
