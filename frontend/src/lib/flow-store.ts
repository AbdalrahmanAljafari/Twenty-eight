import { create } from "zustand";

import type { GenerateBodyResponse, GenerateFaceResponse } from "./types";

export type FlowPhase = "face" | "body" | "complete";

interface FlowState {
  phase: FlowPhase;
  faceResult: GenerateFaceResponse | null;
  faceSourcePreview: string | null;
  bodyFrontPreview: string | null;
  bodySidePreview: string | null;
  bodyResult: GenerateBodyResponse | null;
  setPhase: (phase: FlowPhase) => void;
  setFaceResult: (result: GenerateFaceResponse, sourcePreview: string) => void;
  setBodyPreviews: (front: string | null, side: string | null) => void;
  setBodyResult: (result: GenerateBodyResponse) => void;
  reset: () => void;
}

const initialState = {
  phase: "face" as FlowPhase,
  faceResult: null,
  faceSourcePreview: null,
  bodyFrontPreview: null,
  bodySidePreview: null,
  bodyResult: null,
};

export const useFlowStore = create<FlowState>((set) => ({
  ...initialState,
  setPhase: (phase) => set({ phase }),
  setFaceResult: (result, sourcePreview) =>
    set({ faceResult: result, faceSourcePreview: sourcePreview }),
  setBodyPreviews: (front, side) =>
    set({ bodyFrontPreview: front, bodySidePreview: side }),
  setBodyResult: (result) => set({ bodyResult: result }),
  reset: () => set(initialState),
}));
