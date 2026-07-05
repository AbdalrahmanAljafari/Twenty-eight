import { Check } from "lucide-react";

import { cn } from "@/lib/utils";

export interface Step {
  id: string;
  label: string;
}

interface StepperProps {
  steps: Step[];
  currentStep: number;
}

export function Stepper({ steps, currentStep }: StepperProps) {
  return (
    <ol className="flex flex-wrap items-center gap-2 md:gap-4">
      {steps.map((step, index) => {
        const isComplete = index < currentStep;
        const isCurrent = index === currentStep;

        return (
          <li key={step.id} className="flex items-center gap-2 md:gap-4">
            <div className="flex items-center gap-2">
              <span
                className={cn(
                  "flex h-8 w-8 items-center justify-center rounded-full border text-sm font-semibold",
                  isComplete && "border-primary bg-primary text-primary-foreground",
                  isCurrent && "border-primary bg-secondary text-secondary-foreground",
                  !isComplete && !isCurrent && "border-border bg-card text-muted-foreground",
                )}
              >
                {isComplete ? <Check className="h-4 w-4" /> : index + 1}
              </span>
              <span
                className={cn(
                  "text-sm font-medium",
                  isCurrent ? "text-foreground" : "text-muted-foreground",
                )}
              >
                {step.label}
              </span>
            </div>
            {index < steps.length - 1 && (
              <div className="hidden h-px w-8 bg-border md:block lg:w-12" />
            )}
          </li>
        );
      })}
    </ol>
  );
}
