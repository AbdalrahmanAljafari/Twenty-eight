import type {
  ApiError,
  GenerateBodyResponse,
  GenerateFaceResponse,
  HealthResponse,
  Provider,
} from "./types";

function getApiBase(): string {
  if (typeof window !== "undefined") {
    return "/api/backend";
  }
  return process.env.BACKEND_URL ?? "http://127.0.0.1:8000";
}

async function parseError(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as ApiError;
    if (typeof payload.detail === "string") return payload.detail;
  } catch {
    // ignore JSON parse errors
  }

  if (response.status === 500) {
    return "Connection to the backend was interrupted. Face generation can take several minutes — restart the frontend dev server after updating next.config.ts, and keep the backend running.";
  }

  return `Request failed with status ${response.status}`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${getApiBase()}${path}`, init);

  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  return (await response.json()) as T;
}

export async function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/health");
}

export interface GenerateFaceOptions {
  image: File;
  extractionProvider?: Provider;
  generationProvider?: Provider;
  validationProvider?: Provider;
}

export async function generateFace(
  options: GenerateFaceOptions,
): Promise<GenerateFaceResponse> {
  const formData = new FormData();
  formData.append("image", options.image);

  if (options.extractionProvider) {
    formData.append("extraction_provider", options.extractionProvider);
  }
  if (options.generationProvider) {
    formData.append("generation_provider", options.generationProvider);
  }
  if (options.validationProvider) {
    formData.append("validation_provider", options.validationProvider);
  }

  return request<GenerateFaceResponse>("/face/generate", {
    method: "POST",
    body: formData,
  });
}

export interface GenerateBodyOptions {
  frontImage: File;
  sideImage: File;
  heightCm: number;
  age: number;
}

export async function generateBody(
  options: GenerateBodyOptions,
): Promise<GenerateBodyResponse> {
  const formData = new FormData();
  formData.append("front_image", options.frontImage);
  formData.append("side_image", options.sideImage);
  formData.append("height_cm", String(options.heightCm));
  formData.append("age", String(options.age));

  return request<GenerateBodyResponse>("/body/generate", {
    method: "POST",
    body: formData,
  });
}
