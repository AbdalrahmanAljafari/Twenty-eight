"use client";

import { useMutation } from "@tanstack/react-query";

import { generateBody } from "@/lib/api";
import type { GenerateBodyResponse } from "@/lib/types";

interface UseBodyGenerateOptions {
  onSuccess?: (data: GenerateBodyResponse) => void;
  onError?: (error: Error) => void;
}

export function useBodyGenerate(options?: UseBodyGenerateOptions) {
  return useMutation({
    mutationFn: (payload: {
      frontImage: File;
      sideImage: File;
      heightCm: number;
      age: number;
    }) => generateBody(payload),
    onSuccess: options?.onSuccess,
    onError: options?.onError,
  });
}
