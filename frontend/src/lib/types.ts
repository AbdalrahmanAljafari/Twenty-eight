export type Provider = "gemini" | "gpt";

export interface PortraitQAResult {
  passed: boolean;
  score: number;
  failures: string[];
  corrections: string[];
  raw_text: string;
}

export interface GenerateFaceResponse {
  client_id: string;
  portrait_path: string;
  portrait_base64: string;
  source_path: string;
  result_path: string;
  extracted: Record<string, unknown>;
  portrait_qa: PortraitQAResult;
  pipeline: Record<string, string>;
  attempts: number;
}

export interface GenerateBodyResponse {
  message: string;
  client_id: string;
  height_cm: number;
  age: number;
  front_image_size_bytes: number;
  side_image_size_bytes: number;
  front_apose_path: string;
  side_apose_path: string;
  front_apose_base64: string;
  side_apose_base64: string;
  result_path: string;
  pipeline: Record<string, string>;
}

export interface HealthResponse {
  status: string;
}

export interface ApiError {
  detail: string;
}
