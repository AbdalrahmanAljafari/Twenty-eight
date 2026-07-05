import Link from "next/link";

import { copy } from "@/lib/copy";

export function SiteHeader() {
  return (
    <header className="border-b border-border bg-card/80 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 md:px-6">
        <Link href="/" className="text-lg font-bold text-primary">
          {copy.brand}
        </Link>

        <nav>
          <Link
            href="/"
            className="rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          >
            Home
          </Link>
        </nav>
      </div>
    </header>
  );
}
