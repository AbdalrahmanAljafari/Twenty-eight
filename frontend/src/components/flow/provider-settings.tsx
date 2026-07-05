"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { copy } from "@/lib/copy";
import type { Provider } from "@/lib/types";
import { cn } from "@/lib/utils";

export interface PipelineProviders {
  extractionProvider: Provider;
  generationProvider: Provider;
  validationProvider: Provider;
}

export const defaultPipelineProviders: PipelineProviders = {
  extractionProvider: "gemini",
  generationProvider: "gemini",
  validationProvider: "gemini",
};

interface ProviderSettingsProps {
  value: PipelineProviders;
  onChange: (value: PipelineProviders) => void;
  disabled?: boolean;
  className?: string;
}

const providerOptions: { value: Provider; label: string }[] = [
  { value: "gemini", label: "Gemini" },
  { value: "gpt", label: "GPT" },
];

function ProviderSelect({
  id,
  label,
  value,
  onChange,
  disabled,
}: {
  id: string;
  label: string;
  value: Provider;
  onChange: (value: Provider) => void;
  disabled?: boolean;
}) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={id}>{label}</Label>
      <select
        id={id}
        value={value}
        disabled={disabled}
        onChange={(event) => onChange(event.target.value as Provider)}
        className={cn(
          "flex h-10 w-full rounded-lg border border-input bg-card px-3 py-2 text-sm",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
          "disabled:cursor-not-allowed disabled:opacity-50",
        )}
      >
        {providerOptions.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
}

export function ProviderSettings({
  value,
  onChange,
  disabled = false,
  className,
}: ProviderSettingsProps) {
  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">{copy.providers.title}</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-3 sm:grid-cols-3">
        <ProviderSelect
          id="extraction-provider"
          label={copy.providers.extraction}
          value={value.extractionProvider}
          disabled={disabled}
          onChange={(extractionProvider) =>
            onChange({ ...value, extractionProvider })
          }
        />
        <ProviderSelect
          id="generation-provider"
          label={copy.providers.generation}
          value={value.generationProvider}
          disabled={disabled}
          onChange={(generationProvider) =>
            onChange({ ...value, generationProvider })
          }
        />
        <ProviderSelect
          id="validation-provider"
          label={copy.providers.validation}
          value={value.validationProvider}
          disabled={disabled}
          onChange={(validationProvider) =>
            onChange({ ...value, validationProvider })
          }
        />
      </CardContent>
    </Card>
  );
}
