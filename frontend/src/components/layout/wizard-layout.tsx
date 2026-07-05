import type { ReactNode } from "react";

import { Stepper, type Step } from "@/components/shared/stepper";

interface WizardLayoutProps {
  title: string;
  description?: string;
  steps: Step[];
  currentStep: number;
  tips?: ReactNode;
  preview?: ReactNode;
  children: ReactNode;
}

export function WizardLayout({
  title,
  description,
  steps,
  currentStep,
  tips,
  preview,
  children,
}: WizardLayoutProps) {
  return (
    <div className="mx-auto max-w-7xl space-y-6 px-4 py-8 md:px-6">
      <div className="space-y-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-primary">{title}</h1>
          {description && (
            <p className="mt-2 max-w-2xl text-muted-foreground">{description}</p>
          )}
        </div>
        <Stepper steps={steps} currentStep={currentStep} />
      </div>

      <div className="grid gap-6 lg:grid-cols-[260px_minmax(0,1fr)_280px]">
        <aside className="order-2 lg:order-1">{tips}</aside>
        <main className="order-1 lg:order-2">{children}</main>
        <aside className="order-3">{preview}</aside>
      </div>
    </div>
  );
}
