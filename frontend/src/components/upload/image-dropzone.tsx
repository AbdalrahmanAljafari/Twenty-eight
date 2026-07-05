"use client";

import { ImagePlus, Upload } from "lucide-react";
import { useCallback } from "react";
import { useDropzone } from "react-dropzone";

import { Button } from "@/components/ui/button";
import { cn, formatBytes } from "@/lib/utils";

interface ImageDropzoneProps {
  label: string;
  value: File | null;
  previewUrl?: string | null;
  onChange: (file: File | null) => void;
  disabled?: boolean;
}

export function ImageDropzone({
  label,
  value,
  previewUrl,
  onChange,
  disabled = false,
}: ImageDropzoneProps) {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      const file = acceptedFiles[0];
      if (file) onChange(file);
    },
    [onChange],
  );

  const { getRootProps, getInputProps, isDragActive, open } = useDropzone({
    onDrop,
    accept: { "image/*": [".png", ".jpg", ".jpeg", ".webp"] },
    maxFiles: 1,
    disabled,
    noClick: true,
    noKeyboard: true,
  });

  return (
    <div className="space-y-3">
      <div
        {...getRootProps()}
        className={cn(
          "relative flex min-h-[280px] flex-col items-center justify-center rounded-xl border-2 border-dashed bg-card p-6 transition-colors",
          isDragActive ? "border-primary bg-accent/40" : "border-primary/40",
          disabled && "opacity-60",
        )}
      >
        <input {...getInputProps()} />

        {previewUrl ? (
          <div className="flex w-full flex-col items-center gap-4">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={previewUrl}
              alt="Preview"
              className="max-h-72 w-full rounded-lg object-contain"
            />
            {value && (
              <p className="text-sm text-muted-foreground">
                {value.name} · {formatBytes(value.size)}
              </p>
            )}
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3 text-center">
            <div className="rounded-full bg-secondary p-4 text-primary">
              <ImagePlus className="h-8 w-8" />
            </div>
            <div>
              <p className="font-medium">{label}</p>
              <p className="text-sm text-muted-foreground">
                Drag and drop an image here, or choose a file
              </p>
            </div>
          </div>
        )}
      </div>

      <div className="flex flex-wrap gap-2">
        <Button type="button" onClick={open} disabled={disabled}>
          <Upload className="h-4 w-4" />
          Choose file
        </Button>
        {value && (
          <Button
            type="button"
            variant="outline"
            onClick={() => onChange(null)}
            disabled={disabled}
          >
            Remove
          </Button>
        )}
      </div>
    </div>
  );
}
