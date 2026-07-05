"use client";

import { useMutation } from "@tanstack/react-query";

import { generateFace } from "@/lib/api";
import type { GenerateFaceResponse, Provider } from "@/lib/types";

interface UseFaceGenerateOptions {
  onSuccess?: (data: GenerateFaceResponse) => void;
  onError?: (error: Error) => void;
}

export function useFaceGenerate(options?: UseFaceGenerateOptions) {
  return useMutation({
    mutationFn: (payload: {
      image: File;
      extractionProvider?: Provider;
      generationProvider?: Provider;
      validationProvider?: Provider;
    }) => generateFace(payload),
    onSuccess: options?.onSuccess,
    onError: options?.onError,
  });
}
