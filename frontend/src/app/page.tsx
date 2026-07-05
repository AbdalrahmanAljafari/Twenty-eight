import Link from "next/link";
import { ArrowRight } from "lucide-react";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { getHealth } from "@/lib/api";
import { copy } from "@/lib/copy";

export default async function HomePage() {
  let apiStatus = "unknown";

  try {
    const health = await getHealth();
    apiStatus = health.status;
  } catch {
    apiStatus = "offline";
  }

  return (
    <main className="mx-auto flex min-h-[calc(100vh-4rem)] max-w-lg flex-col justify-center px-4 py-12">
      <h1 className="text-3xl font-bold text-primary">{copy.home.title}</h1>
      <p className="mt-3 text-muted-foreground">{copy.home.description}</p>

      <Alert
        variant={apiStatus === "ok" ? "success" : "destructive"}
        className="mt-6"
      >
        {apiStatus === "ok" ? "API connected" : "API offline — start backend on port 8000"}
      </Alert>

      <Button asChild size="lg" className="mt-8 w-full sm:w-auto">
        <Link href="/flow">
          {copy.home.startFlow}
          <ArrowRight className="h-4 w-4" />
        </Link>
      </Button>
    </main>
  );
}
