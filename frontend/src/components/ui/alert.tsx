import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export function Alert({
  className,
  variant = "default",
  ...props
}: HTMLAttributes<HTMLDivElement> & {
  variant?: "default" | "destructive" | "success";
}) {
  return (
    <div
      role="alert"
      className={cn(
        "rounded-lg border px-4 py-3 text-sm",
        variant === "default" && "border-border bg-card",
        variant === "destructive" &&
          "border-destructive/30 bg-destructive/10 text-destructive",
        variant === "success" && "border-green-200 bg-green-50 text-green-800",
        className,
      )}
      {...props}
    />
  );
}
